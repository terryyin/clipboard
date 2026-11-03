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
nothing copied and every public reader reads absence. Step 5: a child's
``clipboard.copy_image()`` leaves a background ``wl-copy`` owner; a child
``clear()`` ends that owner within the bound and ``paste_image()`` is
``None``. Step 6: ``clear()`` twice on the cleared selection succeeds. Step 7:
with ``PATH`` lacking ``wl-copy``, ``clear()`` raises
``ClipboardContentError`` naming ``wl-clipboard``. Step 8: an independent
``wl-copy --type text/uri-list`` producer of a ``file://`` URI naming an
existing temp file, then a child ``clear()``, then nothing copied and every
reader (``paste_files()`` included) reads absence. Step 9: the same with an
unknown ``application/x-clipboard-probe`` type.

Prints one JSON object on stdout. Exit 0 when every step holds, 1 naming the
failed steps, and 2 with ``evidence_limit`` when no Wayland session, no
running Sway, or no wl-clipboard is available (never silent verified
success). Scoped to Sway. Not run by default pytest.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from native_clear_support import (
    OWNER_EXIT_BOUND_S,
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
from native_probe_wayland import COMPOSITOR, sway_running, wayland_paste_environment

WL_PASTE_LIST = ["wl-paste", "-l"]
WL_COPY_CLEAR = ["wl-copy", "--clear"]
HTML_TYPE = "text/html"
TEXT_TYPE = "text/plain;charset=utf-8"
HTML_BODY = b"<p><b>clear probe</b> html</p>"
TEXT_BODY = b"clear probe text"
URI_LIST_TYPE = "text/uri-list"
UNKNOWN_TYPE = "application/x-clipboard-probe"
UNKNOWN_BODY = b"clear probe custom bytes"
OFFER_WAIT_S = 5.0
COPY_IMAGE_CHILD = """
from PIL import Image
import clipboard

clipboard.copy_image(Image.new("RGB", (4, 4), (255, 0, 0)))
"""


def _listing(observed: dict) -> list[str] | None:
    """``wl-paste -l`` types, or ``None`` when the helper did not exit 0."""
    if observed.get("returncode") != 0:
        return None
    return [line for line in observed.get("stdout", "").splitlines() if line]


def _wait_listed(mime_type: str) -> dict:
    """Poll ``wl-paste -l`` until ``mime_type`` is offered (bounded)."""
    deadline = time.monotonic() + OFFER_WAIT_S
    while True:
        listed = helper(WL_PASTE_LIST)
        if mime_type in (_listing(listed) or []) or time.monotonic() > deadline:
            listed["offered"] = mime_type in (_listing(listed) or [])
            return listed
        time.sleep(0.1)


def _nothing_copied(observed: dict) -> bool:
    from clipboard import _desktop

    return observed.get("returncode", 0) != 0 and (
        _desktop._wl_paste_reports_nothing_copied(observed.get("stderr", ""))
    )


def _produce(mime_type: str, body: bytes) -> dict:
    """An independent ``wl-copy`` producer (not the library) offering one type."""
    cmd = ["wl-copy", "--type", mime_type]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        proc.communicate(input=body, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}
    return {"cmd": cmd, "returncode": proc.returncode}


def _raw_wl_copy_clear() -> dict:
    """``wl-copy --clear`` itself, output to files (a fork cannot hold a pipe)."""
    started = time.monotonic()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            result = subprocess.run(
                WL_COPY_CLEAR,
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"cmd": WL_COPY_CLEAR, "error": f"{type(exc).__name__}: {exc}"}
        out.seek(0)
        err.seek(0)
        return {
            "cmd": WL_COPY_CLEAR,
            "returncode": result.returncode,
            "stdout": out.read().decode("utf-8", "replace"),
            "stderr": err.read().decode("utf-8", "replace").strip(),
            "elapsed_s": round(time.monotonic() - started, 3),
        }


def _raw_clear_ends_foreground_owner(observed: dict) -> dict:
    """Early probe: raw ``wl-copy --clear`` against a ``text/html`` owner."""
    cmd = ["wl-copy", "--foreground", "--type", HTML_TYPE]
    owner = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        try:
            owner.stdin.write(HTML_BODY)
            owner.stdin.close()
        except BrokenPipeError:
            pass  # the owner died early; the offer check below fails the step
        offered = _wait_listed(HTML_TYPE)
        raw_clear = _raw_wl_copy_clear()
        after = helper(WL_PASTE_LIST)
        try:
            owner_exit = owner.wait(timeout=OWNER_EXIT_BOUND_S)
        except subprocess.TimeoutExpired:
            owner_exit = None
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=5)
    observed["raw_wl_copy_clear"] = raw_clear
    nothing = _nothing_copied(after)
    return step(
        "2_early_raw_wl_copy_clear_ends_html_owner",
        offered["offered"]
        and raw_clear.get("returncode") == 0
        and nothing
        and owner_exit is not None,
        owner={"cmd": cmd, "pid": owner.pid, "exit_code": owner_exit},
        owner_exit_bound_s=OWNER_EXIT_BOUND_S,
        offered_before=offered,
        raw_clear=raw_clear,
        wl_paste_list_after=after,
        classified_nothing_copied=nothing,
    )


