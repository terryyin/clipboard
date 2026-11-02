"""Non-mutating clipboard offer inspection (kinds + native format ids)."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from clipboard._errors import ClipboardContentError

ClipboardKind = Literal["text", "image", "html", "files"]


@dataclass(frozen=True)
class ClipboardOfferSnapshot:
    """Non-mutating snapshot of offered kinds and native format identifiers.

    ``kinds`` uses the fixed library vocabulary
    ``{text, image, html, files}``. ``formats`` lists platform-native type
    identifiers for this offer (may include undecodable types).
    """

    kinds: frozenset[ClipboardKind]
    formats: tuple[str, ...]


def _default_clipboard_inspector() -> ClipboardOfferSnapshot:
    """Stub until desktop enumerators land; inject fakes for desktop-free tests."""
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
    ``ClipboardImageError``). Until native enumerators land, the default
    path raises ``ClipboardContentError``; tests inject via
    ``set_clipboard_inspector``.
    """
    try:
        return _clipboard_inspector()
    except ClipboardContentError:
        raise
    except Exception as exc:
        raise ClipboardContentError(f"clipboard offer inspect failed: {exc}") from exc
