#!/usr/bin/env python3
"""Gated early probe: Windows HTML Format + Unicode text via copy_html.

Without a usable Windows desktop session, prints an explicit evidence-limit
JSON and exits 2 — never silent verified success. A successful future probe
must include non-ASCII HTML Format fragment/context offset checks plus an
independent text consumer after writer exit.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    on_windows = sys.platform == "win32"
    reason = (
        "Windows desktop host present, but this probe script does not yet "
        "implement the dual-consumer HTML Format verification loop "
        "(including non-ASCII fragment/context offsets); refusing silent "
        "verified success."
        if on_windows
        else ("No usable Windows desktop session was available for this probe.")
    )
    payload = {
        "ok": False,
        "desktop": "Windows desktop",
        "evidence_limit": True,
        "verified": False,
        "reason": reason,
        "environment": {
            "platform": sys.platform,
            "html_format_expectation": (
                "CF_HTML / HTML Format with correct UTF-8 StartHTML/EndHTML/"
                "StartFragment/EndFragment byte offsets for non-ASCII content, "
                "plus Unicode text alternative in the same offer"
            ),
        },
        "non_ascii_case_required_for_verification": True,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
