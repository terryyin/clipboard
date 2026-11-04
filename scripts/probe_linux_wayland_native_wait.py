#!/usr/bin/env python3
"""Gated probe: Linux Wayland (Sway) ``wait_for_kind`` / ``wait_for_text_change``
against an independent ``wl-copy`` producer.

The four steps are ``native_wait_support``'s, shared with the macOS, Linux
X11 and Windows wait probes. Setup before steps 1, 2 and 4:
``clipboard.clear()`` in this process; an independent ``wl-paste -l`` must
then report nothing copied.

Step 1: a child Python starts ``wait_for_kind("text", timeout=20)`` on the
empty selection; about 1 s after its first observation an independent
``wl-copy`` (no ``--type``; its forked source serves the text) copies text,
the copy counting as finished once ``wl-paste -n -t
text/plain;charset=utf-8`` reads it back. Holds when the returned snapshot
lists ``"text"``, an earlier observation saw no text, and the wait returned
after the copy within one interval plus two observations plus 0.1 s. Every
observation's kinds and native formats are recorded
(``child.outcome.observations``, summarised as ``observed_kinds``), with the
``wl-paste -l`` listing after the copy. Step 2: a child
``wait_for_kind("html", timeout=1)`` with nothing copied returns ``None``
within the timeout plus one observation. Step 3: an independent ``wl-copy``
copies the old text, a child ``wait_for_text_change(timeout=20)`` reads it as
its baseline, and an independent ``wl-copy`` copies the new text, which the
wait returns. Step 4: baseline old text, ``clear()``, then an identical
independent recopy; the wait returns ``None`` at its 3 s timeout.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` without a Wayland session, a
running Sway or wl-clipboard (the wrapper fails on it). Scoped to Sway. Not
run by default pytest. **Replaces the selection.**
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from linux_wayland_native_clear_support import WAYLAND
from linux_wayland_native_text_support import UTF8_TYPE, offer
from native_clear_support import distro
from native_probe_wayland import COMPOSITOR, sway_running, wayland_paste_environment
from native_wait_support import INTERVAL_S, WaitDesktop, report, run_steps


def wl_copy_produce(text: str) -> dict:
    """Independent producer: ``wl-copy`` with no type, until it serves ``text``."""
    try:
        produced = offer(text.encode("utf-8"), [], UTF8_TYPE)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return {"argv": ["wl-copy"], "error": f"{type(exc).__name__}: {exc}"}
    return {**produced, "served": UTF8_TYPE}


DESKTOP = WaitDesktop(
    producer="wl_copy",
    produce=wl_copy_produce,
    listing=WAYLAND.listing,
    is_empty=WAYLAND.is_empty,
)


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
    steps = run_steps(DESKTOP)
    failed = [s["step"] for s in steps if not s["ok"]]
    env = wayland_paste_environment(
        distro=distro(),
        producer="wl-copy (independent, no --type, forked source)",
        consumer="wl-paste -l (independent)",
        library_under_test=(
            "clipboard.wait_for_kind / clipboard.wait_for_text_change in a child Python"
        ),
    )
    report(
        ok=not failed,
        verified=not failed,
        evidence_limit=False,
        desktop=f"Linux Wayland ({COMPOSITOR})",
        compositor_generalization=False,
        failed_steps=failed,
        steps=steps,
        environment=env,
        floors={
            "compositor_version": env["compositor_version"],
            "wl_clipboard_version": env["wl_clipboard_version"],
            "interval_s": INTERVAL_S,
        },
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
