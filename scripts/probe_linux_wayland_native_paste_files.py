#!/usr/bin/env python3
"""Gated early probe: Linux Wayland file-list paste via paste_files + wl-paste.

On a usable Wayland session with ``wl-paste -t text/uri-list`` (or equivalent)
on a **named** compositor and a **named** file manager independently offering
local files, would consume with ``paste_files()``, prove non-mutation for a
later consumer, ignore cut-marker companions for side effects, and record
floors — never generalizing one compositor (or one Linux file manager) to all
environments.

Without that session/helper/compositor/FM path, prints an explicit
evidence-limit JSON and exits 2 (never silent verified success). This Darwin
execution host cannot satisfy the premises (``wl-paste`` not on ``PATH``; no
Wayland session). Does not run under default pytest as a verified claim.
"""

from __future__ import annotations

import json
import os
import shutil
import sys


def main() -> int:
    wayland = os.environ.get("WAYLAND_DISPLAY") or ""
    wl_paste = shutil.which("wl-paste")
    desktop = (
        os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or ""
    )
    session_ready = (
        sys.platform.startswith("linux") and bool(wayland) and bool(wl_paste)
    )
    reason = (
        "Wayland session and wl-paste present, but this probe does not claim "
        "verified paste_files success without an independent named file "
        "manager offering text/uri-list on a named compositor in this run; "
        "refusing silent verified success and refusing to generalize one "
        "Wayland compositor (or one Linux file manager) to all environments."
        if session_ready
        else (
            "No usable Wayland session with wl-paste able to request "
            "text/uri-list from a named file manager on a named compositor "
            "was available for this probe (Darwin checkout; wl-paste not on "
            "PATH / WAYLAND_DISPLAY unset)."
        )
    )
    payload = {
        "ok": False,
        "desktop": "Linux Wayland",
        "evidence_limit": True,
        "verified": False,
        "compositor_generalization": False,
        "file_manager_generalization": False,
        "reason": reason,
        "environment": {
            "platform": sys.platform,
            "WAYLAND_DISPLAY": wayland or None,
            "desktop_hint": desktop or None,
            "wl-paste": wl_paste,
            "helper_expectation": (
                "wl-paste -t text/uri-list (or equivalent) after a named "
                "file manager copies local files on a named compositor; do "
                "not generalize one Wayland compositor's result to all "
                "environments"
            ),
            "named_file_manager_required": True,
            "named_compositor_required": True,
        },
        "commitments": {
            "55": (
                "Supported desktop: Linux Wayland + helper able to request "
                "text/uri-list (or equivalent) from a named file manager, "
                "scoped to the compositor actually proved when one is "
                "available — evidence-limited here, not verified"
            ),
            "59": (
                "Do not generalize one Wayland compositor's result to all "
                "environments (compositor_generalization: false)"
            ),
            "91": (
                "Linux Wayland support is scoped to the compositor actually "
                "proved when one is available"
            ),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
