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

_EMPTY_READERS = {
    "inspect_kinds": [],
    "inspect_formats": [],
    "paste_html_is_none": True,
    "paste": "",
    "paste_files_is_none": True,
    "paste_image_is_none": True,
}


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
    cases = report["cases"]

    html_text = cases["html_and_text"]
    assert {"public.html", "public.utf8-plain-text"} <= set(html_text["types_before"])
    assert html_text["child_clear"]["exited"] is True
    assert html_text["types_after"] == []
    assert html_text["pbpaste_after"] == ""
    assert html_text["readers_after"] == _EMPTY_READERS

    png = cases["png_only"]
    assert "public.png" in png["types_before"]
    assert png["types_after"] == []
    assert png["pbpaste_after"] == ""
    assert png["readers_after"] == _EMPTY_READERS

    twice = cases["clear_twice_on_cleared"]
    assert twice["child_clear"]["exited"] is True
    assert twice["types_after"] == []

    contrast = cases["copy_empty_vs_clear"]
    assert "public.utf8-plain-text" in contrast["types_after_copy_empty"]
    assert contrast["types_after_clear"] == []

    files = cases["file_url"]
    assert "public.file-url" in files["types_before"]
    assert files["file_existed"] is True
    assert files["child_clear"]["exited"] is True
    assert files["types_after"] == []
    assert files["readers_after"]["paste_files_is_none"] is True
    assert files["readers_after"] == _EMPTY_READERS

    custom = cases["unknown_custom_type"]
    assert "com.example.clipboard-probe" in custom["types_before"]
    assert custom["child_clear"]["exited"] is True
    assert custom["types_after"] == []
    assert custom["readers_after"] == _EMPTY_READERS
