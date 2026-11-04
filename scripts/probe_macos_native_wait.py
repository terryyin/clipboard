#!/usr/bin/env python3
"""Gated probe: macOS Aqua ``wait_for_kind`` / ``wait_for_text_change``
against an independent producer.

Setup: ``clipboard.clear()`` in this process; an independent JXA
``NSPasteboard types`` listing must then be empty.

Step 1: a **child** Python starts ``wait_for_kind("text", timeout=20)``
(default 0.5 s interval) on the empty pasteboard and announces its first
observation on stdout; about 1 s after that an **independent** ``pbcopy``
process copies text while the child is still waiting. The child reports the
returned snapshot, its elapsed time, and every snapshot its observations
returned (the default native inspector, wrapped only to record each result).
Holds when the snapshot lists ``"text"``, at least one earlier observation
saw no text, and the wait
returned after the copy within one interval plus two observations (one may
have started just before the copy landed) plus 0.1 s of process slack.

Step 2: ``clear()`` again, then a child ``wait_for_kind("html", timeout=1)``
with nothing copied returns ``None`` no earlier than the timeout and no later
than the timeout plus one observation (plus 0.1 s of process slack), with no
observation started after the deadline.

Step 3: an independent ``pbcopy`` copies the old text, then a child
``wait_for_text_change(timeout=20)`` reads it as its baseline and announces
that read; about 1 s later an independent ``pbcopy`` copies the new text.
Holds when the baseline observation saw the old text, the child returned the
new text, and it returned after the copy within the step 1 latency bound.

Step 4: an independent ``pbcopy`` copies the old text, a child
``wait_for_text_change(timeout=3)`` reads it as its baseline, then
``clear()`` empties the pasteboard and about 1 s later an independent
``pbcopy`` copies the identical old text again. Holds when an observation saw
the cleared pasteboard (``""``), a later one saw the old text again, and the
wait returned ``None`` within the step 2 timeout bound, with no observation
started after the deadline (clearing and identical recopy are not changes).

The four steps live in ``native_wait_support`` and are the same on the
Linux X11, Linux Wayland and Windows wait probes; this probe supplies the
macOS desktop (``macos_native_wait_support.MACOS``) and its session gate.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` off a macOS Aqua session
(not darwin, no console session, or a locked screen; the wrapper fails on it,
never a silent verified success). Needs no ``clipboard[images]``. Not run by
default pytest. **Replaces the live clipboard.**
"""

from __future__ import annotations

import sys

from macos_native_wait_support import MACOS, session_state
from native_probe_common import macos_environment
from native_wait_harness import INTERVAL_S
from native_wait_support import report, run_steps


def main() -> int:
    if sys.platform != "darwin":
        report(
            ok=False,
            verified=False,
            evidence_limit=True,
            reason=f"not macOS Aqua (platform {sys.platform!r})",
        )
        return 2
    session = session_state()
    if session["locked"] or not session["on_console"]:
        report(
            ok=False,
            verified=False,
            evidence_limit=True,
            reason="macOS Aqua session not usable: locked screen or not on console",
            session=session,
        )
        return 2
    steps = run_steps(MACOS)
    failed = [s["step"] for s in steps if not s["ok"]]
    env = macos_environment(
        producer="pbcopy (independent process, LANG=en_US.UTF-8)",
        library_under_test=(
            "clipboard.wait_for_kind / clipboard.wait_for_text_change in a child Python"
        ),
        type_consumer="osascript -l JavaScript NSPasteboard.generalPasteboard.types",
        helper="osascript + pbcopy (macOS built-in)",
    )
    report(
        ok=not failed,
        verified=not failed,
        evidence_limit=False,
        failed_steps=failed,
        steps=steps,
        session=session,
        environment=env,
        floors={
            "macos_product": env["macos_product"],
            "macos_build": env["macos_build"],
            "machine": env["machine"],
            "interval_s": INTERVAL_S,
        },
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
