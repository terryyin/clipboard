"""Independent processes and floors for the gated Windows text probe.

Producers / consumers here are not this library: Windows PowerShell 5.1 and
(when present) PowerShell 7 ``Get-Clipboard``, the ctypes
``windows_clipboard_consumer.py --text`` reader, Notepad driven by
``windows_notepad_consumer.py``, and a child Python that runs
``clipboard.copy`` and exits. Text crosses process boundaries as UTF-8 files,
JSON with ASCII escapes, or base64, never as raw command-line text.
"""

from __future__ import annotations

import base64
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from windows_powershell_producers import FLOORS, PRODUCERS, powershell

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = Path(__file__).with_name("windows_clipboard_consumer.py")
NOTEPAD = Path(__file__).with_name("windows_notepad_consumer.py")

# ``-Raw`` string and array form, each line as base64 of its UTF-8 bytes.
GET_CLIPBOARD = (
    "function B($s) { if ($null -eq $s) { $null } else "
    "{ [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([string]$s)) } }\n"
    "$raw = Get-Clipboard -Raw\n"
    "$lines = @(Get-Clipboard)\n"
    "@{ raw_null = ($null -eq $raw); raw = (B $raw); count = $lines.Count; "
    "lines = @($lines | ForEach-Object { B $_ }); "
    "ps = $PSVersionTable.PSVersion.ToString() } | ConvertTo-Json -Compress"
)

_CHILD = """
import json, os, sys
sys.path.insert(0, %r)
import clipboard
out = {"pid": os.getpid()}
try:
    clipboard.copy(json.loads(sys.argv[1]))
    out["copied"] = True
except Exception as exc:
    out["error"] = f"{type(exc).__name__}: {exc}"
print(json.dumps(out))
"""


def _b64(value: str | None) -> str | None:
    return None if value is None else base64.b64decode(value).decode("utf-8")


def decode_get_clipboard(stdout: str) -> dict:
    """Decode :data:`GET_CLIPBOARD` JSON into ``raw`` / ``lines`` strings.

    PowerShell 5.1 may serialize a one-element array as a bare value, so a
    non-list ``lines`` is wrapped.
    """
    payload = json.loads(stdout)
    lines = payload.get("lines")
    if lines is None:
        lines = []
    elif not isinstance(lines, list):
        lines = [lines]
    return {
        "raw_null": payload.get("raw_null"),
        "raw": _b64(payload.get("raw")),
        "count": payload.get("count"),
        "lines": [_b64(line) for line in lines],
        "ps": payload.get("ps"),
    }


def get_clipboard(exe: str = "powershell.exe") -> dict:
    """Independent consumer: ``Get-Clipboard -Raw`` and array form in ``exe``."""
    result = powershell(GET_CLIPBOARD, exe=exe)
    if result.returncode != 0:
        return {"exe": exe, "error": result.stderr.strip()[-1000:]}
    try:
        return {"exe": exe, **decode_get_clipboard(result.stdout)}
    except (ValueError, UnicodeDecodeError) as exc:
        return {"exe": exe, "error": f"undecodable output {result.stdout!r}: {exc}"}


def pwsh() -> str | None:
    """PowerShell 7 (``pwsh``) when installed, else ``None``."""
    return shutil.which("pwsh")


def _json_child(script: Path, *args: str, timeout: float) -> dict | str:
    """Run ``script`` isolated; its stdout JSON, or its output when not JSON."""
    result = subprocess.run(
        [sys.executable, "-I", str(script), *args],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
    )
    try:
        return json.loads(result.stdout)
    except ValueError:
        return (result.stderr or result.stdout).strip()


def consume() -> dict:
    """Independent ctypes consumer in a child process (formats + text)."""
    report = _json_child(CONSUMER, "--text", timeout=60)
    return {"consumer_error": report} if isinstance(report, str) else report


