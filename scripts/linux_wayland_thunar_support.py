"""Optional, recorded-only Thunar Paste attempt on headless Sway (Wayland GTK).

Thunar runs with ``GDK_BACKEND=wayland`` in the probe's isolated D-Bus
session; Sway IPC (``swaymsg``) finds and focuses its destination window and
``wtype`` sends Ctrl+V through Sway's virtual-keyboard protocol. The copy
oracle (``assert_copies``) is shared with the X11 Thunar harness. Every step
is bounded, and any failure is returned as data: the attempt never decides
the probe's verdict until it has been observed to be reliable.
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from linux_x11_thunar_support import PASTE_WAIT, assert_copies

WINDOW_WAIT = 15
STEP_TIMEOUT = 15


def _sway_env() -> dict:
    env = dict(os.environ, GDK_BACKEND="wayland")
    if not env.get("SWAYSOCK"):
        runtime = env.get("XDG_RUNTIME_DIR", "")
        sockets = sorted(glob.glob(os.path.join(runtime, "sway-ipc.*.sock")))
        if sockets:
            env["SWAYSOCK"] = sockets[-1]
    return env


def _run(env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, env=env, capture_output=True, text=True, timeout=STEP_TIMEOUT, check=True
    )


def _find_window(node: dict, title_part: str) -> int | None:
    if node.get("app_id") in ("thunar", "Thunar") and title_part in (
        node.get("name") or ""
    ):
        return node["id"]
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        found = _find_window(child, title_part)
        if found is not None:
            return found
    return None


def _wait_window(env: dict, destination: Path, launched) -> int:
    deadline = time.monotonic() + WINDOW_WAIT
    while time.monotonic() < deadline:
        status = launched.poll()
        if status not in (None, 0):
            raise RuntimeError(f"Thunar exited with status {status}")
        tree = json.loads(_run(env, "swaymsg", "-r", "-t", "get_tree").stdout)
        found = _find_window(tree, destination.name)
        if found is not None:
            return found
        time.sleep(0.2)
    raise RuntimeError(f"Thunar window for {destination.name} did not appear")


def missing_prerequisites() -> list[str]:
    missing = [t for t in ("thunar", "wtype", "swaymsg") if shutil.which(t) is None]
    if os.environ.get("CLIPBOARD_FILE_MANAGER_ISOLATED") != "1":
        missing.append("CLIPBOARD_FILE_MANAGER_ISOLATED=1")
    if not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        missing.append("isolated D-Bus session")
    return missing


def attempt_thunar_paste(
    source: Path, destination: Path, expected: dict[str, bytes], log
) -> dict:
    """Try Ctrl+V into a Wayland Thunar window; report what happened."""
    missing = missing_prerequisites()
    if missing:
        return {"attempted": False, "copies_match": False, "missing": missing}
    env = _sway_env()
    report: dict = {"attempted": True, "copies_match": False, "error": None}
    launched = subprocess.Popen(
        ["thunar", str(destination)], env=env, stdout=log, stderr=log
    )
    try:
        window = _wait_window(env, destination, launched)
        report["sway_con_id"] = window
        _run(env, "swaymsg", f"[con_id={window}] focus")
        _run(env, "wtype", "-k", "Escape")
        _run(env, "wtype", "-M", "ctrl", "v", "-m", "ctrl")
        deadline = time.monotonic() + PASTE_WAIT
        while time.monotonic() < deadline:
            if all((destination / name).is_file() for name in expected):
                break
            time.sleep(0.1)
        assert_copies(source, destination, expected)
        report["copies_match"] = True
    except Exception as exc:  # recorded, never raised: the attempt is not gated
        stderr = getattr(exc, "stderr", None)
        report["error"] = f"{type(exc).__name__}: {exc}" + (
            f" ({stderr.strip()})" if stderr else ""
        )
    finally:
        report["destination_entries"] = sorted(p.name for p in destination.iterdir())
        # Own D-Bus session only, so this cannot close a user's window.
        try:
            subprocess.run(
                ["thunar", "--quit"], env=env, stdout=log, stderr=log, timeout=15
            )
            launched.wait(timeout=10)
        except subprocess.TimeoutExpired:
            launched.kill()
    report["paste_action"] = "Sway IPC focus + wtype ctrl+v (GDK_BACKEND=wayland)"
    return report
