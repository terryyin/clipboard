"""Independent xclip producers / consumers and child runs for the X11 text probe.

Producers are background ``xclip -selection clipboard [-t T] -i`` owners and
consumers are ``xclip -selection clipboard -o -t T`` runs, never this
library. ``child`` runs ``clipboard.copy`` / ``paste`` in another Python that
exits before the caller looks, timing each operation.
"""

from __future__ import annotations

import json
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path

from native_probe_common import linux_x11_environment

ROOT = Path(__file__).resolve().parents[1]
TEXT = "  héllo 👋 ﾃｽﾄ\nline 2 "
LATIN = "café ½ naïve"
BOUND_S = 10.0  # documented X11 text read / write bound
SLACK_S = 1.5  # child start-up and measurement slack over the bound
NO_XCLIP_PATH = "/nonexistent-clipboard-probe-path"
_producers: list[subprocess.Popen] = []

_CHILD = """
import json, sys, time
sys.path.insert(0, %r)
import clipboard
out = []
try:
    backend = clipboard._text._select_text_backend()
except Exception as exc:
    backend = f"{type(exc).__name__}: {exc}"
for op in json.loads(sys.argv[1]):
    entry = {"op": op[0]}
    started = time.monotonic()
    try:
        if op[0] == "copy":
            clipboard.copy(op[1])
        else:
            entry["paste"] = clipboard.paste()
    except Exception as exc:
        entry["error_type"] = type(exc).__name__
        entry["error"] = str(exc)
    entry["seconds"] = round(time.monotonic() - started, 3)
    out.append(entry)
print(json.dumps({"backend": backend, "ops": out}))
"""


def child(ops: list[list[str]], env: dict | None = None) -> dict:
    result = subprocess.run(
        [sys.executable, "-c", _CHILD % str(ROOT), json.dumps(ops)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    out = {"returncode": result.returncode, "stderr": result.stderr.strip()}
    try:
        out.update(json.loads(result.stdout))
    except ValueError:
        out["stdout"] = result.stdout
    return out


def xclip_out(target: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["xclip", "-selection", "clipboard", "-o", "-t", target],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=env,
        timeout=15,
        check=False,
    )


def record(result: subprocess.CompletedProcess) -> dict:
    return {
        "returncode": result.returncode,
        "stdout_hex": result.stdout.hex(),
        "stderr": result.stderr.decode("utf-8", "replace").strip(),
    }


def targets() -> list[str]:
    result = xclip_out("TARGETS")
    return [] if result.returncode else result.stdout.decode("ascii", "replace").split()


def own(data: bytes, target: str | None, expect: str) -> None:
    """Independent producer: a background xclip owner serving ``data`` as ``expect``."""
    args = [
        "xclip",
        "-selection",
        "clipboard",
        *(["-t", target] if target else []),
        "-i",
    ]
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
        served = xclip_out(expect)
        if served.returncode == 0 and served.stdout == data:
            return
        time.sleep(0.05)
    raise RuntimeError(f"independent xclip producer did not serve {expect} in time")


def release_all() -> None:
    """Stop every xclip owner (producers and the library's) so CLIPBOARD is unowned."""
    for proc in _producers:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    subprocess.run(["pkill", "-x", "xclip"], capture_output=True, check=False)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and xclip_out("TARGETS").returncode == 0:
        time.sleep(0.05)


def dead_display() -> str:
    """A display number with no server (``xvfb-run -a`` itself starts at :99)."""
    current = os.environ.get("DISPLAY", "")
    for n in range(90, 200):
        free = not Path(f"/tmp/.X11-unix/X{n}").exists()
        if f":{n}" != current and free and not Path(f"/tmp/.X{n}-lock").exists():
            return f":{n}"
    raise RuntimeError("no free X display number for the dead-display step")


def paste_now() -> dict:
    import clipboard

    try:
        return {"paste": clipboard.paste()}
    except Exception as exc:  # noqa: BLE001 — record for the JSON report
        return {"error": f"{type(exc).__name__}: {exc}"}


def step(name: str, ok: bool, **observed) -> dict:
    return {"step": name, "ok": bool(ok), **observed}


def errors_within_bound(child: dict, must_contain: list[str]) -> bool:
    ops = child.get("ops") or []
    return len(ops) == 2 and all(
        op.get("error_type") == "ClipboardContentError"
        and op["seconds"] < BOUND_S + SLACK_S
        and all(text and text in op["error"] for text in must_contain)
        for op in ops
    )


def _version_output(cmd: list[str]) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def xvfb_version() -> str | None:
    """The installed Xvfb: the apt package version, else its stderr banner."""
    package = _version_output(["dpkg-query", "-W", "-f=${Version}", "xvfb"])
    if package is not None and package.returncode == 0 and package.stdout.strip():
        return f"xvfb {package.stdout.strip()}"
    banner = _version_output(["Xvfb", "-version"])
    if banner is None:
        return None
    lines = [line.strip() for line in (banner.stderr + banner.stdout).splitlines()]
    lines = [line for line in lines if line]
    return next(
        (line for line in lines if "x server" in line.lower()),
        next((line for line in lines if "version" in line.lower()), None),
    )


def environment() -> dict:
    try:
        distro = platform.freedesktop_os_release().get("PRETTY_NAME")
    except OSError:
        distro = None
    return linux_x11_environment(
        distro=distro,
        kernel=platform.release(),
        xvfb_version=xvfb_version(),
        producer="xclip -selection clipboard [-t T] -i (independent, background)",
        consumer="xclip -selection clipboard -o -t UTF8_STRING (independent)",
    )


def report(**fields) -> None:
    fields.setdefault("environment", environment())
    print(json.dumps(fields, indent=2, sort_keys=True, ensure_ascii=False))
