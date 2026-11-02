#!/usr/bin/env python3
"""Independent Windows clipboard holder for the gated text probe.

Plain ctypes in a separate process (not ``clipboard`` or pyperclip): opens the
clipboard with ``OpenClipboard(NULL)``, prints one JSON line
``{"ready": true, ...}`` once it holds it, keeps it open for ``argv[1]``
seconds, then closes it and prints ``{"released": true, ...}``. Prints
``{"ready": false, "open_error": <GetLastError>}`` when it never gets the
clipboard within 5 s. Never empties or sets the clipboard.
"""

import ctypes
import json
import sys
import time


def _say(**fields) -> None:
    print(json.dumps(fields), flush=True)


def main() -> None:
    hold = float(sys.argv[1])
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.OpenClipboard.argtypes = [ctypes.c_void_p]
    deadline = time.monotonic() + 5
    while not u.OpenClipboard(None):
        if time.monotonic() > deadline:
            _say(ready=False, open_error=ctypes.get_last_error())
            return
        time.sleep(0.05)
    opened = time.monotonic()
    try:
        _say(ready=True, hold_seconds=hold)
        time.sleep(hold)
    finally:
        closed = u.CloseClipboard()
    _say(
        released=True,
        held_seconds=round(time.monotonic() - opened, 3),
        close_ok=bool(closed),
    )


if __name__ == "__main__":
    main()
