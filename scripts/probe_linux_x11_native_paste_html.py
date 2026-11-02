#!/usr/bin/env python3
"""Independent-producer probe: Linux X11 CLIPBOARD ``text/html`` → paste_html().

The producer is ``xclip -selection clipboard -t text/html -i`` (not this
library's copy_html), left running as the CLIPBOARD owner. Checks that
paste_html() returns exactly the offered fragment, that a later independent
``xclip -o -t text/html`` consumer still gets the same bytes and TARGETS
(non-mutating read), and that text-only, image-only and unowned (empty)
CLIPBOARD give ``None``, while a missing DISPLAY or a missing xclip give
ClipboardContentError. Intended venue: gated GitHub Actions under Xvfb.

Prints one JSON object on stdout. Exit 0 on success, 1 on a failed check, and
2 with ``evidence_limit`` / ``verified: false`` when no X11 session or no
xclip is available (never silent verified success). Not default pytest.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from native_probe_common import linux_x11_environment
from stdlib_png import solid_red_png_bytes

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT = (
    '<a href="https://example.com/caf%C3%A9" style="color:#c00">'
    "<b>café → naïve 日本</b></a>"
)
PLAIN_TEXT = "café → naïve 日本 (plain text only)"
CONSUMER_API = "xclip -selection clipboard -o -t text/html"
_producers: list[subprocess.Popen] = []


def _distro() -> str | None:
    try:
        return platform.freedesktop_os_release().get("PRETTY_NAME")
    except OSError:
        return None


def _environment() -> dict:
    return linux_x11_environment(
        distro=_distro(),
        producer="xclip -selection clipboard -t text/html -i (independent)",
        consumer_api=CONSUMER_API,
    )


def _evidence_limit(reason: str) -> int:
    payload = {
        "ok": False,
        "desktop": "Linux X11",
        "evidence_limit": True,
        "verified": False,
        "reason": reason,
        "environment": _environment(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 2


def _xclip_out(target: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["xclip", "-selection", "clipboard", "-o", "-t", target],
        capture_output=True,
        timeout=10,
        check=False,
    )


def _targets() -> list[str]:
    result = _xclip_out("TARGETS")
    if result.returncode != 0:
        return []
    return result.stdout.decode("utf-8", "replace").split()


def _own_clipboard(data: bytes, target: str | None, expect: str) -> None:
    """Start an xclip producer that keeps owning CLIPBOARD; wait for ``expect``."""
    args = ["xclip", "-selection", "clipboard", "-i"]
    if target is not None:
        args[3:3] = ["-t", target]
    proc = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    _producers.append(proc)
    assert proc.stdin is not None
    proc.stdin.write(data)
    proc.stdin.close()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if expect in _targets():
            return
        time.sleep(0.05)
    raise RuntimeError(f"xclip producer did not offer {expect} in time")


def _release_clipboard() -> None:
    """Stop every producer (xclip forks; kill each session) so CLIPBOARD is unowned."""
    for proc in _producers:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and _xclip_out("TARGETS").returncode == 0:
        time.sleep(0.05)


def _paste_html() -> dict:
    import clipboard

    clipboard.set_html_clipboard_reader(None)
    try:
        return {"paste_html": clipboard.paste_html()}
    except clipboard.ClipboardContentError as exc:
        return {"paste_html": None, "error": f"ClipboardContentError: {exc}"}


def _child_paste_html(env: dict) -> dict:
    """paste_html() in a child with a modified environment; record the outcome."""
    child = (
        "import clipboard\n"
        "try:\n"
        "    print(repr(clipboard.paste_html()))\n"
        "except clipboard.ClipboardContentError as exc:\n"
        "    print('ClipboardContentError:', exc)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", child],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    out = result.stdout.strip()
    return {
        "returncode": result.returncode,
        "outcome": out or result.stderr.strip(),
        "content_error": out.startswith("ClipboardContentError:"),
        "names_xclip": "xclip" in out and "apt install xclip" in out,
    }


def _probe_html() -> dict:
    raw = FRAGMENT.encode("utf-8")
    _own_clipboard(raw, "text/html", "text/html")
    targets_before = _targets()
    started = time.monotonic()
    read = _paste_html()
    elapsed = time.monotonic() - started
    later = _xclip_out("text/html")
    return {
        **read,
        "expected": FRAGMENT,
        "matches": read["paste_html"] == FRAGMENT,
        "seconds": round(elapsed, 3),
        "targets_before": targets_before,
        "targets_after": _targets(),
        "independent_consumer_same_bytes": (
            later.returncode == 0 and later.stdout == raw
        ),
    }


def _probe_absent() -> list[dict]:
    cases = []
    _own_clipboard(PLAIN_TEXT.encode("utf-8"), None, "UTF8_STRING")
    cases.append({"case": "text_only", "targets": _targets(), **_paste_html()})
    _own_clipboard(solid_red_png_bytes(), "image/png", "image/png")
    cases.append({"case": "image_only", "targets": _targets(), **_paste_html()})
    _release_clipboard()
    empty = _xclip_out("TARGETS")
    cases.append(
        {
            "case": "unowned_empty",
            "xclip_targets_exit": empty.returncode,
            "xclip_targets_stderr": empty.stderr.decode("utf-8", "replace").strip(),
            **_paste_html(),
        }
    )
    return cases


def _probe_failures() -> dict:
    base = dict(os.environ)
    no_display = {k: v for k, v in base.items() if k != "DISPLAY"}
    no_xclip = {**base, "PATH": "/nonexistent-clipboard-probe-path"}
    return {
        "no_display": _child_paste_html(no_display),
        "no_xclip": _child_paste_html(no_xclip),
    }


def main() -> int:
    if not sys.platform.startswith("linux"):
        return _evidence_limit(f"not Linux (platform {sys.platform!r})")
    if not os.environ.get("DISPLAY"):
        return _evidence_limit("no X11 session (DISPLAY unset); run under xvfb-run")
    if os.environ.get("WAYLAND_DISPLAY"):
        return _evidence_limit("Wayland session; X11 HTML read probe needs X11 only")
    if shutil.which("xclip") is None:
        return _evidence_limit("xclip not found on PATH (apt install xclip)")
    try:
        html = _probe_html()
        absent = _probe_absent()
        failures = _probe_failures()
    finally:
        _release_clipboard()
    ok = (
        html["matches"]
        and html["independent_consumer_same_bytes"]
        and html["targets_before"] == html["targets_after"]
        and all(c["paste_html"] is None and "error" not in c for c in absent)
        and all(f["content_error"] and f["names_xclip"] for f in failures.values())
    )
    report = {
        "ok": ok,
        "verified": ok,
        "desktop": "Linux X11",
        "html": html,
        "absent": absent,
        "failures": failures,
        "environment": _environment(),
    }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
