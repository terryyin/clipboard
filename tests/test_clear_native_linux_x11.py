"""Optional Linux X11 + xclip native clear probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable on a fresh Xvfb (see the
``native-linux-x11-clear`` CI job) with:

  CLIPBOARD_NATIVE_PROBE=1 xvfb-run -a uv run --locked --extra images \\
    pytest tests/test_clear_native_linux_x11.py -v -rP

The probe must run before anything owns CLIPBOARD on that X server: its first
step reads the fresh, unowned clipboard. Its JSON report is printed (``-rP``
shows it on success). An evidence limit fails here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_x11_native_clear.py"
EMPTY_READS = {
    "inspect": {"value": {"kinds": [], "formats": []}},
    "paste": {"value": ""},
    "paste_html": {"value": None},
    "paste_files": {"value": None},
    "paste_image": {"value": None},
}

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux X11 + xclip probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native X11 clear probe",
    ),
    pytest.mark.skipif(
        not os.environ.get("DISPLAY"),
        reason="requires a Linux X11 session (DISPLAY)",
    ),
]


def test_linux_x11_native_clear_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    assert report["failed_steps"] == []
    steps = {step["step"]: step for step in report["steps"]}
    fresh = steps["1_fresh_unowned_clipboard_reads_empty"]
    assert fresh["xclip_targets"]["returncode"] != 0
    assert fresh["classified_no_owner"] is True
    assert fresh["reads"] == EMPTY_READS

    raw = steps["2_early_raw_xsetselectionowner_none_ends_html_owner"]
    assert raw["offered_before"]["offered"] is True
    assert raw["raw_relinquish"]["returncode"] == 0
    libx11 = raw["raw_relinquish"]["libx11"]
    assert libx11["display_opened"] is True
    assert libx11["owner_before"] != 0
    assert libx11["owner_after"] == 0
    assert raw["classified_no_owner"] is True
    assert raw["owner"]["exit_code"] is not None

    html = steps["3_html_producer_then_child_clear_reads_empty"]
    assert html["producer"]["returncode"] == 0
    assert html["offered_before"]["offered"] is True
    assert html["child_clear"]["outcome"] == {"raised": None}
    assert html["producer_xclip_owner_pids"]
    assert html["owner_exit"]["exited"] is True
    assert html["classified_no_owner"] is True
    assert html["reads"] == EMPTY_READS

    image = steps["4_copy_image_owner_ends_after_child_clear"]
    assert image["copy_image_child"]["returncode"] == 0
    assert image["offered_before"]["offered"] is True
    assert image["library_xclip_owner_pids"]
    assert image["child_clear"]["outcome"] == {"raised": None}
    assert image["owner_exit"]["exited"] is True
    assert image["owner_exit"]["waited_s"] <= image["owner_exit"]["bound_s"]
    assert image["classified_no_owner"] is True
    assert image["reads"]["paste_image"] == {"value": None}
    assert image["reads"] == EMPTY_READS

    twice = steps["5_clear_twice_on_cleared_succeeds"]
    assert twice["first"]["outcome"] == {"raised": None}
    assert twice["second"]["outcome"] == {"raised": None}
    assert twice["classified_no_owner"] is True
    assert twice["reads"] == EMPTY_READS

    bad = steps["6_unopenable_display_raises_naming_display"]
    assert bad["child_clear"]["returncode"] == 3
    outcome = bad["child_clear"]["outcome"]
    assert outcome["raised"] == "ClipboardContentError"
    assert f"DISPLAY={bad['child_display']!r}" in outcome["message"]
    assert bad["child_clear"]["elapsed_s"] < bad["library_bound_s"]

    for name, mime_type in (
        ("7_file_list_producer_then_child_clear_reads_empty", "text/uri-list"),
        (
            "8_unknown_type_producer_then_child_clear_reads_empty",
            "application/x-clipboard-probe",
        ),
    ):
        produced = steps[name]
        assert produced["producer"]["returncode"] == 0
        assert mime_type in produced["producer"]["cmd"]
        assert produced["offered_before"]["offered"] is True
        assert produced["producer_xclip_owner_pids"]
        assert produced["child_clear"]["outcome"] == {"raised": None}
        assert produced["owner_exit"]["exited"] is True
        assert produced["classified_no_owner"] is True
        assert produced["reads"] == EMPTY_READS
    files = steps["7_file_list_producer_then_child_clear_reads_empty"]
    assert files["file_uri"].startswith("file:///")
    assert files["file_existed"] is True
    assert files["reads"]["paste_files"] == {"value": None}

    assert [step["step"] for step in report["steps"]] == [
        "1_fresh_unowned_clipboard_reads_empty",
        "2_early_raw_xsetselectionowner_none_ends_html_owner",
        "3_html_producer_then_child_clear_reads_empty",
        "4_copy_image_owner_ends_after_child_clear",
        "5_clear_twice_on_cleared_succeeds",
        "6_unopenable_display_raises_naming_display",
        "7_file_list_producer_then_child_clear_reads_empty",
        "8_unknown_type_producer_then_child_clear_reads_empty",
    ]
    env = report["environment"]
    assert env["xclip_version"], "xclip version"
    assert env["xvfb_version"], "Xvfb version"
