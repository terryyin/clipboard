"""Optional Linux X11 native copy_files probe: xclip consumer + Thunar Paste.

Skipped unless on Linux with an X11 ``DISPLAY``, ``xclip`` on PATH,
``CLIPBOARD_NATIVE_PROBE=1`` and ``CLIPBOARD_FILE_MANAGER_ISOLATED=1`` (the
probe replaces CLIPBOARD and quits Thunar, so it needs its own D-Bus/X11
session; see the ``native-linux-x11-copy-files`` CI job). A probe that cannot
verify exits non-zero and fails this wrapper. The report checks also run
desktop-free against a synthetic report.
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
PROBE = ROOT / "scripts" / "probe_linux_x11_native_copy_files.py"
NAMES = ["report final.pdf", "données é.csv"]


@pytest.mark.skipif(
    not sys.platform.startswith("linux")
    or not os.environ.get("DISPLAY")
    or shutil.which("xclip") is None,
    reason="needs a Linux X11 DISPLAY with xclip on PATH",
)
@pytest.mark.skipif(
    os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1"
    or os.environ.get("CLIPBOARD_FILE_MANAGER_ISOLATED") != "1",
    reason="set native and isolated-file-manager gates in an isolated X11 session",
)
def test_x11_copy_files_independent_consumer_and_thunar_paste_probe():
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
    assert_x11_copy_files_report(json.loads(result.stdout))


def assert_x11_copy_files_report(report: dict) -> None:
    assert report["ok"] is True
    assert report["failed_observations"] == []
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
    assert "apt-get install xclip" in report["missing_helper"]["writer"]["stderr"]
    assert report["thunar_paste"]["copies_match"] is True
    assert report["sources_before"] == report["sources_after"]
    assert report["floors"]["thunar"] and report["floors"]["xclip"]
    relative = report["relative_directory_duplicate"]
    assert relative["relative_args"] == [
        "report final.pdf",
        "a dir",
        "report final.pdf",
    ]
    assert [PurePosixPath(p).name for p in relative["expected_paths"]] == [
        "report final.pdf",
        "a dir",
        "report final.pdf",
    ]
    assert relative["expected_paths"][0] == relative["expected_paths"][2]
    assert relative["independent"]["body"] == relative["expected_body"]
    assert relative["paste_files"]["value"] == relative["expected_paths"]
    assert relative["writer"]["exited"] is True
    assert relative["writer"]["returncode"] == 0


def _synthetic_report() -> dict:
    paths = [f"/tmp/p/sources/{name}" for name in NAMES]
    body = "".join(f"file://{p}\r\n" for p in paths)
    relative_paths = [
        "/tmp/p/sources/report final.pdf",
        "/tmp/p/sources/a dir",
        "/tmp/p/sources/report final.pdf",
    ]
    relative_body = "".join(f"file://{p}\r\n" for p in relative_paths)
    recheck = {"t_s": 0.0, "ok": True, "targets_list_uri_list": True, "error": None}
    return {
        "ok": True,
        "failed_observations": [],
        "observations": {
            "independent_body_equal": True,
            "relative_directory_duplicate_writer_exited_ok": True,
            "relative_directory_duplicate_independent_body_equal": True,
            "relative_directory_duplicate_targets_list_uri_list": True,
            "relative_directory_duplicate_paste_files_agrees": True,
        },
        "expected_paths": paths,
        "expected_body": body,
        "independent": {"body": body},
        "writer": {"exited": True, "returncode": 0},
        "rechecks_after_exit": [recheck] * 3,
        "missing_helper": {"writer": {"stderr": "sudo apt-get install xclip"}},
        "thunar_paste": {"copies_match": True},
        "relative_directory_duplicate": {
            "relative_args": [
                "report final.pdf",
                "a dir",
                "report final.pdf",
            ],
            "expected_paths": relative_paths,
            "expected_body": relative_body,
            "independent": {"body": relative_body},
            "paste_files": {"value": relative_paths},
            "writer": {"exited": True, "returncode": 0},
        },
        "sources_before": {"a": "1"},
        "sources_after": {"a": "1"},
        "floors": {"thunar": "thunar 4.18.8", "xclip": "xclip version 0.13"},
    }


def test_report_assertions_accept_a_complete_report():
    assert_x11_copy_files_report(_synthetic_report())


@pytest.mark.parametrize(
    "damage",
    [
        lambda r: r["observations"].update(thunar_paste_copies_match=False),
        lambda r: r["independent"].update(body="file:///other\r\n"),
        lambda r: r["rechecks_after_exit"].__setitem__(2, {"t_s": 10, "ok": False}),
        lambda r: r["missing_helper"]["writer"].update(stderr="error"),
        lambda r: r["thunar_paste"].update(copies_match=False),
        lambda r: r["sources_after"].update(a="2"),
        lambda r: r["relative_directory_duplicate"]["independent"].update(
            body="file:///other\r\n"
        ),
        lambda r: r["relative_directory_duplicate"]["paste_files"].update(
            value=["/tmp/p/sources/report final.pdf"]
        ),
    ],
)
def test_report_assertions_reject_a_failed_observation(damage):
    report = copy.deepcopy(_synthetic_report())
    damage(report)
    with pytest.raises(AssertionError):
        assert_x11_copy_files_report(report)
