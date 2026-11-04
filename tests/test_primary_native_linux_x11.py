"""Optional Linux X11 + xclip native PRIMARY probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable under Xvfb with:

  CLIPBOARD_NATIVE_PROBE=1 xvfb-run -a uv run --locked \\
    pytest tests/test_primary_native_linux_x11.py -v -rP

Independent producers are background ``xclip -selection primary|clipboard
-i`` owners and independent consumers are ``xclip -selection
primary|clipboard -o``; library calls run in exiting child Pythons. The probe
overwrites CLIPBOARD and PRIMARY and leaves both unowned. An evidence limit
(no X11 session, no xclip or xsel, an unobserved step) fails here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_x11_native_primary.py"
STEPS = [
    "4_fresh_unowned_primary_reads_empty",
    "1_different_owners_paste_primary_and_paste",
    "2_child_copy_primary_exits_then_independent_consumers",
    "3_child_copy_leaves_primary",
    "9_rejected_copy_primary_keeps_primary",
    "8_path_with_xsel_but_no_xclip_names_xclip_within_bound",
]

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux X11 + xclip probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native X11 PRIMARY probe",
    ),
]


def test_linux_x11_native_primary_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert [step["step"] for step in report["steps"]] == STEPS
    env = report["environment"]
    for floor in ("distro", "kernel", "xclip_version", "xvfb_version", "python"):
        assert env[floor], floor
