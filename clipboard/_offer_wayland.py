"""Linux Wayland MIME-list enumeration for offer inspect."""

from __future__ import annotations

import os
import subprocess

from clipboard._desktop import _helper_failure_detail
from clipboard._errors import ClipboardContentError
from clipboard._offer import ClipboardOfferSnapshot, snapshot_from_native_formats

# Bound wl-paste -l so a contended clipboard cannot hang forever.
_WAYLAND_MIME_LIST_TIMEOUT_S = 15.0


def _enumerate_wayland_mime_types() -> tuple[str, ...]:
    """List offered MIME types via ``wl-paste -l`` without fetching payloads.

    Empty stdout → empty tuple (empty offer). Missing helper / access /
    timeout / helper failure raise ``ClipboardContentError`` (never a
    fabricated empty success from a failed helper).
    """
    try:
        result = subprocess.run(
            ["wl-paste", "-l"],
            capture_output=True,
            text=True,
            check=False,
            timeout=_WAYLAND_MIME_LIST_TIMEOUT_S,
        )
    except FileNotFoundError as exc:
        raise ClipboardContentError(
            "missing Linux clipboard enumeration helper: install wl-clipboard "
            "and ensure wl-paste is on PATH (wl-paste -l), or inject an "
            "inspector with set_clipboard_inspector for tests"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ClipboardContentError(
            "Linux Wayland MIME-list enumeration timed out "
            f"(limit {_WAYLAND_MIME_LIST_TIMEOUT_S:g}s); clipboard may be "
            "contended (wl-paste -l)"
        ) from exc
    except OSError as exc:
        raise ClipboardContentError(
            f"Linux Wayland MIME-list enumeration failed: {exc} (wl-paste -l)"
        ) from exc
    if result.returncode != 0:
        detail = _helper_failure_detail(result)
        raise ClipboardContentError(
            "Linux Wayland MIME-list enumeration failed"
            + (f": {detail}" if detail else "")
            + " (wl-paste -l)"
        )
    raw = (result.stdout or "").rstrip("\n")
    if not raw:
        return ()
    return tuple(line for line in raw.splitlines() if line)


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
    return snapshot_from_native_formats(_enumerate_wayland_mime_types())
