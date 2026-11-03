"""Optional Linux X11 + xclip native clear probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable on a fresh Xvfb (see the
``native-linux-x11-clear`` CI job) with:

  CLIPBOARD_NATIVE_PROBE=1 xvfb-run -a uv run --locked --extra images \\
    pytest tests/test_clear_native_linux_x11.py -v -rP

The probe must run before anything owns CLIPBOARD on that X server: its first
step reads the fresh, unowned clipboard. Its JSON report is printed (``-rP``
shows it on success). An evidence limit fails here.
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
EMPTY_READS = {
    "inspect": {"value": {"kinds": [], "formats": []}},
    "paste": {"value": ""},
    "paste_html": {"value": None},
    "paste_files": {"value": None},
    "paste_image": {"value": None},
}

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
    steps = {step["step"]: step for step in report["steps"]}
    fresh = steps["1_fresh_unowned_clipboard_reads_empty"]
    assert fresh["xclip_targets"]["returncode"] != 0
    assert fresh["classified_no_owner"] is True
    assert fresh["reads"] == EMPTY_READS
    env = report["environment"]
    assert env["xclip_version"], "xclip version"
    assert env["xvfb_version"], "Xvfb version"
