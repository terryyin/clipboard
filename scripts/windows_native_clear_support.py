"""Independent processes for the gated Windows ``clear()`` probe.

None of these use this library: Windows PowerShell 5.1 / .NET
``System.Windows.Forms.Clipboard`` producers (HTML + text, image, a
``CF_HDROP`` file list, and an unknown registered format), the ctypes
``windows_clipboard_consumer.py`` format lister, a raw ctypes
``OpenClipboard(NULL)`` / ``EmptyClipboard`` / ``CloseClipboard`` process for
the early probe, and ``windows_clipboard_holder.py`` holding the clipboard
open with its own window. Each runs as a separate process. ``no_formats`` is
the consumer's empty-clipboard predicate for ``cleared_step``. The two holder
steps (7 past the library's ``OpenClipboard`` bound, 8 released within it)
live here because they prove the bound, not the shared "cleared" rule.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from native_clear_support import child_clear, child_cleared, step
from windows_powershell_producers import PRODUCERS, powershell

CONSUMER = Path(__file__).with_name("windows_clipboard_consumer.py")
HOLDER = Path(__file__).with_name("windows_clipboard_holder.py")
CUSTOM_FORMAT = "ClipboardProbe.Custom"
HTML_FORMAT = "HTML Format"
CF_BITMAP, CF_DIB, CF_UNICODETEXT, CF_HDROP, CF_DIBV5 = 2, 8, 13, 15, 17
PROBE_HTML = "<b>clear probe</b> html"
PROBE_TEXT = "clear probe text"
HTML_TEXT_FORMATS = (HTML_FORMAT, CF_UNICODETEXT)
# Margin past the library's OpenClipboard bound for the long holder.
HOLD_PAST_BOUND_S = 10.0
SHORT_HOLD_S = 3.0

CLEAR_PRODUCERS = {
    "html_and_text": (
        "$o = New-Object Windows.Forms.DataObject\n"
        f"$o.SetText('{PROBE_TEXT}')\n"
        "$o.SetText([IO.File]::ReadAllText($in, [Text.Encoding]::UTF8), "
        "[Windows.Forms.TextDataFormat]::Html)\n"
        "[Windows.Forms.Clipboard]::SetDataObject($o, $true, 10, 100)"
    ),
    "image_only": PRODUCERS["image_only"],
    "file_list": (
        "$c = New-Object Collections.Specialized.StringCollection\n"
        "[void]$c.Add([IO.File]::ReadAllText($in, [Text.Encoding]::UTF8))\n"
        "[Windows.Forms.Clipboard]::SetFileDropList($c)"
    ),
    "custom_format": (
        "$b = [IO.File]::ReadAllBytes($in)\n"
        "$o = New-Object Windows.Forms.DataObject\n"
        f"$o.SetData('{CUSTOM_FORMAT}', "
        "(New-Object IO.MemoryStream -ArgumentList (,$b)))\n"
        "[Windows.Forms.Clipboard]::SetDataObject($o, $true, 10, 100)"
    ),
}

# The raw mechanism without the library, in its own process.
RAW_EMPTY = r"""
import ctypes, json, time
u = ctypes.WinDLL("user32", use_last_error=True)
u.OpenClipboard.argtypes = [ctypes.c_void_p]
started = time.monotonic()
opened = False
while time.monotonic() - started < 15:
    if u.OpenClipboard(None):
        opened = True
        break
    time.sleep(0.05)
report = {"opened": opened, "open_error": 0 if opened else ctypes.get_last_error()}
if opened:
    try:
        emptied = bool(u.EmptyClipboard())
        report["emptied"] = emptied
        report["empty_error"] = 0 if emptied else ctypes.get_last_error()
    finally:
        report["closed"] = bool(u.CloseClipboard())
