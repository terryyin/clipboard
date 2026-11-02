"""Linux X11 paste_files: desktop-free reader checks + evidence-limit probe.

Default pytest stays green without a desktop. The probe asserts an explicit
evidence_limit exit when no usable X11 + xclip + named file manager session
exists (this Darwin host). Full independent-FM verification stays owner-held.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import clipboard

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_x11_native_paste_files.py"


def test_linux_x11_paste_files_probe_records_evidence_limit():
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
    assert report["file_manager_generalization"] is False
    assert report["desktop"] == "Linux X11"
    assert "text/uri-list" in report["environment"]["helper_expectation"]
    assert report["environment"]["named_file_manager_required"] is True


def test_linux_x11_reader_missing_helper_raises_content_error(
    restore_files_clipboard_reader, monkeypatch
):
    monkeypatch.setattr(clipboard._files_native.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(
        clipboard._files_native_linux.shutil, "which", lambda _name: None
    )
    clipboard.set_files_clipboard_reader(None)

    with pytest.raises(clipboard.ClipboardContentError) as raised:
        clipboard.paste_files()

    assert raised.value.__class__ is clipboard.ClipboardContentError
    assert not isinstance(raised.value, clipboard.ClipboardImageError)
    message = str(raised.value).lower()
    assert "xclip" in message or "display" in message
    assert "session/helper unavailable" in message


def test_linux_x11_reader_uri_list_uses_contract_normalize(
    restore_files_clipboard_reader, monkeypatch
):
    monkeypatch.setattr(clipboard._files_native.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":99")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(
        clipboard._files_native_linux.shutil, "which", lambda name: "/usr/bin/xclip"
    )
    uri_list = "file:///tmp/plain.txt\r\nfile:///tmp/caf%C3%A9%20space.txt\r\n"
    completed = MagicMock(
        returncode=0,
        stdout=uri_list,
        stderr="",
    )
    monkeypatch.setattr(
        clipboard._files_native_linux.subprocess,
        "run",
        lambda *args, **kwargs: completed,
    )
    clipboard.set_files_clipboard_reader(None)

    assert clipboard.paste_files() == [
        "/tmp/plain.txt",
        "/tmp/café space.txt",
    ]


def test_linux_x11_reader_missing_uri_list_target_is_absence(
    restore_files_clipboard_reader, monkeypatch
):
    monkeypatch.setattr(clipboard._files_native.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":99")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(
        clipboard._files_native_linux.shutil, "which", lambda name: "/usr/bin/xclip"
    )
    completed = MagicMock(
        returncode=1,
        stdout="",
        stderr="Error: target text/uri-list not available\n",
    )
    monkeypatch.setattr(
        clipboard._files_native_linux.subprocess,
        "run",
        lambda *args, **kwargs: completed,
    )
    clipboard.set_files_clipboard_reader(None)

    assert clipboard.paste_files() is None
