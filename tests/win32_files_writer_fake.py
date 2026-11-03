"""Scripted user32/kernel32 stand-in for the Windows CF_HDROP copy writer.

Install ``FakeWin32FilesWriter(...).api`` as
``clipboard._files_native_windows_writer._win32_files_write_api`` so
``copy_files`` writer tests need neither Windows nor a real clipboard.
"""

from __future__ import annotations

from types import SimpleNamespace

from clipboard import _files_native_windows_writer

DROP_EFFECT_FORMAT_ID = 0xC0E1
OWNER_WINDOW = 0x0001_0042


class FakeWin32FilesWriter:
    """Scripted user32/kernel32 for the CF_HDROP writer.

    ``fail_on`` maps an entry-point name to the 1-based call that fails with
    ``last_error`` set, e.g. ``{"GlobalAlloc": 2}``. Records ``calls``,
    ``sleeps``, memory written per global, ``freed`` globals, and the
    ``clipboard`` (format → global) the system now owns.
    """

    def __init__(self, *, open_failures: int = 0, fail_on=None, error: int = 5):
        self.open_failures = open_failures
        self.fail_on = dict(fail_on or {})
        self.error = error
        self.counts: dict[str, int] = {}
        self.calls: list[tuple] = []
        self.sleeps: list[float] = []
        self.last_error = 0
        self.memory: dict[int, bytes] = {}
        self.alloc_flags: dict[int, int] = {}
        self.freed: list[int] = []
        self.clipboard: dict[int, int] = {}
        self.window_alive = False
        self.is_open = False
        self.locked: set[int] = set()
        self.user32 = SimpleNamespace(
            RegisterClipboardFormatW=self.register,
            CreateWindowExW=self.create_window,
            DestroyWindow=self.destroy_window,
            OpenClipboard=self.open,
            EmptyClipboard=self.empty,
            SetClipboardData=self.set_data,
            CloseClipboard=self.close,
        )
        self.kernel32 = SimpleNamespace(
            GlobalAlloc=self.alloc,
            GlobalLock=self.lock,
            GlobalUnlock=self.unlock,
            GlobalFree=self.free,
        )

    def api(self) -> _files_native_windows_writer._Win32FilesWriteApi:
        return _files_native_windows_writer._Win32FilesWriteApi(
            user32=self.user32,
            kernel32=self.kernel32,
            get_last_error=lambda: self.last_error,
            format_error=lambda code: f"message {code}",
            write_bytes=self.write_bytes,
            sleep=self.sleeps.append,
        )

    def names(self) -> list[str]:
        return [call[0] for call in self.calls]

    def _call(self, name: str, *args) -> bool:
        """Record the call; True when this call is scripted to fail."""
        self.calls.append((name, *args))
        self.counts[name] = self.counts.get(name, 0) + 1
        if self.fail_on.get(name) == self.counts[name]:
            self.last_error = self.error
            return True
        return False

    def register(self, name):
        if self._call("RegisterClipboardFormatW", name):
            return 0
        assert name == "Preferred DropEffect"
        return DROP_EFFECT_FORMAT_ID

    def create_window(self, *args):
        if self._call("CreateWindowExW", *args):
            return None
        assert args[1] == "STATIC"
        self.window_alive = True
        return OWNER_WINDOW

    def destroy_window(self, hwnd):
        self._call("DestroyWindow", hwnd)
        assert hwnd == OWNER_WINDOW and self.window_alive and not self.is_open
        self.window_alive = False
        return 1

    def open(self, hwnd):
        self.calls.append(("OpenClipboard", hwnd))
        assert hwnd == OWNER_WINDOW and self.window_alive
        if self.open_failures:
            self.open_failures -= 1
            self.last_error = self.error
            return 0
        self.is_open = True
        return 1

    def empty(self):
        if self._call("EmptyClipboard"):
            return 0
        assert self.is_open
        self.clipboard.clear()
        return 1

    def set_data(self, fmt, memory):
        if self._call("SetClipboardData", fmt, memory):
            return None
        assert self.is_open and memory in self.memory and memory not in self.locked
        self.clipboard[fmt] = memory
        return memory

    def close(self):
        self._call("CloseClipboard")
        assert self.is_open
        self.is_open = False
        return 1

    def alloc(self, flags, size):
        if self._call("GlobalAlloc", flags, size):
            return None
        memory = 0x5000 + 0x10 * self.counts["GlobalAlloc"]
        self.memory[memory] = bytes(size)
        self.alloc_flags[memory] = flags
        return memory

    def lock(self, memory):
        if self._call("GlobalLock", memory):
            return None
        self.locked.add(memory)
        return memory + 1  # pointer distinct from the handle

    def unlock(self, memory):
        self._call("GlobalUnlock", memory)
        self.locked.discard(memory)
        return 0

    def free(self, memory):
        self._call("GlobalFree", memory)
        assert memory not in self.clipboard.values(), "freed clipboard-owned data"
        self.freed.append(memory)
        return None

    def write_bytes(self, pointer, data):
        memory = pointer - 1
        assert memory in self.locked and len(data) == len(self.memory[memory])
        self.memory[memory] = bytes(data)
