"""Optional macOS native paste_html probe (skipped unless explicitly enabled).

Default pytest stays green without a desktop. Enable with:

  CLIPBOARD_NATIVE_PROBE=1 ./scripts/dev uv run --locked \\
    pytest tests/test_paste_html_native_macos.py -v

The probe drives Google Chrome (or a recorded JXA fallback writer) and
overwrites the clipboard.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_macos_native_paste_html.py"

pytestmark = [
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS pasteboard probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native pasteboard probe",
    ),
]


def test_macos_independent_producer_paste_html_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    html = report["html"]
    assert report["ok"] is True
    assert html["producer"]["kind"] in {"browser", "fallback"}
    assert html["fragment_markers_ok"] is True
    assert html["context_excluded"] is True
    assert html["independent_consumer_same_offer"] is True
    assert html["change_count_before"] == html["change_count_after"]
    assert {case["case"]: case["paste_html"] for case in report["absent"]} == {
        "text_only": None,
        "image_only": None,
        "file_list": None,
    }
    assert report["environment"]["os"] == "Darwin"
    assert report["environment"]["macos_product"]
    assert report["environment"]["macos_build"]
