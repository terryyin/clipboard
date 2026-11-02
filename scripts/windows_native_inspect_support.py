"""Independent producers/consumers for the Windows desktop inspect probe.

Uses PowerShell / .NET ``System.Windows.Forms.Clipboard`` as the producer and
post-inspect consumer — not ``clipboard.inspect`` / ``clipboard.copy*``
same-library round-trips alone. Does not require ``clipboard[images]`` or
``win32clipboard``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from native_probe_common import die

ROOT = Path(__file__).resolve().parents[1]

PROBE_HTML = (
    "<html><body><!--StartFragment-->"
    '<a href="https://example.com/inspect" style="color:#06c"><b>café</b></a>'
    "<!--EndFragment--></body></html>"
)
PROBE_TEXT = "café → https://example.com/inspect"
HTML_MARKERS = ("<a href=", "café", "</b>", "example.com/inspect")
TEXT_EXACT = PROBE_TEXT
HTML_FORMAT_IDS = ("HTML Format",)
TEXT_FORMAT_IDS = ("CF_UNICODETEXT", "CF_TEXT")
IMAGE_FORMAT_IDS = ("CF_DIB", "CF_DIBV5", "CF_BITMAP", "PNG")
FILE_FORMAT_IDS = ("CF_HDROP",)


def _run_powershell(script: str, *, timeout: float = 30.0) -> str:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"PowerShell clipboard helper failed: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        die(f"PowerShell clipboard helper failed: {detail or 'unknown error'}")
    return (result.stdout or "").rstrip("\n")


def produce_html_text_independent() -> None:
    """Offer HTML Format + Unicode text via .NET Clipboard (independent)."""
    html_ps = PROBE_HTML.replace("'", "''")
    text_ps = PROBE_TEXT.replace("'", "''")
    _run_powershell(
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$d = New-Object System.Windows.Forms.DataObject; "
        f"$d.SetText('{text_ps}'); "
        f"$d.SetText('{html_ps}', "
        "[System.Windows.Forms.TextDataFormat]::Html); "
        "[System.Windows.Forms.Clipboard]::SetDataObject($d, $true)"
    )


def produce_text_independent() -> None:
    text_ps = PROBE_TEXT.replace("'", "''")
    _run_powershell(
        "Add-Type -AssemblyName System.Windows.Forms; "
        f"[System.Windows.Forms.Clipboard]::SetText('{text_ps}')"
    )


def consume_text_independent() -> str:
    return _run_powershell(
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[Console]::Out.Write("
        "[System.Windows.Forms.Clipboard]::GetText())"
    )


def consume_html_independent() -> str:
    return _run_powershell(
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$h = [System.Windows.Forms.Clipboard]::GetText("
        "[System.Windows.Forms.TextDataFormat]::Html); "
        "if ($null -eq $h) { $h = '' }; [Console]::Out.Write($h)"
    )


def formats_still_include(*needles: str) -> bool:
    listed = _run_powershell(
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$fmts = [System.Windows.Forms.Clipboard]::GetDataObject()"
        ".GetFormats(); "
        "if ($null -eq $fmts) { '' } else { $fmts -join \"`n\" }"
    )
    lower = {line.lower() for line in listed.splitlines() if line}
    return all(n.lower() in lower for n in needles)


def inspect_via_library() -> dict:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        import clipboard
    except ImportError as exc:
        die(f"missing clipboard import: {exc}")
    snapshot = clipboard.inspect()
    return {
        "kinds": sorted(snapshot.kinds),
        "formats": list(snapshot.formats),
    }


def windows_environment(**extra: object) -> dict:
    import platform

    env = {
        "os": platform.system(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "desktop": "Windows desktop",
        "helper": "ctypes user32 EnumClipboardFormats + GetClipboardFormatNameW",
        "python": sys.version.split()[0],
        "platform": sys.platform,
    }
    env.update(extra)
    return env
