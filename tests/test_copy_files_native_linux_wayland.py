"""Optional Linux Wayland native copy_files probe: wl-paste independent consumer.

Skipped unless on Linux with ``WAYLAND_DISPLAY``, ``wl-copy`` and ``wl-paste``
on PATH and ``CLIPBOARD_NATIVE_PROBE=1`` (the probe replaces the Wayland
selection; see the ``native-linux-wayland-copy-files`` CI job on headless
Sway). A probe that cannot verify exits non-zero and fails this wrapper. The
report checks also run desktop-free against a synthetic report.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_wayland_native_copy_files.py"
NAMES = ["report final.pdf", "données é.csv"]
GATED = {
    "missing_helper_content_error",
    "missing_helper_install_hint",
    "missing_helper_prior_text_survives",
    "writer_exited_ok",
    "independent_body_equal",
    "types_list_uri_list",
    "offer_held_after_exit",
    "paste_files_agrees",
    "sources_unchanged",
}


@pytest.mark.skipif(
    not sys.platform.startswith("linux")
    or not os.environ.get("WAYLAND_DISPLAY")
    or shutil.which("wl-copy") is None
    or shutil.which("wl-paste") is None,
    reason="needs a Linux Wayland session with wl-clipboard on PATH",
)
@pytest.mark.skipif(
    os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
    reason="set CLIPBOARD_NATIVE_PROBE=1 to run the native Wayland copy_files probe",
)
def test_wayland_copy_files_independent_consumer_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    assert result.returncode == 0, result.stderr or result.stdout
    assert_wayland_copy_files_report(json.loads(result.stdout))


def assert_wayland_copy_files_report(report: dict) -> None:
    assert report["ok"] is True
    assert report["failed_observations"] == []
    assert set(report["observations"]) == GATED
    assert all(report["observations"].values()), report["observations"]
    expected = report["expected_paths"]
    assert [PurePosixPath(p).name for p in expected] == NAMES
    assert report["expected_body"].endswith("\r\n")
    assert report["independent"]["body"] == report["expected_body"]
    assert report["writer"]["exited"] is True and report["writer"]["returncode"] == 0
    assert [r["t_s"] >= 0 and r["ok"] for r in report["rechecks_after_exit"]] == [
        True,
        True,
        True,
    ]
    stderr = report["missing_helper"]["writer"]["stderr"]
    assert "apt-get install wl-clipboard" in stderr
    assert report["sources_before"] == report["sources_after"]
    floors = report["floors"]
    assert floors["sway"] and floors["wl_clipboard"] and floors["python"]
    assert floors["distribution"]


def _synthetic_report() -> dict:
    paths = [f"/tmp/p/sources/{name}" for name in NAMES]
    body = "".join(f"file://{p}\r\n" for p in paths)
    recheck = {"t_s": 0.0, "ok": True, "types_list_uri_list": True, "error": None}
    return {
        "ok": True,
        "failed_observations": [],
        "observations": dict.fromkeys(GATED, True),
        "expected_paths": paths,
        "expected_body": body,
        "independent": {"body": body},
        "writer": {"exited": True, "returncode": 0},
        "rechecks_after_exit": [recheck] * 3,
        "missing_helper": {"writer": {"stderr": "sudo apt-get install wl-clipboard"}},
        "sources_before": {"a": "1"},
        "sources_after": {"a": "1"},
        "floors": {
            "distribution": "Ubuntu 24.04.5 LTS",
            "sway": "sway version 1.9",
            "wl_clipboard": "wl-clipboard 2.2.1",
            "python": "3.13.14",
        },
    }


def test_report_assertions_accept_a_complete_report():
    assert_wayland_copy_files_report(_synthetic_report())


@pytest.mark.parametrize(
    "damage",
    [
        lambda r: r["observations"].update(offer_held_after_exit=False),
        lambda r: r["observations"].pop("paste_files_agrees"),
        lambda r: r["independent"].update(body="file:///other\r\n"),
        lambda r: r["rechecks_after_exit"].__setitem__(2, {"t_s": 10, "ok": False}),
        lambda r: r["missing_helper"]["writer"].update(stderr="error"),
        lambda r: r["sources_after"].update(a="2"),
        lambda r: r["floors"].update(sway=None),
    ],
)
def test_report_assertions_reject_a_failed_observation(damage):
    report = copy.deepcopy(_synthetic_report())
    damage(report)
    with pytest.raises(AssertionError):
        assert_wayland_copy_files_report(report)
