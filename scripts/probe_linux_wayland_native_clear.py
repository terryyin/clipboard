#!/usr/bin/env python3
"""Gated probe: Linux Wayland (Sway) empty selection and ``clear()``.

Step 1 runs first, on a fresh headless Sway where nothing has been copied: an
independent ``wl-paste -l`` records wl-paste's own exit code and
nothing-copied stderr, and the library's public readers must read absence:
``inspect()`` empty, ``paste()`` ``""``, ``paste_html()`` /
``paste_files()`` / ``paste_image()`` ``None``.

Step 2 is the early probe of the mechanism, without the library: an
independent ``wl-copy --foreground --type text/html`` owner, then the raw
``wl-copy --clear`` (exit code, stderr and time recorded), then ``wl-paste -l``
reports nothing copied and the owner process exits within a bound. Steps 3-4:
an independent ``wl-copy`` producer of ``text/html`` and, separately, of
``text/plain;charset=utf-8`` (one wl-copy offers one type), then a child
Python calls ``clipboard.clear()`` and exits, then ``wl-paste -l`` reports
nothing copied, every public reader reads absence, and the producer's
background ``wl-copy`` exits within the bound. Step 5: a child's
``clipboard.copy_image()`` leaves a background ``wl-copy`` owner; a child
``clear()`` ends that owner within the bound and ``paste_image()`` is
``None``. Step 6: ``clear()`` twice on the cleared selection succeeds. Step 7:
with ``PATH`` lacking ``wl-copy``, ``clear()`` raises
``ClipboardContentError`` naming ``wl-clipboard``. Step 8: an independent
``wl-copy --type text/uri-list`` producer of a ``file://`` URI naming an
existing temp file, then a child ``clear()``, then nothing copied, the
producer exits, and every reader (``paste_files()`` included) reads absence.
Step 9: the same with an unknown ``application/x-clipboard-probe`` type.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no Wayland session, no
running Sway, or no wl-clipboard is available (never silent verified
success). Scoped to Sway. Not run by default pytest.
"""

from __future__ import annotations

import os
import shutil

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
from linux_wayland_native_clear_support import (
    WAYLAND,
    raw_clear_ends_foreground_owner,
)
from linux_wayland_native_text_support import evidence_limit
from native_clear_support import child_clear, distro, report, step
from native_probe_wayland import COMPOSITOR, wayland_paste_environment

TEXT_TYPE = "text/plain;charset=utf-8"
TEXT_BODY = b"clear probe text"


def _path_without_wl_copy_names_wl_clipboard() -> dict:
    kept = [
        entry
        for entry in os.environ.get("PATH", "").split(os.pathsep)
        if entry and not os.path.exists(os.path.join(entry, "wl-copy"))
    ]
    path = os.pathsep.join(kept)
    env = {**os.environ, "PATH": path}
    run = child_clear(env=env)
    outcome = run.get("outcome") or {}
    return step(
        "7_path_without_wl_copy_names_wl_clipboard",
        shutil.which("wl-copy", path=path) is None
        and run.get("returncode") == 3
        and outcome.get("raised") == "ClipboardContentError"
        and "wl-clipboard" in outcome.get("message", ""),
        child_path=path,
        wl_copy_on_child_path=shutil.which("wl-copy", path=path),
        child_clear=run,
    )


def _probe(observed: dict) -> list[dict]:
    return [
        fresh_reads_empty(WAYLAND, "1_fresh_nothing_copied_reads_empty", observed),
        raw_clear_ends_foreground_owner(observed),
        producer_then_child_clear(
            WAYLAND,
            "3_html_producer_then_child_clear_reads_empty",
            HTML_TYPE,
            HTML_BODY,
        ),
        producer_then_child_clear(
            WAYLAND,
            "4_text_producer_then_child_clear_reads_empty",
            TEXT_TYPE,
            TEXT_BODY,
        ),
        copy_image_owner_ends(WAYLAND, "5_copy_image_owner_ends_after_child_clear"),
        clear_twice_on_cleared(WAYLAND, "6_clear_twice_on_cleared_succeeds"),
        _path_without_wl_copy_names_wl_clipboard(),
        file_list_producer_then_child_clear(
            WAYLAND, "8_file_list_producer_then_child_clear_reads_empty"
        ),
        producer_then_child_clear(
            WAYLAND,
            "9_unknown_type_producer_then_child_clear_reads_empty",
            UNKNOWN_TYPE,
            UNKNOWN_BODY,
        ),
    ]


def main() -> int:
    reason = evidence_limit()
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
    steps = _probe(observed)
    failed = [s["step"] for s in steps if not s["ok"]]
    report(
        ok=not failed,
        verified=not failed,
        desktop=f"Linux Wayland ({COMPOSITOR})",
        compositor_generalization=False,
        failed_steps=failed,
        observed=observed,
        steps=steps,
        environment=wayland_paste_environment(distro=distro()),
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
