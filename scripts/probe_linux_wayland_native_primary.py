#!/usr/bin/env python3
"""Independent producer/consumer probe: Linux Wayland (Sway) PRIMARY <-> *_primary.

Producers and consumers that are not this library run in other processes:
``wl-copy [--primary] --type text/plain;charset=utf-8`` producers (each forks
its own source) and ``wl-paste [--primary] -n`` consumers. Every library call
runs in a child Python (no ``DISPLAY``, so text dispatch is Wayland's) that
exits before the independent consumer reads (writer-exit lifetime), so a
same-process write-then-read is never the evidence. Steps follow seed
SEED-001#primary-selection example 5 (examples 1–4 and 9 on Sway): a fresh,
unselected PRIMARY reads ``""``; different PRIMARY / CLIPBOARD offers are
read apart; ``copy_primary`` leaves CLIPBOARD; ``copy`` leaves PRIMARY;
rejected text leaves PRIMARY; ``copy_primary("")`` leaves PRIMARY reading
``""``; a ``PATH`` without ``wl-paste`` raises naming wl-clipboard within the
bound.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no Wayland session, no
running Sway, or no wl-clipboard is available (never silent verified
success). Expects a fresh Sway (PRIMARY never set); overwrites and finally
clears CLIPBOARD and PRIMARY. Not default pytest. Scoped to Sway; it does
not generalize to other compositors, and a compositor without
primary-selection support is not observed here.
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path

from linux_wayland_native_text_support import (
    UTF8_TYPE,
    evidence_limit,
    failures_within_bound,
    path_with_only_wl_copy,
    report,
    session_env,
    wl_copy,
    wl_paste,
)
from linux_x11_native_text_support import BOUND_S, child, record, step
from native_probe_wayland import COMPOSITOR

COPIED = "copied ✓"
SELECTED = "selected ✓"
MIDDLE = "for middle click ✓"
NEW_COPY = "new copy ✓"
NOTHING = ("Nothing is copied", "No selection")
FLAGS = "[--primary] "


def _flags(primary: bool) -> list[str]:
    return ["--primary"] if primary else []


def _serves(primary: bool) -> dict:
    """What an independent ``wl-paste [--primary] -n`` consumer reads."""
    out = record(wl_paste(*_flags(primary), "-n"))
    out["text"] = bytes.fromhex(out["stdout_hex"]).decode("utf-8", "replace")
    return out


def _offer(text: str, primary: bool) -> dict:
    """Independent producer: wl-copy ``text``, then wait until it is served."""
    produced = wl_copy([*_flags(primary), "--type", UTF8_TYPE], text.encode())
    if produced["returncode"] != 0:
        raise RuntimeError(f"independent producer failed: {produced}")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if _serves(primary)["text"] == text:
            return produced
        time.sleep(0.05)
    raise RuntimeError(f"independent wl-copy {_flags(primary)} did not serve in time")


def _clear_both() -> None:
    for primary in (True, False):
        wl_copy([*_flags(primary), "--clear"], None)


def _ops_ok(kid: dict) -> bool:
    return (
        kid.get("returncode") == 0
        and kid.get("backend") == "wayland"
        and all("error" not in op for op in kid.get("ops") or [{}])
    )


def _probe(observed: dict) -> list[dict]:
    steps = []
    env = session_env()

    listing = record(wl_paste("--primary", "--list-types"))
    observed["fresh_primary_list_types"] = listing
    kid = child([["paste_primary"]], env)
    steps.append(
        step(
            "4_fresh_unselected_primary_reads_empty",
            listing["returncode"] != 0
            and listing["stderr"] in NOTHING
            and _ops_ok(kid)
            and kid["ops"][0].get("paste_primary") == "",
            primary_list_types=listing,
            child=kid,
        )
    )

    producers = {
        "clipboard": _offer(COPIED, primary=False),
        "primary": _offer(SELECTED, primary=True),
    }
    observed["primary_list_types"] = record(wl_paste("--primary", "--list-types"))
    kid = child([["paste_primary"], ["paste"]], env)
    ops = kid.get("ops") or [{}, {}]
    steps.append(
        step(
            "1_different_offers_paste_primary_and_paste",
            _ops_ok(kid)
            and ops[0].get("paste_primary") == SELECTED
            and ops[1].get("paste") == COPIED,
            producers=producers,
            child=kid,
        )
    )

    kid = child([["copy_primary", MIDDLE]], env)
    primary, clip = _serves(True), _serves(False)
    steps.append(
        step(
            "2_child_copy_primary_exits_then_independent_consumers",
            _ops_ok(kid) and primary["text"] == MIDDLE and clip["text"] == COPIED,
            child=kid,
            primary_consumer=primary,
            clipboard_consumer=clip,
        )
    )

    kid = child([["copy", NEW_COPY]], env)
    primary, clip = _serves(True), _serves(False)
    steps.append(
        step(
            "3_child_copy_leaves_primary",
            _ops_ok(kid) and clip["text"] == NEW_COPY and primary["text"] == MIDDLE,
            child=kid,
            primary_consumer=primary,
            clipboard_consumer=clip,
        )
    )

    kid = child([["copy_primary", "a\x00b"]], env)
    ops = kid.get("ops") or [{}]
    primary, clip = _serves(True), _serves(False)
    steps.append(
        step(
            "9_rejected_copy_primary_keeps_primary",
            ops[0].get("error_type") == "ClipboardContentError"
            and primary["text"] == MIDDLE
            and clip["text"] == NEW_COPY,
            child=kid,
            primary_consumer=primary,
            clipboard_consumer=clip,
        )
    )

    kid = child([["copy_primary", ""]], env)
    primary, clip = _serves(True), _serves(False)
    reader = child([["paste_primary"]], env)
    steps.append(
        step(
            "5_child_copy_primary_empty_reads_empty",
            _ops_ok(kid)
            and primary["returncode"] == 0
            and primary["text"] == ""
            and _ops_ok(reader)
            and reader["ops"][0].get("paste_primary") == ""
            and clip["text"] == NEW_COPY,
            child=kid,
            primary_consumer=primary,
            clipboard_consumer=clip,
            reader=reader,
        )
    )

    with tempfile.TemporaryDirectory(prefix="clipboard-no-wl-paste-") as raw:
        path = path_with_only_wl_copy(Path(raw))
        kid = child([["paste_primary"], ["copy_primary", "x"]], session_env(PATH=path))
    primary, clip = _serves(True), _serves(False)
    hint = "apt-get install wl-clipboard"
    steps.append(
        step(
            "7_path_without_wl_paste_names_wl_clipboard_within_bound",
            failures_within_bound(kid, {"paste_primary": hint, "copy_primary": hint})
            and all("primary selection" in op["error"] for op in kid["ops"])
            and primary["text"] == ""
            and clip["text"] == NEW_COPY,
            path=path,
            child=kid,
            primary_consumer=primary,
            clipboard_consumer=clip,
            bound_s=BOUND_S,
        )
    )
    return steps


def main() -> int:
    reason = evidence_limit()
    if reason is not None:
        report(
            FLAGS,
            ok=False,
            verified=False,
            evidence_limit=True,
            compositor_generalization=False,
            reason=reason,
        )
        return 2
    observed: dict = {}
    try:
        steps = _probe(observed)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        steps = [step("probe_aborted", False, error=f"{type(exc).__name__}: {exc}")]
    finally:
        _clear_both()
    failed = [s["step"] for s in steps if not s["ok"]]
    report(
        FLAGS,
        ok=not failed,
        verified=not failed,
        desktop=f"Linux Wayland ({COMPOSITOR})",
        compositor_generalization=False,
        backend="wayland wl-clipboard --primary",
        failed_steps=failed,
        observed=observed,
        steps=steps,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
