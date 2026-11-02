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


class ClipboardContentError(Exception):
    """HTML/rich clipboard content operation failed."""


def _default_grabclipboard():
    from PIL.ImageGrab import grabclipboard

    return grabclipboard()


_grabclipboard: Callable = _default_grabclipboard


def set_image_grabclipboard(grabclipboard: Callable | None) -> None:
    """Inject an ImageGrab.grabclipboard-compatible callable (tests / fakes)."""
    global _grabclipboard
    _grabclipboard = _default_grabclipboard if grabclipboard is None else grabclipboard


def _default_html_clipboard_writer(html: str, text: str) -> NoReturn:
    raise ClipboardContentError(
        "copy_html native dual-offer writer is not available; "
        "inject a writer with set_html_clipboard_writer for tests"
    )


_html_clipboard_writer: Callable[[str, str], None] = _default_html_clipboard_writer


def set_html_clipboard_writer(
    writer: Callable[[str, str], None] | None,
) -> None:
    """Inject an HTML+plain-text dual-offer writer (tests / fakes)."""
    global _html_clipboard_writer
    _html_clipboard_writer = (
        _default_html_clipboard_writer if writer is None else writer
    )


def _validate_copy_html_args(html: object, text: object) -> tuple[str, str]:
    """Reject invalid HTML/text before any clipboard replace (fail-before-replace).

    Empty HTML (no usable fragment after strip) is invalid. ``text`` must be a
    non-empty ``str``; the plain-text alternative is caller-supplied and is not
    synthesized from HTML.
    """
    if not isinstance(html, str) or not isinstance(text, str):
        raise ClipboardContentError(
            "copy_html requires html and text as str "
            f"(got html={type(html).__name__}, text={type(text).__name__})"
        )
    if not html.strip():
        raise ClipboardContentError(
            "copy_html requires a non-empty HTML fragment "
            "(empty or whitespace-only HTML is invalid)"
        )
    if text == "":
        raise ClipboardContentError(
            "copy_html requires a non-empty plain-text alternative"
        )
    return html, text


def copy_html(html: str, text: str) -> None:
    """Publish HTML and a matching plain-text alternative as one clipboard offer.

    Does not require the optional ``clipboard[images]`` extra. Failures raise
    ``ClipboardContentError``. Invalid arguments are rejected before the
    injected writer runs. Native platform writers arrive separately; until
    then the default path fails unless a writer is injected via
    ``set_html_clipboard_writer``. Writers must publish both representations
    together; inability to offer both, or transfer failure, must surface as
    ``ClipboardContentError`` (not silent text-only success).
    """
    html, text = _validate_copy_html_args(html, text)
    try:
        _html_clipboard_writer(html, text)
    except ClipboardContentError:
        raise
    except Exception as exc:
        raise ClipboardContentError(f"clipboard HTML+text write failed: {exc}") from exc


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
