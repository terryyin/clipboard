"""Opt-in real Thunar paste experiment; default tests need no desktop."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_x11_file_manager_offers.py"

pytestmark = pytest.mark.skipif(
    os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1"
    or os.environ.get("CLIPBOARD_FILE_MANAGER_ISOLATED") != "1",
    reason="set both native and isolated-file-manager gates in an isolated X11 session",
)


def test_thunar_pastes_helper_file_offers_after_writer_exits():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    print(result.stdout)
    assert report["ok"] is True
    assert report["environment"]["os"] == "Linux"
    assert report["environment"]["thunar"]
    assert [r["label"] for r in report["rounds"]] == [
        "positive-before",
        "uri-list",
        "positive-after",
    ]
    for round_ in report["rounds"]:
        assert round_["writer_exited_before_paste"] is True
        assert round_["writer_returncode"] == 0
        assert round_["no_paste_control_rejected_by_copy_assertions"] is True
        assert round_["sources_unchanged"] is True
        assert round_["mime"] in round_["targets"]
        if round_["mime"] == "x-special/gnome-copied-files":
            assert round_["outcome"] == "copies verified"
        else:
            assert round_["outcome"] in ("copies verified", "no copies observed")
