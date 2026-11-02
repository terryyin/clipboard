#!/usr/bin/env python3
"""Independent producer/consumer probe: Windows CF_UNICODETEXT <-> copy/paste.

``clipboard.copy`` / ``paste`` on Windows delegate to pyperclip's Windows
backend (``OpenClipboard`` retried about 0.5 s). Producers and consumers that
are not this library run in other processes (``windows_native_text_support``):
Windows PowerShell 5.1 ``Set-Clipboard`` / ``Get-Clipboard`` (plus PowerShell
7 ``Get-Clipboard`` when installed), .NET ``Clipboard.SetImage`` under
``-STA``, a ctypes reader, Notepad pasting via ``WM_PASTE``, a ctypes
``OpenClipboard`` holder with its own window that signals readiness on stdout
(``windows_text_hold``), and a child Python whose ``copy`` exits before reading.
Every producer is read back by the ctypes reader before ``paste`` is judged.

Prints one JSON object. Exit 0 when every step passed; 1 when a step failed
or could not be observed (named in ``evidence_limits`` / ``failed_steps`` /
``observation_limits``);
2 when no usable Windows clipboard session or Windows PowerShell exists.
Overwrites the clipboard. Not run by default pytest.
"""

from __future__ import annotations

import json
import shutil
import sys

from windows_native_text_support import (
    attempt,
    child_copy,
    consume,
    get_clipboard,
    notepad,
    pwsh,
    set_clipboard,
    step,
    windows_floors,
)
from windows_powershell_producers import PRODUCERS, powershell
from windows_text_hold import held_clipboard_step, short_hold

TEXT_CRLF = "  héllo 👋 ﾃｽﾄ\r\nline 2 "
TEXT_LF = "héllo 👋\nline 2"
KEEP = "keep"


def _crlf_producer(clipboard) -> dict:
    producer = set_clipboard(TEXT_CRLF)
    got = attempt(clipboard.paste)
    limit = None if producer["producer_exact"] else "set_clipboard_not_exact"
    return step(
        "1_set_clipboard_crlf_to_paste",
        got["value"] == TEXT_CRLF,
        limit,
        producer=producer,
        paste=got,
        get_clipboard_raw=get_clipboard().get("raw"),
    )


def _child_copy_lf() -> dict:
    """Required: exact LF text stored and in ``Get-Clipboard -Raw``.

    Notepad's line count settles seed example 9b (recorded, true or false);
    ``Get-Clipboard`` array line counts are recorded facts.
    """
    set_clipboard(KEEP)
    child = child_copy(TEXT_LF)
    stored = consume()
    consumers = [get_clipboard()]
    if pwsh():
        consumers.append(get_clipboard(pwsh()))
    pad = notepad()
    two_lines = [c["exe"] for c in consumers if c.get("lines") == TEXT_LF.split("\n")]
    stored_text = stored.get("text")
    ok = (
        child.get("copied") is True
        and child["exit"] == 0
        and stored_text == TEXT_LF
        and consumers[0].get("raw") == TEXT_LF
    )
    unavailable = pad.get("unavailable")
    return step(
        "2_child_copy_lf_exits_to_get_clipboard",
        ok,
        child=child,
        stored_text=stored_text,
        stored_has_crlf=stored_text is not None and "\r\n" in stored_text,
        formats=stored.get("formats"),
        get_clipboard=consumers,
        get_clipboard_raw_exact=[
            c["exe"] for c in consumers if c.get("raw") == TEXT_LF
        ],
        get_clipboard_line_counts={c["exe"]: c.get("count") for c in consumers},
        two_line_consumers=two_lines,
        notepad=pad,
        notepad_two_lines=None if unavailable else pad.get("line_count") == 2,
        notepad_unavailable=unavailable,
    )


def _copy_empty(clipboard) -> dict:
    set_clipboard(KEEP)
    wrote = attempt(clipboard.copy, "")
    stored = consume()
    consumer = get_clipboard()
    got = attempt(clipboard.paste)
    empty = consumer.get("raw_null") is True or consumer.get("raw") == ""
    ok = wrote["error"] is None and got["value"] == "" and empty
    return step(
        "3_copy_empty_to_get_clipboard_and_paste",
        ok,
        copy=wrote,
        paste=got,
        get_clipboard=consumer,
        formats=stored.get("formats"),
        stored_text=stored.get("text"),
    )


def _image_only(clipboard) -> dict:
    produced = powershell(PRODUCERS["image_only"])
    stored = consume()
    got = attempt(clipboard.paste)
    snap = attempt(clipboard.inspect)
    kinds = sorted(snap["value"].kinds) if snap["value"] else None
    formats = list(snap["value"].formats) if snap["value"] else None
    image_only = produced.returncode == 0 and stored.get("text") is None
    ok = (
        got["value"] == ""
        and got["error"] is None
        and kinds is not None
        and "image" in kinds
        and "text" not in kinds
    )
    return step(
        "4_image_only_paste_empty",
        ok,
        None if image_only else "image_only_producer_failed",
        producer_exit=produced.returncode,
        producer_stderr=produced.stderr.strip()[-1000:],
        consumer_formats=stored.get("formats"),
        consumer_text=stored.get("text"),
        paste=got,
        inspect_kinds=kinds,
        inspect_formats=formats,
        inspect_error=snap["error"],
    )


def evidence_limit(reason: str) -> int:
    report = {"ok": False, "verified": False, "evidence_limit": True}
    report.update(evidence_limits=[reason], desktop="Windows desktop")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2


def main() -> int:
    if sys.platform != "win32":
        return evidence_limit(f"not Windows (platform {sys.platform!r})")
    if shutil.which("powershell.exe") is None:
        return evidence_limit("Windows PowerShell (powershell.exe) not on PATH")
    session = consume()
    if "seq" not in session:
        return evidence_limit(f"no usable clipboard session: {session}")
    import clipboard

    clipboard.set_text_clipboard_writer(None)
    clipboard.set_text_clipboard_reader(None)
    steps = [
        _crlf_producer(clipboard),
        _child_copy_lf(),
        _copy_empty(clipboard),
        _image_only(clipboard),
        held_clipboard_step(clipboard),
    ]
    short = short_hold(clipboard)
    powershell(PRODUCERS["cleared_empty"])
    limits = [s["evidence_limit"] for s in steps if s["evidence_limit"]]
    failed = [s["step"] for s in steps if not s["ok"]]
    observation_limits = [
        f"notepad_unavailable: {s['notepad_unavailable']}"
        for s in steps
        if s.get("notepad_unavailable")
    ]
    verified = not failed and not observation_limits
    report = {
        "ok": verified,
        "verified": verified,
        "evidence_limit": bool(limits),
        "evidence_limits": limits,
        "observation_limits": observation_limits,
        "failed_steps": failed,
        "desktop": "Windows desktop",
        "backend": clipboard._text._select_text_backend(),
        "steps": steps,
        "short_hold_observed": short,
        "environment": windows_floors(),
        "commitments": "independent processes only: PowerShell 5.1 Set-Clipboard "
        "(UTF-8 file) and .NET SetImage (-STA) producers; ctypes CF_UNICODETEXT "
        "reader, Get-Clipboard (5.1, pwsh 7 if present) and Notepad WM_PASTE "
        "consumers; ctypes OpenClipboard(own hidden hwnd) holder with a stdout "
        "ready line and GetOpenClipboardWindow evidence; child copy() exits first",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
