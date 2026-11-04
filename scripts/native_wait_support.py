"""Four shared steps, runner and report for every native wait probe.

The child-wait harness and timing rules live in ``native_wait_harness``;
each desktop's probe keeps only its session gate and environment floors.
Probes import ``WaitDesktop`` and ``INTERVAL_S`` from the harness module.
"""

from __future__ import annotations

import json
import time

from native_wait_harness import (
    WaitDesktop,
    ended_at_timeout,
    finish_child,
    returned_after_copy,
    start_kind_child,
    start_text_change_child,
)

WAIT_TIMEOUT_S = 20
NONE_TIMEOUT_S = 1
COPY_DELAY_S = 1.0
PRODUCED_TEXT = "wait probe text"
CHANGE_TIMEOUT_S = 20
RECOPY_TIMEOUT_S = 3
OLD_TEXT = "wait probe old text"
NEW_TEXT = "wait probe new text"


def step(name: str, ok: bool, **observed) -> dict:
    return {"step": name, "ok": bool(ok), **observed}


def text_appears_step(desktop: WaitDesktop) -> dict:
    """Step 1: ``wait_for_kind("text")`` from empty ends after the copy."""
    setup = desktop.cleared()
    child = start_kind_child("text", WAIT_TIMEOUT_S)
    time.sleep(COPY_DELAY_S)
    copied = desktop.copy(PRODUCED_TEXT)
    run = finish_child(child, WAIT_TIMEOUT_S + 30)
    listing_after_copy = desktop.listing()
    timely, observations, evidence = returned_after_copy(run, copied, WAIT_TIMEOUT_S)
    snapshot = (run.get("outcome") or {}).get("snapshot")
    ok = (
        setup["empty"]
        and timely
        and "text" in (snapshot or {}).get("kinds", [])
        and any("text" not in o["kinds"] for o in observations[:-1])
    )
    return step(
        f"1_wait_for_text_returns_after_independent_{desktop.producer}",
        ok,
        setup=setup,
        producer=copied,
        child=run,
        snapshot=snapshot,
        observed_kinds=[o["kinds"] for o in observations],
        listing_after_copy=listing_after_copy,
        **evidence,
    )


def nothing_copied_step(desktop: WaitDesktop) -> dict:
    """Step 2: ``wait_for_kind("html", timeout=1)`` with nothing copied."""
    setup = desktop.cleared()
    child = start_kind_child("html", NONE_TIMEOUT_S)
    run = finish_child(child, NONE_TIMEOUT_S + 30)
    bounded, observations, evidence = ended_at_timeout(run, "snapshot", NONE_TIMEOUT_S)
    return step(
        "2_wait_for_html_with_nothing_copied_returns_none_at_timeout",
        setup["empty"] and bounded,
        setup=setup,
        child=run,
        observed_kinds=[o["kinds"] for o in observations],
        **evidence,
    )


def text_change_step(desktop: WaitDesktop) -> dict:
    """Step 3: baseline old text, then the independent new text ends the wait."""
    baseline = desktop.copy(OLD_TEXT)
    child = start_text_change_child(CHANGE_TIMEOUT_S)
    time.sleep(COPY_DELAY_S)
    copied = desktop.copy(NEW_TEXT)
    run = finish_child(child, CHANGE_TIMEOUT_S + 30)
    timely, observations, evidence = returned_after_copy(run, copied, CHANGE_TIMEOUT_S)
    texts = [o["text"] for o in observations]
    text = (run.get("outcome") or {}).get("text", "missing")
    ok = (
        baseline.get("returncode") == 0
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


def clear_then_recopy_step(desktop: WaitDesktop) -> dict:
    """Step 4: clearing and an identical recopy are not changes."""
    baseline = desktop.copy(OLD_TEXT)
    child = start_text_change_child(RECOPY_TIMEOUT_S)
    cleared = desktop.cleared()
    time.sleep(COPY_DELAY_S)
    recopied = desktop.copy(OLD_TEXT)
    run = finish_child(child, RECOPY_TIMEOUT_S + 30)
    bounded, observations, evidence = ended_at_timeout(run, "text", RECOPY_TIMEOUT_S)
    texts = [o["text"] for o in observations]
    first_clear = texts.index("") if "" in texts else len(texts)
    ok = (
        baseline.get("returncode") == 0
        and cleared["empty"]
        and recopied.get("returncode") == 0
        and bounded
        and texts[:1] == [OLD_TEXT]
        and OLD_TEXT in texts[first_clear + 1 :]
    )
    final_clear = desktop.cleared()
    return step(
        "4_wait_for_text_change_ignores_clear_then_identical_recopy",
        ok,
        baseline_producer=baseline,
        clear=cleared,
        producer=recopied,
        child=run,
        observed_texts=texts,
        final_clear=final_clear,
        **evidence,
    )


def run_steps(desktop: WaitDesktop) -> list[dict]:
    """Reset the seams the children rely on, then run the four steps."""
    import clipboard

    for reset in (
        clipboard.set_clipboard_inspector,
        clipboard.set_clipboard_clearer,
        clipboard.set_text_clipboard_reader,
    ):
        reset(None)
    return [
        text_appears_step(desktop),
        nothing_copied_step(desktop),
        text_change_step(desktop),
        clear_then_recopy_step(desktop),
    ]


def report(**fields) -> None:
    print(json.dumps(fields, indent=2, sort_keys=True, ensure_ascii=False))