def notepad() -> dict:
    """Notepad pastes the clipboard (``WM_PASTE``); line count, text, build.

    ``unavailable`` names why Notepad could not be driven; it is never folded
    into a line count.
    """
    report = _json_child(NOTEPAD, timeout=90)
    if isinstance(report, str):
        report = {"unavailable": "notepad consumer gave no JSON"}
    path = report.get("notepad_path")
    if path:
        version = powershell(
            "(Get-Item ([IO.File]::ReadAllText($in))).VersionInfo.FileVersion", path
        )
        report["notepad_version"] = version.stdout.strip() or None
    return report


def set_clipboard(text: str) -> dict:
    """Independent producer: ``Set-Clipboard`` with the text from a UTF-8 file."""
    produced = powershell(PRODUCERS["text_only"], text)
    readback = consume()
    return {
        "producer_exit": produced.returncode,
        "producer_stderr": produced.stderr.strip()[-1000:],
        "readback": readback.get("text"),
        "producer_exact": produced.returncode == 0 and readback.get("text") == text,
    }


def step(name: str, ok: bool, limit: str | None = None, **observed) -> dict:
    """``limit`` names an evidence limit (the runner could not set up the case)."""
    return {
        "step": name,
        "ok": ok and limit is None,
        "evidence_limit": limit,
        **observed,
    }


def child_copy(text: str) -> dict:
    """Run ``clipboard.copy(text)`` in a child Python and wait for it to exit."""
    result = subprocess.run(
        [sys.executable, "-c", _CHILD % str(ROOT), json.dumps(text)],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
        check=False,
    )
    try:
        out = json.loads(result.stdout)
    except ValueError:
        out = {"error": (result.stderr or result.stdout).strip()[-1000:]}
    return {**out, "exit": result.returncode, "exited": True}


def attempt(operation, *args) -> dict:
    """Call ``operation`` and record value or error, cause and duration."""
    start = time.monotonic()
    try:
        value, error, cause = operation(*args), None, None
    except Exception as exc:  # noqa: BLE001 - recorded for the JSON report
        value, error = None, {"type": type(exc).__name__, "message": str(exc)}
        cause = exc.__cause__
        if cause is not None:
            cause = {"type": type(cause).__name__, "message": str(cause)}
    return {
        "value": value,
        "error": error,
        "cause": cause,
        "duration_s": round(time.monotonic() - start, 3),
    }


def windows_floors() -> dict:
    """OS, runner image, PowerShell, Python and pyperclip floors."""
    import pyperclip

    ps = powershell(FLOORS)
    try:
        ps_floors = json.loads(ps.stdout)
    except ValueError:
        ps_floors = {"error": ps.stderr.strip()[-500:]}
    pwsh_exe = pwsh()
    pwsh_version = None
    if pwsh_exe:
        got = powershell("$PSVersionTable.PSVersion.ToString()", exe=pwsh_exe)
        pwsh_version = got.stdout.strip() or None
    win = sys.getwindowsversion() if sys.platform == "win32" else None
    return {
        "os": platform.system(),
        "windows_release": platform.release(),
        "windows_version": platform.version(),
        "windows_build": win.build if win else None,
        "windows_edition": platform.win32_edition() if win else None,
        "machine": platform.machine(),
        "runner_image_os": os.environ.get("ImageOS"),
        "runner_image_version": os.environ.get("ImageVersion"),
        "github_actions": os.environ.get("GITHUB_ACTIONS") == "true",
        "powershell": ps_floors.get("ps"),
        "powershell_edition": ps_floors.get("edition"),
        "powershell_os": ps_floors.get("os"),
        "clr": ps_floors.get("clr"),
        "pwsh": pwsh_version,
        "python": platform.python_version(),
        "pyperclip": importlib.metadata.version("pyperclip"),
        "pyperclip_paste": getattr(pyperclip.paste, "__qualname__", None),
        "pyperclip_copy": getattr(pyperclip.copy, "__qualname__", None),
    }
