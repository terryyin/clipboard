"""Windows observers for the copy_files probe: PowerShell consumer, shell paste.

Both run in Windows PowerShell 5.1 (``-STA``), independent of this library:
the consumer reads the file drop list and ``Preferred DropEffect``; the shell
paste asks Explorer's ``Shell.Application`` to paste into a folder.
"""

from __future__ import annotations

import base64
import ctypes
import json
import subprocess
import textwrap
from pathlib import Path

# Independent consumer (PowerShell, STA). Paths travel as base64 UTF-8.
CONSUMER = textwrap.dedent(
    r"""
    function B($s) {
        [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([string]$s))
    }
    $o = [Windows.Forms.Clipboard]::GetDataObject()
    $formats = @()
    if ($null -ne $o) { $formats = @($o.GetFormats()) }
    $drop = @([Windows.Forms.Clipboard]::GetFileDropList() | ForEach-Object { B $_ })
    # PowerShell 5.1 emits the drop list as one collection object, so
    # unroll it: ``$_.FullName`` on it is an array that [string] joins.
    $gc = @(foreach ($item in @(Get-Clipboard -Format FileDropList)) {
        foreach ($name in @($item.FullName)) { B $name }
    })
    $effect = $null
    $effectBytes = $null
    if ($null -ne $o -and $o.GetDataPresent('Preferred DropEffect')) {
        $s = $o.GetData('Preferred DropEffect')
        if ($s -is [IO.MemoryStream]) {
            $raw = $s.ToArray()
            $effectBytes = [BitConverter]::ToString($raw)
            if ($raw.Length -ge 4) { $effect = [BitConverter]::ToUInt32($raw, 0) }
        }
    }
    @{ drop_list = $drop; get_clipboard = $gc; formats = $formats;
       effect = $effect; effect_bytes = $effectBytes;
       ps = $PSVersionTable.PSVersion.ToString() } | ConvertTo-Json -Compress
    """
)

# Explorer shell paste into $dest; waits in-process because the shell copy
# engine runs inside this PowerShell process and dies with it.
SHELL_PASTE = textwrap.dedent(
    r"""
    $cfg = [IO.File]::ReadAllText($in, [Text.Encoding]::UTF8) | ConvertFrom-Json
    $dest = $cfg.dest
    function Done() {
        foreach ($i in 0..($cfg.names.Count - 1)) {
            $p = [IO.Path]::Combine($dest, $cfg.names[$i])
            if (-not [IO.File]::Exists($p)) { return $false }
            if ((New-Object IO.FileInfo $p).Length -ne $cfg.sizes[$i]) { return $false }
        }
        return $true
    }
    function Wait($seconds) {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        while ($sw.Elapsed.TotalSeconds -lt $seconds) {
            if (Done) { return $true }
            Start-Sleep -Milliseconds 250
        }
        return (Done)
    }
    $shell = New-Object -ComObject Shell.Application
    $folder = $shell.NameSpace($dest)
    if ($null -eq $folder) { throw "Shell.Application NameSpace(dest) is null" }
    $item = $folder.Self
    $verbs = @($item.Verbs() | ForEach-Object { $_.Name })
    $attempts = @()
    $item.InvokeVerb('Paste')
    $ok = Wait $cfg.wait_s
    $attempts += @{ method = "FolderItem.InvokeVerb('Paste')"; done = $ok }
    if (-not $ok) {
        $verb = $item.Verbs() |
            Where-Object { ($_.Name -replace '&', '') -eq 'Paste' } |
            Select-Object -First 1
        if ($null -ne $verb) {
            $verb.DoIt()
            $ok = Wait $cfg.wait_s
            $attempts += @{ method = 'FolderItemVerb Paste DoIt'; done = $ok }
        }
    }
    Start-Sleep -Seconds 2
    $listing = @(Get-ChildItem -LiteralPath $dest -Force | ForEach-Object {
        [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($_.Name)) })
    @{ done = $ok; attempts = $attempts; verbs = $verbs; listing = $listing } |
        ConvertTo-Json -Compress -Depth 4
    """
)


def _decode_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    return [base64.b64decode(item).decode("utf-8") for item in value]


def _run_powershell(script: str, payload: str = "") -> tuple[dict | None, str]:
    from windows_powershell_producers import powershell

    try:
        result = powershell(script, payload)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip()[-2000:]
    try:
        return json.loads(result.stdout), ""
    except ValueError:
        return None, f"unparseable output: {result.stdout.strip()[-2000:]}"


def sequence_number() -> int:
    user32 = ctypes.WinDLL("user32")
    user32.GetClipboardSequenceNumber.restype = ctypes.c_uint32
    return int(user32.GetClipboardSequenceNumber())


def independent_consumer() -> dict:
    seen, error = _run_powershell(CONSUMER)
    if seen is None:
        return {"error": error}
    return {
        "drop_list": _decode_list(seen.get("drop_list")),
        "get_clipboard_file_drop_list": _decode_list(seen.get("get_clipboard")),
        "formats": seen.get("formats") or [],
        "drop_effect": seen.get("effect"),
        "drop_effect_bytes": seen.get("effect_bytes"),
        "powershell": seen.get("ps"),
        "sequence_number": sequence_number(),
    }


def consumer_ok(seen: dict, paths: list[str]) -> bool:
    return (
        "error" not in seen
        and seen["drop_list"] == paths
        and seen["get_clipboard_file_drop_list"] == paths
        and seen["drop_effect"] == 1
        and seen["drop_effect_bytes"] == "01-00-00-00"
    )


def shell_paste(sources: list[Path], dest: Path) -> dict:
    config = {
        "dest": str(dest),
        "names": [p.name for p in sources],
        "sizes": [p.stat().st_size for p in sources],
        "wait_s": 30,
    }
    seen, error = _run_powershell(SHELL_PASTE, json.dumps(config))
    copies = []
    for source in sources:
        target = dest / source.name
        copies.append(
            {
                "name": source.name,
                "exists": target.is_file(),
                "bytes_equal": target.is_file()
                and target.read_bytes() == source.read_bytes(),
            }
        )
    listing = sorted(p.name for p in dest.iterdir())
    return {
        "error": error or None,
        "shell": seen,
        "shell_listing": _decode_list((seen or {}).get("listing")),
        "dest_listing": listing,
        "copies": copies,
        "copies_match": all(c["bytes_equal"] for c in copies)
        and listing == sorted(p.name for p in sources),
    }
