#!/usr/bin/env python3
"""Independent producer/consumer probe: Windows CF_UNICODETEXT <-> copy/paste.

``clipboard.copy`` / ``paste`` on Windows delegate to pyperclip's Windows
backend (``OpenClipboard`` retried about 0.5 s). Producers and consumers that
are not this library run in other processes (``windows_native_text_support``):
Windows PowerShell 5.1 ``Set-Clipboard`` / ``Get-Clipboard`` (plus PowerShell
7 ``Get-Clipboard`` when installed), .NET ``Clipboard.SetImage`` under
``-STA``, a ctypes reader, a ctypes ``OpenClipboard`` holder that signals
readiness on stdout, and a child Python whose ``copy`` exits before reading.
Every producer is read back by the ctypes reader before ``paste`` is judged.

Prints one JSON object. Exit 0 when every step passed; 1 when a step failed
or could not be observed (named in ``evidence_limits`` / ``failed_steps``);
2 when no usable Windows clipboard session or Windows PowerShell exists.
Overwrites the clipboard. Not run by default pytest.
"""

from __future__ import annotations

import json
import shutil
import sys
import time

from windows_native_text_support import (
    attempt,
    child_copy,
    consume,
    get_clipboard,
    held,
    pwsh,
    set_clipboard,
    step,
    windows_floors,
)
from windows_powershell_producers import PRODUCERS, powershell

TEXT_CRLF = "  héllo 👋 ﾃｽﾄ\r\nline 2 "
TEXT_LF = "héllo 👋\nline 2"
KEEP = "keep"
HELD = "held text ✓"
HOLD_SECONDS = 4.0
SHORT_HOLD_SECONDS = 0.1


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
    set_clipboard(KEEP)
    child = child_copy(TEXT_LF)
    stored = consume()
    consumers = [get_clipboard()]
    if pwsh():
        consumers.append(get_clipboard(pwsh()))
    two_lines = [c["exe"] for c in consumers if c.get("lines") == TEXT_LF.split("\n")]
    stored_text = stored.get("text")
    ok = (
        child.get("copied") is True
        and child["exit"] == 0
        and stored_text == TEXT_LF
        and consumers[0].get("raw") == TEXT_LF
        and bool(two_lines)
    )
    return step(
        "2_child_copy_lf_exits_to_get_clipboard",
        ok,
        child=child,
        stored_text=stored_text,
        stored_has_crlf=stored_text is not None and "\r\n" in stored_text,
        formats=stored.get("formats"),
        get_clipboard=consumers,
        two_line_consumers=two_lines,
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


def _held_clipboard(clipboard) -> dict:
    producer = set_clipboard(HELD)
    with held(HOLD_SECONDS) as holder:
        if holder.get("ready"):
            ready_at = time.monotonic()
            during_paste = attempt(clipboard.paste)
            during_copy = attempt(clipboard.copy, "must not land")
            within = time.monotonic() - ready_at < HOLD_SECONDS
        else:
            during_paste = during_copy = None
    if not holder.get("ready"):
        return step(
            "5_held_clipboard_raises_then_recovers",
            False,
            "holder_could_not_open_clipboard",
            holder=holder,
        )
    stored = consume()
    after = attempt(clipboard.paste)
    raised = all(
        r["value"] is None
        and r["error"]
        and r["error"]["type"] == "ClipboardContentError"
        and r["cause"]
        and r["cause"]["type"] == "PyperclipWindowsException"
        for r in (during_paste, during_copy)
    )
    ok = raised and stored.get("text") == HELD and after["value"] == HELD
    return step(
        "5_held_clipboard_raises_then_recovers",
        ok,
        None if producer["producer_exact"] and within else "hold_not_established",
        hold_seconds=HOLD_SECONDS,
        holder=holder,
        during_paste=during_paste,
        during_copy=during_copy,
        calls_within_hold=within,
        after_release_consumer_text=stored.get("text"),
        after_release_paste=after,
    )


def _short_hold(clipboard) -> dict:
    """Recorded only: a hold shorter than pyperclip's ~0.5 s retry."""
    set_clipboard(HELD)
    with held(SHORT_HOLD_SECONDS) as holder:
        got = attempt(clipboard.paste) if holder.get("ready") else None
    return {
        "hold_seconds": SHORT_HOLD_SECONDS,
        "holder": holder,
        "paste": got,
        "succeeded": bool(got) and got["value"] == HELD,
    }


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
        _held_clipboard(clipboard),
    ]
    short = _short_hold(clipboard)
    powershell(PRODUCERS["cleared_empty"])
    limits = [s["evidence_limit"] for s in steps if s["evidence_limit"]]
    failed = [s["step"] for s in steps if not s["ok"]]
    report = {
        "ok": not failed,
        "verified": not failed,
        "evidence_limit": bool(limits),
        "evidence_limits": limits,
        "failed_steps": failed,
        "desktop": "Windows desktop",
        "backend": clipboard._text._select_text_backend(),
        "steps": steps,
        "short_hold_observed": short,
        "environment": windows_floors(),
        "commitments": "independent processes only: PowerShell 5.1 Set-Clipboard "
        "(UTF-8 file) and .NET SetImage (-STA) producers; ctypes CF_UNICODETEXT "
        "reader and Get-Clipboard (5.1, pwsh 7 if present) consumers; ctypes "
        "OpenClipboard holder with a stdout ready line; child copy() exits first",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
