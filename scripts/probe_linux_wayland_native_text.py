#!/usr/bin/env python3
"""Independent producer/consumer probe: Linux Wayland (Sway) text <-> copy/paste.

Producers and consumers that are not this library run in other processes:
``wl-copy [--type T]`` producers (each forks its own source) and
``wl-paste -n [-t T]`` consumers. ``copy()`` runs in a child Python that
exits before the independent consumer reads (writer-exit lifetime). Failure
steps run in child Pythons with a ``WAYLAND_DISPLAY`` that has no socket and
with ``PATH`` lacking ``wl-paste``, and record wl-clipboard's own stderr so
the classification premise is settled by observation. Observations that
decide open premises (``-n`` and trailing newlines, an empty-input offer,
untyped wl-copy type guessing, copy-then-immediate-paste visibility) are
recorded under ``observed``.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no Wayland session, no
running Sway, or no wl-clipboard is available (never silent verified
success). Overwrites and finally clears the selection. Not default pytest.
Scoped to Sway; it does not generalize to other compositors.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from linux_wayland_native_text_support import (
    NEWLINE_TEXT,
    SCRIPT_TEXT,
    UTF8_TYPE,
    child_copy_then_consume,
    clear,
    failures_within_bound,
    immediate_visibility,
    offer,
    path_with_only_wl_copy,
    report,
    session_env,
    stale_display,
    types,
    wl_copy,
    wl_paste,
)
from linux_x11_native_text_support import BOUND_S, TEXT, child, paste_now, record, step
from native_probe_wayland import COMPOSITOR, sway_running
from stdlib_png import solid_red_png_bytes


def _probe(observed: dict) -> list[dict]:
    import clipboard

    steps = []
    data = TEXT.encode()
    produced = offer(data, [], UTF8_TYPE)
    observed["untyped_producer_types"] = types()
    observed["wl_paste_without_n"] = record(wl_paste("-t", UTF8_TYPE))
    got = paste_now()
    steps.append(
        step(
            "1_independent_producer_to_paste",
            got == {"paste": TEXT},
            **got,
            producer=produced,
            types=observed["untyped_producer_types"],
        )
    )

    steps.append(
        step(
            "2_child_copy_exits_then_independent_wl_paste",
            **child_copy_then_consume(TEXT),
        )
    )
    observed["default_type_consumer"] = record(wl_paste("-n"))
    script = child_copy_then_consume(SCRIPT_TEXT)
    steps.append(
        step(
            "2b_script_like_text_keeps_text_types",
            script.pop("ok") and UTF8_TYPE in script["types"],
            **script,
        )
    )
    # Why the writer passes --type: what untyped wl-copy offers for a script.
    observed["untyped_wl_copy_script"] = {
        "producer": wl_copy([], SCRIPT_TEXT.encode()),
        "types": types(),
    }

    clipboard.copy("")
    got = paste_now()
    steps.append(
        step(
            "3_copy_empty_then_paste",
            got == {"paste": ""},
            **got,
            list_types=record(wl_paste("--list-types")),
        )
    )
    # Premise for copy(""): does wl-copy with empty input serve an empty offer?
    offer(b"before", ["--type", UTF8_TYPE], UTF8_TYPE)
    empty = {
        "typed": wl_copy(["--type", UTF8_TYPE], b""),
        "list_types": record(wl_paste("--list-types")),
        "consumer": record(wl_paste("-n", "-t", UTF8_TYPE)),
        **paste_now(),
    }
    observed["empty_input_offer"] = empty
    steps.append(
        step(
            "3b_independent_empty_offer_reads_empty",
            # A refused empty input leaves no empty offer to read (recorded).
            empty["typed"]["returncode"] != 0 or empty.get("paste") == "",
            **empty,
        )
    )

    offer(NEWLINE_TEXT.encode(), ["--type", UTF8_TYPE], UTF8_TYPE)
    got = paste_now()
    observed["newline_wl_paste_without_n"] = record(wl_paste("-t", UTF8_TYPE))
    copied = child_copy_then_consume(NEWLINE_TEXT)
    steps.append(
        step(
            "4_trailing_newline_round_trip",
            got == {"paste": NEWLINE_TEXT} and copied.pop("ok"),
            **got,
            expected=NEWLINE_TEXT,
            child_copy=copied,
        )
    )

    offer(solid_red_png_bytes(), ["--type", "image/png"], "image/png")
    got = paste_now()
    steps.append(
        step("5a_image_only_reads_empty", got == {"paste": ""}, **got, types=types())
    )
    clear()
    cleared = record(wl_paste("--list-types"))
    observed["cleared_list_types"] = cleared
    got = paste_now()
    steps.append(
        step("5b_cleared_reads_empty", got == {"paste": ""}, **got, list_types=cleared)
    )

    stale = stale_display()
    env = session_env(WAYLAND_DISPLAY=stale["name"])
    direct = {
        "paste": record(wl_paste("--list-types", env=env))["stderr"],
        "copy": wl_copy(["--type", UTF8_TYPE], b"x", env=env)["stderr"],
    }
    observed["stale_wayland_display"] = {**stale, "stderr": direct}
    kid = child([["paste"], ["copy", "x"]], env)
    steps.append(
        step(
            "6_stale_wayland_display_raises_quoting_helper_within_bound",
            kid.get("backend") == "wayland" and failures_within_bound(kid, direct),
            display=stale,
            helper_stderr=direct,
            child=kid,
            bound_s=BOUND_S,
        )
    )

    with tempfile.TemporaryDirectory(prefix="clipboard-no-wl-paste-") as raw:
        path = path_with_only_wl_copy(Path(raw))
        kid = child([["paste"], ["copy", "x"]], session_env(PATH=path))
    hint = "apt-get install wl-clipboard"
    steps.append(
        step(
            "7_path_without_wl_paste_names_install_hint",
            failures_within_bound(kid, {"paste": hint, "copy": hint})
            and all("wl-paste" in op["error"] for op in kid["ops"]),
            path=path,
            diagnosis="session dispatch (no DISPLAY)",
            child=kid,
        )
    )

    steps.append(
        step(
            "8_copy_then_immediate_paste_sees_new_text",
            **immediate_visibility(observed),
        )
    )
    return steps


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
    import clipboard

    clipboard.set_text_clipboard_writer(None)
    clipboard.set_text_clipboard_reader(None)
    observed: dict = {}
    backend = clipboard._text._select_text_backend()
    try:
        steps = _probe(observed)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        steps = [step("probe_aborted", False, error=f"{type(exc).__name__}: {exc}")]
    finally:
        clear()
    failed = [s["step"] for s in steps if not s["ok"]]
    report(
        ok=not failed,
        verified=not failed,
        desktop=f"Linux Wayland ({COMPOSITOR})",
        compositor_generalization=False,
        backend=backend,
        failed_steps=failed,
        observed=observed,
        steps=steps,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
