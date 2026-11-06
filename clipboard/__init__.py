"""Cross-platform clipboard: text, image, HTML, files, inspect, clear, and waits.

``copy_primary`` / ``paste_primary`` reach the Linux PRIMARY selection only.
"""

from __future__ import annotations

import subprocess as subprocess  # noqa: F401 — tests monkeypatch ``clipboard.subprocess``

from clipboard import _clear, _files, _html, _offer, _text
from clipboard._clear import clear, set_clipboard_clearer
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
from clipboard._primary import copy_primary, paste_primary
from clipboard._text import (
    copy,
    paste,
    set_text_clipboard_reader,
    set_text_clipboard_writer,
)
from clipboard._wait import wait_for_kind, wait_for_text_change

VERSION = "1.0.0"

__all__ = [
    "VERSION",
    "ClipboardContentError",
    "ClipboardImageError",
    "ClipboardKind",
    "ClipboardOfferSnapshot",
    "clear",
    "copy",
    "copy_files",
    "copy_html",
    "copy_image",
    "copy_primary",
    "inspect",
    "paste",
    "paste_files",
    "paste_html",
    "paste_image",
    "paste_primary",
    "set_clipboard_clearer",
    "set_clipboard_inspector",
    "set_files_clipboard_reader",
    "set_files_clipboard_writer",
    "set_html_clipboard_reader",
    "set_html_clipboard_writer",
    "set_image_grabclipboard",
    "set_image_writeclipboard",
    "set_text_clipboard_reader",
    "set_text_clipboard_writer",
    "wait_for_kind",
    "wait_for_text_change",
]


# Private injection globals re-read from their owning module on each access,
# so ``set_*`` swaps stay visible through the package facade.
_INJECTION_GLOBAL_OWNERS = {
    "_text_clipboard_writer": _text,
    "_default_text_clipboard_writer": _text,
    "_text_clipboard_reader": _text,
    "_default_text_clipboard_reader": _text,
    "_clipboard_clearer": _clear,
    "_default_clipboard_clearer": _clear,
    "_clipboard_inspector": _offer,
    "_default_clipboard_inspector": _offer,
    "_files_clipboard_reader": _files,
    "_default_files_clipboard_reader": _files,
    "_files_clipboard_writer": _files,
    "_default_files_clipboard_writer": _files,
    "_html_clipboard_writer": _html,
    "_default_html_clipboard_writer": _html,
    "_html_clipboard_reader": _html,
    "_default_html_clipboard_reader": _html,
}


def __getattr__(name: str):
    """Resolve mutable private injection globals from their owning modules."""
    owner = _INJECTION_GLOBAL_OWNERS.get(name)
    if owner is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(owner, name)
