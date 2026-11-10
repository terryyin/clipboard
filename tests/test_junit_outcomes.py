"""The CI converter keeps each case's outcome, path and optional measurement."""

import subprocess
import sys
from pathlib import Path

import pytest

CONVERTER = Path(__file__).resolve().parents[1] / "scripts" / "junit-outcomes.py"


def convert(tmp_path, cases, *, with_times=True):
    report = tmp_path / "junit.xml"
    report.write_text(f"<testsuite>{cases}</testsuite>", encoding="utf-8")
    times = tmp_path / "times.txt"
    command = [sys.executable, str(CONVERTER), str(report)]
    if with_times:
        command.extend(["--times", str(times)])
    return subprocess.run(command, text=True, capture_output=True), times


def test_case_outcomes_and_recorded_seconds_keep_repeated_paths(tmp_path):
    result, times = convert(
        tmp_path,
        '<testcase file="tests/test_a.py" time="0.125" />'
        '<testcase file="tests/test_a.py" time="0.250"><failure /></testcase>'
        '<testcase file="tests/test_b.py" time="0"><skipped /></testcase>'
        '<testcase file="tests/test_b.py" />'
        '<testcase file="tests/test_c.py" time="1.5"><error /></testcase>',
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "passed\ttests/test_a.py",
        "failed\ttests/test_a.py",
        "other\ttests/test_b.py",
        "passed\ttests/test_b.py",
        "failed\ttests/test_c.py",
    ]
    assert times.read_text(encoding="utf-8").splitlines() == [
        "0.125\ttests/test_a.py",
        "0.25\ttests/test_a.py",
        "0.0\ttests/test_b.py",
        "1.5\ttests/test_c.py",
    ]


def test_outcomes_only_cli_remains_supported(tmp_path):
    result, times = convert(
        tmp_path, '<testcase file="tests/test_a.py" />', with_times=False
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "passed\ttests/test_a.py\n"
    assert not times.exists()


@pytest.mark.parametrize("time", ["", "invalid", "-1", "NaN", "inf", "1e308"])
def test_invalid_timing_cannot_publish_complete_evidence(tmp_path, time):
    result, times = convert(
        tmp_path, f'<testcase file="tests/test_a.py" time="{time}" />'
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert not times.exists()


@pytest.mark.parametrize(
    "attribute",
    [
        "",
        'file=""',
        'file="/tmp/test_a.py"',
        'file="C:/temp/test_a.py"',
        'file="tests/../test_a.py"',
        'file="tests//test_a.py"',
        'file="tests/test_a.py&#9;extra"',
        'file="tests\\test_a.py"',
    ],
)
def test_unusable_case_file_cannot_publish_evidence(tmp_path, attribute):
    result, times = convert(tmp_path, f'<testcase {attribute} time="0.125" />')
    assert result.returncode != 0
    assert result.stdout == ""
    assert not times.exists()


def test_bad_later_case_does_not_leave_partial_success(tmp_path):
    result, times = convert(
        tmp_path,
        '<testcase file="tests/test_a.py" time="0.125" />'
        '<testcase name="global collection error"><error /></testcase>',
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert not times.exists()


def test_all_untimed_cases_write_no_measurements(tmp_path):
    result, times = convert(tmp_path, '<testcase file="tests/test_a.py" />')
    assert result.returncode == 0, result.stderr
    assert times.read_text(encoding="utf-8") == ""


def test_missing_report_fails_without_creating_timing(tmp_path):
    times = tmp_path / "times.txt"
    result = subprocess.run(
        [
            sys.executable,
            str(CONVERTER),
            str(tmp_path / "absent.xml"),
            "--times",
            str(times),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert not times.exists()
