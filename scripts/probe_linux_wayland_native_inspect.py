#!/usr/bin/env python3
"""Independent-producer probe: Linux Wayland MIME list → clipboard.inspect().

An **independent** producer (``wl-copy --type …``, not clipboard.inspect /
same-library round-trip alone) places a typed offer; ``inspect()`` runs; an
independent ``wl-paste -t …`` consumer still sees the offer (non-mutation).

Stock ``wl-copy`` owns one MIME type per offer, so HTML and plain-text are
separate offers. Image-only is optional. Verified success records a **named
compositor** and must not be generalized to all Wayland. Missing session /
helper / compositor name → evidence-limit JSON, exit 2 — never silent
verified success.

Exit 0 on HTML + text inspect success; exit 2 on evidence limit; other
non-zero on failure. Not default pytest. No ``clipboard[images]`` required.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

from linux_wayland_native_inspect_support import (
    html_inspect_case,
    image_only_inspect_case,
    named_compositor,
    text_inspect_case,
)
from native_probe_common import linux_wayland_environment


def _evidence_limit(*, reason: str) -> int:
    wayland = os.environ.get("WAYLAND_DISPLAY") or ""
    desktop = (
        os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or ""
    )
    payload = {
        "ok": False,
        "desktop": "Linux Wayland",
        "evidence_limit": True,
        "reason": reason,
        "environment": {
            "platform": sys.platform,
            "WAYLAND_DISPLAY": wayland or None,
            "desktop_hint": desktop or None,
            "compositor": named_compositor(),
            "wl-paste": shutil.which("wl-paste"),
            "wl-copy": shutil.which("wl-copy"),
            "helper_expectation": (
                "wl-paste able to list offered MIME types via wl-paste -l "
                "on a named compositor; do not generalize one compositor "
                "to all Wayland"
            ),
        },
        "verified": False,
        "compositor_generalization": False,
        "method": "wl-paste -l → clipboard.inspect",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


def main() -> int:
    wayland = (os.environ.get("WAYLAND_DISPLAY") or "").strip()
    wl_paste = shutil.which("wl-paste")
    wl_copy = shutil.which("wl-copy")
    compositor = named_compositor()
    if not sys.platform.startswith("linux"):
        return _evidence_limit(
            reason=(
                "No usable Linux Wayland session with wl-paste -l on a named "
                f"compositor was available for this probe (platform="
                f"{sys.platform!r}; WAYLAND_DISPLAY={wayland or None!r}; "
                f"wl-paste={wl_paste!r}; wl-copy={wl_copy!r}; "
                f"compositor={compositor!r}). Do not generalize one "
                "compositor to all Wayland."
            )
        )
    if not wayland or not wl_paste or not wl_copy:
        return _evidence_limit(
            reason=(
                "No usable Wayland session with helpers that can list offered "
                "MIME types was available (need WAYLAND_DISPLAY, wl-paste, "
                "and wl-copy on PATH for wl-paste -l / wl-copy --type)."
            )
        )
    if not compositor:
        return _evidence_limit(
            reason=(
                "Wayland session and wl-clipboard helpers are present, but no "
                "named compositor could be recorded (set "
                "CLIPBOARD_WAYLAND_COMPOSITOR or XDG_CURRENT_DESKTOP / "
                "DESKTOP_SESSION). Refusing silent verified success and "
                "compositor generalization."
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

    html = html_inspect_case()
    text = text_inspect_case()
    image_only: dict | None = None
    image_error: str | None = None
    try:
        image_only = image_only_inspect_case()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — optional case; record
        image_error = f"{type(exc).__name__}: {exc}"

    env = linux_wayland_environment(
        producer=(
            "wl-copy --type <mime> "
            "(independent of clipboard.inspect / not same-library round-trip)"
        ),
        inspector="clipboard.inspect() → wl-paste -l",
        html_consumer="wl-paste -t text/html",
        text_consumer="wl-paste -t text/plain",
        image_producer="wl-copy --type image/png (no Pillow)",
        helper="wl-paste -l / wl-copy",
        compositor=compositor,
        desktop=f"Wayland under {compositor}",
        dual_type_note=(
            "stock wl-copy offers one MIME type per owner process; HTML and "
            "text probed as separate independent offers"
        ),
    )
    ok = html["ok"] is True and text["ok"] is True
    report = {
        "ok": ok,
        "evidence_limit": False,
        "verified": ok,
        "compositor_generalization": False,
        "environment": env,
        "floors": {
            "compositor": compositor,
            "wayland_display": env.get("wayland_display"),
            "wl_clipboard_version": env.get("wl_clipboard_version"),
            "machine": env.get("machine"),
            "os_release": env.get("os_release"),
            "method": "wl-paste -l → clipboard.inspect",
            "compositor_scope_only": True,
        },
        "html": html,
        "text": text,
        "image_only": image_only,
        "image_only_error": image_error,
        "commitments": {
            "independent_producer": (
                "wl-copy --type <mime> "
                "(not clipboard.inspect same-library round-trip alone)"
            ),
            "library_under_test": "clipboard.inspect()",
            "independent_consumer_after_inspect": (
                "wl-paste -t text/html|text/plain; wl-paste -l still lists image/png"
            ),
            "helper_flags": "wl-paste -l",
            "compositor_scope": compositor,
            "authorization": "normal Wayland clipboard; no entitlement bypass",
            "no_images_extra": True,
            "do_not_generalize_compositor": True,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
