#!/usr/bin/env python3
"""Gated early probe: Windows CF_HDROP file-list paste via paste_files.

On a usable Windows desktop with Explorer (or equivalent) independently
copying two local files including Unicode/spaces, would consume with
``paste_files()`` from ``CF_HDROP``, prove non-mutation for a later consumer,
ignore PreferredDropEffect cut/move for side effects, and record floors —
never silent verified success.

Without that Windows session, prints an explicit evidence-limit JSON and
exits 2. This Darwin execution host cannot satisfy the premises (no Windows
desktop). Does not run under default pytest as a verified claim.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    on_windows = sys.platform == "win32"
    reason = (
        "Windows desktop host present, but this probe does not claim verified "
        "paste_files success without an independent Explorer (or equivalent) "
        "CF_HDROP offer of two local files (Unicode + spaces) plus "
        "non-mutation / PreferredDropEffect ignore checks in this run; "
        "refusing silent verified success."
        if on_windows
        else (
            "No usable Windows desktop session was available for this probe "
            "(Darwin checkout; no Explorer CF_HDROP venue)."
        )
    )
    payload = {
        "ok": False,
        "desktop": "Windows desktop",
        "evidence_limit": True,
        "verified": False,
        "reason": reason,
        "environment": {
            "platform": sys.platform,
            "helper_expectation": (
                "ctypes CF_HDROP / DragQueryFileW path-list read after Explorer "
                "(or equivalent) copies local files; PreferredDropEffect ignored "
                "for library behavior; no win32clipboard public dependency"
            ),
            "named_file_manager_required": True,
            "file_manager": "Explorer (or equivalent)",
        },
        "commitments": {
            "32": (
                "Normalization includes reading Windows CF_HDROP path lists — "
                "evidence-limited here, not verified"
            ),
            "52": (
                "Supported desktop: Windows desktop with Explorer (or "
                "equivalent) producing CF_HDROP — evidence-limited here, "
                "not verified"
            ),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
