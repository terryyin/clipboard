"""Non-mutating clipboard offer inspection (kinds + native format ids)."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from clipboard._errors import ClipboardContentError

ClipboardKind = Literal["text", "image", "html", "files"]

# Known native format identifiers → library kinds. Labels are platform-local
# (macOS UTIs / pasteboard types, Linux MIME / X11 atoms, Windows format
# names); unknown identifiers still appear in ``formats`` without a kind.
_NATIVE_FORMAT_TO_KIND: dict[str, ClipboardKind] = {
    # text
    "public.utf8-plain-text": "text",
    "public.plain-text": "text",
    "NSPasteboardTypeString": "text",
    "text/plain": "text",
    "UTF8_STRING": "text",
    "STRING": "text",
    "TEXT": "text",
    "CF_UNICODETEXT": "text",
    "CF_TEXT": "text",
    # html
    "public.html": "html",
    "NSPasteboardTypeHTML": "html",
    "text/html": "html",
    "HTML Format": "html",
    # image
    "public.png": "image",
    "public.tiff": "image",
    "public.jpeg": "image",
    "NSPasteboardTypePNG": "image",
    "NSPasteboardTypeTIFF": "image",
    "image/png": "image",
    "image/jpeg": "image",
    "image/bmp": "image",
    "CF_DIB": "image",
    "CF_DIBV5": "image",
    "CF_BITMAP": "image",
    "PNG": "image",
    # file-list (kind only; paste/copy of files is out of scope)
    "public.file-url": "files",
    "NSFilenamesPboardType": "files",
    "com.apple.pasteboard.promised-file-url": "files",
    "text/uri-list": "files",
    "CF_HDROP": "files",
}


@dataclass(frozen=True)
class ClipboardOfferSnapshot:
    """Non-mutating snapshot of offered kinds and native format identifiers.

    ``kinds`` uses the fixed library vocabulary
    ``{text, image, html, files}``. ``formats`` lists platform-native type
    identifiers for this offer (may include undecodable types).
    """

    kinds: frozenset[ClipboardKind]
    formats: tuple[str, ...]


def kinds_from_native_formats(
    formats: Sequence[str],
) -> frozenset[ClipboardKind]:
    """Map enumerated native format ids onto the fixed kind vocabulary.

    Kind membership uses the type list alone — no representation payloads.
    Unmapped identifiers contribute no kind but remain listable by callers.
    """
    kinds: set[ClipboardKind] = set()
    for fmt in formats:
        kind = _NATIVE_FORMAT_TO_KIND.get(fmt)
        if kind is not None:
            kinds.add(kind)
    return frozenset(kinds)


def snapshot_from_native_formats(
    formats: Sequence[str],
) -> ClipboardOfferSnapshot:
    """Build an offer snapshot from a native type enumeration (no body reads)."""
    return ClipboardOfferSnapshot(
        kinds=kinds_from_native_formats(formats),
        formats=tuple(formats),
    )


def _default_clipboard_inspector() -> ClipboardOfferSnapshot:
    """Platform-selected enumerator (Darwin Aqua; Linux X11 via xclip TARGETS)."""
    if sys.platform == "darwin":
        from clipboard._offer_macos import _macos_clipboard_inspector

        return _macos_clipboard_inspector()
    if sys.platform.startswith("linux"):
        from clipboard._offer_x11 import (
            _is_linux_wayland,
            _linux_x11_clipboard_inspector,
        )

        if _is_linux_wayland():
            raise ClipboardContentError(
                "inspect format enumeration is not available yet on Linux "
                "Wayland; need wl-paste -l (or equivalent) on a named "
                "compositor, or inject an inspector with "
                "set_clipboard_inspector for tests"
            )
        return _linux_x11_clipboard_inspector()
    raise ClipboardContentError(
        "inspect format enumeration is not available yet "
        f"({sys.platform}); need a usable desktop session with a helper that "
        "can list offered clipboard formats/types (Windows desktop; macOS "
        "Aqua pasteboard types; Linux X11: CLIPBOARD TARGETS helper; Linux "
        "Wayland: MIME-list helper on a named compositor), or inject an "
        "inspector with set_clipboard_inspector for tests"
    )


_clipboard_inspector: Callable[[], ClipboardOfferSnapshot] = (
    _default_clipboard_inspector
)


def set_clipboard_inspector(
    inspector: Callable[[], ClipboardOfferSnapshot] | None,
) -> None:
    """Inject a clipboard-offer inspector (tests / fakes)."""
    global _clipboard_inspector
    _clipboard_inspector = (
        _default_clipboard_inspector if inspector is None else inspector
    )


def inspect() -> ClipboardOfferSnapshot:
    """Return kinds and native format ids for the current clipboard offer.

    Does not require ``clipboard[images]``. Does not mutate the clipboard.
    An empty offer yields empty ``kinds`` / ``formats``. Access or
    enumeration failures raise ``ClipboardContentError`` (not
    ``ClipboardImageError``). On macOS Aqua the default path enumerates
    pasteboard types via ``osascript`` / AppKit without fetching payloads.
    On Linux X11 (``DISPLAY`` set, not Wayland-only) it enumerates CLIPBOARD
    TARGETS via ``xclip -selection clipboard -o -t TARGETS``. Wayland and
    Windows still need an injected inspector via
    ``set_clipboard_inspector`` until their native enumerators land.
    """
    try:
        return _clipboard_inspector()
    except ClipboardContentError:
        raise
    except Exception as exc:
        raise ClipboardContentError(f"clipboard offer inspect failed: {exc}") from exc
