#!/usr/bin/env python3
"""Gated probe: Linux X11 (Xvfb) empty CLIPBOARD and ``clear()``.

Step 1 runs first, on a fresh X server whose CLIPBOARD nobody has owned: an
independent ``xclip -selection clipboard -o -t TARGETS`` records xclip's own
exit code and no-owner stderr (the wording is version-dependent), and the
library's public readers must read absence: ``inspect()`` empty, ``paste()``
``""``, ``paste_html()`` / ``paste_files()`` / ``paste_image()`` ``None``.

Step 2 is the early probe of the mechanism, without the library: an
independent foreground ``xclip -quiet -t text/html`` owner, then a separate
Python process running the raw libX11 ``ctypes`` sequence
(``XOpenDisplay`` / ``XInternAtom("CLIPBOARD")`` /
``XSetSelectionOwner(None, CurrentTime)`` / ``XSync`` /
``XGetSelectionOwner`` / ``XCloseDisplay``; exit code, output and time
recorded), then ``xclip -o -t TARGETS`` reports no owner and the owner
process exits within a bound. Step 3: an independent background ``xclip -t
text/html`` producer, then a child Python calls ``clipboard.clear()`` and
exits, then no owner, every public reader reads absence, and the producer's
``xclip`` exits. Step 4: a child's ``clipboard.copy_image()`` leaves a
background ``xclip`` owner; a child ``clear()`` ends it within the bound and
``paste_image()`` is ``None``. Step 5: ``clear()`` twice on the cleared
clipboard succeeds. Step 6: with ``DISPLAY`` naming a display that does not
exist, a child ``clear()`` raises ``ClipboardContentError`` naming
``DISPLAY`` within the library's bound.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no X11-only session or no
xclip is available (never silent verified success). Not run by default
pytest.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from linux_native_clear_support import (
    child_clear,
    child_cleared,
    child_python,
    distro,
    helper,
    helper_pids,
    read_everything,
    reads_empty,
    report,
    step,
    wait_pids_exit,
)
from linux_x11_native_clear_support import (
    HTML_BODY,
    HTML_TYPE,
    XCLIP_TARGETS,
    absent_display,
    raw_relinquish_ends_html_owner,
    wait_targeted,
    xclip_no_owner,
)
from linux_x11_native_text_support import xvfb_version
from native_probe_common import linux_x11_environment

COPY_IMAGE_CHILD = """
from PIL import Image
import clipboard

clipboard.copy_image(Image.new("RGB", (4, 4), (255, 0, 0)))
"""


def _html_producer_then_child_clear() -> dict:
    before = helper_pids("xclip")
    cmd = ["xclip", "-selection", "clipboard", "-t", HTML_TYPE, "-i"]
    try:
        # xclip forks a background owner and the foreground process exits;
        # no pipes, so the forked owner cannot hold this run open.
        producer = subprocess.run(
            cmd,
            input=HTML_BODY,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
            start_new_session=True,
        )
        produced = {"cmd": cmd, "returncode": producer.returncode}
    except (OSError, subprocess.TimeoutExpired) as exc:
        produced = {"cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}
    offered = wait_targeted(HTML_TYPE)
    owners = helper_pids("xclip", argv_contains=HTML_TYPE) - before
    cleared = child_clear()
    owner_exit = wait_pids_exit(owners)
    after = helper(XCLIP_TARGETS)
    reads = read_everything()
    no_owner = xclip_no_owner(after)
    return step(
        "3_html_producer_then_child_clear_reads_empty",
        produced.get("returncode") == 0
        and offered["offered"]
        and child_cleared(cleared)
        and no_owner
        and reads_empty(reads)
        and owner_exit["exited"],
        producer=produced,
        offered_before=offered,
        producer_xclip_owner_pids=sorted(owners),
        child_clear=cleared,
        owner_exit=owner_exit,
        xclip_targets_after=after,
        classified_no_owner=no_owner,
        reads=reads,
    )


def _copy_image_owner_ends() -> dict:
    before = helper_pids("xclip")
    writer = child_python(COPY_IMAGE_CHILD)
    offered = wait_targeted("image/png")
    owners = helper_pids("xclip", argv_contains="image/png") - before
    cleared = child_clear()
    owner_exit = wait_pids_exit(owners)
    after = helper(XCLIP_TARGETS)
    reads = read_everything()
    no_owner = xclip_no_owner(after)
    return step(
        "4_copy_image_owner_ends_after_child_clear",
        writer.get("returncode") == 0
        and offered["offered"]
        and bool(owners)
        and child_cleared(cleared)
        and owner_exit["exited"]
        and no_owner
        and reads["paste_image"] == {"value": None}
        and reads_empty(reads),
        copy_image_child=writer,
        offered_before=offered,
        library_xclip_owner_pids=sorted(owners),
        child_clear=cleared,
        owner_exit=owner_exit,
        xclip_targets_after=after,
        classified_no_owner=no_owner,
        reads=reads,
    )


def _clear_twice_on_cleared() -> dict:
    first = child_clear()
    second = child_clear()
    after = helper(XCLIP_TARGETS)
    reads = read_everything()
    no_owner = xclip_no_owner(after)
    return step(
        "5_clear_twice_on_cleared_succeeds",
        child_cleared(first)
        and child_cleared(second)
        and no_owner
        and reads_empty(reads),
        first=first,
        second=second,
        xclip_targets_after=after,
        classified_no_owner=no_owner,
        reads=reads,
    )


def _unopenable_display_names_display() -> dict:
    from clipboard import _clear_x11

    display = absent_display()
    run = child_clear(env={**os.environ, "DISPLAY": display})
    outcome = run.get("outcome") or {}
    message = outcome.get("message", "")
    return step(
        "6_unopenable_display_raises_naming_display",
        run.get("returncode") == 3
        and outcome.get("raised") == "ClipboardContentError"
        and f"DISPLAY={display!r}" in message
        and run.get("elapsed_s", float("inf")) < _clear_x11._X11_CLEAR_TIMEOUT_S,
        child_display=display,
        library_bound_s=_clear_x11._X11_CLEAR_TIMEOUT_S,
        child_clear=run,
    )


def _probe(observed: dict) -> list[dict]:
    steps = []
    fresh = helper(XCLIP_TARGETS)
    observed["fresh_unowned_targets"] = fresh
    reads = read_everything()
    no_owner = xclip_no_owner(fresh)
    steps.append(
        step(
            "1_fresh_unowned_clipboard_reads_empty",
            no_owner and reads_empty(reads),
            xclip_targets=fresh,
            classified_no_owner=no_owner,
            reads=reads,
        )
    )
    steps.append(raw_relinquish_ends_html_owner(observed))
    steps.append(_html_producer_then_child_clear())
    steps.append(_copy_image_owner_ends())
    steps.append(_clear_twice_on_cleared())
    steps.append(_unopenable_display_names_display())
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
    steps = _probe(observed)
    failed = [s["step"] for s in steps if not s["ok"]]
    report(
        ok=not failed,
        verified=not failed,
        desktop="Linux X11",
        failed_steps=failed,
        observed=observed,
        steps=steps,
        environment=linux_x11_environment(
            distro=distro(),
            kernel=os.uname().release,
            xvfb_version=xvfb_version(),
            consumer="xclip -selection clipboard -o -t TARGETS (independent)",
        ),
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
