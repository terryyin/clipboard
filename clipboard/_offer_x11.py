"""Linux X11 CLIPBOARD TARGETS enumeration for offer inspect."""

from __future__ import annotations

import os

from clipboard._desktop import _xclip_targets_inspect
from clipboard._errors import ClipboardContentError
from clipboard._offer import ClipboardOfferSnapshot, snapshot_from_native_formats


def _linux_x11_clipboard_inspector() -> ClipboardOfferSnapshot:
    """Linux X11 default: map ``xclip`` TARGETS → offer snapshot."""
    if not (os.environ.get("DISPLAY") or "").strip():
        raise ClipboardContentError(
            "Linux X11 clipboard inspect requires a usable DISPLAY session "
            "and xclip on PATH (xclip -selection clipboard -o -t TARGETS); "
            "no DISPLAY is set, or inject an inspector with "
            "set_clipboard_inspector for tests"
        )
    return snapshot_from_native_formats(_xclip_targets_inspect())
