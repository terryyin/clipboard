"""Optional Linux Wayland + wl-paste native paste_html probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable inside a Sway session
(see the ``native-linux-wayland-paste-html`` CI job) with:

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked \\
    pytest tests/test_paste_html_native_linux_wayland.py -v

The independent producer is ``wl-copy --type text/html``; the probe
overwrites the Wayland clipboard and leaves it cleared. The result is scoped
to Sway and does not generalize to other compositors.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_wayland_native_paste_html.py"
sys.path.insert(0, str(ROOT / "scripts"))
from native_probe_paste_html import FRAGMENT  # noqa: E402

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux Wayland + wl-paste probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Wayland read probe",
    ),
    pytest.mark.skipif(
        not os.environ.get("WAYLAND_DISPLAY"),
        reason="requires a Linux Wayland session (WAYLAND_DISPLAY)",
    ),
]


def test_linux_wayland_independent_producer_paste_html_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    print(result.stdout)
    report = json.loads(result.stdout)
    html = report["html"]
    assert report["ok"] is True
    assert report["verified"] is True
    assert report["compositor_generalization"] is False
    assert html["paste_html"] == FRAGMENT
    assert html["independent_consumer_same_bytes"] is True
    assert html["types_before"] == html["types_after"]
    assert "text/html" in html["types_before"]
    assert {case["case"]: case["paste_html"] for case in report["absent"]} == {
        "text_only": None,
        "image_only": None,
        "cleared_empty": None,
    }
    assert all("error" not in case for case in report["absent"])
    for failure in report["failures"].values():
        assert failure["content_error"] is True, failure
        assert failure["names_wl_paste"] is True, failure
    env = report["environment"]
    assert env["os"] == "Linux"
    assert env["compositor"] == "Sway"
    assert env["compositor_running"] is True
    assert env["compositor_version"]
    assert env["helper"] == "wl-paste"
    assert env["wl_clipboard_version"]
    assert env["wayland_display"]
    assert env["python"]
