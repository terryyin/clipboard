#!/usr/bin/env python3
"""Gated probe: Linux X11 (Xvfb) empty CLIPBOARD and ``clear()``.

Step 1 runs first, on a fresh X server whose CLIPBOARD nobody has owned: an
independent ``xclip -selection clipboard -o -t TARGETS`` records xclip's own
exit code and no-owner stderr (the wording is version-dependent), and the
library's public readers must read absence: ``inspect()`` empty, ``paste()``
``""``, ``paste_html()`` / ``paste_files()`` / ``paste_image()`` ``None``.
Later ``clear()`` steps append to ``_probe``.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no X11-only session or no
xclip is available (never silent verified success). Not run by default
pytest.
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
from linux_x11_native_text_support import xvfb_version
from native_probe_common import linux_x11_environment

XCLIP_TARGETS = ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"]


def _probe(observed: dict) -> list[dict]:
    from clipboard import _desktop

    steps = []
    fresh = helper(XCLIP_TARGETS)
    observed["fresh_unowned_targets"] = fresh
    reads = read_everything()
    no_owner = fresh.get("returncode", 0) != 0 and _desktop._xclip_reports_no_owner(
        fresh.get("stderr", "")
    )
    steps.append(
        step(
            "1_fresh_unowned_clipboard_reads_empty",
            no_owner and reads_empty(reads),
            xclip_targets=fresh,
            classified_no_owner=no_owner,
            reads=reads,
        )
    )
    return steps


def main() -> int:
    reason = None
    if not sys.platform.startswith("linux"):
        reason = f"not Linux (platform {sys.platform!r})"
    elif not os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        reason = "needs an X11-only session (DISPLAY set, no WAYLAND_DISPLAY)"
    elif shutil.which("xclip") is None:
        reason = "xclip not found on PATH (apt install xclip)"
    if reason is not None:
        report(ok=False, verified=False, evidence_limit=True, reason=reason)
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
        desktop="Linux X11",
        failed_steps=failed,
        observed=observed,
        steps=steps,
        environment=linux_x11_environment(
            distro=distro(),
            kernel=os.uname().release,
            xvfb_version=xvfb_version(),
            consumer="xclip -selection clipboard -o -t TARGETS (independent)",
        ),
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
