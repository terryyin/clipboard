"""Optional macOS native copy_html dual-offer probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable with:

  CLIPBOARD_NATIVE_PROBE=1 ./scripts/dev uv run --locked \\
    pytest tests/test_copy_html_native_macos.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_macos_native_copy_html.py"

pytestmark = [
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS pasteboard probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native pasteboard probe",
    ),
]


def test_macos_copy_html_independent_dual_consumer_probe():
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
    assert report["writer_exited_before_consume"] is True
    assert report["observed"]["html_markers_ok"] is True
    assert report["observed"]["text_exact_ok"] is True
    assert report["environment"]["os"] == "Darwin"
    assert report["floors"]["macos_product"]
    assert report["floors"]["macos_build"]
