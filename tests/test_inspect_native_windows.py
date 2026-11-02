"""Optional Windows desktop inspect() probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable with:

  CLIPBOARD_NATIVE_PROBE=1 uv run --locked \\
    pytest tests/test_inspect_native_windows.py -v

Requires win32 + a usable Windows desktop clipboard session. On hosts
without that session the probe script records an evidence limit (exit 2)
rather than claiming verified.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_windows_native_inspect.py"

pytestmark = [
    pytest.mark.skipif(
        sys.platform != "win32",
        reason="Windows desktop inspect probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Windows inspect probe",
    ),
]


def test_windows_inspect_independent_producer_probe():
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report.get("evidence_limit") is not True
    assert report["ok"] is True
    html_text = report["html_and_text"]
    assert html_text["ok"] is True
    assert html_text["has_html_kind"] is True
    assert html_text["has_text_kind"] is True
    assert html_text["has_html_format"] is True
    assert html_text["has_text_format"] is True
    assert html_text["non_mutation"] is True
    assert report["commitments"]["no_win32clipboard_required"] is True
    assert report["floors"]["method"]
