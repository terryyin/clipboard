"""Windows desktop file-list copy writer (CF_HDROP + Preferred DropEffect).

Stdlib ``ctypes`` only (no pywin32). The writer's Win32 entry points come from
``_win32_files_write_api`` so tests can replace it with a fake and run without
a Windows session.
"""

from __future__ import annotations

import struct
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ._errors import ClipboardContentError
from ._files_native_windows import (
    _CF_HDROP,
    _NATIVE_FILES_READ_TIMEOUT_S,
    _OPEN_CLIPBOARD_RETRY_S,
)

# Registered shell format: a DWORD DROPEFFECT telling the paste target to
# copy (1) rather than move (2) the referenced files.
_CFSTR_PREFERREDDROPEFFECT = "Preferred DropEffect"
_DROPEFFECT_COPY = 1
_GMEM_MOVEABLE = 0x0002
# DROPFILES: DWORD pFiles; POINT pt (two LONGs); BOOL fNC; BOOL fWide.
_DROPFILES = struct.Struct("<IiiII")
# The writer retries OpenClipboard over the same bound as the reader, counted
# in attempts so the wait stays bounded whatever the clock does.
_OPEN_CLIPBOARD_WRITE_ATTEMPTS = (
    round(_NATIVE_FILES_READ_TIMEOUT_S / _OPEN_CLIPBOARD_RETRY_S) + 1
)


@dataclass(frozen=True)
class _Win32FilesWriteApi:
    """Win32 entry points the file-list writer needs (real ``ctypes`` or a fake)."""

    user32: Any
    kernel32: Any
    get_last_error: Callable[[], int]
    format_error: Callable[[int], str]
    write_bytes: Callable[[int, bytes], None]
    sleep: Callable[[float], None]


def _win32_files_write_api() -> _Win32FilesWriteApi:
    """Load user32/kernel32 with ``use_last_error`` and declare signatures."""
    import ctypes

    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    except (AttributeError, OSError) as exc:
        raise ClipboardContentError(
            "Windows file-list clipboard write failed: user32/kernel32 "
            "unavailable (need win32 with a usable desktop clipboard session); "
            "inject a writer with set_files_clipboard_writer for tests"
        ) from exc

    handle = ctypes.c_void_p  # HWND / HANDLE / HGLOBAL / LPVOID
    uint, boolean, wstr = ctypes.c_uint, ctypes.c_int, ctypes.c_wchar_p
    signatures = (
        (user32.RegisterClipboardFormatW, [wstr], uint),
        (
            user32.CreateWindowExW,
            [ctypes.c_uint32, wstr, wstr, ctypes.c_uint32]
            + [ctypes.c_int] * 4
            + [handle] * 4,
            handle,
        ),
        (user32.DestroyWindow, [handle], boolean),
        (user32.OpenClipboard, [handle], boolean),
        (user32.EmptyClipboard, [], boolean),
        (user32.SetClipboardData, [uint, handle], handle),
        (user32.CloseClipboard, [], boolean),
        (kernel32.GlobalAlloc, [uint, ctypes.c_size_t], handle),
        (kernel32.GlobalLock, [handle], handle),
        (kernel32.GlobalUnlock, [handle], boolean),
        (kernel32.GlobalFree, [handle], handle),
    )
    for function, argtypes, restype in signatures:
        function.argtypes = argtypes
        function.restype = restype
    return _Win32FilesWriteApi(
        user32=user32,
        kernel32=kernel32,
        get_last_error=ctypes.get_last_error,
        format_error=lambda code: ctypes.FormatError(code).strip(),
        write_bytes=lambda pointer, data: ctypes.memmove(pointer, data, len(data)),
        sleep=time.sleep,
    )


def _windows_files_write_error(
    api: _Win32FilesWriteApi, detail: str, code: int | None = None
) -> ClipboardContentError:
    if code is None:
        code = api.get_last_error()
    win32 = f"Win32 error {code}" + (
        f": {api.format_error(code)}" if code else " (no error code)"
    )
    return ClipboardContentError(
        f"Windows file-list clipboard write failed: {detail} ({win32}); "
        "copy_files needs an interactive Windows desktop session with "
        "clipboard access"
    )


def _cf_hdrop_bytes(paths: list[str]) -> bytes:
    """Wide ``DROPFILES`` header then the NUL-separated, double-NUL-ended list."""
    header = _DROPFILES.pack(_DROPFILES.size, 0, 0, 0, 1)
    return header + ("\0".join(paths) + "\0\0").encode("utf-16-le")


