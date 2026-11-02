#!/usr/bin/env python3
"""Independent-producer probe: Linux Wayland ``text/html`` (Sway) → paste_html().

The producer is ``wl-copy --type text/html`` (not this library's copy_html),
which forks a background source that keeps serving the selection. Checks that
paste_html() returns exactly the offered fragment, that a later independent
``wl-paste --no-newline --type text/html`` consumer still gets the same bytes
and the same type list (non-mutating read), and that text-only, image-only
and cleared (empty) clipboards give ``None``, while a missing wl-paste or no
reachable compositor give ClipboardContentError. Intended venue: gated GitHub
Actions under headless Sway. The result is scoped to Sway; it does not
generalize to other Wayland compositors.

Prints one JSON object on stdout. Exit 0 on success, 1 on a failed check, and
2 with ``evidence_limit`` / ``verified: false`` when no Wayland session, no
running Sway, or no wl-clipboard is available (never silent verified
success). Not default pytest.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from native_probe_paste_html import FRAGMENT, PLAIN_TEXT, child_paste_html, paste_html
from native_probe_wayland import COMPOSITOR, sway_running, wayland_paste_environment
from stdlib_png import solid_red_png_bytes

ROOT = Path(__file__).resolve().parents[1]
CONSUMER_API = "wl-paste --no-newline --type text/html"
PRODUCER = "wl-copy --type text/html (independent)"


def _environment() -> dict:
    return wayland_paste_environment(producer=PRODUCER, consumer_api=CONSUMER_API)


def _evidence_limit(reason: str) -> int:
    payload = {
        "ok": False,
        "desktop": f"Linux Wayland ({COMPOSITOR})",
        "evidence_limit": True,
        "verified": False,
        "compositor_generalization": False,
        "reason": reason,
        "environment": _environment(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 2


def _wl_paste(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["wl-paste", *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=10,
        check=False,
    )


def _types() -> list[str]:
    result = _wl_paste("--list-types")
    if result.returncode != 0:
        return []
    return result.stdout.decode("utf-8", "replace").split()


def _wl_copy(args: list[str], data: bytes | None) -> None:
    """Run wl-copy; stdout/stderr to /dev/null so its forked source never pins them."""
    proc = subprocess.Popen(
        ["wl-copy", *args],
        stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proc.communicate(input=data, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"wl-copy {args} exited with status {proc.returncode}")


def _offer(data: bytes, mime_type: str | None, expect: str) -> None:
    """Producer-side setup: wl-copy an offer, then wait until ``expect`` is listed."""
    _wl_copy(["--type", mime_type] if mime_type else [], data)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if expect in _types():
            return
        time.sleep(0.05)
    raise RuntimeError(f"wl-copy producer did not offer {expect} in time")


def _clear() -> None:
    _wl_copy(["--clear"], None)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and _wl_paste("--list-types").returncode == 0:
        time.sleep(0.05)


def _outcome(result: subprocess.CompletedProcess[bytes]) -> dict:
    """Record a raw wl-paste result (the empty-clipboard evidence)."""
    return {
        "exit": result.returncode,
        "stdout": result.stdout.decode("utf-8", "replace"),
        "stderr": result.stderr.decode("utf-8", "replace").strip(),
    }


def _probe_html() -> dict:
    raw = FRAGMENT.encode("utf-8")
    _offer(raw, "text/html", "text/html")
    types_before = _types()
    started = time.monotonic()
    read = paste_html()
    elapsed = time.monotonic() - started
    later = _wl_paste("--no-newline", "--type", "text/html")
    with_newline = _wl_paste("--type", "text/html")
    return {
        **read,
        "expected": FRAGMENT,
        "matches": read["paste_html"] == FRAGMENT,
        "seconds": round(elapsed, 3),
        "types_before": types_before,
        "types_after": _types(),
        "independent_consumer_same_bytes": (
            later.returncode == 0 and later.stdout == raw
        ),
        # Why the reader passes --no-newline: without it wl-paste appends "\n".
        "wl_paste_without_no_newline_appends_newline": (
            with_newline.returncode == 0 and with_newline.stdout == raw + b"\n"
        ),
    }


def _probe_absent() -> list[dict]:
    cases = []
    _offer(PLAIN_TEXT.encode("utf-8"), "text/plain;charset=utf-8", "text/plain")
    cases.append({"case": "text_only", "types": _types(), **paste_html()})
    _offer(solid_red_png_bytes(), "image/png", "image/png")
    cases.append({"case": "image_only", "types": _types(), **paste_html()})
    _clear()
    cases.append(
        {
            "case": "cleared_empty",
            "wl_paste_list_types": _outcome(_wl_paste("--list-types")),
            "wl_paste_type_html": _outcome(
                _wl_paste("--no-newline", "--type", "text/html")
            ),
            **paste_html(),
        }
    )
    return cases


def _child(env: dict) -> dict:
    return child_paste_html(
        env,
        root=ROOT,
        names_key="names_wl_paste",
        names=("wl-paste", "apt install wl-clipboard"),
    )


def _probe_failures(runtime_dir: Path) -> dict:
    base = dict(os.environ)
    # No compositor: no WAYLAND_DISPLAY / WAYLAND_SOCKET, and an empty runtime
    # dir so libwayland's wayland-0 fallback cannot find a socket either.
    # XDG_SESSION_TYPE=wayland keeps the Wayland reader selected.
    no_compositor = {
        k: v for k, v in base.items() if k not in {"WAYLAND_DISPLAY", "WAYLAND_SOCKET"}
    }
    no_compositor.update(XDG_SESSION_TYPE="wayland", XDG_RUNTIME_DIR=str(runtime_dir))
    no_helper = {**base, "PATH": "/nonexistent-clipboard-probe-path"}
    return {
        "no_compositor": _child(no_compositor),
        "no_wl_paste": _child(no_helper),
    }


def main() -> int:
    if not sys.platform.startswith("linux"):
        return _evidence_limit(f"not Linux (platform {sys.platform!r})")
    if not os.environ.get("WAYLAND_DISPLAY"):
        return _evidence_limit("no Wayland session (WAYLAND_DISPLAY unset)")
    if shutil.which("wl-paste") is None or shutil.which("wl-copy") is None:
        return _evidence_limit(
            "wl-paste/wl-copy not found on PATH (apt install wl-clipboard)"
        )
    if not sway_running():
        return _evidence_limit(
            f"no running {COMPOSITOR}; this probe proves the named compositor only"
        )
    try:
        html = _probe_html()
        absent = _probe_absent()
        with tempfile.TemporaryDirectory(prefix="clipboard-no-wayland-") as raw:
            failures = _probe_failures(Path(raw))
    finally:
        _clear()
    ok = (
        html["matches"]
        and html["independent_consumer_same_bytes"]
        and html["types_before"] == html["types_after"]
        and all(c["paste_html"] is None and "error" not in c for c in absent)
        and all(f["content_error"] and f["names_wl_paste"] for f in failures.values())
    )
    report = {
        "ok": ok,
        "verified": ok,
        "compositor_generalization": False,
        "desktop": f"Linux Wayland ({COMPOSITOR})",
        "html": html,
        "absent": absent,
        "failures": failures,
        "environment": _environment(),
    }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
