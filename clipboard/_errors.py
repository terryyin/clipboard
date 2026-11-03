"""Clipboard failure types for image and other clipboard content operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

_T = TypeVar("_T")


class ClipboardImageError(Exception):
    """Image clipboard read or write failed; not ordinary absence (``None``)."""


class ClipboardContentError(Exception):
    """Clipboard content operation failed (text, HTML, file-list, inspect, …).

    Raised instead of ordinary absence (``""`` / ``None``) or a silent no-op;
    the underlying helper or pyperclip error, when there is one, is
    ``__cause__``.
    """


def _call_content_backend(operation: str, backend: Callable[..., _T], *args) -> _T:
    """Run a clipboard content backend; non-content failures become
    ``ClipboardContentError`` while backend ``ClipboardContentError`` passes as is.
    """
    try:
        return backend(*args)
    except ClipboardContentError:
        raise
    except Exception as exc:
        raise ClipboardContentError(f"clipboard {operation} failed: {exc}") from exc
