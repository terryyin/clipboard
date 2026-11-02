"""Shared helpers for gated Linux Wayland probes (compositor and helper facts)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from native_probe_common import linux_wayland_environment

COMPOSITOR = "Sway"


def _first_line(args: list[str]) -> str | None:
    try:
        out = subprocess.check_output(
            args, stderr=subprocess.STDOUT, text=True, timeout=10
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    lines = (out or "").strip().splitlines()
    return lines[0].strip() if lines else None


def sway_version() -> str | None:
    """``sway --version`` of the Sway binary on PATH (e.g. ``sway version 1.10``)."""
    return _first_line(["sway", "--version"])


def sway_running() -> bool:
    """Whether a process named ``sway`` runs here (Linux ``/proc``)."""
    for comm in Path("/proc").glob("[0-9]*/comm"):
        try:
            if comm.read_text().strip() == "sway":
                return True
        except OSError:
            continue
    return False


def wl_paste_version() -> str | None:
    return _first_line(["wl-paste", "--version"])


def wayland_paste_environment(**extra: object) -> dict:
    """Wayland probe environment for a ``wl-paste`` consumer on named Sway."""
    return linux_wayland_environment(
        compositor=COMPOSITOR,
        compositor_version=sway_version(),
        compositor_running=sway_running(),
        compositor_generalization=False,
        helper="wl-paste",
        wl_paste_version=wl_paste_version(),
        xdg_runtime_dir=os.environ.get("XDG_RUNTIME_DIR"),
        **extra,
    )
