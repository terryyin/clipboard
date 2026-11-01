"""Exercise the release guard through its command-line interface."""

import subprocess
import sys

import pytest

import clipboard


@pytest.mark.parametrize("prefix", ["", "v"])
def test_release_accepts_matching_version(prefix):
    result = subprocess.run(
        [sys.executable, "scripts/check_release.py", prefix + clipboard.VERSION],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("tag", "message"),
    [
        ("v999.0.0", "does not match"),
        ("v01.2.3", "must be X.Y.Z"),
        ("v0.0.2rc1", "must be X.Y.Z"),
        ("v0.0", "must be X.Y.Z"),
        ("web-1.0.0", "must be X.Y.Z"),
    ],
)
def test_release_rejects_invalid_tag(tag, message):
    result = subprocess.run(
        [sys.executable, "scripts/check_release.py", tag],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert message in result.stderr
