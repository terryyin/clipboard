"""Optional Windows desktop native paste_html probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable on a Windows desktop
session (see the ``native-windows-paste-html`` CI job) with:

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked \\
    pytest tests/test_paste_html_native_windows.py -v -rP

Producers are Windows PowerShell 5.1 / .NET Framework processes (not
copy_html); the probe overwrites the Windows clipboard and leaves it cleared.
An evidence-limit probe report (exit 2) fails this wrapper, matching
X11/Wayland/macOS native paste_html tests — never skip or pass as verified.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_windows_native_paste_html.py"
EVIDENCE_LIMIT_EXIT = 2
FRAGMENT = (
    '<a href="https://example.com/caf%C3%A9" style="color:#c00">'
    "<b>café → naïve 日本</b></a>"
)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows desktop probe only")
@pytest.mark.skipif(
    os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
    reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Windows read probe",
)
def test_windows_independent_producer_paste_html_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["verified"] is True
    required, *observed = report["html"]
    assert required["case"] == "dotnet_stream"
    assert required["offset_unit"] == "utf8_bytes"
    assert required["paste_html"] == FRAGMENT
    assert "Version:" not in required["paste_html"]
    assert required["unchanged"] is True
    assert "HTML Format" in required["formats"]
    for case in observed:  # recorded producer behavior; reads never mutate
        if case["producer_exit"] == 0:
            assert case["unchanged"] is True, case
        if case["case"] == "set_clipboard_as_html":
            if case.get("offset_unit") == "utf8_bytes":
                assert case["paste_html"] == FRAGMENT, case
    assert {case["case"]: case["paste_html"] for case in report["absent"]} == {
        "text_only": None,
        "image_only": None,
        "cleared_empty": None,
    }
    assert all("error" not in case for case in report["absent"])
    assert all(case["unchanged"] for case in report["absent"])
    env = report["environment"]
    assert env["os"] == "Windows"
    assert env["windows_build"]
    assert env["powershell"]
    assert env["python"]


def test_evidence_limit_report_fails_windows_paste_html_wrapper(monkeypatch):
    """Desktop-free: exit-2 evidence_limit must fail the gated wrapper.

    Without removing the former ``pytest.skip`` on exit 2, this check would
    see a skip instead of an assertion failure and would not establish the
    CI-fail promise for ``native-windows-paste-html`` / ``ci-passed``.
    """
    limit_stdout = json.dumps(
        {
            "ok": False,
            "evidence_limit": True,
            "verified": False,
            "reason": "synthetic: no usable Windows clipboard session",
        }
    )
    fake = subprocess.CompletedProcess(
        args=[sys.executable, str(PROBE)],
        returncode=EVIDENCE_LIMIT_EXIT,
        stdout=limit_stdout,
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake)
    with pytest.raises(AssertionError):
        test_windows_independent_producer_paste_html_probe()
