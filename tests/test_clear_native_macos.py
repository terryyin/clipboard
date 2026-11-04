"""Optional macOS native clear() probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable with (replaces the live
clipboard):

  CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked --extra images \\
    pytest tests/test_clear_native_macos.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_macos_native_clear.py"

pytestmark = [
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS pasteboard probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native pasteboard probe",
    ),
]

CASES = [
    "html_and_text",
    "png_only",
    "clear_twice_on_cleared",
    "copy_empty_vs_clear",
    "file_url",
    "unknown_custom_type",
]


def test_macos_clear_independent_producer_and_consumer_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["environment"]["os"] == "Darwin"
    assert report["floors"]["macos_product"]
    assert report["floors"]["macos_build"]
    assert list(report["cases"]) == sorted(CASES)
    assert [case["ok"] for case in report["cases"].values()] == [True] * len(CASES)
