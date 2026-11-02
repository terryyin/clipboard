"""Cross-platform clipboard access, provided by pyperclip."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from pyperclip import copy as copy
from pyperclip import paste as paste

if TYPE_CHECKING:
    from PIL import Image

VERSION = "0.0.5"

_MISSING_IMAGES_EXTRA = (
    "paste_image requires the optional images extra "
    "(Pillow). Install with: pip install 'clipboard[images]'"
)


def _default_grabclipboard():
    from PIL.ImageGrab import grabclipboard

    return grabclipboard()


_grabclipboard: Callable = _default_grabclipboard


def set_image_grabclipboard(grabclipboard: Callable | None) -> None:
    """Inject an ImageGrab.grabclipboard-compatible callable (tests / fakes)."""
    global _grabclipboard
    _grabclipboard = _default_grabclipboard if grabclipboard is None else grabclipboard


def paste_image() -> Image.Image | None:
    """Return a Pillow Image from the clipboard, or None when none is offered.

    Requires the optional ``clipboard[images]`` extra (Pillow). The read does
    not modify clipboard contents. Failures other than ordinary absence raise.

    Non-image clipboard offers — including a Windows filename / file-list
    result from ``ImageGrab.grabclipboard`` and URL-only strings — are
    ordinary absence (``None``). Paths from those offers are not opened.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(_MISSING_IMAGES_EXTRA) from exc

    result = _grabclipboard()
    # ImageGrab may return list[str] (Windows CF_HDROP) or other non-Image offers.
    if isinstance(result, Image.Image):
        return result
    return None
