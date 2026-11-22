"""System screen-access prompt, invoked only after an explicit preview/share action."""

import ctypes
import sys


def screen_access(*, library=None):
    if sys.platform != 'darwin':
        return True
    core = library or ctypes.CDLL(
        '/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
    check = core.CGPreflightScreenCaptureAccess
    request = core.CGRequestScreenCaptureAccess
    for function in (check, request):
        function.argtypes = []
        function.restype = ctypes.c_bool
    return bool(check() or request())


def permission_state(kind, *, library=None):
    """'granted', 'denied' or 'undetermined' for camera, microphone or screen, never prompting."""
    if kind == "screen":
        if sys.platform != "darwin":
            return "granted"
        core = library or ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        check = core.CGPreflightScreenCaptureAccess
        check.argtypes = []
        check.restype = ctypes.c_bool
        # macOS does not say "denied" for screen access, only whether it is already granted.
        return "granted" if check() else "undetermined"
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    permission = _qt_permission(kind)
    if permission is None or app is None:
        return "granted"
    status = app.checkPermission(permission)
    if status == Qt.PermissionStatus.Granted:
        return "granted"
    return "denied" if status == Qt.PermissionStatus.Denied else "undetermined"


def _qt_permission(kind):
    from PySide6.QtCore import QCameraPermission, QMicrophonePermission

    factory = {"camera": QCameraPermission, "microphone": QMicrophonePermission}.get(kind)
    return factory() if factory else None
