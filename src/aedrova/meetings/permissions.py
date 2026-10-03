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
