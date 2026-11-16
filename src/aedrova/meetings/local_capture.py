"""Visible, consent-triggered local audio capture. No network or hosted speech fallback."""

import json
import queue
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal

from aedrova.agents.runtime import environment
from aedrova.meetings.local_speech import Transcriber, ready


def helper_path():
    source_bundle = Path(sys.executable).parent.parent / "Helpers/aedrova-meeting-audio"
    if source_bundle.is_file():
        return source_bundle
    bundled = Path(__file__).parents[1] / "desktop/assets/bin/aedrova-meeting-audio"
    if bundled.is_file():
        return bundled
    if not getattr(sys, "frozen", False):
        return Path(__file__).parents[3] / "work/apple-setup-nov5/aedrova-meeting-audio"
    return bundled


def possible_meeting_apps():
    helper = helper_path()
    if sys.platform != "darwin" or not helper.is_file():
        return {"names": [], "active": False}
    result = subprocess.run(
        [str(helper), "--detect"], capture_output=True, timeout=3, env=environment(), check=True
    )
    if len(result.stdout) > 4096:
        return {"names": [], "active": False}
    data = json.loads(result.stdout)
    return {
        "names": [
            name for name in data.get("names", [])
            if name in {"Zoom", "Teams", "Webex", "Browser", "Google Meet"}
        ],
        "active": data.get("active") is True,
    }


def validate_chunk(root, event):
    name = event.get("file", "")
    source = event.get("source")
    offset = event.get("offset")
    if (
        source not in {"microphone", "computer"}
        or not isinstance(name, str)
        or not re.fullmatch(source + r"-[A-Fa-f0-9-]{36}\.wav", name)
        or not isinstance(offset, (float, int))
        or not 0 <= offset <= 7300
    ):
        raise ValueError("Invalid local audio chunk")
    path = root / name
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 16 * 1024 * 1024:
        raise ValueError("Invalid local audio file")
    return path


class LocalCapture(QObject):
    status = Signal(str)
    segment = Signal(dict)
    level = Signal(float)
    finished = Signal()
    prepared = Signal()
    worker_finished = Signal()

    def __init__(self, parent=None, *, transcriber_factory=Transcriber, duration_seconds=7200):
        super().__init__(parent)
        self.factory = transcriber_factory
        self.duration_seconds = max(1, min(7200, int(duration_seconds)))
        self.cancelled = threading.Event()
        self.capture_done = threading.Event()
        self.chunks = queue.Queue(maxsize=8)
        self.temporary = None
        self.active = False
        self.buffer = bytearray()
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.process_error)
        self.prepared.connect(self.launch)
        self.worker_finished.connect(self.complete)
        self.duration = QTimer(self)
        self.duration.setSingleShot(True)
        self.duration.timeout.connect(self.stop)

    def start(self, *, consent):
        if self.active:
            return
        if not consent:
            raise PermissionError("Confirm participant consent before starting meeting notes.")
        if sys.platform != "darwin" or not helper_path().is_file():
            raise ValueError(
                "Computer-audio meeting notes are currently available in the Mac build."
            )
        if not ready():
            raise ValueError("Download the on-device speech model first.")
        self.active = True
        self.cancelled.clear()
        self.capture_done.clear()
        self.temporary = tempfile.TemporaryDirectory(prefix="aedrova-meeting-audio-")
        self.status.emit("Preparing on-device transcription…")
        threading.Thread(target=self.work, daemon=True).start()

    def launch(self):
        if self.cancelled.is_set() or self.capture_done.is_set():
            self.capture_done.set()
            return
        env = QProcessEnvironment()
        for key, value in environment().items():
            env.insert(key, value)
        self.process.setProcessEnvironment(env)
        self.process.setProgram(str(helper_path()))
        self.process.setArguments([self.temporary.name])
        self.process.start()
        self.duration.start(self.duration_seconds * 1000)
        self.status.emit("Allow microphone and system audio access in macOS to begin.")

    def read_output(self):
        self.buffer.extend(bytes(self.process.readAllStandardOutput()))
        if len(self.buffer) > 32768:
            self.status.emit("Audio capture returned an invalid response.")
            self.stop()
            self.buffer.clear()
            return
        while b"\n" in self.buffer:
            line, _, self.buffer = self.buffer.partition(b"\n")
            try:
                event = json.loads(line)
                if event.get("event") == "chunk":
                    path = validate_chunk(Path(self.temporary.name), event)
                    self.chunks.put_nowait((path, event))
                elif event.get("event") == "permission":
                    self.status.emit(
                        "Allow microphone access in macOS to begin."
                        if event.get("target") == "microphone"
                        else "Allow system audio access in macOS to begin."
                    )
                elif event.get("event") == "level":
                    value = event.get("value")
                    if isinstance(value, (float, int)) and 0 <= value <= 1:
                        self.level.emit(float(value))
                elif event.get("event") == "ready":
                    self.status.emit("Listening locally · microphone and computer audio")
                elif event.get("event") == "error":
                    self.status.emit(
                        "Audio capture stopped. Check macOS microphone and audio permissions."
                    )
                    self.stop()
            except queue.Full:
                self.status.emit(
                    "This Mac cannot keep up. Capture stopped so you can review what was heard."
                )
                self.stop()
            except (ValueError, TypeError, OSError):
                self.status.emit("Local audio capture could not be verified.")
                self.stop()

    def work(self):
        try:
            transcriber = self.factory()
            self.prepared.emit()
            while not self.cancelled.is_set():
                try:
                    path, event = self.chunks.get(timeout=0.2)
                except queue.Empty:
                    if self.capture_done.is_set():
                        break
                    continue
                try:
                    for row in transcriber.transcribe(path):
                        if self.cancelled.is_set():
                            break
                        self.segment.emit(
                            {**row, "offset": event["offset"], "source": event["source"]}
                        )
                finally:
                    path.unlink(missing_ok=True)
        except Exception:
            self.status.emit("On-device transcription failed. No audio was sent to a provider.")
        finally:
            self.worker_finished.emit()

    def stop(self):
        self.duration.stop()
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.write(b"stop\n")
            QTimer.singleShot(3000, self.kill_if_running)
        else:
            self.capture_done.set()

    def kill_if_running(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

    def process_finished(self, *_):
        self.read_output()
        self.capture_done.set()
        if self.active:
            self.status.emit("Finishing the on-device transcript…")

    def process_error(self, *_):
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self.capture_done.set()
            self.status.emit("Could not start local audio capture. Check macOS permissions.")

    def complete(self):
        self.stop()
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)
        self.active = False
        if self.temporary:
            self.temporary.cleanup()
            self.temporary = None
        self.finished.emit()

    def discard(self):
        self.cancelled.set()
        self.stop()
