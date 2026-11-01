"""Exercise the public API without requiring a desktop clipboard in CI."""

import json
import subprocess
import sys
from importlib.metadata import version

import pytest

import clipboard


@pytest.mark.parametrize("value", ["abc", "", "Hello, 世界 👋", "line 1\nline 2"])
def test_copy_paste_round_trip(value):
    # Let pyperclip initialize its lazy API against an in-memory OS boundary.
    # A subprocess gives each case the same first-import behavior as a consumer.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import json
import sys
import pyperclip

contents = None
def copy(value):
    global contents
    contents = value
def paste():
    return contents
pyperclip.determine_clipboard = lambda: (copy, paste)

import clipboard
clipboard.copy(json.loads(sys.argv[1]))
print(json.dumps(clipboard.paste()))
""",
            json.dumps(value),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == value


def test_public_version_matches_distribution():
    assert clipboard.VERSION == version("clipboard")
