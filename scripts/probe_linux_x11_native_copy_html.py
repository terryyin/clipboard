#!/usr/bin/env python3
"""Gated early probe: Linux X11 HTML+text dual-offer via copy_html.

On a usable X11 session with a multi-type-capable helper, would publish via
copy_html, exit the writer, and consume with independent rich/text tools.
Without that session/helper, prints an explicit evidence-limit JSON and exits 2
(never silent verified success). Does not run under default pytest.
"""

from __future__ import annotations

import json
import os
import shutil
import sys


def main() -> int:
    display = os.environ.get("DISPLAY") or ""
    xclip = shutil.which("xclip")
    session_ready = sys.platform.startswith("linux") and bool(display) and bool(xclip)
    reason = (
        "X11 session and xclip present, but this probe script does not yet "
        "implement the dual-consumer verification loop on this host path; "
        "refusing silent verified success."
        if session_ready
        else (
            "No usable X11 session with a multi-type-capable HTML+text helper "
            "was available for this probe."
        )
    )
    payload = {
        "ok": False,
        "desktop": "Linux X11",
        "evidence_limit": True,
        "reason": reason,
        "environment": {
            "platform": sys.platform,
            "DISPLAY": display or None,
            "xclip": xclip,
            "helper_expectation": (
                "xclip (or equivalent) able to offer text/html and text/plain "
                "together on CLIPBOARD"
            ),
        },
        "verified": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
