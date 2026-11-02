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


class ClipboardImageError(Exception):
    """Image clipboard read failed; distinct from ordinary absence (``None``)."""


def _pillow_image(operation: str):
    """Return ``PIL.Image``, or raise ``ImportError`` for the images extra."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            f"{operation} requires the optional images extra "
            "(Pillow). Install with: pip install 'clipboard[images]'"
        ) from exc
    return Image


def _default_grabclipboard():
    from PIL.ImageGrab import grabclipboard

    return grabclipboard()


_grabclipboard: Callable = _default_grabclipboard


def set_image_grabclipboard(grabclipboard: Callable | None) -> None:
    """Inject an ImageGrab.grabclipboard-compatible callable (tests / fakes)."""
    global _grabclipboard
    _grabclipboard = _default_grabclipboard if grabclipboard is None else grabclipboard


def _default_writeclipboard(image: Image.Image) -> None:
    # Native publication lands in later slices; injectable for desktop-free tests.
    raise NotImplementedError("clipboard image write is not implemented yet")


_writeclipboard: Callable = _default_writeclipboard


def set_image_writeclipboard(writeclipboard: Callable | None) -> None:
    """Inject a clipboard image-write callable (tests / fakes)."""
    global _writeclipboard
    _writeclipboard = (
        _default_writeclipboard if writeclipboard is None else writeclipboard
    )


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
    Image = _pillow_image("paste_image")

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


def copy_image(image: Image.Image) -> None:
    """Copy a Pillow Image onto the clipboard.

    Requires the optional ``clipboard[images]`` extra (Pillow). Platform-native
    publication is provided by later writers; tests may inject a fake via
    ``set_image_writeclipboard``.
    """
    _pillow_image("copy_image")
    _writeclipboard(image)
