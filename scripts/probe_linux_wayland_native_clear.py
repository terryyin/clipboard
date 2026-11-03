#!/usr/bin/env python3
"""Gated probe: Linux Wayland (Sway) empty selection and ``clear()``.

Step 1 runs first, on a fresh headless Sway where nothing has been copied: an
independent ``wl-paste -l`` records wl-paste's own exit code and
nothing-copied stderr, and the library's public readers must read absence:
``inspect()`` empty, ``paste()`` ``""``, ``paste_html()`` /
``paste_files()`` / ``paste_image()`` ``None``. Later ``clear()`` steps
append to ``_probe``.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no Wayland session, no
running Sway, or no wl-clipboard is available (never silent verified
success). Scoped to Sway. Not run by default pytest.
"""

from __future__ import annotations

import os
import shutil
import sys

from linux_native_clear_support import (
    distro,
    helper,
    read_everything,
    reads_empty,
    report,
    step,
)
from native_probe_wayland import COMPOSITOR, sway_running, wayland_paste_environment

WL_PASTE_LIST = ["wl-paste", "-l"]


def _probe(observed: dict) -> list[dict]:
    from clipboard import _desktop

    steps = []
    fresh = helper(WL_PASTE_LIST)
    observed["fresh_nothing_copied_list"] = fresh
    reads = read_everything()
    nothing = fresh.get(
        "returncode", 0
    ) != 0 and _desktop._wl_paste_reports_nothing_copied(fresh.get("stderr", ""))
    steps.append(
        step(
            "1_fresh_nothing_copied_reads_empty",
            nothing and reads_empty(reads),
            wl_paste_list=fresh,
            classified_nothing_copied=nothing,
            reads=reads,
        )
    )
    return steps


def main() -> int:
    reason = None
    if not sys.platform.startswith("linux"):
        reason = f"not Linux (platform {sys.platform!r})"
    elif not os.environ.get("WAYLAND_DISPLAY"):
        reason = "no Wayland session (WAYLAND_DISPLAY unset)"
    elif shutil.which("wl-paste") is None or shutil.which("wl-copy") is None:
        reason = "wl-paste/wl-copy not found on PATH (apt install wl-clipboard)"
    elif not sway_running():
        reason = f"no running {COMPOSITOR}; this probe proves the named compositor only"
    if reason is not None:
        report(
            ok=False,
            verified=False,
            evidence_limit=True,
            compositor_generalization=False,
            reason=reason,
        )
        return 2
    import clipboard

    clipboard.set_text_clipboard_writer(None)
    clipboard.set_text_clipboard_reader(None)
    observed: dict = {}
    steps = _probe(observed)
    failed = [s["step"] for s in steps if not s["ok"]]
    report(
        ok=not failed,
        verified=not failed,
        desktop=f"Linux Wayland ({COMPOSITOR})",
        compositor_generalization=False,
        failed_steps=failed,
        observed=observed,
        steps=steps,
        environment=wayland_paste_environment(distro=distro()),
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
