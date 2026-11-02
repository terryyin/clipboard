#!/usr/bin/env python3
"""Independent-producer probe: Linux X11 CLIPBOARD → clipboard.inspect().

An **independent** producer (``xclip -selection clipboard -t … -i``, not
clipboard.inspect / same-library round-trip alone) places a typed offer; the
library under test calls ``inspect()``; an independent ``xclip -o -t …``
consumer then still sees the offer (non-mutation).

Stock ``xclip`` owns one target type per offer, so HTML and plain-text are
probed as separate independent offers (not one dual-type update). Image-only
is optional when feasible.

Without a usable Linux X11 session + ``xclip`` on PATH, prints an explicit
evidence-limit JSON and exits 2 — never silent verified success.

Prints one JSON object on stdout. Exit 0 on HTML + text inspect success;
exit 2 on evidence limit; other non-zero on failure. Does not run under
default pytest. Does not require ``clipboard[images]``.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

from linux_x11_native_inspect_support import (
    HTML_FORMAT_IDS,
    HTML_MARKERS,
    IMAGE_FORMAT_IDS,
    TEXT_EXACT,
    TEXT_FORMAT_IDS,
    consume_html_independent,
    consume_image_type_present,
    consume_text_independent,
    inspect_via_library,
    produce_html_independent,
    produce_image_only_independent,
    produce_text_independent,
)
from native_probe_common import linux_x11_environment


def _evidence_limit(*, reason: str) -> int:
    display = os.environ.get("DISPLAY") or ""
    xclip = shutil.which("xclip")
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
                "xclip able to list CLIPBOARD targets via "
                "xclip -selection clipboard -o -t TARGETS"
            ),
        },
        "verified": False,
        "method": "xclip -selection clipboard -o -t TARGETS → clipboard.inspect",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


def _html_case() -> dict:
    produce_html_independent()
    snapshot = inspect_via_library()
    observed_html = consume_html_independent()
    kinds = set(snapshot["kinds"])
    formats = snapshot["formats"]
    has_html_kind = "html" in kinds
    has_html_fmt = any(f in formats for f in HTML_FORMAT_IDS)
    html_ok = all(marker in observed_html for marker in HTML_MARKERS)
    ok = has_html_kind and has_html_fmt and html_ok
    return {
        "case": "html",
        "ok": ok,
        "kinds": sorted(kinds),
        "formats": formats,
        "has_html_kind": has_html_kind,
        "has_html_format": has_html_fmt,
        "consumer_after_inspect": {
            "html_markers_ok": html_ok,
            "html": observed_html,
        },
        "non_mutation": html_ok,
    }


def _text_case() -> dict:
    produce_text_independent()
    snapshot = inspect_via_library()
    observed_text = consume_text_independent()
    kinds = set(snapshot["kinds"])
    formats = snapshot["formats"]
    has_text_kind = "text" in kinds
    has_text_fmt = any(f in formats for f in TEXT_FORMAT_IDS)
    text_ok = observed_text == TEXT_EXACT
    ok = has_text_kind and has_text_fmt and text_ok
    return {
        "case": "text",
        "ok": ok,
        "kinds": sorted(kinds),
        "formats": formats,
        "has_text_kind": has_text_kind,
        "has_text_format": has_text_fmt,
        "consumer_after_inspect": {
            "text_exact_ok": text_ok,
            "text": observed_text,
        },
        "non_mutation": text_ok,
    }


def _image_only_case() -> dict:
    produce_image_only_independent()
    snapshot = inspect_via_library()
    still_offered = consume_image_type_present()
    kinds = set(snapshot["kinds"])
    formats = snapshot["formats"]
    has_image = "image" in kinds
    no_text_html = "text" not in kinds and "html" not in kinds
    has_image_fmt = any(f in IMAGE_FORMAT_IDS or "png" in f.lower() for f in formats)
    ok = has_image and no_text_html and has_image_fmt and still_offered
    return {
        "case": "image_only",
        "ok": ok,
        "kinds": sorted(kinds),
        "formats": formats,
        "has_image_kind": has_image,
        "no_text_or_html_kind": no_text_html,
        "has_image_format": has_image_fmt,
        "type_still_offered_after_inspect": still_offered,
        "non_mutation": still_offered,
    }


def main() -> int:
    display = (os.environ.get("DISPLAY") or "").strip()
    xclip = shutil.which("xclip")
    if not sys.platform.startswith("linux"):
        return _evidence_limit(
            reason=(
                "No usable Linux X11 session with xclip was available for this "
                f"probe (platform={sys.platform!r}; DISPLAY="
                f"{display or None!r}; xclip={xclip!r})."
            )
        )
    if not display or not xclip:
        return _evidence_limit(
            reason=(
                "No usable X11 session with a helper that can list CLIPBOARD "
                "TARGETS was available (need DISPLAY and xclip on PATH for "
                "xclip -selection clipboard -o -t TARGETS)."
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

    html = _html_case()
    text = _text_case()
    image_only: dict | None = None
    image_error: str | None = None
    try:
        image_only = _image_only_case()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — optional case; record limit
        image_error = f"{type(exc).__name__}: {exc}"

    env = linux_x11_environment(
        producer=(
            "xclip -selection clipboard -t <mime> -i "
            "(independent of clipboard.inspect / not same-library round-trip)"
        ),
        inspector=("clipboard.inspect() → xclip -selection clipboard -o -t TARGETS"),
        html_consumer="xclip -selection clipboard -o -t text/html",
        text_consumer="xclip -selection clipboard -o -t text/plain",
        image_producer="xclip -selection clipboard -t image/png -i (no Pillow)",
        helper="xclip",
        dual_type_note=(
            "stock xclip offers one target type per owner process; HTML and "
            "text probed as separate independent offers"
        ),
    )
    floors = {
        "display": env.get("display"),
        "xclip_version": env.get("xclip_version"),
        "machine": env.get("machine"),
        "os_release": env.get("os_release"),
        "method": "xclip -selection clipboard -o -t TARGETS → clipboard.inspect",
    }
    ok = html["ok"] is True and text["ok"] is True
    report = {
        "ok": ok,
        "evidence_limit": False,
        "verified": ok,
        "environment": env,
        "floors": floors,
        "html": html,
        "text": text,
        "image_only": image_only,
        "image_only_error": image_error,
        "commitments": {
            "independent_producer": (
                "xclip -selection clipboard -t <mime> -i "
                "(not clipboard.inspect same-library round-trip alone)"
            ),
            "library_under_test": "clipboard.inspect()",
            "independent_consumer_after_inspect": (
                "xclip -o -t text/html|text/plain; TARGETS still lists image/png"
            ),
            "helper_flags": "xclip -selection clipboard -o -t TARGETS",
            "authorization": "normal X11 CLIPBOARD; no entitlement bypass",
            "no_images_extra": True,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
