"""Optional Linux Wayland + wl-clipboard native clear probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable on a fresh headless Sway
(see the ``native-linux-wayland-clear`` CI job) with:

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked --extra images \\
    pytest tests/test_clear_native_linux_wayland.py -v -rP

The probe must run before anything is copied in that Sway session: its first
step reads the fresh, nothing-copied selection. Later steps clear with the raw
``wl-copy --clear`` (early probe) and then with ``clipboard.clear()`` in child
processes against independent producers and a ``copy_image`` owner. Its JSON
report is printed (``-rP`` shows it on success). An evidence limit fails here.
Results are scoped to Sway.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_wayland_native_clear.py"
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
        reason="Linux Wayland + wl-clipboard probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Wayland clear probe",
    ),
    pytest.mark.skipif(
        not os.environ.get("WAYLAND_DISPLAY")
        or shutil.which("wl-copy") is None
        or shutil.which("wl-paste") is None,
        reason="requires a Linux Wayland session with wl-clipboard on PATH",
    ),
]


def test_linux_wayland_native_clear_probe():
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
    assert report["compositor_generalization"] is False
    steps = {step["step"]: step for step in report["steps"]}
    fresh = steps["1_fresh_nothing_copied_reads_empty"]
    assert fresh["wl_paste_list"]["returncode"] != 0
    assert fresh["classified_nothing_copied"] is True
    assert fresh["reads"] == EMPTY_READS
    raw = steps["2_early_raw_wl_copy_clear_ends_html_owner"]
    assert raw["raw_clear"]["returncode"] == 0
    assert raw["classified_nothing_copied"] is True
    assert raw["owner"]["exit_code"] is not None
    for name in (
        "3_html_producer_then_child_clear_reads_empty",
        "4_text_producer_then_child_clear_reads_empty",
    ):
        assert steps[name]["offered_before"]["offered"] is True
        assert steps[name]["child_clear"]["outcome"] == {"raised": None}
        assert steps[name]["classified_nothing_copied"] is True
        assert steps[name]["reads"] == EMPTY_READS
    image = steps["5_copy_image_owner_ends_after_child_clear"]
    assert image["library_wl_copy_owner_pids"]
    assert image["owner_exit"]["exited"] is True
    assert image["reads"]["paste_image"] == {"value": None}
    twice = steps["6_clear_twice_on_cleared_succeeds"]
    assert twice["first"]["outcome"] == twice["second"]["outcome"] == {"raised": None}
    missing = steps["7_path_without_wl_copy_names_wl_clipboard"]
    assert missing["wl_copy_on_child_path"] is None
    assert missing["child_clear"]["outcome"]["raised"] == "ClipboardContentError"
    assert "wl-clipboard" in missing["child_clear"]["outcome"]["message"]
    env = report["environment"]
    assert env["compositor_version"], "sway version"
    assert env["wl_clipboard_version"], "wl-clipboard version"
