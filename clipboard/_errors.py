"""Clipboard failure types shared by the content and image paths."""


class ClipboardImageError(Exception):
    """Image clipboard read or write failed; not ordinary absence (``None``)."""


class ClipboardContentError(Exception):
    """HTML/rich clipboard content operation failed."""
