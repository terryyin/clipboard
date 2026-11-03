"""Optional Windows native copy_files CF_HDROP + Explorer shell probe.

Skipped unless on win32 with ``CLIPBOARD_NATIVE_PROBE=1`` (see the
``native-windows-copy-files`` CI job):

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked \\
    pytest tests/test_copy_files_native_windows.py -v -rP

The probe overwrites the Windows clipboard. A probe that cannot verify exits
non-zero and fails this wrapper; it never skips. The report checks below also
run desktop-free against synthetic reports.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_windows_native_copy_files.py"
NAMES = ["report final.pdf", "données é.csv"]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows desktop probe only")
@pytest.mark.skipif(
    os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
    reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Windows copy_files probe",
)
def test_windows_copy_files_independent_consumer_and_shell_paste_probe():
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
    assert_windows_copy_files_report(json.loads(result.stdout))


def assert_windows_copy_files_report(report: dict) -> None:
    assert report["ok"] is True
    assert report["failed_observations"] == []
    assert all(report["observations"].values()), report["observations"]
    expected = report["expected_paths"]
    assert [PureWindowsPath(p).name for p in expected] == NAMES
    writer = report["writer"]
    assert writer["exited"] is True and writer["returncode"] == 0
    seen = report["independent"]
    assert seen["drop_list"] == expected
    assert seen["get_clipboard_file_drop_list"] == expected
    assert seen["drop_effect"] == 1
    assert seen["drop_effect_bytes"] == "01-00-00-00"
    rechecks = report["rechecks_after_exit"]
    assert all(r["ok"] for r in rechecks)
    assert rechecks[-1]["t_s"] >= 10
    assert report["sequence_before"] != rechecks[0]["sequence_number"]
    assert report["paste_files"]["value"] == expected  # consistency only
    paste = report["shell_paste"]
    assert paste["copies_match"] is True
    assert [c["name"] for c in paste["copies"]] == NAMES
    assert all(c["exists"] and c["bytes_equal"] for c in paste["copies"])
    assert sorted(paste["dest_listing"]) == sorted(NAMES)
    assert report["sources_before"] == report["sources_after"]
    floors = report["floors"]
    assert floors["os"] == "Windows"
    for key in ("windows_version", "windows_build", "powershell", "python", "machine"):
        assert floors[key], key
    relative = report["relative_directory_duplicate"]
    assert relative["relative_args"] == [
        "report final.pdf",
        "a dir",
        "report final.pdf",
    ]
    assert [PureWindowsPath(p).name for p in relative["expected_paths"]] == [
        "report final.pdf",
        "a dir",
        "report final.pdf",
    ]
    assert relative["expected_paths"][0] == relative["expected_paths"][2]
    assert relative["independent"]["drop_list"] == relative["expected_paths"]
    assert relative["paste_files"]["value"] == relative["expected_paths"]
    assert relative["writer"]["exited"] is True
    assert relative["writer"]["returncode"] == 0


def _passing_report() -> dict:
    expected = [rf"C:\t\sources\{name}" for name in NAMES]
    relative_paths = [
        r"C:\t\sources\report final.pdf",
        r"C:\t\sources\a dir",
        r"C:\t\sources\report final.pdf",
    ]
    fingerprint = {n: {"size": 1, "mtime_ns": 2, "sha256": "x"} for n in NAMES}
    return {
        "ok": True,
        "failed_observations": [],
        "observations": {
            "shell_paste_copies_match": True,
            "relative_directory_duplicate_writer_exited_ok": True,
            "relative_directory_duplicate_independent_paths_equal": True,
            "relative_directory_duplicate_paste_files_agrees": True,
        },
        "expected_paths": expected,
        "writer": {"exited": True, "returncode": 0},
        "independent": {
            "drop_list": expected,
            "get_clipboard_file_drop_list": expected,
            "drop_effect": 1,
            "drop_effect_bytes": "01-00-00-00",
        },
        "sequence_before": 7,
        "rechecks_after_exit": [
            {"t_s": t, "ok": True, "sequence_number": 9} for t in (0, 5, 10)
        ],
        "paste_files": {"value": expected},
        "shell_paste": {
            "copies_match": True,
            "copies": [{"name": n, "exists": True, "bytes_equal": True} for n in NAMES],
            "dest_listing": NAMES,
        },
        "relative_directory_duplicate": {
            "relative_args": [
                "report final.pdf",
                "a dir",
                "report final.pdf",
            ],
            "expected_paths": relative_paths,
            "independent": {"drop_list": relative_paths},
            "paste_files": {"value": relative_paths},
            "writer": {"exited": True, "returncode": 0},
        },
        "sources_before": fingerprint,
        "sources_after": copy.deepcopy(fingerprint),
        "floors": {
            "os": "Windows",
            "windows_version": "10.0.26100",
            "windows_build": 26100,
            "powershell": "5.1.26100.1",
            "python": "3.13.5",
            "machine": "AMD64",
        },
    }


def test_report_check_accepts_a_complete_report():
    assert_windows_copy_files_report(_passing_report())


@pytest.mark.parametrize(
    "spoil",
    [
        lambda r: r["independent"].update(drop_effect=2),
        lambda r: r["independent"].update(drop_list=r["expected_paths"][::-1]),
        lambda r: r["shell_paste"].update(copies_match=False),
        lambda r: r["shell_paste"].update(dest_listing=[]),
        lambda r: r["rechecks_after_exit"][-1].update(ok=False),
        lambda r: r["floors"].update(windows_build=None),
        lambda r: r["relative_directory_duplicate"]["independent"].update(
            drop_list=r["relative_directory_duplicate"]["expected_paths"][:1]
        ),
        lambda r: r["relative_directory_duplicate"]["paste_files"].update(
            value=[r"C:\t\sources\report final.pdf"]
        ),
    ],
)
def test_report_check_rejects_a_missing_observation(spoil):
    report = _passing_report()
    spoil(report)
    with pytest.raises(AssertionError):
        assert_windows_copy_files_report(report)


def test_unverified_probe_exit_fails_the_wrapper(monkeypatch):
    """Desktop-free: an exit-2 evidence limit must fail, never skip."""
    limit = json.dumps({"ok": False, "evidence_limit": True, "reason": "synthetic"})
    fake = subprocess.CompletedProcess([sys.executable], 2, limit, "")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake)
    with pytest.raises(AssertionError):
        test_windows_copy_files_independent_consumer_and_shell_paste_probe()
