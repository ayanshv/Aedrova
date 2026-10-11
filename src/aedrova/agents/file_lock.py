"""Nonblocking process leases with native Windows and POSIX locking."""

import errno
import os
import stat
import sys


def open_private_file(path, *, truncate=False):
    """Open a regular file without following a final symlink/reparse point."""
    if sys.platform == "win32":
        fd = _open_windows(path)
    else:
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError("Lease file must be a regular file")
        if truncate:
            os.ftruncate(fd, 0)
        return os.fdopen(fd, "r+b", buffering=0)
    except BaseException:
        os.close(fd)
        raise


def _open_windows(path):
    # OPEN_REPARSE_POINT opens the link itself, allowing rejection before any write.
    # DELETE sharing allows leased snapshots to be renamed by their owner.
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.GetFileInformationByHandleEx.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
    handle = kernel.CreateFileW(str(path), 0xC0000000, 7, None, 4, 0x00200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attributes = (wintypes.DWORD * 2)()
        if not kernel.GetFileInformationByHandleEx(
            handle, 9, attributes, ctypes.sizeof(attributes)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if attributes[0] & 0x400:
            raise OSError("Linked lease files are forbidden")
        fd = msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY | os.O_NOINHERIT)
    except BaseException:
        kernel.CloseHandle(handle)
        raise
    return fd  # The CRT descriptor now owns the handle.


def lock_exclusive(stream):
    """Lock until stream.close(); contention is always BlockingIOError."""
    if sys.platform == "win32":
        _lock_windows(stream)
    else:
        import fcntl

        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _lock_windows(stream):
    import msvcrt

    stream.seek(0)
    try:
        # CRT locking permits a one-byte region beyond EOF; no file write needed.
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError as error:
        if error.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
            raise BlockingIOError("Lease already held") from error
        raise
