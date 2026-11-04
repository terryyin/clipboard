#!/usr/bin/env python3
"""Gated probe: Linux X11 (Xvfb) ``wait_for_kind`` / ``wait_for_text_change``
against an independent ``xclip`` producer.

The four steps are ``native_wait_support``'s, shared with the macOS, Linux
Wayland and Windows wait probes. Setup before steps 1, 2 and 4:
``clipboard.clear()`` in this process; an independent ``xclip -selection
clipboard -o -t TARGETS`` must then report no CLIPBOARD owner.

Step 1: a child Python starts ``wait_for_kind("text", timeout=20)`` on the
unowned CLIPBOARD; about 1 s after its first observation an independent
background ``xclip -selection clipboard -i`` owner serves text (the copy
counts as finished once ``xclip -o -t UTF8_STRING`` reads it back). Holds when
the returned snapshot lists ``"text"``, an earlier observation saw no text,
and the wait returned after the copy within one interval plus two
observations plus 0.1 s. Every observation's kinds and native formats are
recorded (``child.outcome.observations``, summarised as ``observed_kinds``),
with the ``TARGETS`` listing after the copy. Step 2: a child
``wait_for_kind("html", timeout=1)`` with nothing copied returns ``None``
within the timeout plus one observation. Step 3: an independent ``xclip``
copies the old text, a child ``wait_for_text_change(timeout=20)`` reads it as
its baseline, and an independent ``xclip`` copies the new text, which the
wait returns. Step 4: baseline old text, ``clear()``, then an identical
independent recopy; the wait returns ``None`` at its 3 s timeout.

Every ``xclip`` owner is stopped when the probe ends. Prints one JSON object
on stdout. Exit 0 when every step holds, 1 naming the failed steps, and 2
with ``evidence_limit`` without an X11-only session or ``xclip`` (the wrapper
fails on it). Not run by default pytest. **Replaces the CLIPBOARD.**
"""

from __future__ import annotations

import os
import shutil
import sys

from linux_x11_native_clear_support import X11
from linux_x11_native_text_support import own, release_all, xvfb_version
from native_clear_support import distro
from native_probe_common import linux_x11_environment
from native_wait_harness import INTERVAL_S, WaitDesktop
from native_wait_support import report, run_steps

PRODUCER = ["xclip", "-selection", "clipboard", "-i"]


def xclip_produce(text: str) -> dict:
    """Independent producer: a background ``xclip`` owner serving ``text``."""
    try:
        own(text.encode("utf-8"), None, "UTF8_STRING")
    except (OSError, RuntimeError) as exc:
        return {"cmd": PRODUCER, "error": f"{type(exc).__name__}: {exc}"}
    return {"cmd": PRODUCER, "returncode": 0, "served": "UTF8_STRING"}


DESKTOP = WaitDesktop(
    producer="xclip",
    produce=xclip_produce,
    listing=X11.listing,
    is_empty=X11.is_empty,
)


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
    try:
        steps = run_steps(DESKTOP)
    finally:
        release_all()
    failed = [s["step"] for s in steps if not s["ok"]]
    env = linux_x11_environment(
        distro=distro(),
        kernel=os.uname().release,
        xvfb_version=xvfb_version(),
        producer="xclip -selection clipboard -i (independent, background owner)",
        consumer="xclip -selection clipboard -o -t TARGETS (independent)",
        library_under_test=(
            "clipboard.wait_for_kind / clipboard.wait_for_text_change in a child Python"
        ),
    )
    report(
        ok=not failed,
        verified=not failed,
        evidence_limit=False,
        desktop="Linux X11",
        failed_steps=failed,
        steps=steps,
        environment=env,
        floors={
            "xclip_version": env["xclip_version"],
            "xvfb_version": env["xvfb_version"],
            "interval_s": INTERVAL_S,
        },
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
