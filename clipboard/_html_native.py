"""Platform-native HTML clipboard readers (paste_html default dispatch)."""

from __future__ import annotations

import sys

from clipboard._desktop import _is_linux_wayland
from clipboard._errors import ClipboardContentError
from clipboard._html_envelope import _HtmlOffer
from clipboard._html_native_linux import (
    _linux_wayland_html_clipboard_reader,
    _linux_x11_html_clipboard_reader,
)
from clipboard._html_native_macos import _macos_html_clipboard_reader
from clipboard._html_native_windows import _windows_html_clipboard_reader


def _default_html_clipboard_reader() -> _HtmlOffer | None:
    """Platform-selected HTML reader.

    Darwin reads NSPasteboard via osascript; a Linux Wayland session reads
    ``text/html`` via ``wl-paste``; other Linux sessions read X11 CLIPBOARD
    ``text/html`` via ``xclip -o``; Windows reads the registered ``HTML
    Format`` via user32/kernel32 (``ctypes``).
    """
    if sys.platform == "darwin":
        return _macos_html_clipboard_reader()
    if sys.platform == "win32":
        return _windows_html_clipboard_reader()
    if sys.platform.startswith("linux"):
        if _is_linux_wayland():
            return _linux_wayland_html_clipboard_reader()
        return _linux_x11_html_clipboard_reader()
    raise ClipboardContentError(
        "paste_html native HTML reader is not available on this platform "
        f"({sys.platform}); supported: Windows, macOS, Linux X11 / Wayland; "
        "inject a reader with "
        "set_html_clipboard_reader for tests"
    )
