"""Bounded file transfers; private objects are never opened or rendered automatically."""

import hashlib
import os
import tempfile
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024


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
