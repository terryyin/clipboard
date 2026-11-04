"""Optional macOS native wait probe (skipped unless enabled): wait_for_kind and
wait_for_text_change.

Default pytest stays green without a desktop. Enable with (replaces the live
clipboard):

  CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked \\
    pytest tests/test_wait_native_macos.py -v -rP

The probe's JSON report is printed (``-rP`` shows it on success). An evidence
limit (locked screen, no console session) fails here; it never skips on
darwin.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_macos_native_wait.py"
STEPS = [
    "1_wait_for_text_returns_after_independent_pbcopy",
    "2_wait_for_html_with_nothing_copied_returns_none_at_timeout",
    "3_wait_for_text_change_returns_independent_new_text",
    "4_wait_for_text_change_ignores_clear_then_identical_recopy",
]

pytestmark = [
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS pasteboard probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native pasteboard probe",
    ),
]


def test_macos_wait_independent_producer_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
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
    assert report["environment"]["os"] == "Darwin"
    for floor in ("macos_product", "macos_build", "machine"):
        assert report["floors"][floor], floor
