"""Optional macOS native inspect() probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable with:

  CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked \\
    pytest tests/test_inspect_native_macos.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_macos_native_inspect.py"

pytestmark = [
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS pasteboard probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native pasteboard probe",
    ),
]


def test_macos_inspect_independent_producer_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    html_text = report["html_and_text"]
    assert html_text["ok"] is True
    assert html_text["has_html_kind"] is True
    assert html_text["has_text_kind"] is True
    assert html_text["has_html_format"] is True
    assert html_text["has_text_format"] is True
    assert html_text["non_mutation"] is True
    assert report["environment"]["os"] == "Darwin"
    assert report["floors"]["macos_product"]
    assert report["floors"]["macos_build"]
    # Image-only is optional when feasible; when present it must also pass.
    image_only = report.get("image_only")
    if image_only is not None:
        assert image_only["ok"] is True
        assert image_only["has_image_kind"] is True
        assert image_only["no_text_or_html_kind"] is True
        assert image_only["non_mutation"] is True
