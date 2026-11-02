#!/usr/bin/env python3
"""Independent-producer probe: Windows ``HTML Format`` (CF_HTML) → paste_html().

Producers are Windows PowerShell 5.1 / .NET Framework (not this library's
copy_html), each run as a separate ``powershell.exe -STA`` process:

* ``dotnet_stream`` -- a CF_HTML envelope with UTF-8 byte offsets, built by
  this probe, placed byte for byte via ``DataObject.SetData("HTML Format",
  MemoryStream)``. Required for ``verified``.
* ``dotnet_settext_html`` -- the same envelope as a string through
  ``Clipboard.SetText(..., TextDataFormat.Html)``. Observed only: .NET
  Framework picks the bytes (UTF-8, or ANSI under its 4.0 compatibility quirk).
* ``set_clipboard_as_html`` -- ``Set-Clipboard -AsHtml`` builds its own
  envelope (PowerShell source: UTF-8 byte offsets counted per UTF-16 char,
  StartHTML at the header's own line break) and hands it to ``SetText``.
  When ``-AsHtml`` exists and the bytes on the clipboard carry UTF-8 byte
  offsets, paste_html() must return exactly the fragment; otherwise (e.g.
  .NET wrote ANSI) its offsets, bytes and outcome are recorded.

Non-ASCII text sits before and inside every fragment, so character offsets
cannot give the right answer. Each producer's raw bytes are read back by an
independent ctypes consumer in a child process before and after paste_html()
(same bytes, formats and clipboard sequence number: a non-mutating read). The
``dotnet_stream`` envelope must yield exactly the fragment; text-only,
image-only and cleared clipboards must give ``None``.

Prints one JSON object. Exit 0 on success, 1 on a failed check, 2 with
``evidence_limit`` / ``verified: false`` when no usable Windows clipboard
session or no Windows PowerShell exists. Not default pytest.
"""

from __future__ import annotations

import base64
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from native_probe_paste_html import FRAGMENT, PLAIN_TEXT, paste_html
from windows_powershell_producers import FLOORS, PRODUCERS, powershell

TITLE = "Ünïcödé 東京 context"
BEFORE = f"<html><head><title>{TITLE}</title></head><body><p>ñ unselected 前</p>"
AFTER = "<p>après unselected</p></body></html>"
AS_HTML_INPUT = (
    f"<html><head><title>{TITLE}</title></head><body>{FRAGMENT}</body></html>"
)

# Independent consumer: plain ctypes in a child process, not clipboard's reader.
CONSUMER = Path(__file__).with_name("windows_clipboard_consumer.py")


def build_envelope() -> bytes:
    """CF_HTML with UTF-8 byte offsets (independent of clipboard._html_envelope)."""
    pre = (BEFORE + "<!--StartFragment-->").encode()
    frag = FRAGMENT.encode()
    post = ("<!--EndFragment-->" + AFTER).encode()
    template = (
        "Version:0.9\r\nStartHTML:{:010d}\r\nEndHTML:{:010d}\r\n"
        "StartFragment:{:010d}\r\nEndFragment:{:010d}\r\n"
    )
    head = len(template.format(0, 0, 0, 0).encode())
    end = head + len(pre) + len(frag) + len(post)
    offsets = (head, end, head + len(pre), head + len(pre) + len(frag))
    return template.format(*offsets).encode() + pre + frag + post


def consume() -> dict:
    result = subprocess.run(
        [sys.executable, "-I", str(CONSUMER)],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
        check=False,
    )
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {"consumer_error": (result.stderr or result.stdout).strip()}


