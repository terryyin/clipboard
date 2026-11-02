"""Clipboard failure types for image and rich-content operations."""


class ClipboardImageError(Exception):
    """Image clipboard read or write failed; not ordinary absence (``None``)."""


class ClipboardContentError(Exception):
    """Rich clipboard content operation failed (HTML, inspect, …)."""
