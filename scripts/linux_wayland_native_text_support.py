"""Independent wl-clipboard producers / consumers for the Wayland text probe.

Producers are ``wl-copy`` runs (each forks its own background source) and
consumers are ``wl-paste`` runs, never this library. Child Python runs,
step records, and the bound check come from the X11 text probe's support
module (``child`` runs ``clipboard.copy`` / ``paste`` in another Python that
exits before the caller looks, timing each operation).
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path

from linux_x11_native_text_support import BOUND_S, SLACK_S, child, paste_now, record
from native_probe_wayland import wayland_paste_environment

UTF8_TYPE = "text/plain;charset=utf-8"
NEWLINE_TEXT = "line 1\nline 2\n"
SCRIPT_TEXT = "#!/bin/sh\necho 'hi'\n"


def wl_paste(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["wl-paste", *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=env,
        timeout=15,
        check=False,
    )


def wl_copy(args: list[str], data: bytes | None, env: dict | None = None) -> dict:
    """Run an independent wl-copy (stderr to a file its forked source may keep)."""
    with tempfile.TemporaryFile() as log:
        started = time.monotonic()
        proc = subprocess.Popen(
            ["wl-copy", *args],
            stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=log,
            env=env,
            start_new_session=True,
        )
        proc.communicate(input=data, timeout=30)
        log.seek(0)
        return {
            "argv": ["wl-copy", *args],
            "returncode": proc.returncode,
            "stderr": log.read().decode("utf-8", "replace").strip(),
            "seconds": round(time.monotonic() - started, 3),
        }


def types() -> list[str]:
    result = wl_paste("--list-types")
    return [] if result.returncode else result.stdout.decode("utf-8", "replace").split()


def offer(data: bytes, args: list[str], expect: str) -> dict:
    """Independent producer: wl-copy ``data``, then wait until ``expect`` serves it."""
    produced = wl_copy(args, data)
    if produced["returncode"] != 0:
        raise RuntimeError(f"independent producer failed: {produced}")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        served = wl_paste("-n", "-t", expect)
        if served.returncode == 0 and served.stdout == data:
            return produced
        time.sleep(0.05)
    raise RuntimeError(f"independent wl-copy producer did not serve {expect} in time")


def clear() -> dict:
    cleared = wl_copy(["--clear"], None)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and wl_paste("--list-types").returncode == 0:
        time.sleep(0.05)
    return cleared


def stale_display() -> dict:
    """A WAYLAND_DISPLAY name with no socket in XDG_RUNTIME_DIR (prefer wayland-9)."""
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR") or "/nonexistent-runtime")
    current = os.environ.get("WAYLAND_DISPLAY", "")
    for n in range(9, 100):
        name = f"wayland-{n}"
        if name != current and not (runtime / name).exists():
            return {"name": name, "socket": str(runtime / name), "exists": False}
    raise RuntimeError("no unused WAYLAND_DISPLAY name for the stale-socket step")


def session_env(**overrides: str) -> dict:
    """This environment without X11 or WAYLAND_SOCKET, so text dispatch is Wayland's."""
    env = {
        k: v for k, v in os.environ.items() if k not in {"DISPLAY", "WAYLAND_SOCKET"}
    }
    env.update(overrides)
    return env


def path_with_only_wl_copy(directory: Path) -> str:
    """A PATH directory holding wl-copy but no wl-paste (and no xclip)."""
    import shutil

    wl_copy_path = shutil.which("wl-copy")
    if wl_copy_path is None:
        raise RuntimeError("wl-copy not on PATH")
    (directory / "wl-copy").symlink_to(wl_copy_path)
    return str(directory)


def failures_within_bound(kid: dict, quoted: dict[str, str]) -> bool:
    """Each op raised ClipboardContentError within the bound quoting its helper."""
    ops = kid.get("ops") or []
    return len(ops) == len(quoted) and all(
        op.get("error_type") == "ClipboardContentError"
        and op["seconds"] < BOUND_S + SLACK_S
        and quoted.get(op["op"])
        and quoted[op["op"]] in op["error"]
        for op in ops
    )


def child_copy_then_consume(text: str) -> dict:
    kid = child([["copy", text]])
    consumer = wl_paste("-n", "-t", UTF8_TYPE)
    ok = kid["returncode"] == 0 and "error" not in (kid.get("ops") or [{}])[0]
    return {
        "ok": ok and consumer.returncode == 0 and consumer.stdout == text.encode(),
        "child": kid,
        "consumer": record(consumer),
        "expected_hex": text.encode().hex(),
        "types": types(),
    }


def immediate_visibility(observed: dict) -> dict:
    """copy() then an immediate read, in-process and across processes."""
    import clipboard

    in_process = []
    for i in range(20):
        text = f"iteration {i} ✓"
        clipboard.copy(text)
        got = paste_now()
        if got != {"paste": text}:
            in_process.append({"i": i, **got})
    across = []
    for i in range(5):
        text = f"child iteration {i} ✓"
        kid = child([["copy", text], ["paste"]])
        consumer = wl_paste("-n", "-t", UTF8_TYPE)
        ops = kid.get("ops") or [{}, {}]
        if ops[-1].get("paste") != text or consumer.stdout != text.encode():
            across.append({"i": i, "child": kid, "consumer": record(consumer)})
    observed["immediate_visibility"] = {
        "in_process_mismatches": in_process,
        "child_mismatches": across,
    }
    return {"ok": not in_process and not across, "in_process": 20, "children": 5}


def _version(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (out.stdout or out.stderr or "").strip()
    return text.splitlines()[0].strip() if out.returncode == 0 and text else None


def package_version(package: str) -> str | None:
    return _version(["dpkg-query", "-W", "-f=${Version}", package])


def environment() -> dict:
    try:
        distro = platform.freedesktop_os_release().get("PRETTY_NAME")
    except OSError:
        distro = None
    return wayland_paste_environment(
        distro=distro,
        kernel=platform.release(),
        sway_package=package_version("sway"),
        wl_clipboard_package=package_version("wl-clipboard"),
        producer="wl-copy [--type T] (independent, forks its own source)",
        consumer="wl-paste -n [-t T] (independent)",
    )


def report(**fields) -> None:
    fields.setdefault("environment", environment())
    print(json.dumps(fields, indent=2, sort_keys=True, ensure_ascii=False))
