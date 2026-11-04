#!/usr/bin/env python3
"""Gated probe: macOS Aqua ``wait_for_kind`` against an independent producer.

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

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` off a macOS Aqua session
(not darwin, no console session, or a locked screen; the wrapper fails on it,
never a silent verified success). Needs no ``clipboard[images]``. Not run by
default pytest. **Replaces the live clipboard.**
"""

from __future__ import annotations

import json
import sys
import time

from macos_native_clear_support import list_types_independent
from macos_native_wait_support import (
    finish_child,
    pbcopy_independent,
    session_state,
    start_child,
)
from native_probe_common import macos_environment

WAIT_TIMEOUT_S = 20
NONE_TIMEOUT_S = 1
INTERVAL_S = 0.5
COPY_DELAY_S = 1.0
SLACK_S = 0.1
PRODUCED_TEXT = "wait probe text"


def report(**fields) -> None:
    print(json.dumps(fields, indent=2, sort_keys=True, ensure_ascii=False))


def step(name: str, ok: bool, **observed) -> dict:
    return {"step": name, "ok": bool(ok), **observed}


def _cleared(list_types) -> dict:
    import clipboard

    clipboard.clear()
    listing = list_types()
    return {"types_after_clear": listing["types"], "empty": listing["types"] == []}


def _text_appears_step(list_types) -> dict:
    setup = _cleared(list_types)
    child = start_child("text", WAIT_TIMEOUT_S)
    time.sleep(COPY_DELAY_S)
    copied = pbcopy_independent(PRODUCED_TEXT)
    run = finish_child(child, WAIT_TIMEOUT_S + 30)
    outcome = run.get("outcome") or {}
    snapshot = outcome.get("snapshot") or {}
    observations = outcome.get("observations", [])
    longest = max((o["duration_s"] for o in observations), default=0.0)
    latency = outcome.get("finished_at", float("inf")) - copied["finished_at"]
    ok = (
        setup["empty"]
        and copied["returncode"] == 0
        and run.get("returncode") == 0
        and outcome.get("raised") is None
        and "text" in snapshot.get("kinds", [])
        and any("text" not in o["kinds"] for o in observations[:-1])
        and outcome["finished_at"] > copied["started_at"]
        and outcome["elapsed_s"] < WAIT_TIMEOUT_S
        and latency <= INTERVAL_S + 2 * longest + SLACK_S
    )
    return step(
        "1_wait_for_text_returns_after_independent_pbcopy",
        ok,
        setup=setup,
        producer=copied,
        child=run,
        snapshot=outcome.get("snapshot"),
        elapsed_s=outcome.get("elapsed_s"),
        latency_after_copy_s=latency,
        observation_count=len(observations),
        longest_observation_s=longest,
    )


def _nothing_copied_step(list_types) -> dict:
    setup = _cleared(list_types)
    child = start_child("html", NONE_TIMEOUT_S)
    run = finish_child(child, NONE_TIMEOUT_S + 30)
    outcome = run.get("outcome") or {}
    observations = outcome.get("observations", [])
    longest = max((o["duration_s"] for o in observations), default=0.0)
    elapsed = outcome.get("elapsed_s", float("inf"))
    deadline = outcome.get("deadline", float("-inf"))
    ok = (
        setup["empty"]
        and run.get("returncode") == 0
        and outcome.get("raised") is None
        and "snapshot" in outcome
        and outcome["snapshot"] is None
        and bool(observations)
        and all(o["started_at"] <= deadline for o in observations)
        and NONE_TIMEOUT_S <= elapsed <= NONE_TIMEOUT_S + longest + SLACK_S
    )
    return step(
        "2_wait_for_html_with_nothing_copied_returns_none_at_timeout",
        ok,
        setup=setup,
        child=run,
        result=outcome.get("snapshot", "missing"),
        elapsed_s=elapsed,
        timeout_s=NONE_TIMEOUT_S,
        observation_count=len(observations),
        longest_observation_s=longest,
    )


def main() -> int:
    if sys.platform != "darwin":
        report(
            ok=False,
            verified=False,
            evidence_limit=True,
            reason=f"not macOS Aqua (platform {sys.platform!r})",
        )
        return 2
    import clipboard

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
    for reset in (clipboard.set_clipboard_inspector, clipboard.set_clipboard_clearer):
        reset(None)
    steps = [
        _text_appears_step(list_types_independent),
        _nothing_copied_step(list_types_independent),
    ]
    failed = [s["step"] for s in steps if not s["ok"]]
    env = macos_environment(
        producer="pbcopy (independent process, LANG=en_US.UTF-8)",
        library_under_test="clipboard.wait_for_kind in a child Python",
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
