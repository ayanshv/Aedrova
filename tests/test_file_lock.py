import errno
import subprocess
import sys
from types import SimpleNamespace

import pytest

from aedrova.agents.file_lock import _lock_windows, lock_exclusive, open_private_file


def test_lease_excludes_other_process_and_releases_on_close(tmp_path):
    path = tmp_path / "lease"
    stream = open_private_file(path)
    lock_exclusive(stream)
    probe = """
import sys
from aedrova.agents.file_lock import lock_exclusive, open_private_file
with open_private_file(sys.argv[1]) as stream:
    try:
        lock_exclusive(stream)
    except BlockingIOError:
        sys.exit(23)
"""
    assert subprocess.run([sys.executable, "-c", probe, str(path)]).returncode == 23
    stream.close()
    assert subprocess.run([sys.executable, "-c", probe, str(path)]).returncode == 0


def test_linked_lease_cannot_modify_target(tmp_path):
    target = tmp_path / "private"
    target.write_bytes(b"keep")
    path = tmp_path / "lease"
    path.symlink_to(target)
    with pytest.raises(OSError):
        open_private_file(path, truncate=True)
    assert target.read_bytes() == b"keep"


@pytest.mark.parametrize("code", [errno.EACCES, errno.EAGAIN, errno.EDEADLK, errno.EBADF])
def test_windows_lock_contention_is_distinct_from_io_error(monkeypatch, tmp_path, code):
    calls = []

    def locking(fd, mode, size):
        calls.append((fd, mode, size))
        raise OSError(code, "synthetic")

    monkeypatch.setitem(sys.modules, "msvcrt", SimpleNamespace(locking=locking, LK_NBLCK=2))
    with (tmp_path / "lease").open("w+b") as stream:
        stream.seek(10)
        error = OSError if code == errno.EBADF else BlockingIOError
        with pytest.raises(error) as caught:
            _lock_windows(stream)
        assert stream.tell() == 0
        assert calls == [(stream.fileno(), 2, 1)]
        if code == errno.EBADF:
            assert not isinstance(caught.value, BlockingIOError)
