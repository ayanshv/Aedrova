"""Explicit voice attachments: record locally, preview, then share privately."""

import io
import tempfile
import time
import wave
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QUrl, Signal, Slot
from PySide6.QtMultimedia import QAudioOutput, QAudioSource, QMediaDevices, QMediaPlayer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget
from shiboken6 import delete

from aedrova.desktop.dialogs import button
from aedrova.desktop.dictation import Dictation
from aedrova.desktop.voice_pcm import VoicePCM
from aedrova.identity.file_policy import inspect_file
from aedrova.meetings.audio import audio_level

MAX_SECONDS = 300
MAX_PCM = MAX_SECONDS * 32000


def encode_voice(pcm):
    if not 32000 <= len(pcm) <= MAX_PCM or len(pcm) % 2:
        raise ValueError("Record between 1 second and 5 minutes.")
    result = io.BytesIO()
    with wave.open(result, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(pcm)
    return result.getvalue()


def clock(milliseconds):
    seconds = max(0, milliseconds // 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"


class VoicePlayer(QWidget):
    changed = Signal()

    def __init__(self, data, parent=None):
        super().__init__(parent)
        inspect_file("voice.wav", data)
        self.disposed = False
        self.temporary = tempfile.TemporaryDirectory(prefix="aedrova-voice-")
        self.path = Path(self.temporary.name) / "voice.wav"
        self.path.write_bytes(data)
        self.output = QAudioOutput(self)
        self.output.setVolume(0.8)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.output)
        self.play = button("Play", "Play voice message", "outline")
        self.play.clicked.connect(self.toggle)
        self.elapsed = QLabel("0:00")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.play)
        row.addWidget(self.elapsed)
        self.player.positionChanged.connect(self.update_state)
        self.player.durationChanged.connect(self.update_state)
        self.player.playbackStateChanged.connect(self.update_state)
        self.player.errorOccurred.connect(self.failed)
        self.player.setSource(QUrl.fromLocalFile(str(self.path)))

    def toggle(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    @Slot()
    def update_state(self):
        playing = self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        self.play.setText("Pause" if playing else "Play")
        self.play.setAccessibleName("Pause voice message" if playing else "Play voice message")
        self.elapsed.setText(f"{clock(self.player.position())} / {clock(self.player.duration())}")
        self.changed.emit()

    @Slot()
    def failed(self):
        self.elapsed.setText("Audio unavailable. Try again.")
        self.changed.emit()

    def dispose(self):
        if self.disposed:
            return
        self.disposed = True
        self.player.blockSignals(True)
        self.player.stop()
        self.player.setSource(QUrl())
        self.player.setAudioOutput(None)
        # Windows media backends may retain a file handle after setSource(empty).
        # Destroy the backend synchronously before removing the private recording;
        # deleteLater alone leaves it locked until the next event-loop pass.
        delete(self.player)
        self.temporary.cleanup()
        self.deleteLater()


class VoiceMessage(Dictation):
    def __init__(self, composer, context, share):
        super().__init__(composer, context)
        self.share = share
        self.preview = None
        self.recording = b""
        self.mic.setAccessibleName("Record a voice message")
        self.mic.setToolTip("Voice message · record, preview, then send · up to 5 minutes")
        self.cancel_button.setAccessibleName("Discard voice message")
        self.cancel_button.setToolTip("Discard voice message")
        self.stop_button.setAccessibleName("Finish voice recording")
        self.stop_button.setToolTip("Finish voice recording and preview")
        self.send_voice = button("Send voice", "Send voice message", "primary")
        self.send_voice.clicked.connect(self.send_recording)
        self.strip.layout().addWidget(self.send_voice)
        self.send_voice.hide()

    def start(self):
        if self.state in {"preparing", "listening", "processing", "preview", "uploading"}:
            return
        window = self.composer.window()
        call = getattr(window, "meeting_call", None)
        if call is not None and not getattr(call, "closed", False):
            self.show_state("error", "Leave your call before recording a voice message.")
            return
        other = getattr(window, "active_dictation", None)
        if (
            other is not None
            and other is not self
            and other.state in {"preparing", "listening", "preview", "uploading"}
        ):
            self.show_state("error", "Finish your other voice message first.")
            return
        self.scope = self.context()
        if not self.scope:
            self.show_state("error", "Sign in and open a conversation to record.")
            return
        window.active_dictation = self
        self.epoch += 1
        epoch = self.epoch
        self.show_state("preparing", "Microphone permission · recording stays local until you send")
        self.tick.start()
        self.devices.permission("microphone", lambda granted: self.capture(epoch, granted))

    def capture(self, epoch, granted):
        if not self.valid(epoch):
            return
        if not granted:
            self.tick.stop()
            self.show_state("error", "Allow microphone access in your system privacy settings.")
            return
        try:
            device = QMediaDevices.defaultAudioInput()
            fmt = device.preferredFormat()
            if device.isNull() or not device.isFormatSupported(fmt):
                raise ValueError("Unsupported microphone")
            self.converter = VoicePCM(fmt.sampleRate(), fmt.channelCount(), fmt.sampleFormat().name)
            self.pcm.clear()
            self.source = QAudioSource(device, fmt, self)
            self.source.setBufferSize(65536)
            self.source.stateChanged.connect(self.audio_state)
            self.stream = self.source.start()
            if self.stream is None or self.source.error().value:
                raise ValueError("Microphone unavailable")
            self.stream.readyRead.connect(lambda: self.receive(epoch, self.stream))
            self.started = time.monotonic()
            self.show_state("listening", "Recording · 0:00 / 5:00")
        except Exception:
            self.release()
            self.tick.stop()
            self.show_state("error", "Microphone unavailable. Check input device and permission.")

    def receive(self, epoch, stream):
        if not self.valid(epoch) or self.state != "listening":
            return
        data = self.converter.convert(bytes(stream.read(65536)))
        self.pcm.extend(data[: MAX_PCM - len(self.pcm)])
        self.wave.target = audio_level(data, "Int16")
        if len(self.pcm) >= MAX_PCM:
            self.finish()

    def check_scope(self):
        if self.scope is not None and not self.valid(self.epoch):
            self.cancel()
        elif self.state == "listening":
            elapsed = int(time.monotonic() - self.started)
            self.label.setText(f"Recording · {clock(elapsed * 1000)} / 5:00")
            if elapsed >= MAX_SECONDS:
                self.finish()

    def show_state(self, state, text):
        super().show_state(state, text)
        if hasattr(self, "send_voice"):
            self.send_voice.setVisible(state == "preview")
        if state in {"preview", "uploading"}:
            self.cancel_button.show()
            self.mic.setEnabled(False)

    def finish(self):
        if self.state != "listening":
            return
        self.release()
        try:
            self.recording = encode_voice(self.pcm)
        except ValueError:
            self.pcm.clear()
            self.tick.stop()
            self.show_state("error", "Record at least one second, then try again.")
            return
        self.pcm.clear()
        self.preview = VoicePlayer(self.recording, self.strip)
        self.strip.layout().insertWidget(0, self.preview)
        self.wave.hide()
        self.show_state("preview", "Ready to send · only shared when you choose")
        self.tick.start()  # Scope changes discard even a finished recording.

    def send_recording(self):
        if self.state != "preview" or not self.valid(self.epoch):
            self.cancel()
            return
        seconds = (len(self.recording) - 44) // 32000
        epoch = self.epoch

        def completed(result):
            if not self.valid(epoch):
                return
            if result.get("shared"):
                self.cancel()
            else:
                self.show_state("preview", "Not sent · recording kept. Try again or discard.")

        if self.share(
            f"voice-message-{seconds}s.wav",
            self.recording,
            self.scope[-1],
            completed,
            lambda: not self.valid(epoch),
        ):
            self.show_state("uploading", "Sharing your voice message…")
            self.strip.hide()  # The conversation now shows the pending voice card.

    def cancel(self):
        super().cancel()
        self.converter = None
        self.stream = None
        self.recording = b""
        if getattr(self, "preview", None):
            self.preview.dispose()
            self.preview = None
        if hasattr(self, "send_voice"):
            self.send_voice.hide()
        self.wave.show()


class VoicePlayback(QObject):
    """One in-chat playback; discard private cache when scope or window changes."""

    def __init__(self, window, connected, scope):
        super().__init__(window)
        self.window, self.connected, self.scope = window, connected, scope
        self.player = None
        self.identifier = None
        self.generation = 0
        window.installEventFilter(self)
        from PySide6.QtCore import QTimer

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.check_scope)
        self.timer.start()
        self.origin = None

    def eventFilter(self, watched, event):
        if event.type() in {QEvent.Type.Hide, QEvent.Type.Close}:
            self.clear()
        return False

    def check_scope(self):
        if self.origin is not None and self.scope() != self.origin:
            self.clear()

    def clear(self):
        self.generation += 1
        if self.player:
            self.player.dispose()
        self.player = self.identifier = self.origin = None
        self.paint()

    def paint(self):
        for view in (self.window.messages, self.window.thread_messages):
            view.voice_playback = {
                "id": self.identifier,
                "playing": bool(
                    self.player
                    and self.player.player.playbackState()
                    == QMediaPlayer.PlaybackState.PlayingState
                ),
                "position": self.player.player.position() if self.player else 0,
                "duration": self.player.player.duration() if self.player else 0,
            }
            view.viewport().update()

    def toggle(self, identifier):
        if self.identifier == identifier and self.player:
            self.player.toggle()
            return
        self.clear()
        connected = self.connected()
        if not connected:
            return
        self.origin = self.scope()
        epoch = self.generation
        self.identifier = identifier
        self.paint()
        service = connected.account.service

        def loaded(data):
            if epoch != self.generation or self.scope() != self.origin:
                return
            try:
                if not isinstance(data, bytes):
                    raise ValueError("Unavailable audio")
                self.player = VoicePlayer(data, self.window)
                self.player.hide()
                self.player.changed.connect(self.paint)
                self.player.toggle()
            except (ValueError, OSError):
                self.clear()
                self.window.notify("This voice message could not be played.")

        def download():
            try:
                return service.download_attachment(identifier)
            except Exception:
                return None

        if not connected.enqueue(("voice-play", identifier), download, loaded):
            self.clear()
