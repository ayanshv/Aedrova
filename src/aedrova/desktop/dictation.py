"""Explicit, bounded composer dictation with reactive audio feedback and no automatic send."""

import base64
import io
import math
import time
import wave
from uuid import uuid4

from PySide6.QtCore import QEvent, QObject, Qt, QThreadPool, QTimer, Slot
from PySide6.QtGui import QColor, QPainter, QPalette
from PySide6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QWidget

from aedrova.agents.managed import application_origin
from aedrova.desktop.account import AccountJob
from aedrova.desktop.dialogs import button
from aedrova.desktop.meeting_icons import meeting_icon
from aedrova.identity.media import MediaClient
from aedrova.meetings.audio import audio_level
from aedrova.meetings.devices import NativeDevices


class VoiceWave(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(76, 24)
        self.target = self.level = 0.0
        self.phase = 0
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.advance)

    def advance(self):
        self.level += (self.target - self.level) * 0.3
        self.phase += 0.15
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        dark = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        painter.setBrush(QColor("#64A1FF" if dark else "#007AFF"))
        for index in range(11):
            height = 3 + min(1, self.level / 35) * 18 * (
                0.45 + 0.55 * abs(math.sin(self.phase + index * 0.65))
            )
            painter.drawRoundedRect(index * 7.0, (24 - height) / 2, 3.0, height, 1.5, 1.5)


