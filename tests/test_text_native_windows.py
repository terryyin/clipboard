"""Optional Windows desktop native text probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable on a Windows desktop
session (see the ``native-windows-text`` CI job) with:

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked \\
    pytest tests/test_text_native_windows.py -v -rP

Independent producers / consumers are Windows PowerShell ``Set-Clipboard`` /
``Get-Clipboard``, .NET ``SetImage``, a ctypes reader and a ctypes
``OpenClipboard`` holder, each in its own process; the probe overwrites the
Windows clipboard and leaves it cleared. Its JSON report is printed (``-rP``
shows it on success). An evidence limit fails this wrapper; it never skips.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_windows_native_text.py"
sys.path.insert(0, str(ROOT / "scripts"))
from windows_native_text_support import decode_get_clipboard  # noqa: E402

TEXT_CRLF = "  héllo 👋 ﾃｽﾄ\r\nline 2 "
TEXT_LF = "héllo 👋\nline 2"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows desktop probe only")
@pytest.mark.skipif(
    os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
    reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Windows text probe",
)
def test_windows_native_text_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["evidence_limits"] == []
    assert report["failed_steps"] == []
    assert report["backend"] == "pyperclip"
    steps = {step["step"]: step for step in report["steps"]}
    assert all(step["ok"] for step in steps.values())
    crlf = steps["1_set_clipboard_crlf_to_paste"]
    assert crlf["producer"]["readback"] == TEXT_CRLF
    assert crlf["paste"]["value"] == TEXT_CRLF
    lf = steps["2_child_copy_lf_exits_to_get_clipboard"]
    assert lf["child"]["exited"] is True and lf["child"]["exit"] == 0
    assert lf["stored_text"] == TEXT_LF
    assert lf["get_clipboard"][0]["raw"] == TEXT_LF
    assert lf["two_line_consumers"]
    empty = steps["3_copy_empty_to_get_clipboard_and_paste"]
    assert empty["paste"]["value"] == ""
    image = steps["4_image_only_paste_empty"]
    assert image["paste"]["value"] == "" and image["paste"]["error"] is None
    assert "image" in image["inspect_kinds"]
    hold = steps["5_held_clipboard_raises_then_recovers"]
    for during in (hold["during_paste"], hold["during_copy"]):
        assert during["error"]["type"] == "ClipboardContentError"
        assert during["cause"]["type"] == "PyperclipWindowsException"
    assert hold["calls_within_hold"] is True
    assert hold["after_release_paste"]["value"] == hold["after_release_consumer_text"]
    env = report["environment"]
    assert env["os"] == "Windows"
    for floor in ("windows_build", "powershell", "python", "pyperclip"):
        assert env[floor], floor
    assert "windows" in env["pyperclip_paste"]
    if env["github_actions"]:
        assert env["runner_image_os"] and env["runner_image_version"]


def test_evidence_limit_report_fails_windows_text_wrapper(monkeypatch):
    """Desktop-free: an exit-2 evidence limit must fail the gated wrapper."""
    limit_stdout = json.dumps(
        {
            "ok": False,
            "evidence_limit": True,
            "evidence_limits": ["synthetic: no usable Windows clipboard session"],
            "verified": False,
        }
    )
    fake = subprocess.CompletedProcess(
        args=[sys.executable, str(PROBE)], returncode=2, stdout=limit_stdout, stderr=""
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake)
    with pytest.raises(AssertionError):
        test_windows_native_text_probe()


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def test_decode_get_clipboard_restores_exact_text_and_lines():
    stdout = json.dumps(
        {
            "raw_null": False,
            "raw": _b64(TEXT_CRLF),
            "count": 2,
            "lines": [_b64("  héllo 👋 ﾃｽﾄ"), _b64("line 2 ")],
            "ps": "5.1.26100.1",
        }
    )
    decoded = decode_get_clipboard(stdout)
    assert decoded["raw"] == TEXT_CRLF
    assert decoded["lines"] == ["  héllo 👋 ﾃｽﾄ", "line 2 "]
    assert decoded["count"] == 2 and decoded["ps"] == "5.1.26100.1"


def test_decode_get_clipboard_wraps_scalar_line_and_keeps_null():
    one = decode_get_clipboard(json.dumps({"raw": _b64("x"), "lines": _b64("x")}))
    assert one["lines"] == ["x"]
    empty = decode_get_clipboard(json.dumps({"raw_null": True, "raw": None}))
    assert empty["raw"] is None and empty["raw_null"] is True
    assert empty["lines"] == []
