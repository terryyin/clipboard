"""Platform dispatch for native file-list clipboard readers and writers."""

from __future__ import annotations

import sys

from ._errors import ClipboardContentError
from ._files_native_linux import (
    _linux_wayland_files_clipboard_reader,
    _linux_wayland_without_x11,
    _linux_x11_files_clipboard_reader,
)
from ._files_native_macos import (
    _macos_files_clipboard_reader,
    _macos_files_clipboard_writer,
)
from ._files_native_windows import _windows_files_clipboard_reader


def _unavailable_native_reader_message() -> str:
    return (
        "paste_files native file-list reader is not available on this platform "
        f"({sys.platform}); need a usable desktop session with a file-list "
        "helper (Linux X11: text/uri-list via xclip or equivalent; Wayland: "
        "text/uri-list via wl-paste on a named compositor; Windows desktop: "
        "CF_HDROP), or inject a reader with set_files_clipboard_reader for tests"
    )


def _default_files_clipboard_reader() -> object:
    """Platform-selected file-list reader (Darwin; Linux; Windows CF_HDROP)."""
    if sys.platform == "darwin":
        return _macos_files_clipboard_reader()
    if sys.platform.startswith("linux"):
        if _linux_wayland_without_x11():
            return _linux_wayland_files_clipboard_reader()
        return _linux_x11_files_clipboard_reader()
    if sys.platform == "win32":
        return _windows_files_clipboard_reader()
    raise ClipboardContentError(_unavailable_native_reader_message())


def _unavailable_native_writer_message() -> str:
    return (
        "copy_files native file-list writer is not available on this platform "
        f"({sys.platform}); no file-list copy offer adapter exists here yet "
        "(macOS Aqua is supported), so inject a writer with "
        "set_files_clipboard_writer for tests"
    )


def _default_files_clipboard_writer(paths: list[str]) -> None:
    """Platform-selected file-list copy writer.

    Darwin publishes file ``NSURL`` items through ``osascript`` / AppKit.
    Other platforms raise ``ClipboardContentError`` naming the platform until
    their writers land.
    """
    if sys.platform == "darwin":
        _macos_files_clipboard_writer(paths)
        return
    raise ClipboardContentError(_unavailable_native_writer_message())
