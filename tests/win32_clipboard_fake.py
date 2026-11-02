"""Scripted user32/kernel32 stand-in for the Windows ``HTML Format`` reader.

Install ``FakeWin32(...).api`` as ``clipboard._html_native_windows._win32_api``
so reader tests need neither Windows nor a real clipboard.
"""

from __future__ import annotations

from types import SimpleNamespace

from clipboard import _html_native_windows

HTML_FORMAT_ID = 0xC0DE
DATA_HANDLE = 0x7FFF_0000_1234  # 64-bit handle value
LOCKED_POINTER = 0x7FFF_0000_5678
ACCESS_DENIED = 5


class FakeWin32:
    """Scripted user32/kernel32: records every call; reads never mutate."""

    def __init__(
        self,
        *,
        envelope: bytes | None,
        open_failures: int = 0,
        register_fails: bool = False,
        data_missing: bool = False,
        lock_fails: bool = False,
        padding: bytes = b"\x00\x00",
    ):
        self.envelope = envelope
        self.open_failures = open_failures
        self.register_fails = register_fails
        self.data_missing = data_missing
        self.lock_fails = lock_fails
        self.padding = padding  # GlobalSize may exceed the producer's bytes
        self.calls: list[str] = []
        self.sleeps: list[float] = []
        self.last_error = 0
        self.is_open = False
        self.locked = False
        self.user32 = SimpleNamespace(
            RegisterClipboardFormatW=self.register,
            IsClipboardFormatAvailable=self.available,
            OpenClipboard=self.open,
            CloseClipboard=self.close,
            GetClipboardData=self.get_data,
            EmptyClipboard=self.forbidden("EmptyClipboard"),
            SetClipboardData=self.forbidden("SetClipboardData"),
        )
        self.kernel32 = SimpleNamespace(
            GlobalLock=self.lock, GlobalUnlock=self.unlock, GlobalSize=self.size
        )

    def api(self) -> _html_native_windows._Win32Api:
        return _html_native_windows._Win32Api(
            user32=self.user32,
            kernel32=self.kernel32,
            get_last_error=lambda: self.last_error,
            format_error=lambda code: f"message {code}",
            string_at=self.string_at,
            sleep=self.sleeps.append,
        )

    def forbidden(self, name):
        def call(*args):
            self.calls.append(name)
            raise AssertionError(f"read must never call {name}")

        return call

    def _fail(self, code: int, result=0):
        self.last_error = code
        return result

    def register(self, name):
        self.calls.append("RegisterClipboardFormatW")
        assert name == "HTML Format"
        return self._fail(87) if self.register_fails else HTML_FORMAT_ID

    def available(self, fmt):
        self.calls.append("IsClipboardFormatAvailable")
        assert fmt == HTML_FORMAT_ID
        return self.envelope is not None

    def open(self, hwnd):
        self.calls.append("OpenClipboard")
        assert hwnd is None
        if self.open_failures:
            self.open_failures -= 1
            return self._fail(ACCESS_DENIED)
        self.is_open = True
        return 1

    def close(self):
        self.calls.append("CloseClipboard")
        assert self.is_open
        self.is_open = False
        return 1

    def get_data(self, fmt):
        self.calls.append("GetClipboardData")
        assert self.is_open and fmt == HTML_FORMAT_ID
        return self._fail(1418) if self.data_missing else DATA_HANDLE

    def lock(self, handle):
        self.calls.append("GlobalLock")
        assert handle == DATA_HANDLE
        if self.lock_fails:
            return self._fail(6)
        self.locked = True
        return LOCKED_POINTER

    def unlock(self, handle):
        self.calls.append("GlobalUnlock")
        assert handle == DATA_HANDLE and self.locked
        self.locked = False
        return 0  # 0 with no error is GlobalUnlock's "now unlocked"

    def size(self, handle):
        self.calls.append("GlobalSize")
        assert handle == DATA_HANDLE
        return len(self.envelope + self.padding)

    def string_at(self, pointer, size):
        assert pointer == LOCKED_POINTER and self.locked and self.is_open
        return (self.envelope + self.padding)[:size]
