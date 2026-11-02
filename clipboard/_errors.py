"""Clipboard failure types for image and rich-content operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

_T = TypeVar("_T")


class ClipboardImageError(Exception):
    """Image clipboard read or write failed; not ordinary absence (``None``)."""


class ClipboardContentError(Exception):
    """Rich clipboard content operation failed (HTML, file-list, inspect, …)."""


def _call_content_backend(operation: str, backend: Callable[..., _T], *args) -> _T:
    """Run a rich-content clipboard backend; non-content failures become
    ``ClipboardContentError`` while backend ``ClipboardContentError`` passes as is.
    """
    try:
        return backend(*args)
    except ClipboardContentError:
        raise
    except Exception as exc:
        raise ClipboardContentError(f"clipboard {operation} failed: {exc}") from exc
