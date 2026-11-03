"""Windows paste_files: desktop-free CF_HDROP checks + evidence-limit probe.

Default pytest stays green without a desktop. The probe asserts an explicit
evidence_limit exit when no usable Windows Explorer CF_HDROP session exists
(this Darwin host). Full independent-FM verification stays owner-held.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import clipboard

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_windows_native_paste_files.py"


def test_windows_paste_files_probe_records_evidence_limit():
    """Probe must not claim verified; records evidence_limit (exit 2)."""
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["ok"] is False
    assert report["evidence_limit"] is True
    assert report["verified"] is False
    assert report["desktop"] == "Windows desktop"
    assert "CF_HDROP" in report["environment"]["helper_expectation"]
    assert report["environment"]["named_file_manager_required"] is True
    assert "32" in report["commitments"]
    assert "52" in report["commitments"]


def test_windows_reader_non_windows_raises_content_error(fake_platform):
    """Non-win32 platform forces the unavailable stub (desktop-free)."""
    fake_platform("darwin")
    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard._files_native_windows._windows_files_clipboard_reader()

    assert raised.value.__class__ is clipboard.ClipboardContentError
    assert not isinstance(raised.value, clipboard.ClipboardImageError)
    message = str(raised.value).lower()
    assert "cf_hdrop" in message or "windows" in message
    assert "unavailable" in message


def test_windows_reader_path_list_uses_contract_normalize(
    restore_files_clipboard_reader, monkeypatch, fake_platform
):
    fake_platform("win32")
    paths = [r"C:\tmp\plain.txt", r"C:\tmp\café space.txt"]
    monkeypatch.setattr(
        clipboard._files_native_windows,
        "_read_cf_hdrop_offer",
        lambda: paths,
    )
    clipboard.set_files_clipboard_reader(None)

    assert clipboard.paste_files() == paths


def test_windows_reader_missing_cf_hdrop_is_absence(
    restore_files_clipboard_reader, monkeypatch, fake_platform
):
    fake_platform("win32")
    monkeypatch.setattr(
        clipboard._files_native_windows,
        "_read_cf_hdrop_offer",
        lambda: None,
    )
    clipboard.set_files_clipboard_reader(None)

    assert clipboard.paste_files() is None
