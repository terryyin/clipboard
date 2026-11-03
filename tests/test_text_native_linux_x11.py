"""Optional Linux X11 + xclip native text probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable under Xvfb with:

  CLIPBOARD_NATIVE_PROBE=1 xvfb-run -a uv run --locked \\
    pytest tests/test_text_native_linux_x11.py -v -rP

Independent producers are background ``xclip -i`` owners and the independent
consumer is ``xclip -o``; the probe overwrites the X11 CLIPBOARD and leaves it
unowned. Its JSON report is printed (``-rP`` shows it on success). An
evidence limit (no X11 session, no xclip, an unobserved step) fails here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_x11_native_text.py"
TEXT = "  héllo 👋 ﾃｽﾄ\nline 2 "

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux X11 + xclip probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native X11 text probe",
    ),
]


def test_linux_x11_native_text_probe():
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
    assert report["failed_steps"] == []
    assert report["backend"] == "x11"
    steps = {step["step"]: step for step in report["steps"]}
    assert all(step["ok"] for step in steps.values())
    assert steps["1_independent_producer_to_paste"]["paste"] == TEXT
    copied = steps["2_child_copy_exits_then_independent_xclip_o"]
    assert copied["consumer"]["stdout_hex"] == TEXT.encode("utf-8").hex()
    assert copied["child"]["backend"] == "x11"
    assert steps["3_copy_empty_then_paste"]["paste"] == ""
    latin = steps["4a_string_only_owner_decoded_latin_1"]
    assert latin["string_only_offer"] is True
    assert latin["paste"] == latin["expected"]
    assert steps["4b_image_only_reads_empty"]["paste"] == ""
    assert steps["4c_unowned_reads_empty"]["paste"] == ""
    dead = steps["5_dead_display_raises_quoting_xclip_within_bound"]
    for op in dead["child"]["ops"]:
        assert op["error_type"] == "ClipboardContentError"
        assert dead["xclip_direct"]["stderr"] in op["error"]
        assert op["seconds"] < dead["bound_s"] + 1.5
    for op in steps["6_path_without_xclip_names_install_hint"]["child"]["ops"]:
        assert op["error_type"] == "ClipboardContentError"
        assert "apt-get install xclip" in op["error"]
    env = report["environment"]
    for floor in ("distro", "kernel", "xclip_version", "xvfb_version", "python"):
        assert env[floor], floor
