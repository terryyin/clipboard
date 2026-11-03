"""Wayland observers for the copy_files probe: wl-clipboard consumer/producer.

Everything here is independent of this library: ``wl-paste`` reads and
``wl-copy`` writes the selection. The child-Python writer is shared with the
X11 probe (``linux_x11_native_copy_files_support.copy_in_exiting_child``).
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from native_probe_common import wl_clipboard_version
from native_probe_wayland import sway_running, sway_version

URI_LIST = "text/uri-list"
TEXT_TYPE = "text/plain;charset=utf-8"


def wl_paste_read(mime_type: str) -> dict:
    """Independent ``wl-paste --type T --no-newline`` read (raw bytes)."""
    try:
        result = subprocess.run(
            ["wl-paste", "--type", mime_type, "--no-newline"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "stdout": b"", "stderr": "wl-paste timed out"}
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr.decode("utf-8", "replace").strip(),
    }


def wl_list_types() -> list[str]:
    try:
        result = subprocess.run(
            ["wl-paste", "--list-types"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def set_text_independently(text: str) -> None:
    """Make an independent ``wl-copy`` (forking server) hold ``text``."""
    # DEVNULL, never pipes: wl-copy's background server would hold them open.
    subprocess.run(
        ["wl-copy", "--type", TEXT_TYPE],
        input=text.encode("utf-8"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=15,
        check=True,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if wl_paste_read(TEXT_TYPE)["stdout"] == text.encode("utf-8"):
            return
        time.sleep(0.1)
    raise RuntimeError("independent wl-copy producer did not publish the prior text")


def require_wayland_only_session() -> None:
    assert sys.platform.startswith("linux"), "Linux is required"
    assert os.environ.get("CLIPBOARD_NATIVE_PROBE") == "1", "native gate is required"
    assert os.environ.get("WAYLAND_DISPLAY"), "WAYLAND_DISPLAY is required"
    # copy_files selects X11 whenever DISPLAY is set; this probe proves Wayland.
    assert not os.environ.get("DISPLAY"), "DISPLAY must be unset (Wayland-only)"
    for executable in ("wl-copy", "wl-paste"):
        assert shutil.which(executable), f"missing required helper: {executable}"
    assert sway_running(), "a running Sway compositor is required"


def _os_release() -> str | None:
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip('"')
    except OSError:
        return None
    return None


def _package_versions(*names: str) -> str | None:
    try:
        return subprocess.run(
            ["dpkg-query", "--show", "--showformat=${Package} ${Version}\n", *names],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None


def wayland_floors() -> dict:
    return {
        "os": platform.system(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "distribution": _os_release(),
        "python": platform.python_version(),
        "sway": sway_version(),
        "wl_clipboard": wl_clipboard_version(),
        "packages": _package_versions("sway", "wl-clipboard"),
        "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
        "xdg_session_type": os.environ.get("XDG_SESSION_TYPE"),
        "session": "Wayland / headless Sway (wlroots data-control)",
    }
