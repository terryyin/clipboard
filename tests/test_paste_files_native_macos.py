"""Optional macOS native file-list pasteboard probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable with:

  CLIPBOARD_NATIVE_PROBE=1 ./scripts/dev uv run --locked \\
    pytest tests/test_paste_files_native_macos.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_macos_native_paste_files.py"

pytestmark = [
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS pasteboard probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native pasteboard probe",
    ),
]


def test_macos_independent_filenames_paste_files_probe():
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
    assert report["preservative"] is True
    assert report["independent_still_sees_offer"] is True
    assert report["files_unchanged"] is True
    assert report["set_files_clipboard_reader"] is None
    assert report["environment"]["os"] == "Darwin"
    assert report["floors"]["macos_product"]
    assert report["floors"]["macos_build"]
    expected = report["expected_paths"]
    assert len(expected) == 2
    assert any(" " in path for path in expected)
    assert report["first_paste"] == expected
