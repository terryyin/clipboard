"""Linux X11 CLIPBOARD TARGETS enumeration for offer inspect."""

from __future__ import annotations

import os
import subprocess

from clipboard._desktop import _helper_failure_detail
from clipboard._errors import ClipboardContentError
from clipboard._offer import ClipboardOfferSnapshot, snapshot_from_native_formats

# Bound xclip TARGETS reads so a contended CLIPBOARD cannot hang forever.
_X11_TARGETS_TIMEOUT_S = 15.0


def _enumerate_x11_clipboard_targets() -> tuple[str, ...]:
    """List X11 CLIPBOARD TARGETS via ``xclip`` without fetching payloads.

    Invokes ``xclip -selection clipboard -o -t TARGETS``. Empty stdout →
    empty tuple (empty offer). Missing helper / access / timeout / helper
    failure raise ``ClipboardContentError`` (never a fabricated empty
    success from a failed helper).
    """
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"],
            capture_output=True,
            text=True,
            check=False,
            timeout=_X11_TARGETS_TIMEOUT_S,
        )
    except FileNotFoundError as exc:
        raise ClipboardContentError(
            "missing Linux clipboard enumeration helper: install xclip "
            "and ensure it is on PATH "
            "(xclip -selection clipboard -o -t TARGETS), or inject an "
            "inspector with set_clipboard_inspector for tests"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ClipboardContentError(
            "Linux X11 CLIPBOARD TARGETS enumeration timed out "
            f"(limit {_X11_TARGETS_TIMEOUT_S:g}s); clipboard may be contended "
            "(xclip -selection clipboard -o -t TARGETS)"
        ) from exc
    except OSError as exc:
        raise ClipboardContentError(
            f"Linux X11 CLIPBOARD TARGETS enumeration failed: {exc} "
            "(xclip -selection clipboard -o -t TARGETS)"
        ) from exc
    if result.returncode != 0:
        detail = _helper_failure_detail(result)
        raise ClipboardContentError(
            "Linux X11 CLIPBOARD TARGETS enumeration failed"
            + (f": {detail}" if detail else "")
            + " (xclip -selection clipboard -o -t TARGETS)"
        )
    raw = (result.stdout or "").rstrip("\n")
    if not raw:
        return ()
    return tuple(line for line in raw.splitlines() if line)


def _linux_x11_clipboard_inspector() -> ClipboardOfferSnapshot:
    """Linux X11 default: map ``xclip`` TARGETS → offer snapshot."""
    if not (os.environ.get("DISPLAY") or "").strip():
        raise ClipboardContentError(
            "Linux X11 clipboard inspect requires a usable DISPLAY session "
            "and xclip on PATH (xclip -selection clipboard -o -t TARGETS); "
            "no DISPLAY is set, or inject an inspector with "
            "set_clipboard_inspector for tests"
        )
    return snapshot_from_native_formats(_enumerate_x11_clipboard_targets())
