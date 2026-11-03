"""xclip observation and the raw libX11 relinquish for the X11 clear probe.

``helper(XCLIP_TARGETS)`` is the independent consumer; ``xclip_no_owner``
classifies its result as an unowned CLIPBOARD and ``wait_targeted`` polls it
until a target is offered. ``raw_relinquish`` runs the mechanism without the
library: a separate Python sets the CLIPBOARD owner to ``None`` through
libX11 ``ctypes`` and reports what libX11 returned;
``raw_relinquish_ends_html_owner`` is the probe's early step 2 built on it.
``absent_display`` names an X display with no server for the failure step.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from native_clear_support import OWNER_EXIT_BOUND_S, child_python, helper, step

XCLIP_TARGETS = ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"]
OFFER_WAIT_S = 5.0
HTML_TYPE = "text/html"
HTML_BODY = b"<p><b>clear probe</b> html</p>"

# The raw mechanism, independent of the library: relinquish CLIPBOARD and
# report what libX11 returned and who owns CLIPBOARD afterwards.
RAW_RELINQUISH = r"""
import ctypes, ctypes.util, json, sys

name = ctypes.util.find_library("X11") or "libX11.so.6"
x = ctypes.CDLL(name)
x.XOpenDisplay.argtypes = [ctypes.c_char_p]
x.XOpenDisplay.restype = ctypes.c_void_p
x.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
x.XInternAtom.restype = ctypes.c_ulong
x.XGetSelectionOwner.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
x.XGetSelectionOwner.restype = ctypes.c_ulong
x.XSetSelectionOwner.argtypes = [ctypes.c_void_p] + [ctypes.c_ulong] * 3
x.XSetSelectionOwner.restype = ctypes.c_int
x.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
x.XCloseDisplay.argtypes = [ctypes.c_void_p]
display = x.XOpenDisplay(None)
if not display:
    print(json.dumps({"library": name, "display_opened": False}))
    sys.exit(4)
atom = x.XInternAtom(display, b"CLIPBOARD", 0)
owner_before = x.XGetSelectionOwner(display, atom)
set_result = x.XSetSelectionOwner(display, atom, 0, 0)
sync_result = x.XSync(display, 0)
owner_after = x.XGetSelectionOwner(display, atom)
x.XCloseDisplay(display)
print(json.dumps({
    "library": name,
    "display_opened": True,
    "clipboard_atom": atom,
    "owner_before": owner_before,
    "set_selection_owner_result": set_result,
    "sync_result": sync_result,
    "owner_after": owner_after,
}))
"""


def xclip_no_owner(observed: dict) -> bool:
    from clipboard import _desktop

    return observed.get("returncode", 0) != 0 and _desktop._xclip_reports_no_owner(
        observed.get("stderr", "")
    )


def _targets(observed: dict) -> list[str]:
    if observed.get("returncode") != 0:
        return []
    return [line for line in observed.get("stdout", "").splitlines() if line]


def wait_targeted(target: str) -> dict:
    """Poll ``xclip -o -t TARGETS`` until ``target`` is offered (bounded)."""
    deadline = time.monotonic() + OFFER_WAIT_S
    while True:
        listed = helper(XCLIP_TARGETS)
        if target in _targets(listed) or time.monotonic() > deadline:
            listed["offered"] = target in _targets(listed)
            return listed
        time.sleep(0.1)


def raw_relinquish() -> dict:
    run = child_python(RAW_RELINQUISH)
    try:
        run["libx11"] = json.loads(run.get("stdout", "").splitlines()[-1])
    except (IndexError, ValueError):
        run["libx11"] = None
    return run


def raw_relinquish_ends_html_owner(observed: dict) -> dict:
    """Early probe: raw libX11 ``XSetSelectionOwner(None)`` from a non-owner."""
    cmd = ["xclip", "-quiet", "-selection", "clipboard", "-t", HTML_TYPE, "-i"]
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
        offered = wait_targeted(HTML_TYPE)
        raw = raw_relinquish()
        after = helper(XCLIP_TARGETS)
        try:
            owner_exit = owner.wait(timeout=OWNER_EXIT_BOUND_S)
        except subprocess.TimeoutExpired:
            owner_exit = None
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(timeout=5)
    observed["raw_xsetselectionowner_none"] = raw
    libx11 = raw.get("libx11") or {}
    no_owner = xclip_no_owner(after)
    return step(
        "2_early_raw_xsetselectionowner_none_ends_html_owner",
        offered["offered"]
        and raw.get("returncode") == 0
        and libx11.get("owner_after") == 0
        and no_owner
        and owner_exit is not None,
        owner={"cmd": cmd, "pid": owner.pid, "exit_code": owner_exit},
        owner_exit_bound_s=OWNER_EXIT_BOUND_S,
        offered_before=offered,
        raw_relinquish=raw,
        xclip_targets_after=after,
        classified_no_owner=no_owner,
    )


def absent_display() -> str:
    """An X display number with no server socket (never the current one)."""
    current = os.environ.get("DISPLAY", "")
    for number in range(1987, 2087):
        name = f":{number}"
        if name != current and not Path(f"/tmp/.X11-unix/X{number}").exists():
            return name
    raise RuntimeError("no free X display number in :1987-:2086")
