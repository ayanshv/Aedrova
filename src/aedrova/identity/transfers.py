"""Bounded file transfers; private objects are never opened or rendered automatically."""

import hashlib
import io
import os
import tempfile
from pathlib import Path

from aedrova.identity.file_policy import MAX_BYTES, inspect_file


def read_upload(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError("Choose a regular file.")
    name = path.name
    if not 1 <= len(name) <= 180 or any(ord(c) < 32 or c in "/\\" for c in name):
        raise ValueError("Unsupported filename.")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if not 1 <= len(data) <= MAX_BYTES:
        raise ValueError("Choose a file between 1 byte and 10 MB.")
    inspect_file(name, data)
    return name, data, hashlib.sha256(data).hexdigest()


def save_download(destination, data):
    destination = Path(destination)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, prefix=".aedrova-", delete=False
        ) as out:
            temporary = out.name
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


class UploadCancelled(Exception):
    """Cancellation while the private request body is still being transferred."""


class UploadReader(io.BufferedReader):
    """SDK-compatible multipart reader with measured progress and chunk cancellation."""

    def __init__(self, data, cancelled, progress):
        super().__init__(io.BytesIO(data))
        self.total = len(data)
        self.cancelled, self.progress = cancelled, progress
        self.last_percent = -1

    def read(self, size=-1):
        if self.cancelled():
            raise UploadCancelled()
        chunk = super().read(size)
        percent = min(100, self.tell() * 100 // max(1, self.total))
        if percent != self.last_percent:
            self.last_percent = percent
            self.progress(f"Uploading · {percent}%")
        return chunk