print(json.dumps(report))
"""


def produce(name: str, payload: str | bytes = "") -> dict:
    """Run one independent PowerShell producer; record exit and stderr."""
    try:
        result = powershell(CLEAR_PRODUCERS[name], payload)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"producer": name, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "producer": name,
        "returncode": result.returncode,
        "stderr": result.stderr.strip()[-1000:],
    }


def _python(args: list[str], timeout: float = 60) -> dict:
    started = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, *args],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
    run = {
        "returncode": result.returncode,
        "stderr": result.stderr.strip()[-1000:],
        "elapsed_s": round(time.monotonic() - started, 3),
    }
    try:
        run["report"] = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError):
        run["report"] = None
        run["stdout"] = result.stdout.strip()[-1000:]
    return run


def consumer_formats() -> dict:
    """Independent ctypes consumer: the offered formats (names or CF ids)."""
    run = _python([str(CONSUMER)])
    report = run.get("report") or {}
    run["formats"] = report.get("formats")
    return run


def raw_empty() -> dict:
    """Early probe: raw ``OpenClipboard(NULL)`` + ``EmptyClipboard`` process."""
    return _python(["-I", "-c", RAW_EMPTY])


class Holder:
    """``windows_clipboard_holder.py`` holding the clipboard for ``seconds``."""

    def __init__(self, seconds: float):
        self.seconds = seconds
        self.proc = subprocess.Popen(
            [sys.executable, str(HOLDER), str(seconds)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.ready = json.loads(self.proc.stdout.readline() or "{}")

    def released(self) -> dict:
        try:
            out, err = self.proc.communicate(timeout=self.seconds + 30)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            out, err = self.proc.communicate()
        lines = [line for line in out.splitlines() if line.strip()]
        try:
            report = json.loads(lines[-1]) if lines else {}
        except ValueError:
            report = {"stdout": out[-1000:]}
        return {**report, "exit": self.proc.returncode, "stderr": err.strip()[-500:]}


def offers(formats: list | None, needles) -> bool:
    """Whether a consumer listing names every one of ``needles``."""
    return formats is not None and all(n in formats for n in needles)


def offers_any(formats: list | None, needles) -> bool:
    """Whether a consumer listing names at least one of ``needles``."""
    return formats is not None and any(n in formats for n in needles)


def no_formats(observed: dict) -> bool:
    """The consumer ran and enumerated no formats (empty clipboard)."""
    return observed.get("returncode") == 0 and observed.get("formats") == []


def held_past_bound() -> dict:
    """Step 7: held past the bound, child ``clear()`` raises; formats remain."""
    from clipboard import _offer_windows

    bound = _offer_windows._OPEN_CLIPBOARD_TIMEOUT_S
    produced = produce("html_and_text", PROBE_HTML)
    before = consumer_formats()
    holder = Holder(bound + HOLD_PAST_BOUND_S)
    cleared = child_clear()
    released = holder.released()
    after = consumer_formats()
    outcome = cleared.get("outcome") or {}
    message = outcome.get("message", "")
    elapsed = cleared.get("elapsed_s", 0.0)
    return step(
        "7_holder_past_bound_raises_and_prior_formats_remain",
        produced.get("returncode") == 0
        and offers(before.get("formats"), HTML_TEXT_FORMATS)
        and holder.ready.get("ready") is True
        and holder.ready.get("holds_at_ready") is True
        and cleared.get("returncode") == 3
        and outcome.get("raised") == "ClipboardContentError"
        and "held by another process" in message
        and "clearing the clipboard" in message
        and bound <= elapsed < holder.seconds
        and released.get("released") is True
        and released.get("holds_before_release") is True
        and offers(after.get("formats"), HTML_TEXT_FORMATS),
        library_bound_s=bound,
        producer=produced,
        consumer_before=before,
        holder_ready=holder.ready,
        holder_seconds=holder.seconds,
        child_clear=cleared,
        holder_released=released,
        consumer_after_release=after,
    )


def held_within_bound() -> dict:
    """Step 8: a holder released within the bound; child ``clear()`` empties."""
    from clipboard import _offer_windows

    bound = _offer_windows._OPEN_CLIPBOARD_TIMEOUT_S
    before = consumer_formats()
    holder = Holder(SHORT_HOLD_S)
    cleared = child_clear()
    released = holder.released()
    after = consumer_formats()
    return step(
        "8_holder_released_within_bound_then_clear_succeeds",
        offers(before.get("formats"), HTML_TEXT_FORMATS)
        and holder.ready.get("ready") is True
        and holder.ready.get("holds_at_ready") is True
        and child_cleared(cleared)
        and cleared.get("elapsed_s", bound) < bound
        and released.get("released") is True
        and released.get("holds_before_release") is True
        and no_formats(after),
        library_bound_s=bound,
        consumer_before=before,
        holder_ready=holder.ready,
        holder_seconds=holder.seconds,
        child_clear=cleared,
        holder_released=released,
        consumer_after=after,
    )
