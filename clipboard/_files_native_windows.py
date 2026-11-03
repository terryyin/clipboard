"""Windows desktop file-list clipboard reader (CF_HDROP via ctypes)."""

from __future__ import annotations

import time
from ctypes import create_unicode_buffer

from . import _platform
from ._errors import ClipboardContentError

# Contended clipboard must not hang callers indefinitely (commitment 78).
_NATIVE_FILES_READ_TIMEOUT_S = 30
_OPEN_CLIPBOARD_RETRY_S = 0.05
# Win32 clipboard format for HDROP path lists (shell32 DragQueryFileW).
_CF_HDROP = 15


def _windows_unavailable_message() -> str:
    return (
        "clipboard file-list read failed: Windows desktop CF_HDROP reader "
        "unavailable (need win32 with a usable desktop clipboard session for "
        "Explorer-equivalent CF_HDROP); inject a reader with "
        "set_files_clipboard_reader for tests"
    )


def _read_cf_hdrop_offer() -> object:
    """Read CF_HDROP as an ordered path list (or None). PreferredDropEffect ignored.

    Uses stdlib ``ctypes`` only (no ``win32clipboard`` dependency). Does not
    clear/rewrite the clipboard, does not call ``DragFinish`` on clipboard-owned
    memory, and does not open referenced files. Cut/move
    ``CF_PREFERREDDROPEFFECT`` is not requested (ignored for library behavior).
    """
    import ctypes
    from ctypes import wintypes

    # WinDLL exists only on Windows; refuse rather than AttributeError noise.
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    except (AttributeError, OSError) as exc:
        raise ClipboardContentError(_windows_unavailable_message()) from exc

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
    user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    shell32.DragQueryFileW.argtypes = [
        wintypes.HANDLE,
        wintypes.UINT,
        wintypes.LPWSTR,
        wintypes.UINT,
    ]
    shell32.DragQueryFileW.restype = wintypes.UINT

    deadline = time.monotonic() + _NATIVE_FILES_READ_TIMEOUT_S
    opened = False
    while time.monotonic() < deadline:
        if user32.OpenClipboard(None):
            opened = True
            break
        time.sleep(_OPEN_CLIPBOARD_RETRY_S)
    if not opened:
        raise ClipboardContentError(
            "clipboard file-list read failed: OpenClipboard timed out "
            "(contended Windows clipboard)"
        )

    try:
        if not user32.IsClipboardFormatAvailable(_CF_HDROP):
            return None

        handle = user32.GetClipboardData(_CF_HDROP)
        if not handle:
            raise ClipboardContentError(
                "clipboard file-list read failed: GetClipboardData(CF_HDROP) "
                "returned no handle"
            )

        count = shell32.DragQueryFileW(handle, 0xFFFFFFFF, None, 0)
        if count == 0:
            return None

        paths: list[str] = []
        for index in range(count):
            length = shell32.DragQueryFileW(handle, index, None, 0)
            if length == 0:
                raise ClipboardContentError(
                    "clipboard file-list read failed: corrupt CF_HDROP "
                    f"metadata at index {index}"
                )
            buf = create_unicode_buffer(length + 1)
            written = shell32.DragQueryFileW(handle, index, buf, length + 1)
            if written == 0 or not buf.value:
                raise ClipboardContentError(
                    "clipboard file-list read failed: corrupt CF_HDROP "
                    f"path at index {index}"
                )
            paths.append(buf.value)
        # Bare path list → paste_files shared CF_HDROP-style normalizer.
        return paths
    finally:
        user32.CloseClipboard()


def _windows_files_clipboard_reader() -> object:
    """Read Explorer-equivalent CF_HDROP path lists (read-only).

    Returns a path ``list[str]`` for ``_normalize_files_offer``. Ordinary
    absence of CF_HDROP is ``None``. Non-Windows hosts raise
    ``ClipboardContentError`` (never silent ``None``).
    """
    if _platform.current() != "win32":
        raise ClipboardContentError(_windows_unavailable_message())
    return _read_cf_hdrop_offer()
