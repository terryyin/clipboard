"""Shared steps for the gated Linux X11 / Wayland ``clear`` probes.

``read_everything`` reads the clipboard through every public reader in this
process, recording each value or error, so a probe can show that an empty
CLIPBOARD reads as absence (``inspect()`` empty, ``paste()`` ``""``,
``paste_html`` / ``paste_files`` / ``paste_image`` ``None``) rather than an
error. ``helper`` records an independent helper run (exit code, stdout,
stderr) so the observed helper wording lands in the report.
"""

from __future__ import annotations

import json
import platform
import subprocess

HELPER_TIMEOUT_S = 15


def helper(cmd: list[str], env: dict | None = None) -> dict:
    """Run an independent clipboard helper; record its exit and output."""
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=HELPER_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "cmd": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr.strip(),
    }


def _attempt(read) -> dict:
    try:
        return {"value": read()}
    except Exception as exc:  # noqa: BLE001 — record for the JSON report
        return {"error_type": type(exc).__name__, "error": str(exc)}


def read_everything() -> dict:
    """Every public reader's value (JSON-shaped) or error, in this process."""
    import clipboard

    def snapshot() -> dict:
        snap = clipboard.inspect()
        return {"kinds": sorted(snap.kinds), "formats": list(snap.formats)}

    def image() -> object:
        found = clipboard.paste_image()
        return None if found is None else f"{found.mode} {found.size}"

    return {
        "inspect": _attempt(snapshot),
        "paste": _attempt(clipboard.paste),
        "paste_html": _attempt(clipboard.paste_html),
        "paste_files": _attempt(clipboard.paste_files),
        "paste_image": _attempt(image),
    }


def reads_empty(reads: dict) -> bool:
    """Whether ``read_everything`` saw an empty clipboard and no errors."""
    return reads == {
        "inspect": {"value": {"kinds": [], "formats": []}},
        "paste": {"value": ""},
        "paste_html": {"value": None},
        "paste_files": {"value": None},
        "paste_image": {"value": None},
    }


def step(name: str, ok: bool, **observed) -> dict:
    return {"step": name, "ok": bool(ok), **observed}


def distro() -> str | None:
    try:
        return platform.freedesktop_os_release().get("PRETTY_NAME")
    except OSError:
        return None


def report(**fields) -> None:
    print(json.dumps(fields, indent=2, sort_keys=True, ensure_ascii=False))
