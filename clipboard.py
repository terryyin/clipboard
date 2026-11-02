"""Cross-platform clipboard access, provided by pyperclip."""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from typing import TYPE_CHECKING, NoReturn

from pyperclip import copy as copy
from pyperclip import paste as paste

if TYPE_CHECKING:
    from PIL import Image

VERSION = "0.0.5"

_MISSING_IMAGES_EXTRA = (
    "paste_image requires the optional images extra "
    "(Pillow). Install with: pip install 'clipboard[images]'"
)


class ClipboardImageError(Exception):
    """Image clipboard read failed; distinct from ordinary absence (``None``)."""


def _default_grabclipboard():
    from PIL.ImageGrab import grabclipboard

    return grabclipboard()


_grabclipboard: Callable = _default_grabclipboard


def set_image_grabclipboard(grabclipboard: Callable | None) -> None:
    """Inject an ImageGrab.grabclipboard-compatible callable (tests / fakes)."""
    global _grabclipboard
    _grabclipboard = _default_grabclipboard if grabclipboard is None else grabclipboard


def _raise_image_failure(exc: BaseException) -> NoReturn:
    raise ClipboardImageError(f"clipboard image read failed: {exc}") from exc


def paste_image() -> Image.Image | None:
    """Return a Pillow Image from the clipboard, or None when none is offered.

    Requires the optional ``clipboard[images]`` extra (Pillow). The read does
    not modify clipboard contents. Failures other than ordinary absence raise
    ``ClipboardImageError`` (access, helper, transfer, or malformed data).

    Non-image clipboard offers — including a Windows filename / file-list
    result from ``ImageGrab.grabclipboard`` and URL-only strings — are
    ordinary absence (``None``). Paths from those offers are not opened.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(_MISSING_IMAGES_EXTRA) from exc

    try:
        result = _grabclipboard()
    except (OSError, NotImplementedError) as exc:
        # Includes PermissionError, ChildProcessError, UnidentifiedImageError.
        _raise_image_failure(exc)

    if isinstance(result, Image.Image):
        return result

    # Image-typed payload that ImageGrab would normally open before returning.
    if isinstance(result, (bytes, bytearray, memoryview)):
        try:
            image = Image.open(BytesIO(bytes(result)))
            image.load()
        except OSError as exc:
            _raise_image_failure(exc)
        return image

    # list[str], URL strings, None, and other non-image offers → absence.
    return None
