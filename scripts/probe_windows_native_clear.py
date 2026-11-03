#!/usr/bin/env python3
"""Gated probe: Windows desktop ``clear()`` against independent processes.

Step 1 is the early probe of the mechanism, without the library: an
independent PowerShell / .NET producer offers HTML + text, a separate Python
process runs the raw ``OpenClipboard(NULL)`` / ``EmptyClipboard`` /
``CloseClipboard``, and the independent ctypes consumer
(``windows_clipboard_consumer.py``) enumerates no formats.

Steps 2-5: an independent producer of HTML + text, an image, a ``CF_HDROP``
file list naming an existing temp file, and only an unknown registered
format (``ClipboardProbe.Custom``); each is followed by ``clipboard.clear()``
in a child Python that exits, then the consumer lists no formats and this
process's readers read absence (``inspect()`` empty, ``paste()`` ``""``,
``paste_html()`` / ``paste_files()`` / ``paste_image()`` ``None``). Step 6:
``clear()`` twice on the cleared clipboard succeeds. Step 7: a holder process
(``windows_clipboard_holder.py``, its own window) keeps the clipboard open
past the library's 15 s bound; a child ``clear()`` raises
``ClipboardContentError`` naming the held clipboard before the holder lets
go, and after the release the consumer still lists the prior formats.
Step 8: a holder that releases within the bound; the child ``clear()``
succeeds and the consumer lists no formats.

Prints one JSON object on stdout with the runner image and OS version.
Exit 0 when every step holds, 1 naming the failed steps, and 2 with
``evidence_limit`` off ``win32`` (the wrapper fails on it; never a skip or a
silent verified success). Requires ``clipboard[images]`` for
``paste_image``. Not run by default pytest. **Replaces the live clipboard.**
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from native_clear_support import (
    child_clear,
    child_cleared,
    read_everything,
    reads_empty,
    report,
    step,
)
from windows_native_clear_support import (
    CF_BITMAP,
    CF_DIB,
    CF_DIBV5,
    CF_HDROP,
    CF_UNICODETEXT,
    CUSTOM_FORMAT,
    HTML_FORMAT,
    PROBE_HTML,
    Holder,
    consumer_formats,
    produce,
    raw_empty,
)

HTML_TEXT_FORMATS = (HTML_FORMAT, CF_UNICODETEXT)
# Margin past the library's OpenClipboard bound for the long holder.
HOLD_PAST_BOUND_S = 10.0
SHORT_HOLD_S = 3.0


def _offers(formats: list | None, needles) -> bool:
    return formats is not None and all(n in formats for n in needles)


def _offers_any(formats: list | None, needles) -> bool:
    return formats is not None and any(n in formats for n in needles)


def _no_formats(observed: dict) -> bool:
    return observed.get("returncode") == 0 and observed.get("formats") == []


def _early_raw_empty() -> dict:
    produced = produce("html_and_text", PROBE_HTML)
    before = consumer_formats()
    raw = raw_empty()
    after = consumer_formats()
    outcome = raw.get("report") or {}
    return step(
        "1_early_raw_empty_clipboard_leaves_no_formats",
        produced.get("returncode") == 0
        and _offers(before.get("formats"), HTML_TEXT_FORMATS)
        and outcome.get("emptied") is True
        and outcome.get("closed") is True
        and _no_formats(after),
        producer=produced,
        consumer_before=before,
        raw_empty=raw,
        consumer_after=after,
    )


def _produced_then_child_clear(name, producer, payload, offered) -> dict:
    produced = produce(producer, payload)
    before = consumer_formats()
    cleared = child_clear()
    after = consumer_formats()
    reads = read_everything()
    return step(
        name,
        produced.get("returncode") == 0
        and offered(before.get("formats"))
        and child_cleared(cleared)
        and _no_formats(after)
        and reads_empty(reads),
        producer=produced,
        consumer_before=before,
        child_clear=cleared,
        consumer_after=after,
        reads=reads,
    )


def _file_list_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="clipboard-clear-probe-") as raw:
        listed = Path(raw) / "clear probe file.txt"
        listed.write_text("clear probe file\n", encoding="utf-8")
        result = _produced_then_child_clear(
            "4_file_list_producer_then_child_clear_reads_empty",
            "file_list",
            str(listed),
            lambda formats: _offers(formats, (CF_HDROP,)),
        )
        result["file_path"] = str(listed)
        result["file_existed"] = listed.is_file()
        result["ok"] = result["ok"] and result["file_existed"]
        return result


def _clear_twice() -> dict:
    first = child_clear()
    second = child_clear()
    after = consumer_formats()
    reads = read_everything()
    return step(
        "6_clear_twice_on_cleared_succeeds",
        child_cleared(first)
        and child_cleared(second)
        and _no_formats(after)
        and reads_empty(reads),
        first=first,
        second=second,
        consumer_after=after,
        reads=reads,
    )


def _held_past_bound() -> dict:
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
        and _offers(before.get("formats"), HTML_TEXT_FORMATS)
        and holder.ready.get("ready") is True
        and holder.ready.get("holds_at_ready") is True
        and cleared.get("returncode") == 3
        and outcome.get("raised") == "ClipboardContentError"
        and "held by another process" in message
        and "clearing the clipboard" in message
        and bound <= elapsed < holder.seconds
        and released.get("released") is True
        and released.get("holds_before_release") is True
        and _offers(after.get("formats"), HTML_TEXT_FORMATS),
        library_bound_s=bound,
        producer=produced,
        consumer_before=before,
        holder_ready=holder.ready,
        holder_seconds=holder.seconds,
        child_clear=cleared,
        holder_released=released,
        consumer_after_release=after,
    )


def _held_within_bound() -> dict:
    from clipboard import _offer_windows

    bound = _offer_windows._OPEN_CLIPBOARD_TIMEOUT_S
    before = consumer_formats()
    holder = Holder(SHORT_HOLD_S)
    cleared = child_clear()
    released = holder.released()
    after = consumer_formats()
    return step(
        "8_holder_released_within_bound_then_clear_succeeds",
        _offers(before.get("formats"), HTML_TEXT_FORMATS)
        and holder.ready.get("ready") is True
        and holder.ready.get("holds_at_ready") is True
        and child_cleared(cleared)
        and cleared.get("elapsed_s", bound) < bound
        and released.get("released") is True
        and released.get("holds_before_release") is True
        and _no_formats(after),
        library_bound_s=bound,
        consumer_before=before,
        holder_ready=holder.ready,
        holder_seconds=holder.seconds,
        child_clear=cleared,
        holder_released=released,
        consumer_after=after,
    )


def _probe() -> list[dict]:
    return [
        _early_raw_empty(),
        _produced_then_child_clear(
            "2_html_and_text_producer_then_child_clear_reads_empty",
            "html_and_text",
            PROBE_HTML,
            lambda formats: _offers(formats, HTML_TEXT_FORMATS),
        ),
        _produced_then_child_clear(
            "3_image_producer_then_child_clear_reads_empty",
            "image_only",
            "",
            lambda formats: _offers_any(formats, (CF_DIB, CF_DIBV5, CF_BITMAP)),
        ),
        _file_list_case(),
        _produced_then_child_clear(
            "5_custom_format_producer_then_child_clear_reads_empty",
            "custom_format",
            b"clear probe custom bytes",
            lambda formats: _offers(formats, (CUSTOM_FORMAT,)),
        ),
        _clear_twice(),
        _held_past_bound(),
        _held_within_bound(),
    ]


def main() -> int:
    if sys.platform != "win32":
        report(
            ok=False,
            verified=False,
            evidence_limit=True,
            reason=f"not a Windows desktop (platform {sys.platform!r})",
        )
        return 2
    from windows_native_text_support import windows_floors

    import clipboard

    clipboard.set_text_clipboard_writer(None)
    clipboard.set_text_clipboard_reader(None)
    clipboard.set_clipboard_clearer(None)
    steps = _probe()
    failed = [s["step"] for s in steps if not s["ok"]]
    report(
        ok=not failed,
        verified=not failed,
        evidence_limit=False,
        desktop="Windows desktop",
        failed_steps=failed,
        steps=steps,
        environment={
            **windows_floors(),
            "producer": "Windows PowerShell 5.1 System.Windows.Forms.Clipboard",
            "consumer": "ctypes EnumClipboardFormats (windows_clipboard_consumer.py)",
            "holder": "windows_clipboard_holder.py (own STATIC window)",
            "library_under_test": "clipboard.clear() in a child Python that exits",
        },
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
