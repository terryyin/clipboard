"""Isolated X11 Thunar harness shared by the file-manager paste probes.

Session gates, environment floors, Thunar window launch/focus/quit, and the
copy oracle. Run only inside dbus-run-session + xvfb-run with Openbox, xclip,
xdotool and Thunar; quitting Thunar there cannot close a user's window.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

PASTE_WAIT = 8


def run(*args: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, timeout=15, **kwargs)


def output(*args: str) -> str:
    return run(*args, capture_output=True, text=True).stdout.strip()


def require_isolated_thunar_session() -> None:
    assert sys.platform.startswith("linux"), "Linux is required"
    assert os.environ.get("CLIPBOARD_NATIVE_PROBE") == "1", "native gate is required"
    assert os.environ.get("CLIPBOARD_FILE_MANAGER_ISOLATED") == "1", (
        "explicit isolated file-manager session acknowledgement is required"
    )
    assert os.environ.get("DISPLAY"), "DISPLAY is required"
    assert os.environ.get("DBUS_SESSION_BUS_ADDRESS"), "isolated D-Bus is required"
    for executable in ("thunar", "xclip", "xdotool"):
        assert shutil.which(executable), f"missing required helper: {executable}"


def x11_floors() -> dict:
    xclip = run("xclip", "-version", capture_output=True, text=True)
    return {
        "os": platform.system(),
        "kernel": platform.release(),
        "distribution": Path("/etc/os-release").read_text(),
        "python": platform.python_version(),
        "thunar": output("thunar", "--version"),
        "xclip": (xclip.stdout + xclip.stderr).strip(),
        "xdotool": output("xdotool", "--version"),
        "desktop_packages": output(
            "dpkg-query",
            "--show",
            "--showformat=${Package} ${Version}\n",
            "xvfb",
            "openbox",
        ),
        "display": os.environ.get("DISPLAY"),
        "session": "X11 / Xvfb / Openbox / isolated D-Bus",
    }


def assert_copies(source: Path, destination: Path, expected: dict[str, bytes]) -> None:
    assert sorted(p.name for p in destination.iterdir()) == sorted(expected), (
        f"destination entries differ: {list(destination.iterdir())}"
    )
    for name, content in expected.items():
        assert (destination / name).read_bytes() == content, f"copy differs: {name}"
        assert (source / name).read_bytes() == content, f"source changed: {name}"


def wait_window(destination: Path, launched: subprocess.Popen) -> str:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        status = launched.poll()
        if status not in (None, 0):
            raise RuntimeError(
                f"Thunar exited with status {status}; inspect thunar.log"
            )
        result = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--class", "Thunar"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"window search failed: {result.stderr}")
        for window in result.stdout.splitlines():
            title = output("xdotool", "getwindowname", window)
            if destination.name in title:
                return window
        time.sleep(0.1)
    raise RuntimeError(f"Thunar destination window did not appear: {destination}")


@contextmanager
def thunar_window(destination: Path, log):
    """Launch Thunar on ``destination``; yield its focused window id."""
    launched = subprocess.Popen(["thunar", str(destination)], stdout=log, stderr=log)
    try:
        window = wait_window(destination, launched)
        run("xdotool", "windowactivate", "--sync", window)
        run("xdotool", "windowfocus", "--sync", window)
        yield window
    finally:
        # Own D-Bus/X11 session only, so this cannot close a user's window.
        run("thunar", "--quit", stdout=log, stderr=log)
        launched.wait(timeout=10)
