"""wl-clipboard observation and the raw ``wl-copy --clear`` for the Wayland probe.

``helper(WL_PASTE_LIST)`` is the independent consumer; ``nothing_copied``
classifies its result as an empty selection and ``wait_listed`` polls it
until a type is offered. ``wl_copy_produce`` is the independent producer, and
``WAYLAND`` describes this desktop to the shared ``linux_native_clear_steps``.
``raw_clear_ends_foreground_owner`` is the probe's early step 2: the raw
``wl-copy --clear`` against a foreground ``text/html`` owner, without the
library.
"""

from __future__ import annotations

import subprocess
import tempfile
import time

from linux_native_clear_steps import HTML_BODY, HTML_TYPE, LinuxDesktop
from native_clear_support import OWNER_EXIT_BOUND_S, helper, step

WL_PASTE_LIST = ["wl-paste", "-l"]
WL_COPY_CLEAR = ["wl-copy", "--clear"]
OFFER_WAIT_S = 5.0


def _listing(observed: dict) -> list[str] | None:
    """``wl-paste -l`` types, or ``None`` when the helper did not exit 0."""
    if observed.get("returncode") != 0:
        return None
    return [line for line in observed.get("stdout", "").splitlines() if line]


def wait_listed(mime_type: str) -> dict:
    """Poll ``wl-paste -l`` until ``mime_type`` is offered (bounded)."""
    deadline = time.monotonic() + OFFER_WAIT_S
    while True:
        listed = helper(WL_PASTE_LIST)
        if mime_type in (_listing(listed) or []) or time.monotonic() > deadline:
            listed["offered"] = mime_type in (_listing(listed) or [])
            return listed
        time.sleep(0.1)


def nothing_copied(observed: dict) -> bool:
    from clipboard import _desktop

    return observed.get("returncode", 0) != 0 and (
        _desktop._wl_paste_reports_nothing_copied(observed.get("stderr", ""))
    )


def wl_copy_produce(mime_type: str, body: bytes) -> dict:
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


WAYLAND = LinuxDesktop(
    owner="wl-copy",
    listing=lambda: helper(WL_PASTE_LIST),
    is_empty=nothing_copied,
    wait_offered=wait_listed,
    produce=wl_copy_produce,
)


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


def raw_clear_ends_foreground_owner(observed: dict) -> dict:
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
        offered = wait_listed(HTML_TYPE)
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
    nothing = nothing_copied(after)
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
