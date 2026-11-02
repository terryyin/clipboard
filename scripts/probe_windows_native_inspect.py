#!/usr/bin/env python3
"""Independent-producer probe: Windows desktop → clipboard.inspect().

An **independent** producer (PowerShell / .NET Clipboard, not
clipboard.inspect / same-library round-trip alone) places HTML+text; the
library under test calls ``inspect()``; an independent consumer then still
sees the offer (non-mutation). Image/file-list cases are optional when
feasible.

Without a usable Windows desktop session (``win32``), prints an explicit
evidence-limit JSON and exits 2 — never silent verified success.

Prints one JSON object on stdout. Exit 0 on HTML+text inspect success;
exit 2 on evidence limit; other non-zero on failure. Does not run under
default pytest. Does not require ``clipboard[images]`` or ``win32clipboard``.
"""

from __future__ import annotations

import json
import sys

from windows_native_inspect_support import (
    HTML_FORMAT_IDS,
    HTML_MARKERS,
    TEXT_EXACT,
    TEXT_FORMAT_IDS,
    consume_html_independent,
    consume_text_independent,
    inspect_via_library,
    produce_html_text_independent,
    windows_environment,
)


def _evidence_limit(*, reason: str) -> int:
    payload = {
        "ok": False,
        "desktop": "Windows desktop",
        "evidence_limit": True,
        "reason": reason,
        "environment": {
            "platform": sys.platform,
            "helper_expectation": (
                "win32 desktop with user32 EnumClipboardFormats + "
                "GetClipboardFormatNameW (ctypes; no win32clipboard required)"
            ),
        },
        "verified": False,
        "method": (
            "ctypes user32 EnumClipboardFormats → clipboard.inspect "
            "(format names/ids; no payload fetch)"
        ),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


def _html_text_case() -> dict:
    produce_html_text_independent()
    snapshot = inspect_via_library()
    observed_html = consume_html_independent()
    observed_text = consume_text_independent()
    kinds = set(snapshot["kinds"])
    formats = snapshot["formats"]
    has_html_kind = "html" in kinds
    has_text_kind = "text" in kinds
    has_html_fmt = any(f in formats for f in HTML_FORMAT_IDS)
    has_text_fmt = any(f in formats for f in TEXT_FORMAT_IDS)
    html_ok = all(marker in observed_html for marker in HTML_MARKERS)
    text_ok = observed_text == TEXT_EXACT
    ok = (
        has_html_kind
        and has_text_kind
        and has_html_fmt
        and has_text_fmt
        and html_ok
        and text_ok
    )
    return {
        "case": "html_and_text",
        "ok": ok,
        "kinds": sorted(kinds),
        "formats": formats,
        "has_html_kind": has_html_kind,
        "has_text_kind": has_text_kind,
        "has_html_format": has_html_fmt,
        "has_text_format": has_text_fmt,
        "consumer_after_inspect": {
            "html_markers_ok": html_ok,
            "text_exact_ok": text_ok,
            "html": observed_html,
            "text": observed_text,
        },
        "non_mutation": html_ok and text_ok,
    }


def main() -> int:
    if sys.platform != "win32":
        return _evidence_limit(
            reason=(
                "No usable Windows desktop session was available for this "
                f"probe (platform={sys.platform!r}). Windows inspect remains "
                "an evidence limit — not verified on this host."
            )
        )

    try:
        import clipboard  # noqa: F401
    except ImportError as exc:
        print(
            json.dumps(
                {"ok": False, "error": f"missing clipboard import: {exc}"},
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    html_text = _html_text_case()
    env = windows_environment(
        producer=(
            "PowerShell System.Windows.Forms.Clipboard HTML+text "
            "(independent of clipboard.inspect / not same-library round-trip)"
        ),
        inspector=(
            "clipboard.inspect() → ctypes user32 EnumClipboardFormats + "
            "GetClipboardFormatNameW"
        ),
        html_consumer="PowerShell Clipboard GetText(Html)",
        text_consumer="PowerShell Clipboard GetText()",
    )
    floors = {
        "os_release": env.get("os_release"),
        "machine": env.get("machine"),
        "method": (
            "ctypes user32 EnumClipboardFormats + GetClipboardFormatNameW "
            "→ clipboard.inspect"
        ),
    }
    ok = html_text["ok"] is True
    report = {
        "ok": ok,
        "evidence_limit": False,
        "verified": ok,
        "environment": env,
        "floors": floors,
        "html_and_text": html_text,
        "commitments": {
            "independent_producer": (
                "PowerShell System.Windows.Forms.Clipboard HTML+text "
                "(not clipboard.inspect same-library round-trip alone)"
            ),
            "library_under_test": "clipboard.inspect()",
            "independent_consumer_after_inspect": (
                "PowerShell GetText Html + GetText plain"
            ),
            "helper_flags": (
                "user32 EnumClipboardFormats / GetClipboardFormatNameW "
                "(ctypes; no win32clipboard)"
            ),
            "authorization": "normal Windows desktop clipboard; no bypass",
            "no_images_extra": True,
            "no_win32clipboard_required": True,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
