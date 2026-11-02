#!/usr/bin/env python3
"""Gated early probe: Linux Wayland HTML+text dual-offer via copy_html.

On a usable Wayland session with a multi-type-capable helper on a named
compositor, would publish via copy_html, exit the writer, and consume with
independent rich/text tools. Without that session/helper, prints an explicit
evidence-limit JSON and exits 2 — never silent verified success, and never
generalizes one compositor to all Wayland environments. Does not run under
default pytest.
"""

from __future__ import annotations

import json
import os
import shutil
import sys


def main() -> int:
    wayland = os.environ.get("WAYLAND_DISPLAY") or ""
    desktop = (
        os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or ""
    )
    wl_copy = shutil.which("wl-copy")
    wl_paste = shutil.which("wl-paste")
    session_ready = sys.platform.startswith("linux") and bool(wayland) and bool(wl_copy)
    reason = (
        "Wayland session and wl-copy present, but this probe script does not "
        "yet implement the dual-consumer verification loop on a named "
        "compositor; refusing silent verified success and compositor "
        "generalization."
        if session_ready
        else (
            "No usable Wayland session with a multi-type-capable HTML+text "
            "helper on a named compositor was available for this probe."
        )
    )
    payload = {
        "ok": False,
        "desktop": "Linux Wayland",
        "evidence_limit": True,
        "verified": False,
        "compositor_generalization": False,
        "reason": reason,
        "environment": {
            "platform": sys.platform,
            "WAYLAND_DISPLAY": wayland or None,
            "desktop_hint": desktop or None,
            "wl-copy": wl_copy,
            "wl-paste": wl_paste,
            "helper_expectation": (
                "multi-type-capable Wayland helper (e.g. wl-copy) offering "
                "text/html and text/plain together; success scoped to the "
                "named compositor actually probed"
            ),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
