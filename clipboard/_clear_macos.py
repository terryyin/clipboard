"""macOS Aqua clear: empty the general pasteboard via osascript / AppKit."""

from __future__ import annotations

import subprocess

from clipboard._desktop import _helper_failure_detail
from clipboard._errors import ClipboardContentError

# Bound osascript so a contended or wedged pasteboard cannot hang the caller.
_MACOS_CLEAR_TIMEOUT_S = 15.0

# Only the general pasteboard: the Find pasteboard and other named pasteboards
# are left alone. clearContents with no declareTypes leaves no type at all.
_MACOS_CLEAR_SCRIPT = "\n".join(
    [
        'use framework "AppKit"',
        'use framework "Foundation"',
        "use scripting additions",
        "set pb to current application's NSPasteboard's generalPasteboard()",
        "pb's clearContents()",
        'return "ok"',
    ]
)


def _macos_clipboard_clearer() -> None:
    """Remove every type from the general pasteboard; return ``None``.

    Uses built-in ``osascript`` / AppKit ``NSPasteboard clearContents`` (same
    stack as ``copy_html`` and ``inspect``; no PyObjC / ``clipboard[images]``).
    Helper, access, or timeout failures raise ``ClipboardContentError``.
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", _MACOS_CLEAR_SCRIPT],
            capture_output=True,
            text=True,
            check=False,
            timeout=_MACOS_CLEAR_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClipboardContentError(
            "macOS pasteboard clear timed out "
            f"(limit {_MACOS_CLEAR_TIMEOUT_S:g}s); pasteboard may be contended"
        ) from exc
    except OSError as exc:
        raise ClipboardContentError(
            f"macOS pasteboard clear failed: could not run osascript ({exc})"
        ) from exc
    if result.returncode != 0:
        detail = _helper_failure_detail(result)
        raise ClipboardContentError(
            "macOS pasteboard clear failed" + (f": {detail}" if detail else "")
        )
