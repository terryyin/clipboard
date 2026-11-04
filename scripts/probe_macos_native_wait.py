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
    INTERVAL_S,
    ended_at_timeout,
    finish_child,
    pbcopy_independent,
    returned_after_copy,
    session_state,
    start_kind_child,
    start_text_change_child,
)
from native_probe_common import macos_environment

WAIT_TIMEOUT_S = 20
NONE_TIMEOUT_S = 1
COPY_DELAY_S = 1.0
PRODUCED_TEXT = "wait probe text"
CHANGE_TIMEOUT_S = 20
RECOPY_TIMEOUT_S = 3
OLD_TEXT = "wait probe old text"
NEW_TEXT = "wait probe new text"


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
    child = start_kind_child("text", WAIT_TIMEOUT_S)
    time.sleep(COPY_DELAY_S)
    copied = pbcopy_independent(PRODUCED_TEXT)
    run = finish_child(child, WAIT_TIMEOUT_S + 30)
    timely, observations, evidence = returned_after_copy(run, copied, WAIT_TIMEOUT_S)
    snapshot = (run.get("outcome") or {}).get("snapshot")
    ok = (
        setup["empty"]
        and timely
        and "text" in (snapshot or {}).get("kinds", [])
        and any("text" not in o["kinds"] for o in observations[:-1])
    )
    return step(
        "1_wait_for_text_returns_after_independent_pbcopy",
        ok,
        setup=setup,
        producer=copied,
        child=run,
        snapshot=snapshot,
        **evidence,
    )


def _nothing_copied_step(list_types) -> dict:
    setup = _cleared(list_types)
    child = start_kind_child("html", NONE_TIMEOUT_S)
    run = finish_child(child, NONE_TIMEOUT_S + 30)
    bounded, _, evidence = ended_at_timeout(run, "snapshot", NONE_TIMEOUT_S)
    return step(
        "2_wait_for_html_with_nothing_copied_returns_none_at_timeout",
        setup["empty"] and bounded,
        setup=setup,
        child=run,
        **evidence,
    )


def _text_change_step() -> dict:
    baseline = pbcopy_independent(OLD_TEXT)
    child = start_text_change_child(CHANGE_TIMEOUT_S)
    time.sleep(COPY_DELAY_S)
    copied = pbcopy_independent(NEW_TEXT)
    run = finish_child(child, CHANGE_TIMEOUT_S + 30)
    timely, observations, evidence = returned_after_copy(run, copied, CHANGE_TIMEOUT_S)
    texts = [o["text"] for o in observations]
    text = (run.get("outcome") or {}).get("text", "missing")
    ok = (
        baseline["returncode"] == 0
        and timely
        and texts[:1] == [OLD_TEXT]
        and text == NEW_TEXT
    )
    return step(
        "3_wait_for_text_change_returns_independent_new_text",
        ok,
        baseline_producer=baseline,
        producer=copied,
        child=run,
        text=text,
        observed_texts=texts,
        **evidence,
    )


def _clear_then_recopy_step(list_types) -> dict:
    import clipboard

    baseline = pbcopy_independent(OLD_TEXT)
    child = start_text_change_child(RECOPY_TIMEOUT_S)
    cleared = _cleared(list_types)
    time.sleep(COPY_DELAY_S)
    recopied = pbcopy_independent(OLD_TEXT)
    run = finish_child(child, RECOPY_TIMEOUT_S + 30)
    bounded, observations, evidence = ended_at_timeout(run, "text", RECOPY_TIMEOUT_S)
    texts = [o["text"] for o in observations]
    first_clear = texts.index("") if "" in texts else len(texts)
    ok = (
        baseline["returncode"] == 0
        and cleared["empty"]
        and recopied["returncode"] == 0
        and bounded
        and texts[:1] == [OLD_TEXT]
        and OLD_TEXT in texts[first_clear + 1 :]
    )
    clipboard.clear()
    return step(
        "4_wait_for_text_change_ignores_clear_then_identical_recopy",
        ok,
        baseline_producer=baseline,
        clear=cleared,
        producer=recopied,
        child=run,
        observed_texts=texts,
        **evidence,
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
    for reset in (
        clipboard.set_clipboard_inspector,
        clipboard.set_clipboard_clearer,
        clipboard.set_text_clipboard_reader,
    ):
        reset(None)
    steps = [
        _text_appears_step(list_types_independent),
        _nothing_copied_step(list_types_independent),
        _text_change_step(),
        _clear_then_recopy_step(list_types_independent),
    ]
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
