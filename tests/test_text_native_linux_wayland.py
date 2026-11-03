"""Optional Linux Wayland + wl-clipboard native text probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable inside a Sway session
(see the ``native-linux-wayland-text`` CI job) with:

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked \\
    pytest tests/test_text_native_linux_wayland.py -v -rP

Independent producers are ``wl-copy`` runs and the independent consumer is
``wl-paste``; the probe overwrites the Wayland selection and leaves it
cleared. Its JSON report is printed (``-rP`` shows it on success). An
evidence limit (no Wayland session, no wl-clipboard, no running Sway, an
unobserved step) fails here. Results are scoped to Sway.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_wayland_native_text.py"
TEXT = "  héllo 👋 ﾃｽﾄ\nline 2 "
NEWLINE_TEXT = "line 1\nline 2\n"

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux Wayland + wl-clipboard probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Wayland text probe",
    ),
]


def test_linux_wayland_native_text_probe():
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
    assert report["backend"] == "wayland"
    assert report["compositor_generalization"] is False
    steps = {step["step"]: step for step in report["steps"]}
    assert all(step["ok"] for step in steps.values())
    assert steps["1_independent_producer_to_paste"]["paste"] == TEXT
    copied = steps["2_child_copy_exits_then_independent_wl_paste"]
    assert copied["consumer"]["stdout_hex"] == TEXT.encode("utf-8").hex()
    assert copied["child"]["backend"] == "wayland"
    assert "text/plain;charset=utf-8" in copied["types"]
    assert steps["3_copy_empty_then_paste"]["paste"] == ""
    newline = steps["4_trailing_newline_round_trip"]
    assert newline["paste"] == NEWLINE_TEXT
    assert newline["child_copy"]["consumer"]["stdout_hex"] == (
        NEWLINE_TEXT.encode().hex()
    )
    assert steps["5a_image_only_reads_empty"]["paste"] == ""
    assert steps["5b_cleared_reads_empty"]["paste"] == ""
    stale = steps["6_stale_wayland_display_raises_quoting_helper_within_bound"]
    assert stale["display"]["exists"] is False
    for op in stale["child"]["ops"]:
        assert op["error_type"] == "ClipboardContentError"
        assert stale["helper_stderr"][op["op"]] in op["error"]
        assert op["seconds"] < stale["bound_s"] + 1.5
    for op in steps["7_path_without_wl_paste_names_install_hint"]["child"]["ops"]:
        assert op["error_type"] == "ClipboardContentError"
        assert "apt-get install wl-clipboard" in op["error"]
    assert steps["8_copy_then_immediate_paste_sees_new_text"]["ok"] is True
    env = report["environment"]
    for floor in ("distro", "kernel", "python"):
        assert env[floor], floor
    assert env["compositor_version"] or env["sway_package"], "sway version"
    assert env["wl_clipboard_version"] or env["wl_clipboard_package"], "wl-clipboard"
