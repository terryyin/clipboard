"""Linux Wayland MIME-list enumeration for offer inspect."""

from __future__ import annotations

import os

from clipboard._desktop import _wl_paste_list_types_inspect
from clipboard._errors import ClipboardContentError
from clipboard._offer import ClipboardOfferSnapshot, snapshot_from_native_formats


def _linux_wayland_clipboard_inspector() -> ClipboardOfferSnapshot:
    """Linux Wayland default: map ``wl-paste -l`` → offer snapshot.

    Success is compositor-scoped at native probe time; this enumerator only
    lists MIME types for the current session's clipboard.
    """
    if not (os.environ.get("WAYLAND_DISPLAY") or "").strip():
        raise ClipboardContentError(
            "Linux Wayland clipboard inspect requires a usable "
            "WAYLAND_DISPLAY session and wl-paste on PATH (wl-paste -l); "
            "no WAYLAND_DISPLAY is set, or inject an inspector with "
            "set_clipboard_inspector for tests"
        )
    return snapshot_from_native_formats(_wl_paste_list_types_inspect())
