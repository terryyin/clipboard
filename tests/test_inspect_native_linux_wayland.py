"""Optional Linux Wayland + wl-paste -l inspect() probe (skipped unless enabled).

Default pytest stays green without a desktop. Enable with:

  CLIPBOARD_NATIVE_PROBE=1 CLIPBOARD_WAYLAND_COMPOSITOR=<Name> \\
    WAYLAND_DISPLAY=wayland-1 nix develop -c uv run --locked \\
    pytest tests/test_inspect_native_linux_wayland.py -v

Requires Linux + WAYLAND_DISPLAY + wl-clipboard + a **named** compositor.
On hosts without that session the probe script records an evidence limit
(exit 2) rather than claiming verified. Do not generalize one compositor
to all Wayland.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_linux_wayland_native_inspect.py"

pytestmark = [
    pytest.mark.skipif(
        not sys.platform.startswith("linux"),
        reason="Linux Wayland + wl-paste -l inspect probe only",
    ),
    pytest.mark.skipif(
        os.environ.get("CLIPBOARD_NATIVE_PROBE") != "1",
        reason="set CLIPBOARD_NATIVE_PROBE=1 to run native Wayland inspect probe",
    ),
]


def test_linux_wayland_inspect_independent_producer_probe():
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
    assert report.get("compositor_generalization") is False
    assert report["html"]["ok"] is True
    assert report["html"]["has_html_kind"] is True
    assert report["html"]["has_html_format"] is True
    assert report["html"]["non_mutation"] is True
    assert report["text"]["ok"] is True
    assert report["text"]["has_text_kind"] is True
    assert report["text"]["has_text_format"] is True
    assert report["text"]["non_mutation"] is True
    assert report["commitments"]["helper_flags"] == "wl-paste -l"
    assert report["commitments"]["do_not_generalize_compositor"] is True
    compositor = report["floors"]["compositor"]
    assert compositor
    assert report["commitments"]["compositor_scope"] == compositor
    assert report["floors"]["compositor_scope_only"] is True
    image_only = report.get("image_only")
    if image_only is not None:
        assert image_only["ok"] is True
        assert image_only["has_image_kind"] is True
        assert image_only["no_text_or_html_kind"] is True
        assert image_only["non_mutation"] is True
