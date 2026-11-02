"""Cross-platform clipboard access, provided by pyperclip."""

from pyperclip import copy, paste

from ._errors import ClipboardContentError, ClipboardImageError
from ._html import (
    copy_html,
    paste_html,
    set_html_clipboard_reader,
    set_html_clipboard_writer,
)
from ._image import (
    copy_image,
    paste_image,
    set_image_grabclipboard,
    set_image_writeclipboard,
)

VERSION = "0.0.5"

__all__ = [
    "VERSION",
    "ClipboardContentError",
    "ClipboardImageError",
    "copy",
    "copy_html",
    "copy_image",
    "paste",
    "paste_html",
    "paste_image",
    "set_html_clipboard_reader",
    "set_html_clipboard_writer",
    "set_image_grabclipboard",
    "set_image_writeclipboard",
]