def _producer_then_child_clear(name: str, mime_type: str, body: bytes) -> dict:
    producer = _produce(mime_type, body)
    offered = _wait_listed(mime_type)
    cleared = child_clear()
    after = helper(WL_PASTE_LIST)
    reads = read_everything()
    nothing = _nothing_copied(after)
    return step(
        name,
        producer.get("returncode") == 0
        and offered["offered"]
        and child_cleared(cleared)
        and nothing
        and reads_empty(reads),
        producer=producer,
        offered_before=offered,
        child_clear=cleared,
        wl_paste_list_after=after,
        classified_nothing_copied=nothing,
        reads=reads,
    )


def _file_list_producer_then_child_clear() -> dict:
    """``text/uri-list`` naming an existing temp file, then child clear."""
    with tempfile.TemporaryDirectory(prefix="clipboard-clear-probe-") as raw:
        listed = Path(raw) / "clear probe file.txt"
        listed.write_text("clear probe file\n", encoding="utf-8")
        body = (listed.as_uri() + "\r\n").encode("ascii")
        result = _producer_then_child_clear(
            "8_file_list_producer_then_child_clear_reads_empty",
            URI_LIST_TYPE,
            body,
        )
        result["file_uri"] = listed.as_uri()
        result["file_existed"] = listed.is_file()
        result["ok"] = result["ok"] and result["file_existed"]
        return result


def _copy_image_owner_ends() -> dict:
    before = helper_pids("wl-copy")
    writer = child_python(COPY_IMAGE_CHILD)
    offered = _wait_listed("image/png")
    owners = helper_pids("wl-copy", argv_contains="image/png") - before
    cleared = child_clear()
    owner_exit = wait_pids_exit(owners)
    after = helper(WL_PASTE_LIST)
    reads = read_everything()
    nothing = _nothing_copied(after)
    return step(
        "5_copy_image_owner_ends_after_child_clear",
        writer.get("returncode") == 0
        and offered["offered"]
        and bool(owners)
        and child_cleared(cleared)
        and owner_exit["exited"]
        and nothing
        and reads["paste_image"] == {"value": None}
        and reads_empty(reads),
        copy_image_child=writer,
        offered_before=offered,
        library_wl_copy_owner_pids=sorted(owners),
        child_clear=cleared,
        owner_exit=owner_exit,
        wl_paste_list_after=after,
        classified_nothing_copied=nothing,
        reads=reads,
    )


def _clear_twice_on_cleared() -> dict:
    first = child_clear()
    second = child_clear()
    after = helper(WL_PASTE_LIST)
    reads = read_everything()
    nothing = _nothing_copied(after)
    return step(
        "6_clear_twice_on_cleared_succeeds",
        child_cleared(first)
        and child_cleared(second)
        and nothing
        and reads_empty(reads),
        first=first,
        second=second,
        wl_paste_list_after=after,
        classified_nothing_copied=nothing,
        reads=reads,
    )


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
    from clipboard import _desktop

    steps = []
    fresh = helper(WL_PASTE_LIST)
    observed["fresh_nothing_copied_list"] = fresh
    reads = read_everything()
    nothing = fresh.get(
        "returncode", 0
    ) != 0 and _desktop._wl_paste_reports_nothing_copied(fresh.get("stderr", ""))
    steps.append(
        step(
            "1_fresh_nothing_copied_reads_empty",
            nothing and reads_empty(reads),
            wl_paste_list=fresh,
            classified_nothing_copied=nothing,
            reads=reads,
        )
    )
    steps.append(_raw_clear_ends_foreground_owner(observed))
    steps.append(
        _producer_then_child_clear(
            "3_html_producer_then_child_clear_reads_empty", HTML_TYPE, HTML_BODY
        )
    )
    steps.append(
        _producer_then_child_clear(
            "4_text_producer_then_child_clear_reads_empty", TEXT_TYPE, TEXT_BODY
        )
    )
    steps.append(_copy_image_owner_ends())
    steps.append(_clear_twice_on_cleared())
    steps.append(_path_without_wl_copy_names_wl_clipboard())
    steps.append(_file_list_producer_then_child_clear())
    steps.append(
        _producer_then_child_clear(
            "9_unknown_type_producer_then_child_clear_reads_empty",
            UNKNOWN_TYPE,
            UNKNOWN_BODY,
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
