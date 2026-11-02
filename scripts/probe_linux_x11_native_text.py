#!/usr/bin/env python3
"""Independent producer/consumer probe: Linux X11 CLIPBOARD text <-> copy/paste.

Producers and consumers that are not this library run in other processes:
background ``xclip -selection clipboard [-t T] -i`` owners and
``xclip -selection clipboard -o -t T`` consumers. ``copy()`` runs in a child
Python that exits before the independent consumer reads (writer-exit
lifetime). Failure steps run in child Pythons with a display that has no
server and with ``PATH`` lacking ``xclip``, and record xclip's own stderr so
the classification premise is settled by observation.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no X11 session or no xclip
is available (never silent verified success). Overwrites and finally empties
the CLIPBOARD (kills every xclip owner). Not run by default pytest.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from linux_x11_native_text_support import (
    BOUND_S,
    LATIN,
    NO_XCLIP_PATH,
    TEXT,
    child,
    dead_display,
    errors_within_bound,
    own,
    paste_now,
    record,
    release_all,
    report,
    step,
    targets,
    xclip_out,
)
from stdlib_png import solid_red_png_bytes


def _probe(observed: dict) -> list[dict]:
    import clipboard

    steps = []
    data = TEXT.encode("utf-8")
    own(data, None, "UTF8_STRING")
    got = paste_now()
    steps.append(
        step(
            "1_independent_producer_to_paste",
            got == {"paste": TEXT},
            **got,
            targets=targets(),
        )
    )

    kid = child([["copy", TEXT]])
    consumer = xclip_out("UTF8_STRING")
    ok = kid["returncode"] == 0 and "error" not in (kid.get("ops") or [{}])[0]
    steps.append(
        step(
            "2_child_copy_exits_then_independent_xclip_o",
            ok and consumer.returncode == 0 and consumer.stdout == data,
            child=kid,
            consumer=record(consumer),
            expected_hex=data.hex(),
            targets=targets(),
        )
    )

    clipboard.copy("")
    got = paste_now()
    steps.append(
        step(
            "3_copy_empty_then_paste",
            got == {"paste": ""},
            **got,
            consumer=record(xclip_out("UTF8_STRING")),
            targets=targets(),
        )
    )

    own(LATIN.encode("latin-1"), "STRING", "STRING")
    offered, utf8_request = targets(), xclip_out("UTF8_STRING")
    observed["string_owner_utf8_request"] = record(utf8_request)
    string_only = "STRING" in offered and "UTF8_STRING" not in offered
    got = paste_now()
    steps.append(
        step(
            "4a_string_only_owner_decoded_latin_1",
            string_only and got == {"paste": LATIN},
            **got,
            targets=offered,
            string_only_offer=string_only,
            expected=LATIN,
        )
    )

    own(solid_red_png_bytes(), "image/png", "image/png")
    got = paste_now()
    steps.append(
        step(
            "4b_image_only_reads_empty", got == {"paste": ""}, **got, targets=targets()
        )
    )

    release_all()
    unowned = xclip_out("TARGETS")
    observed["no_owner_targets"] = record(unowned)
    got = paste_now()
    steps.append(
        step(
            "4c_unowned_reads_empty",
            unowned.returncode != 0 and got == {"paste": ""},
            **got,
            targets=record(unowned),
        )
    )

    dead = dead_display()
    env = {**os.environ, "DISPLAY": dead}
    raw = record(xclip_out("TARGETS", env))
    observed["dead_display"] = {"display": dead, **raw}
    kid = child([["paste"], ["copy", "x"]], env)
    steps.append(
        step(
            "5_dead_display_raises_quoting_xclip_within_bound",
            kid.get("backend") == "x11" and errors_within_bound(kid, [raw["stderr"]]),
            display=dead,
            xclip_direct=raw,
            child=kid,
            bound_s=BOUND_S,
        )
    )

    env = {**os.environ, "PATH": NO_XCLIP_PATH}
    kid = child([["paste"], ["copy", "x"]], env)
    steps.append(
        step(
            "6_path_without_xclip_names_install_hint",
            errors_within_bound(kid, ["xclip", "apt-get install xclip"]),
            path=NO_XCLIP_PATH,
            child=kid,
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
    backend = clipboard._text._select_text_backend()
    try:
        steps = _probe(observed)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        steps = [step("probe_aborted", False, error=f"{type(exc).__name__}: {exc}")]
    finally:
        release_all()
    failed = [s["step"] for s in steps if not s["ok"]]
    report(
        ok=not failed,
        verified=not failed,
        desktop="Linux X11",
        backend=backend,
        failed_steps=failed,
        observed_stderr=observed,
        steps=steps,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
