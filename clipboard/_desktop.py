"""Shared Linux session detection, helper-failure detail, and type listing."""

from __future__ import annotations

import os
import subprocess

from clipboard._errors import ClipboardContentError

# Per-caller listing bounds (image lenient / HTML read / inspect).
_IMAGE_XCLIP_TARGETS_TIMEOUT_S = 2.0
_HTML_LISTING_TIMEOUT_S = 10.0
_INSPECT_LISTING_TIMEOUT_S = 15.0

# Version-dependent xclip stderr when a selection (CLIPBOARD or PRIMARY) has no
# owner (ICCCM owners must answer TARGETS): older releases report the missing
# TARGETS conversion (xclip 0.13 also for an unowned PRIMARY, observed under
# Xvfb); newer ones say "xclip: Error: There is no owner for the CLIPBOARD
# selection" (also on Pillow's ImageGrab silent-error list).
_XCLIP_NO_OWNER_MARKERS = ("target TARGETS not available", "There is no owner for the")
# wl-paste stderr when the selection has no offer (wl-clipboard 2.x variants).
_WL_PASTE_NOTHING_COPIED = frozenset({"Nothing is copied", "No selection"})

_XCLIP_TARGETS_CMD = ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"]
# PRIMARY listing for ``paste_primary`` (text only); same no-owner wording.
_XCLIP_PRIMARY_TARGETS_CMD = ["xclip", "-selection", "primary", "-o", "-t", "TARGETS"]
# HTML read uses the long flag; inspect keeps ``-l`` (tests assert argv).
_WL_PASTE_LIST_TYPES_HTML_CMD = ["wl-paste", "--list-types"]
_WL_PASTE_LIST_TYPES_INSPECT_CMD = ["wl-paste", "-l"]


def _is_linux_wayland() -> bool:
    """Wayland when session type or ``WAYLAND_DISPLAY`` says so.

    Used by image write, HTML read, inspect, and clear. Distinct from
    ``_linux_wayland_without_x11`` (file-list): a session with both
    ``DISPLAY`` and ``WAYLAND_DISPLAY`` still counts as Wayland here.
    """
    session = (os.environ.get("XDG_SESSION_TYPE") or "").strip().lower()
    return session == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def _linux_x11_display() -> str | None:
    """The advertised X11 ``DISPLAY`` value, or ``None`` when unset or empty.

    ``clear()`` dispatches here after ``_is_linux_wayland`` (so a session with
    both ``DISPLAY`` and ``WAYLAND_DISPLAY`` clears Wayland).
    """
    return os.environ.get("DISPLAY") or None


def _linux_wayland_without_x11() -> bool:
    """True when only a Wayland session is advertised (X11 reader not selected).

    File-list readers use this stricter rule: with both ``DISPLAY`` and
    ``WAYLAND_DISPLAY`` set, X11 is selected.
    """
    return bool(os.environ.get("WAYLAND_DISPLAY")) and not bool(
        os.environ.get("DISPLAY")
    )


def _xclip_reports_no_owner(stderr: str) -> bool:
    """Whether xclip stderr says the selection has no owner (nothing offered)."""
    return any(marker in stderr for marker in _XCLIP_NO_OWNER_MARKERS)


def _wl_paste_reports_nothing_copied(stderr: str) -> bool:
    """Whether wl-paste stderr says the selection has no offer at all."""
    return stderr.strip() in _WL_PASTE_NOTHING_COPIED


def _helper_failure_detail(result, *, fallback: str = "") -> str:
    """stderr, else stdout, stripped; ``fallback`` when both are empty.

    Callers keep their current empty-case text: image write uses
    ``fallback="unknown error"``; HTML / files / inspect use default ``""``.
    """
    return (result.stderr or result.stdout or "").strip() or fallback


def _helper_stderr_detail(result: subprocess.CompletedProcess[bytes]) -> str:
    """Stderr-only bytes decoding for binary helper captures (HTML Linux)."""
    return (result.stderr or b"").decode("utf-8", "replace").strip()


def _xclip_targets_lenient() -> bytes:
    """CLIPBOARD TARGETS bytes for image-write polling; empty on any failure."""
    try:
        result = subprocess.run(
            _XCLIP_TARGETS_CMD,
            capture_output=True,
            timeout=_IMAGE_XCLIP_TARGETS_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return b""
    if result.returncode != 0:
        return b""
    return result.stdout or b""


def _xclip_targets_html() -> subprocess.CompletedProcess[bytes] | None:
    """TARGETS for HTML read: ``None`` when CLIPBOARD is unowned.

    Other non-zero exits return the ``CompletedProcess`` for the caller to
    wrap. Timeout / missing helper / OSError propagate for the caller to wrap
    with HTML-specific messages.
    """
    result = subprocess.run(
        _XCLIP_TARGETS_CMD,
        capture_output=True,
        check=False,
        timeout=_HTML_LISTING_TIMEOUT_S,
    )
    if result.returncode != 0 and _xclip_reports_no_owner(
        _helper_stderr_detail(result)
    ):
        return None
    return result


def _wl_paste_list_types_html() -> subprocess.CompletedProcess[bytes] | None:
    """``wl-paste --list-types`` for HTML read: ``None`` when nothing is copied.

    Other non-zero exits return the ``CompletedProcess`` for the caller to
    wrap. Timeout / missing helper / OSError propagate for HTML wrapping.
    """
    result = subprocess.run(
        _WL_PASTE_LIST_TYPES_HTML_CMD,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        timeout=_HTML_LISTING_TIMEOUT_S,
    )
    if result.returncode != 0 and _wl_paste_reports_nothing_copied(
        _helper_stderr_detail(result)
    ):
        return None
    return result


def _xclip_targets_inspect() -> tuple[str, ...]:
    """List X11 CLIPBOARD TARGETS for ``inspect()`` (bounded, strict errors).

    An unowned CLIPBOARD lists nothing (empty snapshot); any other non-zero
    exit raises.
    """
    try:
        result = subprocess.run(
            _XCLIP_TARGETS_CMD,
            capture_output=True,
            text=True,
            check=False,
            timeout=_INSPECT_LISTING_TIMEOUT_S,
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
            f"(limit {_INSPECT_LISTING_TIMEOUT_S:g}s); clipboard may be contended "
            "(xclip -selection clipboard -o -t TARGETS)"
        ) from exc
    except OSError as exc:
        raise ClipboardContentError(
            f"Linux X11 CLIPBOARD TARGETS enumeration failed: {exc} "
            "(xclip -selection clipboard -o -t TARGETS)"
        ) from exc
    if result.returncode != 0:
        if _xclip_reports_no_owner(result.stderr or ""):
            return ()
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


def _wl_paste_list_types_inspect() -> tuple[str, ...]:
    """List Wayland MIME types via ``wl-paste -l`` for ``inspect()``.

    Nothing copied lists nothing (empty snapshot); any other non-zero exit
    raises.
    """
    try:
        result = subprocess.run(
            _WL_PASTE_LIST_TYPES_INSPECT_CMD,
            capture_output=True,
            text=True,
            check=False,
            timeout=_INSPECT_LISTING_TIMEOUT_S,
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
            f"(limit {_INSPECT_LISTING_TIMEOUT_S:g}s); clipboard may be "
            "contended (wl-paste -l)"
        ) from exc
    except OSError as exc:
        raise ClipboardContentError(
            f"Linux Wayland MIME-list enumeration failed: {exc} (wl-paste -l)"
        ) from exc
    if result.returncode != 0:
        if _wl_paste_reports_nothing_copied(result.stderr or ""):
            return ()
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
