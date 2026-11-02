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
HELD = "held text ✓"


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
    assert_windows_text_report(json.loads(result.stdout))


def assert_windows_text_report(report: dict) -> None:
    """The probe report proves slice 6, with Notepad's E9b observation made."""
    assert report["ok"] is True
    assert report["evidence_limits"] == []
    assert report["observation_limits"] == []
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
    assert lf["notepad_unavailable"] is None, lf["notepad"]
    assert isinstance(lf["notepad_two_lines"], bool), lf["notepad"]
    assert lf["notepad"]["edit_class"] in ("Edit", "RichEditD2DPT")
    empty = steps["3_copy_empty_to_get_clipboard_and_paste"]
    assert empty["paste"]["value"] == ""
    image = steps["4_image_only_paste_empty"]
    assert image["paste"]["value"] == "" and image["paste"]["error"] is None
    assert "image" in image["inspect_kinds"]
    hold = steps["5_held_clipboard_raises_then_recovers"]
    holder = hold["holder"]
    assert holder["holds_at_ready"] is True and hold["probe_saw_holder_window"]
    assert holder["release"]["holds_before_release"] is True
    assert holder["release"]["close_ok"] is True
    for during in (hold["during_paste"], hold["during_copy"]):
        assert during["error"]["type"] == "ClipboardContentError"
        assert during["cause"]["type"] == "PyperclipWindowsException"
    assert hold["calls_within_hold"] is True
    assert hold["after_release_consumer_text"] == HELD
    assert hold["after_release_paste"]["value"] == HELD
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


def _report(two_lines, unavailable=None) -> dict:
    """A synthetic passing probe report with the given Notepad observation."""
    raised = {
        "value": None,
        "error": {"type": "ClipboardContentError"},
        "cause": {"type": "PyperclipWindowsException"},
    }
    pad = {"unavailable": unavailable} if unavailable else {"edit_class": "Edit"}
    steps = [
        {
            "step": "1_set_clipboard_crlf_to_paste",
            "producer": {"readback": TEXT_CRLF},
            "paste": {"value": TEXT_CRLF},
        },
        {
            "step": "2_child_copy_lf_exits_to_get_clipboard",
            "child": {"exited": True, "exit": 0},
            "stored_text": TEXT_LF,
            "get_clipboard": [{"raw": TEXT_LF}],
            "notepad": pad,
            "notepad_two_lines": two_lines,
            "notepad_unavailable": unavailable,
        },
        {"step": "3_copy_empty_to_get_clipboard_and_paste", "paste": {"value": ""}},
        {
            "step": "4_image_only_paste_empty",
            "paste": {"value": "", "error": None},
            "inspect_kinds": ["image"],
        },
        {
            "step": "5_held_clipboard_raises_then_recovers",
            "holder": {
                "holds_at_ready": True,
                "release": {"holds_before_release": True, "close_ok": True},
            },
            "probe_saw_holder_window": True,
            "during_paste": raised,
            "during_copy": raised,
            "calls_within_hold": True,
            "after_release_consumer_text": HELD,
            "after_release_paste": {"value": HELD},
        },
    ]
    for one in steps:
        one["ok"] = True
    limits = [f"notepad_unavailable: {unavailable}"] if unavailable else []
    return {
        "ok": not limits,
        "evidence_limits": [],
        "observation_limits": limits,
        "failed_steps": [],
        "backend": "pyperclip",
        "steps": steps,
        "environment": {
            "os": "Windows",
            "windows_build": 26100,
            "powershell": "5.1",
            "python": "3.13",
            "pyperclip": "1.11.0",
            "pyperclip_paste": "init_windows_clipboard.<locals>.paste_windows",
            "github_actions": False,
        },
    }


@pytest.mark.parametrize("two_lines", [True, False])
def test_wrapper_accepts_either_observed_notepad_line_result(two_lines):
    """E9b is decided by Notepad: one line or two, the observation is evidence."""
    assert_windows_text_report(_report(two_lines))


def test_wrapper_fails_when_notepad_could_not_be_driven():
    """An unavailable Notepad is not a one-line result and never passes."""
    with pytest.raises(AssertionError):
        assert_windows_text_report(_report(None, "no new Notepad window"))
    report = _report(None, "no new Notepad window")
    report["ok"], report["observation_limits"] = True, []
    with pytest.raises(AssertionError):
        assert_windows_text_report(report)


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
