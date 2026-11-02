"""Optional macOS native pasteboard probe (skipped unless explicitly enabled).

Default pytest stays green without a desktop. Enable with:

  CLIPBOARD_NATIVE_PROBE=1 nix develop -c uv run --locked --extra images \\
    pytest tests/test_paste_image_native_macos.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_macos_native_paste_image.py"

pytestmark = [
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS pasteboard probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native pasteboard probe",
    ),
]


def test_macos_independent_png_paste_image_probe():
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
    assert report["opaque"]["ok"] is True
    assert report["opaque"]["preservative"] is True
    assert report["opaque"]["set_image_grabclipboard"] is None
    assert report["alpha"]["ok"] is True
    assert report["environment"]["os"] == "Darwin"
    assert report["environment"]["pillow_version"]