def _movable_global(api: _Win32FilesWriteApi, data: bytes, owned: list[int]) -> int:
    """Copy ``data`` into a new ``GMEM_MOVEABLE`` global this process owns."""
    memory = api.kernel32.GlobalAlloc(_GMEM_MOVEABLE, len(data))
    if not memory:
        raise _windows_files_write_error(
            api, f"GlobalAlloc of {len(data)} bytes failed"
        )
    owned.append(memory)
    pointer = api.kernel32.GlobalLock(memory)
    if not pointer:
        raise _windows_files_write_error(api, "GlobalLock failed on new memory")
    try:
        api.write_bytes(pointer, data)
    finally:
        api.kernel32.GlobalUnlock(memory)
    return memory


def _open_clipboard_for_write(api: _Win32FilesWriteApi, window: int) -> None:
    """``OpenClipboard`` with the reader's bounded retry while another holds it."""
    code = 0
    for attempt in range(_OPEN_CLIPBOARD_WRITE_ATTEMPTS):
        if attempt:
            api.sleep(_OPEN_CLIPBOARD_RETRY_S)
        if api.user32.OpenClipboard(window):
            return
        code = api.get_last_error()
    raise _windows_files_write_error(
        api,
        f"OpenClipboard failed {_OPEN_CLIPBOARD_WRITE_ATTEMPTS} times over "
        f"{_NATIVE_FILES_READ_TIMEOUT_S}s; the clipboard is locked by another "
        "process (retry once it is released) or this process has no clipboard "
        "access; the clipboard was not changed",
        code,
    )


def _hand_to_clipboard(
    api: _Win32FilesWriteApi,
    fmt: int,
    memory: int,
    owned: list[int],
    failure: str,
) -> None:
    """``SetClipboardData``; on success the system owns (and frees) ``memory``."""
    if not api.user32.SetClipboardData(fmt, memory):
        raise _windows_files_write_error(api, failure)
    owned.remove(memory)


def _windows_files_clipboard_writer(paths: list[str]) -> None:
    """Replace the clipboard with one copy ``CF_HDROP`` + ``Preferred DropEffect``.

    Writes a wide ``DROPFILES`` path list and ``DROPEFFECT_COPY`` (DWORD 1)
    as ``GMEM_MOVEABLE`` globals, so the system holds the data after this
    process exits. Like pyperclip, a hidden ``STATIC`` window owns the
    clipboard (``EmptyClipboard`` after ``OpenClipboard(NULL)`` leaves no
    owner). ``CloseClipboard`` always runs; globals are freed only when the
    clipboard did not take them. Every failure raises ``ClipboardContentError``.
    """
    api = _win32_files_write_api()
    effect_format = api.user32.RegisterClipboardFormatW(_CFSTR_PREFERREDDROPEFFECT)
    if not effect_format:
        raise _windows_files_write_error(
            api, f"RegisterClipboardFormatW({_CFSTR_PREFERREDDROPEFFECT!r}) failed"
        )
    owned: list[int] = []
    try:
        hdrop = _movable_global(api, _cf_hdrop_bytes(paths), owned)
        effect = _movable_global(api, struct.pack("<I", _DROPEFFECT_COPY), owned)
        window = api.user32.CreateWindowExW(
            0, "STATIC", None, 0, 0, 0, 0, 0, None, None, None, None
        )
        if not window:
            raise _windows_files_write_error(
                api, "CreateWindowExW failed for the clipboard owner window"
            )
        try:
            _open_clipboard_for_write(api, window)
            try:
                if not api.user32.EmptyClipboard():
                    raise _windows_files_write_error(api, "EmptyClipboard failed")
                _hand_to_clipboard(
                    api,
                    _CF_HDROP,
                    hdrop,
                    owned,
                    "SetClipboardData(CF_HDROP) failed after EmptyClipboard; "
                    "the clipboard is now empty",
                )
                _hand_to_clipboard(
                    api,
                    effect_format,
                    effect,
                    owned,
                    f"SetClipboardData({_CFSTR_PREFERREDDROPEFFECT!r}) failed; "
                    "the clipboard holds the file list without its copy marker",
                )
            finally:
                api.user32.CloseClipboard()
        finally:
            api.user32.DestroyWindow(window)
    finally:
        for memory in owned:
            api.kernel32.GlobalFree(memory)
