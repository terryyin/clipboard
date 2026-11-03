"""The native experiment's oracle must reject missing and damaged copies."""

import subprocess
import sys
from pathlib import Path
from runpy import run_path

import pytest

PROBE = (
    Path(__file__).resolve().parents[1]
    / "scripts/probe_linux_x11_file_manager_offers.py"
)
assert_copies = run_path(str(PROBE))["_assert_copies"]


@pytest.mark.parametrize("damage", ["missing", "corrupt-copy", "changed-source", None])
def test_copy_oracle_requires_exact_destination_and_unchanged_source(tmp_path, damage):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    expected = {"report final.txt": b"one", "données é.csv": b"two"}
    for name, content in expected.items():
        (source / name).write_bytes(content)
        (destination / name).write_bytes(content)
    first = next(iter(expected))
    if damage == "missing":
        (destination / first).unlink()
    elif damage == "corrupt-copy":
        (destination / first).write_bytes(b"damaged")
    elif damage == "changed-source":
        (source / first).write_bytes(b"changed")
    if damage:
        with pytest.raises(AssertionError):
            assert_copies(source, destination, expected)
    else:
        assert_copies(source, destination, expected)


def test_failed_file_manager_launch_reports_exit_before_searching_windows(
    tmp_path, monkeypatch
):
    launched = subprocess.Popen([sys.executable, "-c", "raise SystemExit(2)"])
    launched.wait(timeout=5)
    round_ = assert_copies.__globals__["_round"]
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: launched)
    monkeypatch.setitem(round_.__globals__, "_run", lambda *args, **kwargs: None)

    def search_after_failed_launch(*args, **kwargs):
        pytest.fail("window search ran after the file-manager launch failed")

    monkeypatch.setattr(subprocess, "run", search_after_failed_launch)
    with pytest.raises(RuntimeError, match="Thunar exited with status 2"):
        round_(tmp_path, "failed-launch", "text/uri-list", None)
