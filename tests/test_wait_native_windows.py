"""Optional Windows desktop native wait probe (skipped unless enabled):
wait_for_kind and wait_for_text_change against an independent Set-Clipboard.

Default pytest stays green without a desktop. Enable on a Windows desktop
session (see the ``native-windows-wait`` CI job) with (replaces the live
clipboard):

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked \\
    pytest tests/test_wait_native_windows.py -v -rP

The probe's JSON report is printed (``-rP`` shows it on success), including
every snapshot / text each child observation returned. An evidence limit
fails here; it never skips on ``win32``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_windows_native_wait.py"
STEPS = [
    "1_wait_for_text_returns_after_independent_set_clipboard",
    "2_wait_for_html_with_nothing_copied_returns_none_at_timeout",
    "3_wait_for_text_change_returns_independent_new_text",
    "4_wait_for_text_change_ignores_clear_then_identical_recopy",
]

pytestmark = [
    pytest.mark.skipif(sys.platform != "win32", reason="Windows desktop probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Windows wait probe",
    ),
]


def test_windows_wait_independent_producer_probe():
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
    assert report["evidence_limit"] is False
    assert report["ok"] is True
    assert report["failed_steps"] == []
    # Each step's ``ok`` carries its own conditions; the list fixes the order.
    assert [step["step"] for step in report["steps"]] == STEPS
    env = report["environment"]
    assert env["os"] == "Windows"
    for floor in ("windows_version", "windows_build", "powershell", "python"):
        assert env[floor], floor
    if env["github_actions"]:
        assert env["runner_image_os"] and env["runner_image_version"]
