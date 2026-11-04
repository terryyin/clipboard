"""Optional Linux Wayland + wl-clipboard native PRIMARY probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable inside a fresh Sway
session (see the ``native-linux-wayland-text`` CI job) with:

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked \\
    pytest tests/test_primary_native_linux_wayland.py -v -rP

Independent producers are ``wl-copy [--primary]`` runs and independent
consumers are ``wl-paste [--primary] -n``; library calls run in exiting
child Pythons. The probe overwrites CLIPBOARD and PRIMARY and leaves both
cleared. An evidence limit (no Wayland session, no wl-clipboard, no running
Sway, an unobserved step) fails here. Results are scoped to Sway.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_wayland_native_primary.py"
STEPS = [
    "4_fresh_unselected_primary_reads_empty",
    "1_different_offers_paste_primary_and_paste",
    "2_child_copy_primary_exits_then_independent_consumers",
    "3_child_copy_leaves_primary",
    "9_rejected_copy_primary_keeps_primary",
    "empty_copy_primary_reads_empty",
    "8_path_without_wl_paste_names_wl_clipboard_within_bound",
]

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux Wayland + wl-clipboard probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Wayland PRIMARY probe",
    ),
]


def test_linux_wayland_native_primary_probe():
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
    assert report["compositor_generalization"] is False
    assert [step["step"] for step in report["steps"]] == STEPS
    env = report["environment"]
    for floor in ("distro", "kernel", "python"):
        assert env[floor], floor
    assert env["compositor_version"] or env["sway_package"], "sway version"
    assert env["wl_clipboard_version"] or env["wl_clipboard_package"], "wl-clipboard"