class Dictation(QObject):
    def __init__(self, composer, context):
        super().__init__(composer)
        self.composer, self.context = composer, context
        self.epoch = 0
        self.state = "idle"
        self.source = None
        self.pcm = bytearray()
        self.job = None
        self.scope = None
        self.started = 0
        self.client = None
        self.devices = NativeDevices(composer)
        self.strip = QFrame(composer)
        self.strip.setObjectName("DictationStrip")
        layout = QHBoxLayout(self.strip)
        layout.setContentsMargins(8, 6, 8, 6)
        self.wave = VoiceWave(self.strip)
        layout.addWidget(self.wave)
        self.label = QLabel("Ready to dictate", self.strip)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.label, 1)
        self.cancel_button = button("Cancel", "Discard this dictation", "icon")
        self.cancel_button.clicked.connect(self.cancel)
        layout.addWidget(self.cancel_button)
        self.stop_button = button("Done", "Stop recording and transcribe", "primary")
        self.stop_button.clicked.connect(self.finish)
        layout.addWidget(self.stop_button)
        composer.layout().insertWidget(composer.layout().count() - 1, self.strip)
        self.strip.hide()
        self.mic = button("", "Dictate a message", "icon")
        self.mic.setFixedSize(30, 30)
        self.mic.setIcon(
            meeting_icon("microphone", self.mic.palette().color(QPalette.ColorRole.ButtonText))
        )
        self.mic.setToolTip("Dictate · up to 30 seconds · uses team AI allowance")
        bottom = composer.layout().itemAt(composer.layout().count() - 1).layout()
        bottom.insertWidget(bottom.count() - 1, self.mic)
        self.mic.clicked.connect(self.start)
        self.tick = QTimer(self)
        self.tick.setInterval(100)
        self.tick.timeout.connect(self.check_scope)
        composer.window().installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() in {QEvent.Type.Close, QEvent.Type.Hide}:
            self.cancel()
        elif event.type() == QEvent.Type.PaletteChange:
            self.mic.setIcon(
                meeting_icon("microphone", self.mic.palette().color(QPalette.ColorRole.ButtonText))
            )
        return False

    def valid(self, epoch):
        call = getattr(self.composer.window(), "meeting_call", None)
        return (
            epoch == self.epoch
            and self.scope is not None
            and self.context() == self.scope
            and (call is None or getattr(call, "closed", False))
        )

    def show_state(self, state, text):
        self.state = state
        self.label.setText(text)
        self.strip.show()
        self.stop_button.setVisible(state == "listening")
        self.cancel_button.setVisible(state in {"preparing", "listening", "processing"})
        self.mic.setEnabled(state not in {"preparing", "listening", "processing"})
        if state in {"listening", "processing"}:
            self.wave.target = 12 if state == "processing" else 0
            self.wave.timer.start()
        else:
            self.wave.timer.stop()
            self.wave.target = self.wave.level = 0
            self.wave.update()

    def start(self):
        if self.state in {"preparing", "listening", "processing"}:
            return
        window = self.composer.window()
        call = getattr(window, "meeting_call", None)
        if call is not None and not getattr(call, "closed", False):
            self.show_state("error", "Leave your call before dictating a message.")
            return
        other = getattr(window, "active_dictation", None)
        if (
            other is not None
            and other is not self
            and other.state in {"preparing", "listening", "processing"}
        ):
            self.show_state("error", "Finish your other dictation first.")
            return
        window.active_dictation = self
        self.scope = self.context()
        if not self.scope:
            self.show_state("error", "Sign in and open a conversation to dictate.")
            return
        self.epoch += 1
        epoch = self.epoch
        service = self.scope[0]
        self.show_state("preparing", "Preparing dictation…")
        self.tick.start()

        def prepare():
            client = MediaClient(
                application_origin(), service.client.auth.get_session().access_token
            )
            enabled = client.request("/api/chat/speech/capabilities").get("enabled") is True
            return client, enabled

        def ready(result, success):
            if not self.valid(epoch):
                return
            if not success or not result[1]:
                self.tick.stop()
                self.show_state("error", "Dictation is not enabled yet. You can still type.")
                return
            self.client = result[0]
            self.label.setText(
                "Microphone permission · audio goes to your configured speech provider"
            )
            try:
                self.devices.permission("microphone", lambda granted: self.capture(epoch, granted))
            except Exception:
                self.tick.stop()
                self.show_state("error", "Microphone permission could not be requested.")

        self.run(prepare, ready)

    def capture(self, epoch, granted):
        if not self.valid(epoch):
            return
        if not granted:
            self.tick.stop()
            self.show_state("error", "Allow microphone access in your system privacy settings.")
            return
        try:
            device = QMediaDevices.defaultAudioInput()
            fmt = QAudioFormat()
            fmt.setSampleRate(16000)
            fmt.setChannelCount(1)
            fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
            if device.isNull() or not device.isFormatSupported(fmt):
                raise ValueError("Unsupported microphone")
            self.pcm.clear()
            self.source = QAudioSource(device, fmt, self)
            self.source.setBufferSize(32000)
            # Qt's native QAudio::State signal cannot reliably cross PySide's
            # generic callable conversion on macOS. A no-argument Qt slot drops
            # that unused enum and reads the source's authoritative error state.
            self.source.stateChanged.connect(self.audio_state)
            stream = self.source.start()
            if stream is None:
                raise ValueError("Microphone unavailable")
            stream.readyRead.connect(lambda: self.receive(epoch, stream))
            self.started = time.monotonic()
            self.show_state("listening", "Listening · 0:00 / 0:30")
        except Exception:
            self.release()
            self.tick.stop()
            self.show_state(
                "error", "Microphone unavailable. Check your input device and permission."
            )

    @Slot()
    def audio_state(self):
        if self.valid(self.epoch) and self.source and self.source.error().value:
            self.cancel()
            self.show_state("error", "Microphone stopped. Your message draft is unchanged.")

    def receive(self, epoch, stream):
        if not self.valid(epoch) or self.state != "listening":
            return
        data = bytes(stream.read(32000))
        remaining = 960000 - len(self.pcm)
        self.pcm.extend(data[:remaining])
        self.wave.target = audio_level(data, "Int16")
        if len(self.pcm) >= 960000:
            self.finish()

    def check_scope(self):
        if self.scope is not None and not self.valid(self.epoch):
            self.cancel()
        elif self.state == "listening":
            elapsed = int(time.monotonic() - self.started)
            self.label.setText(f"Listening · 0:{elapsed:02d} / 0:30")
            if elapsed >= 30:
                self.finish()

    def release(self):
        source, self.source = self.source, None
        if source:
            source.stop()
            source.deleteLater()

    def cancel(self):
        self.epoch += 1
        self.release()
        self.pcm.clear()
        self.client = self.scope = None
        self.tick.stop()
        self.wave.timer.stop()
        self.state = "idle"
        self.strip.hide()
        self.mic.setEnabled(True)

    def finish(self):
        if self.state != "listening":
            return
        epoch, scope, client = self.epoch, self.scope, self.client
        self.release()
        if not self.valid(epoch):
            self.cancel()
            return
        pcm = bytes(self.pcm[: len(self.pcm) // 2 * 2])
        self.pcm.clear()
        if len(pcm) < 32000:
            self.tick.stop()
            self.show_state("error", "Speak for at least a second, then try again.")
            return
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(pcm)
        encoded = base64.b64encode(output.getvalue()).decode()
        self.show_state("processing", "Turning voice into text…")

        def finished(result, success):
            if not self.valid(epoch):
                return
            self.tick.stop()
            text = result.get("text") if success else None
            if not isinstance(text, str) or len(text) > 4000:
                self.show_state(
                    "error", "Could not transcribe. Check connection or team AI allowance."
                )
                return
            if not text.strip():
                self.show_state("error", "No speech detected. Try again when ready.")
                return
            # Append safely to the CURRENT draft; never replace typing or send automatically.
            draft = self.composer.editor.toPlainText()
            if len(draft) + len(text) + 1 > 10000:
                self.show_state(
                    "error", "Your draft is too long. Shorten it before dictating again."
                )
                return
            cursor = self.composer.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.insertText((" " if draft and not draft[-1].isspace() else "") + text.strip())
            self.cancel()
            self.composer.editor.setFocus()

        self.run(
            lambda: client.request(
                "/api/chat/speech",
                {"channel": scope[3], "identifier": str(uuid4()), "audio": encoded},
            ),
            finished,
        )

    def run(self, operation, completed):
        job = AccountJob(operation)
        self.job = job
        job.signals.finished.connect(completed)
        QThreadPool.globalInstance().start(job)
