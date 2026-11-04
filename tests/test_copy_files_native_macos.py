"""Optional macOS native copy_files file-URL probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable with:

  CLIPBOARD_NATIVE_PROBE=1 ./scripts/dev uv run --locked --extra images \\
    pytest tests/test_copy_files_native_macos.py -v

The probe replaces the developer's clipboard.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_macos_native_copy_files.py"

pytestmark = [
    pytest.mark.skipif(sys.platform != "darwin", reason="macOS pasteboard probe only"),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native pasteboard probe",
    ),
]


def test_macos_copy_files_independent_file_url_consumer_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is True
    expected = report["expected_paths"]
    assert [Path(p).name for p in expected] == ["report final.pdf", "données é.csv"]
    assert report["writer"]["exited"] is True
    assert report["independent"]["paths"] == expected
    assert report["independent"]["change_count"] > report["change_count_before"]
    rechecks = report["rechecks_after_exit"]
    assert report["offer_held_after_exit"] is True
    assert rechecks[-1]["t_s"] >= 20
    assert {r["change_count"] for r in rechecks} == {
        report["independent"]["change_count"]
    }
    assert all("public.file-url" in r["types"] and r["paths_equal"] for r in rechecks)
    assert report["paste_files"] == expected
    assert report["sources_unchanged"] is True
    missing = report["missing_path"]
    assert "missing.txt" in missing["error"]
    assert missing["prior_text_before"] == "keep"
    assert missing["prior_text_after"] == "keep"
    floors = report["floors"]
    for key in ("macos_product", "darwin_release", "machine", "python", "osascript"):
        assert floors[key], key
    relative = report["relative_directory_duplicate"]
    assert relative["relative_args"] == [
        "report final.pdf",
        "a dir",
        "report final.pdf",
    ]
    assert [Path(p).name for p in relative["expected_paths"]] == [
        "report final.pdf",
        "a dir",
        "report final.pdf",
    ]
    assert relative["expected_paths"][0] == relative["expected_paths"][2]
    assert relative["independent"]["paths"] == relative["expected_paths"]
    assert relative["paste_files"] == relative["expected_paths"]
    assert relative["writer"]["exited"] is True
