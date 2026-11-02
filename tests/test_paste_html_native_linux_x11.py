"""Optional Linux X11 + xclip native paste_html probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable under Xvfb with:

  CLIPBOARD_NATIVE_PROBE=1 xvfb-run -a nix develop -c uv run --locked \\
    pytest tests/test_paste_html_native_linux_x11.py -v

The independent producer is ``xclip -t text/html -i``; the probe overwrites
the X11 CLIPBOARD and leaves it unowned.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_x11_native_paste_html.py"
FRAGMENT = (
    '<a href="https://example.com/caf%C3%A9" style="color:#c00">'
    "<b>café → naïve 日本</b></a>"
)

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux X11 + xclip probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native X11 read probe",
    ),
]


def test_linux_x11_independent_producer_paste_html_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    html = report["html"]
    assert report["ok"] is True
    assert report["verified"] is True
    assert html["paste_html"] == FRAGMENT
    assert html["independent_consumer_same_bytes"] is True
    assert html["targets_before"] == html["targets_after"]
    assert "text/html" in html["targets_before"]
    assert {case["case"]: case["paste_html"] for case in report["absent"]} == {
        "text_only": None,
        "image_only": None,
        "unowned_empty": None,
    }
    assert all("error" not in case for case in report["absent"])
    for failure in report["failures"].values():
        assert failure["content_error"] is True, failure
        assert failure["names_xclip"] is True, failure
    env = report["environment"]
    assert env["os"] == "Linux"
    assert env["helper"] == "xclip"
    assert env["xclip_version"]
    assert env["display"]
    assert env["python"]
