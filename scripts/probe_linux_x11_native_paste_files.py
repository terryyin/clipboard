#!/usr/bin/env python3
"""Gated early probe: Linux X11 file-list paste via paste_files + xclip.

On a usable X11 session with ``xclip`` able to request ``text/uri-list`` on
CLIPBOARD (``xclip -o -selection clipboard -t text/uri-list``) and a **named**
file manager independently offering local files, would consume with
``paste_files()``, prove non-mutation for a later consumer, ignore cut-marker
companions for side effects, and record floors — never generalizing one Linux
file manager's result to all environments.

Without that session/helper/FM path, prints an explicit evidence-limit JSON and
exits 2 (never silent verified success). This Darwin execution host cannot
satisfy the premises (``xclip`` not on ``PATH``; no X11 session). Does not run
under default pytest as a verified claim.
"""

from __future__ import annotations

import json
import os
import shutil
import sys


def main() -> int:
    display = os.environ.get("DISPLAY") or ""
    xclip = shutil.which("xclip")
    desktop = (
        os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or ""
    )
    session_ready = sys.platform.startswith("linux") and bool(display) and bool(xclip)
    reason = (
        "X11 session and xclip present, but this probe does not claim verified "
        "paste_files success without an independent named file manager offering "
        "text/uri-list on CLIPBOARD in this run; refusing silent verified "
        "success and refusing to generalize one Linux file manager to all "
        "environments."
        if session_ready
        else (
            "No usable X11 session with xclip able to request text/uri-list on "
            "CLIPBOARD from a named file manager was available for this probe "
            "(Darwin checkout; xclip not on PATH / DISPLAY unset)."
        )
    )
    payload = {
        "ok": False,
        "desktop": "Linux X11",
        "evidence_limit": True,
        "verified": False,
        "file_manager_generalization": False,
        "reason": reason,
        "environment": {
            "platform": sys.platform,
            "DISPLAY": display or None,
            "desktop_hint": desktop or None,
            "xclip": xclip,
            "helper_expectation": (
                "xclip -o -selection clipboard -t text/uri-list "
                "(or equivalent) after a named file manager copies local files; "
                "do not generalize one Linux file manager's result to all "
                "environments"
            ),
            "named_file_manager_required": True,
        },
        "commitments": {
            "54": (
                "Supported desktop: Linux X11 + helper able to request "
                "text/uri-list on CLIPBOARD from a named file manager — "
                "evidence-limited here, not verified"
            ),
            "60": (
                "Do not generalize one Linux file manager's result to all "
                "environments (file_manager_generalization: false)"
            ),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
