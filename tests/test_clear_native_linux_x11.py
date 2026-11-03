"""Optional Linux X11 + xclip native clear probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable on a fresh Xvfb (see the
``native-linux-x11-clear`` CI job) with:

  CLIPBOARD_NATIVE_PROBE=1 xvfb-run -a uv run --locked --extra images \\
    pytest tests/test_clear_native_linux_x11.py -v -rP

The probe must run before anything owns CLIPBOARD on that X server: its first
step reads the fresh, unowned clipboard. Its JSON report is printed (``-rP``
shows it on success); each step's ``ok`` carries that step's conditions, so
the wrapper checks the whole report. An evidence limit fails here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_x11_native_clear.py"

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux X11 + xclip probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native X11 clear probe",
    ),
    pytest.mark.skipif(
        not os.environ.get("DISPLAY"),
        reason="requires a Linux X11 session (DISPLAY)",
    ),
]


def test_linux_x11_native_clear_probe():
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
    assert report["failed_steps"] == []
    assert [step["step"] for step in report["steps"]] == [
        "1_fresh_unowned_clipboard_reads_empty",
        "2_early_raw_xsetselectionowner_none_ends_html_owner",
        "3_html_producer_then_child_clear_reads_empty",
        "4_copy_image_owner_ends_after_child_clear",
        "5_clear_twice_on_cleared_succeeds",
        "6_unopenable_display_raises_naming_display",
        "7_file_list_producer_then_child_clear_reads_empty",
        "8_unknown_type_producer_then_child_clear_reads_empty",
    ]
    env = report["environment"]
    assert env["xclip_version"], "xclip version"
    assert env["xvfb_version"], "Xvfb version"
