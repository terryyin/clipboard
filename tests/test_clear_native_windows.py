"""Optional Windows desktop native clear probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable on a Windows desktop
session (see the ``native-windows-clear`` CI job) with (replaces the live
clipboard):

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked --extra images \\
    pytest tests/test_clear_native_windows.py -v -rP

The probe's JSON report is printed (``-rP`` shows it on success). An evidence
limit fails here; it never skips on ``win32``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_windows_native_clear.py"
EMPTY_READS = {
    "inspect": {"value": {"kinds": [], "formats": []}},
    "paste": {"value": ""},
    "paste_html": {"value": None},
    "paste_files": {"value": None},
    "paste_image": {"value": None},
}
STEPS = [
    "1_early_raw_empty_clipboard_leaves_no_formats",
    "2_html_and_text_producer_then_child_clear_reads_empty",
    "3_image_producer_then_child_clear_reads_empty",
    "4_file_list_producer_then_child_clear_reads_empty",
    "5_custom_format_producer_then_child_clear_reads_empty",
    "6_clear_twice_on_cleared_succeeds",
    "7_holder_past_bound_raises_and_prior_formats_remain",
    "8_holder_released_within_bound_then_clear_succeeds",
]

pytestmark = [
    pytest.mark.skipif(sys.platform != "win32", reason="Windows desktop probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Windows clear probe",
    ),
]


def test_windows_native_clear_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["evidence_limit"] is False
    assert report["ok"] is True
    assert report["failed_steps"] == []
    steps = {step["step"]: step for step in report["steps"]}
    assert [step["step"] for step in report["steps"]] == STEPS

    raw = steps[STEPS[0]]
    assert {"HTML Format", 13} <= set(raw["consumer_before"]["formats"])
    assert raw["raw_empty"]["report"]["emptied"] is True
    assert raw["raw_empty"]["report"]["closed"] is True
    assert raw["consumer_after"]["formats"] == []

    for name, offered in (
        (STEPS[1], {"HTML Format", 13}),
        (STEPS[3], {15}),
        (STEPS[4], {"ClipboardProbe.Custom"}),
    ):
        assert offered <= set(steps[name]["consumer_before"]["formats"]), name
    assert {8, 17, 2} & set(steps[STEPS[2]]["consumer_before"]["formats"])
    for name in STEPS[1:5]:
        produced = steps[name]
        assert produced["producer"]["returncode"] == 0, name
        assert produced["child_clear"]["outcome"] == {"raised": None}, name
        assert produced["consumer_after"]["formats"] == [], name
        assert produced["reads"] == EMPTY_READS, name
    assert steps[STEPS[3]]["file_existed"] is True

    twice = steps[STEPS[5]]
    assert twice["first"]["outcome"] == twice["second"]["outcome"] == {"raised": None}
    assert twice["consumer_after"]["formats"] == []
    assert twice["reads"] == EMPTY_READS

    held = steps[STEPS[6]]
    assert held["holder_ready"]["holds_at_ready"] is True
    assert held["child_clear"]["returncode"] == 3
    outcome = held["child_clear"]["outcome"]
    assert outcome["raised"] == "ClipboardContentError"
    assert "held by another process" in outcome["message"]
    assert "clearing the clipboard" in outcome["message"]
    elapsed = held["child_clear"]["elapsed_s"]
    assert held["library_bound_s"] <= elapsed < held["holder_seconds"]
    assert held["holder_released"]["holds_before_release"] is True
    assert {"HTML Format", 13} <= set(held["consumer_after_release"]["formats"])

    brief = steps[STEPS[7]]
    assert brief["holder_ready"]["holds_at_ready"] is True
    assert brief["child_clear"]["outcome"] == {"raised": None}
    assert brief["child_clear"]["elapsed_s"] < brief["library_bound_s"]
    assert brief["holder_released"]["holds_before_release"] is True
    assert brief["consumer_after"]["formats"] == []

    env = report["environment"]
    assert env["os"] == "Windows"
    for floor in ("windows_version", "windows_build", "powershell", "python"):
        assert env[floor], floor
    if env["github_actions"]:
        assert env["runner_image_os"] and env["runner_image_version"]
