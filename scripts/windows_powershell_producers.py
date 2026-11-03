"""Windows PowerShell 5.1 / .NET Framework clipboard producers for the probe.

Each producer is a script body run by :func:`powershell` as a separate
``powershell.exe -STA`` process; ``$in`` names a file holding its payload.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

PRODUCERS = {
    "dotnet_stream": (
        "$b = [IO.File]::ReadAllBytes($in)\n"
        "$o = New-Object Windows.Forms.DataObject\n"
        "$o.SetData('HTML Format', (New-Object IO.MemoryStream -ArgumentList (,$b)))\n"
        "[Windows.Forms.Clipboard]::SetDataObject($o, $true, 10, 100)"
    ),
    "dotnet_settext_html": (
        "[Windows.Forms.Clipboard]::SetText([IO.File]::ReadAllText($in, "
        "[Text.Encoding]::UTF8), [Windows.Forms.TextDataFormat]::Html)"
    ),
    "set_clipboard_as_html": (
        "Set-Clipboard -AsHtml -Value ([IO.File]::ReadAllText($in, "
        "[Text.Encoding]::UTF8))"
    ),
    "text_only": (
        "Set-Clipboard -Value ([IO.File]::ReadAllText($in, [Text.Encoding]::UTF8))"
    ),
    "image_only": (
        "Add-Type -AssemblyName System.Drawing\n"
        "[Windows.Forms.Clipboard]::SetImage((New-Object Drawing.Bitmap 2, 2))"
    ),
    "cleared_empty": "[Windows.Forms.Clipboard]::Clear()",
}
# PowerShell / CLR / OS floors and whether ``Set-Clipboard -AsHtml`` exists.
FLOORS = (
    "@{ps=$PSVersionTable.PSVersion.ToString(); edition=$PSVersionTable.PSEdition; "
    "clr=$PSVersionTable.CLRVersion.ToString(); "
    "os=[Environment]::OSVersion.VersionString; "
    "as_html=(Get-Command Set-Clipboard).Parameters.ContainsKey('AsHtml')} "
    "| ConvertTo-Json -Compress"
)


def powershell(
    script: str, payload: str | bytes = "", *, exe: str = "powershell.exe"
) -> subprocess.CompletedProcess:
    """Run ``script`` in Windows PowerShell with ``payload`` written to ``$in``.

    ``exe`` selects another PowerShell (e.g. ``pwsh`` 7) with the same flags.
    """
    with tempfile.TemporaryDirectory(prefix="clipboard-probe-") as raw:
        tmp = Path(raw)
        data = tmp / "input.bin"
        data.write_bytes(payload if isinstance(payload, bytes) else payload.encode())
        ps1 = tmp / "producer.ps1"
        ps1.write_text(
            "param($in)\n$ErrorActionPreference = 'Stop'\n"
            f"Add-Type -AssemblyName System.Windows.Forms\n{script}\n",
            encoding="ascii",
        )
        return subprocess.run(
            [exe, "-NoProfile", "-NonInteractive", "-STA"]
            + ["-ExecutionPolicy", "Bypass", "-File", str(ps1), str(data)],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=60,
            check=False,
        )
