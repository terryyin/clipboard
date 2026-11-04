"""Optional macOS native text probe (skipped unless explicitly enabled).

Default pytest stays green without a desktop. Enable with:

  CLIPBOARD_NATIVE_PROBE=1 ./scripts/dev uv run --locked --extra images \\
    pytest tests/test_text_native_macos.py -v

The probe uses independent osascript / pbpaste producers and consumers, a
child Python with an empty environment, and overwrites the clipboard. Any
unobserved step is an evidence limit and fails this test rather than skipping.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_macos_native_text.py"
TEXT = "  héllo 👋 ﾃｽﾄ\nline 2 "

pytestmark = [
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS pasteboard probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native pasteboard probe",
    ),
]


def test_macos_native_text_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["evidence_limits"] == []
    steps = {step["step"]: step for step in report["steps"]}
    assert all(step["ok"] for step in steps.values())
    assert steps["1_independent_producer_to_paste"]["paste"] == TEXT
    copied = steps["2_empty_env_child_copy_to_independent_consumers"]
    assert copied["pbpaste_utf8"]["bytes"] == TEXT.encode("utf-8").hex()
    assert copied["osascript_the_clipboard"] == TEXT
    assert not any(k.startswith(("LC_", "LANG")) for k in copied["child"]["environ"])
    assert steps["3_empty_env_child_paste"]["child"]["paste"] == TEXT
    assert steps["4_copy_empty_then_paste"]["paste"] == ""
    assert steps["6a_cleared_reads_empty"]["paste"] == ""
    assert steps["6b_image_only_reads_empty"]["paste"] == ""
    assert report["environment"]["backend"] == "macos"
    for floor in ("macos_product", "macos_build", "os_release", "machine", "python"):
        assert report["environment"][floor]
