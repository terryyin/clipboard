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
``DISPLAY`` within the library's bound. Step 7: an independent background
``xclip -t text/uri-list`` owner of a ``file://`` URI naming an existing temp
file, then a child ``clear()``, then no owner, the producer exits, and every
reader (``paste_files()`` included) reads absence. Step 8: the same with an
unknown ``application/x-clipboard-probe`` type.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no X11-only session or no
xclip is available (never silent verified success). Not run by default
pytest.
"""

from __future__ import annotations

import os
import shutil
import sys

from linux_native_clear_steps import (
    HTML_BODY,
    HTML_TYPE,
    UNKNOWN_BODY,
    UNKNOWN_TYPE,
    clear_twice_on_cleared,
    copy_image_owner_ends,
    file_list_producer_then_child_clear,
    fresh_reads_empty,
    producer_then_child_clear,
)
from linux_x11_native_clear_support import (
    X11,
    absent_display,
    raw_relinquish_ends_html_owner,
)
from linux_x11_native_text_support import xvfb_version
from native_clear_support import child_clear, distro, report, step
from native_probe_common import linux_x11_environment


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
    return [
        fresh_reads_empty(X11, "1_fresh_unowned_clipboard_reads_empty", observed),
        raw_relinquish_ends_html_owner(observed),
        producer_then_child_clear(
            X11, "3_html_producer_then_child_clear_reads_empty", HTML_TYPE, HTML_BODY
        ),
        copy_image_owner_ends(X11, "4_copy_image_owner_ends_after_child_clear"),
        clear_twice_on_cleared(X11, "5_clear_twice_on_cleared_succeeds"),
        _unopenable_display_names_display(),
        file_list_producer_then_child_clear(
            X11, "7_file_list_producer_then_child_clear_reads_empty"
        ),
        producer_then_child_clear(
            X11,
            "8_unknown_type_producer_then_child_clear_reads_empty",
            UNKNOWN_TYPE,
            UNKNOWN_BODY,
        ),
    ]


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
