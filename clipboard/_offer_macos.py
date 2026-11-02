"""macOS Aqua pasteboard type enumeration for offer inspect."""

from __future__ import annotations

import subprocess

from clipboard._errors import ClipboardContentError
from clipboard._offer import ClipboardOfferSnapshot, snapshot_from_native_formats

# Bound osascript type-list reads so a contended pasteboard cannot hang forever.
_MACOS_TYPES_TIMEOUT_S = 15.0

_MACOS_TYPES_SCRIPT = "\n".join(
    [
        'use framework "AppKit"',
        'use framework "Foundation"',
        "use scripting additions",
        "set pb to current application's NSPasteboard's generalPasteboard()",
        "set typeArray to pb's types()",
        'if typeArray is missing value then return ""',
        "set typeCount to typeArray's |count|()",
        'if typeCount is 0 then return ""',
        'set out to ""',
        "repeat with i from 0 to (typeCount - 1)",
        "    set t to (typeArray's objectAtIndex:i) as text",
        '    if out is "" then',
        "        set out to t",
        "    else",
        "        set out to out & linefeed & t",
        "    end if",
        "end repeat",
        "return out",
    ]
)


def _enumerate_macos_pasteboard_types() -> tuple[str, ...]:
    """List NSPasteboard type / UTI identifiers without fetching payloads.

    Uses built-in ``osascript`` / AppKit (same stack as ``copy_html``; no
    PyObjC / ``clipboard[images]``). Empty type list → empty tuple (empty
    offer). Helper / access / timeout failures raise ``ClipboardContentError``.
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", _MACOS_TYPES_SCRIPT],
            capture_output=True,
            text=True,
            check=False,
            timeout=_MACOS_TYPES_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClipboardContentError(
            "macOS pasteboard type enumeration timed out "
            f"(limit {_MACOS_TYPES_TIMEOUT_S:g}s); pasteboard may be contended"
        ) from exc
    except OSError as exc:
        raise ClipboardContentError(
            f"macOS pasteboard type enumeration failed: {exc}"
        ) from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ClipboardContentError(
            "macOS pasteboard type enumeration failed"
            + (f": {detail}" if detail else "")
        )
    raw = (result.stdout or "").rstrip("\n")
    if not raw:
        return ()
    return tuple(line for line in raw.splitlines() if line)


def _macos_clipboard_inspector() -> ClipboardOfferSnapshot:
    """Darwin Aqua default: map enumerated pasteboard types → offer snapshot."""
    return snapshot_from_native_formats(_enumerate_macos_pasteboard_types())