def offset_unit(raw: bytes) -> dict:
    """Which unit the producer's StartFragment/EndFragment offsets use."""
    found = dict(re.findall(rb"(StartFragment|EndFragment):(-?\d+)", raw[:400]))
    if len(found) != 2:
        return {"offset_unit": "unparsed"}
    start, end = int(found[b"StartFragment"]), int(found[b"EndFragment"])
    text = raw.decode("utf-8", "replace")
    unit = (
        "utf8_bytes"
        if raw[start:end] == FRAGMENT.encode()
        else "chars"
        if text[start:end] == FRAGMENT
        else "fragment_bytes_absent"
        if FRAGMENT.encode() not in raw
        else "other"
    )
    return {"offset_unit": unit, "start_fragment": start, "end_fragment": end}


def run_case(name: str, payload: str | bytes) -> dict:
    produced = powershell(PRODUCERS[name], payload)
    case: dict = {"case": name, "producer_exit": produced.returncode}
    if produced.returncode != 0:
        return {**case, "producer_stderr": produced.stderr.strip()[-2000:]}
    before = consume()
    case.update(paste_html())
    after = consume()
    case["formats"] = before.get("formats")
    case["unchanged"] = "seq" in before and before == after
    if before.get("html"):
        raw = base64.b64decode(before["html"])
        case.update(offset_unit(raw), envelope_head=raw[:200].decode("latin-1"))
        case["matches"] = case["paste_html"] == FRAGMENT
    return case


def environment(floors: dict) -> dict:
    return {
        "os": platform.system(),
        "windows_release": platform.release(),
        "windows_version": platform.version(),
        "windows_build": sys.getwindowsversion().build
        if sys.platform == "win32"
        else None,
        "machine": platform.machine(),
        "python": platform.python_version(),
        "powershell": floors.get("ps"),
        "powershell_edition": floors.get("edition"),
        "clr": floors.get("clr"),
        "set_clipboard_as_html_available": floors.get("as_html"),
        "consumer_api": "ctypes user32 GetClipboardData in a child process",
    }


def evidence_limit(reason: str, floors: dict | None = None) -> int:
    payload = {
        "ok": False,
        "desktop": "Windows desktop",
        "evidence_limit": True,
        "verified": False,
        "reason": reason,
        "environment": environment(floors or {}),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


def main() -> int:
    if sys.platform != "win32":
        return evidence_limit(f"not Windows (platform {sys.platform!r})")
    if shutil.which("powershell.exe") is None:
        return evidence_limit("Windows PowerShell (powershell.exe) not on PATH")
    floors_run = powershell(FLOORS)
    try:
        floors = json.loads(floors_run.stdout)
    except ValueError:
        return evidence_limit(
            f"Windows PowerShell did not run: {floors_run.stderr.strip()[-500:]}"
        )
    session = consume()
    if "seq" not in session:
        return evidence_limit(f"no usable clipboard session: {session}", floors)
    envelope = build_envelope()
    html = [run_case("dotnet_stream", envelope)]
    html.append(run_case("dotnet_settext_html", envelope.decode()))
    if floors.get("as_html"):
        html.append(run_case("set_clipboard_as_html", AS_HTML_INPUT))
    absent = [
        run_case("text_only", PLAIN_TEXT),
        run_case("image_only", b""),
        run_case("cleared_empty", b""),
    ]
    required = html[0]
    # -AsHtml envelopes with byte offsets must yield the fragment (StartHTML
    # at its header's line break is tolerated); SetText stays recorded only.
    as_html_ok = all(
        c.get("matches") is True
        for c in html
        if c["case"] == "set_clipboard_as_html" and c.get("offset_unit") == "utf8_bytes"
    )
    ok = (
        required.get("matches") is True
        and required.get("offset_unit") == "utf8_bytes"
        and as_html_ok
        and all(c["producer_exit"] == 0 for c in [required, *absent])
        and all(c["unchanged"] for c in html + absent if c["producer_exit"] == 0)
        and all(c["paste_html"] is None and "error" not in c for c in absent)
    )
    report = {
        "ok": ok,
        "verified": ok,
        "desktop": "Windows desktop",
        "html": html,
        "absent": absent,
        "expected_fragment": FRAGMENT,
        "environment": environment(floors),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
