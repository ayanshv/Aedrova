"""Explicit model download, offline transcription and extractive draft notes."""

import hashlib
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

REVISION = "ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66"
FILES = {
    "config.json": (2309, "56a6d8110d311f19c8f0471e562832c7527f146b567275bfca59fcf7c184da9a"),
    "model.bin": (145217532, "d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9"),
    "tokenizer.json": (2203239, "fb7b63191e9bb045082c79fd742a3106a12c99513ab30df4a0d47fa6cb6fd0ab"),
    "vocabulary.txt": (459861, "34ce3fe1c5041027b3f8d42912270993f986dbc4bb34cf27f951e34a1e453913"),
}
_LOCK = threading.Lock()


def model_root():
    if sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / ".local/share"))
    return base / "Aedrova/Speech" / REVISION


def ready():
    root = model_root()
    return all(
        (root / name).is_file()
        and not (root / name).is_symlink()
        and (root / name).stat().st_size == size
        for name, (size, _) in FILES.items()
    )


def verify(root):
    for name, (size, digest) in FILES.items():
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            raise ValueError("The offline speech model needs to be downloaded or repaired.")
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise ValueError("Offline speech model verification failed. Download it again.")


def download(progress=lambda _: None, cancelled=lambda: False):
    """Only fixed public model bytes leave this explicit install path. No user data."""
    import httpx

    root = model_root()
    with _LOCK:
        if ready():
            verify(root)
            return
        root.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="speech-install-", dir=root.parent) as temporary:
            stage = Path(temporary) / "model"
            stage.mkdir()
            total, done = sum(size for size, _ in FILES.values()), 0
            with httpx.Client(follow_redirects=True, timeout=60, trust_env=False) as client:
                for name, (expected, digest) in FILES.items():
                    url = f"https://huggingface.co/Systran/faster-whisper-base/resolve/{REVISION}/{name}"
                    count, checksum = 0, hashlib.sha256()
                    with client.stream("GET", url) as response, (stage / name).open("wb") as target:
                        response.raise_for_status()
                        for block in response.iter_bytes(1024 * 256):
                            if cancelled():
                                raise InterruptedError("Speech download cancelled")
                            count += len(block)
                            if count > expected:
                                raise ValueError("Speech download exceeded the expected size.")
                            checksum.update(block)
                            target.write(block)
                            progress(round((done + count) / total * 100))
                    if count != expected or checksum.hexdigest() != digest:
                        raise ValueError("Speech download could not be verified.")
                    done += count
            verify(stage)
            if root.exists():
                raise ValueError(
                    "Remove the incomplete speech model directory before repairing it."
                )
            shutil.move(stage, root)


class Transcriber:
    def __init__(self):
        from faster_whisper import WhisperModel

        root = model_root()
        verify(root)
        self.model = WhisperModel(
            str(root),
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=1,
            local_files_only=True,
        )

    def transcribe(self, path):
        segments, _ = self.model.transcribe(
            str(path),
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
            no_speech_threshold=0.65,
            hallucination_silence_threshold=2,
        )
        return [
            {"start": row.start, "end": row.end, "text": row.text.strip()}
            for row in segments
            if row.text.strip() and row.avg_logprob > -1.0
        ]


def render_transcript(rows):
    lines = []
    for row in sorted(rows, key=lambda row: (row["offset"] + row["start"], row["source"])):
        seconds = max(0, int(row["offset"] + row["start"]))
        speaker = "Microphone" if row["source"] == "microphone" else "Computer audio"
        lines.append(f"[{seconds // 60:02d}:{seconds % 60:02d}] {speaker}: {row['text']}")
    return "\n".join(lines)


def draft_notes(rows):
    """Extract verbatim lines, not invented decisions, assignments or an AI summary."""
    cues = ("we will", "we should", "agreed", "decided", "next step", "follow up", "deadline")
    ordered = sorted(rows, key=lambda row: row["offset"] + row["start"])
    chosen = [row for row in ordered if any(cue in row["text"].casefold() for cue in cues)]
    if not chosen:
        chosen = ordered[:8]
    return "\n".join("• " + row["text"] for row in chosen[:20])
