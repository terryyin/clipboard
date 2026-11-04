"""Optional Linux X11 + xclip native wait probe (skipped unless enabled):
wait_for_kind and wait_for_text_change against an independent xclip.

Default pytest stays green without a desktop. Enable under Xvfb (see the
``native-linux-x11-wait`` CI job) with (replaces the CLIPBOARD):

  CLIPBOARD_NATIVE_PROBE=1 xvfb-run -a uv run --locked \\
    pytest tests/test_wait_native_linux_x11.py -v -rP

The probe's JSON report is printed (``-rP`` shows it on success), including
every snapshot / text each child observation returned. Each step's ``ok``
carries that step's conditions, so the wrapper checks the whole report. An
evidence limit fails here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_x11_native_wait.py"
STEPS = [
    "1_wait_for_text_returns_after_independent_xclip",
    "2_wait_for_html_with_nothing_copied_returns_none_at_timeout",
    "3_wait_for_text_change_returns_independent_new_text",
    "4_wait_for_text_change_ignores_clear_then_identical_recopy",
]

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux X11 + xclip probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native X11 wait probe",
    ),
    pytest.mark.skipif(
        not os.environ.get("DISPLAY"),
        reason="requires a Linux X11 session (DISPLAY)",
    ),
]


def test_linux_x11_wait_independent_producer_probe():
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
    assert report["environment"]["os"] == "Linux"
    for floor in ("xclip_version", "xvfb_version"):
        assert report["floors"][floor], floor
