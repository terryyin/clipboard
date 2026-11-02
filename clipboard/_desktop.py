"""Shared Linux session detection and helper-failure detail formatting."""

from __future__ import annotations

import os
import subprocess


def _is_linux_wayland() -> bool:
    """Wayland when session type or ``WAYLAND_DISPLAY`` says so.

    Used by image write, HTML read, and inspect. Distinct from
    ``_linux_wayland_without_x11`` (file-list): a session with both
    ``DISPLAY`` and ``WAYLAND_DISPLAY`` still counts as Wayland here.
    """
    session = (os.environ.get("XDG_SESSION_TYPE") or "").strip().lower()
    return session == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def _linux_wayland_without_x11() -> bool:
    """True when only a Wayland session is advertised (X11 reader not selected).

    File-list readers use this stricter rule: with both ``DISPLAY`` and
    ``WAYLAND_DISPLAY`` set, X11 is selected.
    """
    return bool(os.environ.get("WAYLAND_DISPLAY")) and not bool(
        os.environ.get("DISPLAY")
    )


def _helper_failure_detail(result, *, fallback: str = "") -> str:
    """stderr, else stdout, stripped; ``fallback`` when both are empty.

    Callers keep their current empty-case text: image write uses
    ``fallback="unknown error"``; HTML / files / inspect use default ``""``.
    """
    return (result.stderr or result.stdout or "").strip() or fallback


def _helper_stderr_detail(result: subprocess.CompletedProcess[bytes]) -> str:
    """Stderr-only bytes decoding for binary helper captures (HTML Linux)."""
    return (result.stderr or b"").decode("utf-8", "replace").strip()
