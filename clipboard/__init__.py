"""Cross-platform clipboard: text, image, HTML, files, and inspect."""

from __future__ import annotations

import subprocess as subprocess  # noqa: F401 — tests monkeypatch ``clipboard.subprocess``
import sys as sys  # noqa: F401 — tests monkeypatch ``clipboard.sys.platform``

from pyperclip import copy as copy
from pyperclip import paste as paste

from clipboard import _html, _offer
from clipboard._errors import ClipboardContentError, ClipboardImageError
from clipboard._files import (
    copy_files,
    paste_files,
    set_files_clipboard_reader,
    set_files_clipboard_writer,
)
from clipboard._html import (
    copy_html,
    paste_html,
    set_html_clipboard_reader,
    set_html_clipboard_writer,
)
from clipboard._image_read import paste_image, set_image_grabclipboard
from clipboard._image_write import copy_image, set_image_writeclipboard
from clipboard._offer import (
    ClipboardKind,
    ClipboardOfferSnapshot,
    inspect,
    set_clipboard_inspector,
)

VERSION = "0.0.5"

__all__ = [
    "VERSION",
    "ClipboardContentError",
    "ClipboardImageError",
    "ClipboardKind",
    "ClipboardOfferSnapshot",
    "copy",
    "copy_files",
    "copy_html",
    "copy_image",
    "inspect",
    "paste",
    "paste_files",
    "paste_html",
    "paste_image",
    "set_clipboard_inspector",
    "set_files_clipboard_reader",
    "set_files_clipboard_writer",
    "set_html_clipboard_reader",
    "set_html_clipboard_writer",
    "set_image_grabclipboard",
    "set_image_writeclipboard",
]


def __getattr__(name: str):
    """Resolve mutable private injection globals from their owning modules."""
    if name == "_clipboard_inspector":
        return _offer._clipboard_inspector
    if name == "_default_clipboard_inspector":
        return _offer._default_clipboard_inspector
    if name == "_files_clipboard_reader":
        from clipboard import _files

        return _files._files_clipboard_reader
    if name == "_default_files_clipboard_reader":
        from clipboard import _files

        return _files._default_files_clipboard_reader
    if name == "_files_clipboard_writer":
        from clipboard import _files

        return _files._files_clipboard_writer
    if name == "_default_files_clipboard_writer":
        from clipboard import _files

        return _files._default_files_clipboard_writer
    if name == "_html_clipboard_writer":
        return _html._html_clipboard_writer
    if name == "_default_html_clipboard_writer":
        return _html._default_html_clipboard_writer
    if name == "_html_clipboard_reader":
        return _html._html_clipboard_reader
    if name == "_default_html_clipboard_reader":
        return _html._default_html_clipboard_reader
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
