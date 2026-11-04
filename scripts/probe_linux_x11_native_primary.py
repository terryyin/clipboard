#!/usr/bin/env python3
"""Independent producer/consumer probe: Linux X11 PRIMARY <-> *_primary calls.

Producers and consumers that are not this library run in other processes:
background ``xclip -selection primary|clipboard -i`` owners and
``xclip -selection primary|clipboard -o -t UTF8_STRING`` consumers. Every
library call runs in a child Python that exits before the independent
consumer reads (writer-exit lifetime), so a same-process write-then-read is
never the evidence. Steps follow seed SEED-001#primary-selection examples:
a fresh unowned PRIMARY reads ``""`` (4); different PRIMARY / CLIPBOARD
owners are read apart (1); ``copy_primary`` leaves CLIPBOARD (2); ``copy``
leaves PRIMARY (3); rejected text leaves PRIMARY (9); a ``PATH`` with
``xsel`` but no ``xclip`` still pastes CLIPBOARD through pyperclip while
PRIMARY raises naming ``xclip`` within the bound (8).

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no X11 session or no xclip
is available (never silent verified success). Overwrites and finally empties
CLIPBOARD and PRIMARY (kills every xclip owner). Not run by default pytest.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

from linux_x11_native_text_support import (
    BOUND_S,
    SLACK_S,
    child,
    own,
    record,
    release_all,
    report,
    step,
    xclip_out,
)

COPIED = "copied ✓"
SELECTED = "selected ✓"
MIDDLE = "for middle click ✓"
NEW_COPY = "new copy ✓"
SELECTIONS = "primary|clipboard"


def _serves(selection: str) -> dict:
    """What an independent consumer reads from ``selection`` as UTF8_STRING."""
    out = record(xclip_out("UTF8_STRING", selection=selection))
    out["text"] = bytes.fromhex(out["stdout_hex"]).decode("utf-8", "replace")
    return out


def _ops_ok(kid: dict) -> bool:
    return kid.get("returncode") == 0 and all(
        "error" not in op for op in kid.get("ops") or [{}]
    )


def _primary_error(op: dict) -> bool:
    return (
        op.get("error_type") == "ClipboardContentError"
        and "primary selection" in op.get("error", "")
        and "xclip" in op.get("error", "")
        and op["seconds"] < BOUND_S + SLACK_S
    )


def _probe(observed: dict, xsel_dir: str) -> list[dict]:
    steps = []

    unowned = xclip_out("TARGETS", selection="primary")
    observed["no_owner_primary_targets"] = record(unowned)
    kid = child([["paste_primary"]])
    steps.append(
        step(
            "4_fresh_unowned_primary_reads_empty",
            unowned.returncode != 0
            and _ops_ok(kid)
            and kid["ops"][0].get("paste_primary") == "",
            primary_targets=record(unowned),
            child=kid,
        )
    )

    own(COPIED.encode(), None, "UTF8_STRING", "clipboard")
    own(SELECTED.encode(), None, "UTF8_STRING", "primary")
    kid = child([["paste_primary"], ["paste"]])
    ops = kid.get("ops") or [{}, {}]
    steps.append(
        step(
            "1_different_owners_paste_primary_and_paste",
            _ops_ok(kid)
            and ops[0].get("paste_primary") == SELECTED
            and ops[1].get("paste") == COPIED,
            child=kid,
        )
    )

    kid = child([["copy_primary", MIDDLE]])
    primary, clip = _serves("primary"), _serves("clipboard")
    steps.append(
        step(
            "2_child_copy_primary_exits_then_independent_consumers",
            _ops_ok(kid) and primary["text"] == MIDDLE and clip["text"] == COPIED,
            child=kid,
            primary_consumer=primary,
            clipboard_consumer=clip,
        )
    )

    kid = child([["copy", NEW_COPY]])
    primary, clip = _serves("primary"), _serves("clipboard")
    steps.append(
        step(
            "3_child_copy_leaves_primary",
            _ops_ok(kid) and clip["text"] == NEW_COPY and primary["text"] == MIDDLE,
            child=kid,
            primary_consumer=primary,
            clipboard_consumer=clip,
        )
    )

    kid = child([["copy_primary", "a\x00b"]])
    ops = kid.get("ops") or [{}]
    primary, clip = _serves("primary"), _serves("clipboard")
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

    env = {**os.environ, "PATH": xsel_dir}
    kid = child([["paste"], ["paste_primary"], ["copy_primary", "x"]], env)
    ops = kid.get("ops") or [{}, {}, {}]
    primary, clip = _serves("primary"), _serves("clipboard")
    steps.append(
        step(
            "8_path_with_xsel_but_no_xclip_names_xclip_within_bound",
            kid.get("backend") == "pyperclip"
            and len(ops) == 3
            and ops[0].get("paste") == NEW_COPY
            and all(_primary_error(op) for op in ops[1:])
            and primary["text"] == MIDDLE
            and clip["text"] == NEW_COPY,
            path=xsel_dir,
            path_entries=sorted(os.listdir(xsel_dir)),
            child=kid,
            primary_consumer=primary,
            clipboard_consumer=clip,
            bound_s=BOUND_S,
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
    elif shutil.which("xsel") is None:
        reason = "xsel not found on PATH (apt install xsel; example 8 needs it)"
    if reason is not None:
        report(SELECTIONS, ok=False, verified=False, evidence_limit=True, reason=reason)
        return 2
    observed: dict = {}
    with tempfile.TemporaryDirectory() as xsel_dir:
        # A PATH whose only clipboard helper is xsel (no xclip).
        os.symlink(shutil.which("xsel"), os.path.join(xsel_dir, "xsel"))
        try:
            release_all()
            steps = _probe(observed, xsel_dir)
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            steps = [step("probe_aborted", False, error=f"{type(exc).__name__}: {exc}")]
        finally:
            release_all()
    failed = [s["step"] for s in steps if not s["ok"]]
    report(
        SELECTIONS,
        ok=not failed,
        verified=not failed,
        desktop="Linux X11",
        backend="x11 xclip -selection primary",
        failed_steps=failed,
        observed_stderr=observed,
        steps=steps,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
