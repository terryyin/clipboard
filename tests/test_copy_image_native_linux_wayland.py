"""Optional Linux Wayland + wl-copy native write probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable under Sway with:

  CLIPBOARD_NATIVE_PROBE=1 WAYLAND_DISPLAY=wayland-1 \\
    nix develop -c uv run --locked --extra images \\
    pytest tests/test_copy_image_native_linux_wayland.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_wayland_native_copy_image.py"

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux Wayland + wl-copy probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Wayland write probe",
    ),
]


def test_linux_wayland_independent_consumer_copy_image_probe():
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
    assert report["opaque"]["ok"] is True
    assert report["opaque"]["writer_exited_before_consume"] is True
    assert report["opaque"]["not_paste_image_alone"] is True
    assert report["opaque"]["consumer_api"] == "wl-paste -t image/png"
    assert report["alpha"]["ok"] is True
    assert "alpha_preserved" in report["alpha"]
    assert report["alpha"]["alpha_note"]
    assert report["environment"]["os"] == "Linux"
    assert report["environment"]["pillow_version"]
    assert report["environment"]["helper"] == "wl-copy"
    assert report["environment"]["compositor"] == "Sway"
    assert report["environment"]["wayland_display"]
    assert report["commitments"]["compositor_scope"] == "Sway"
