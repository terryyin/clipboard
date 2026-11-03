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
``clear()`` twice on the cleared clipboard succeeds. Steps 2-6 end in the
shared ``native_clear_support.cleared_step`` rule with the consumer listing
and its no-formats predicate. Step 7: a holder process
(``windows_clipboard_holder.py``, its own window) keeps the clipboard open
past the library's 15 s bound; a child ``clear()`` raises
``ClipboardContentError`` naming the held clipboard before the holder lets
go, and after the release the consumer still lists the prior formats.
Step 8: a holder that releases within the bound; the child ``clear()``
succeeds and the consumer lists no formats. Steps 7-8 live in
``windows_native_clear_support``.

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

from native_clear_support import child_clear, cleared_step, report, step
from windows_native_clear_support import (
    CF_BITMAP,
    CF_DIB,
    CF_DIBV5,
    CF_HDROP,
    CUSTOM_FORMAT,
    HTML_TEXT_FORMATS,
    PROBE_HTML,
    consumer_formats,
    held_past_bound,
    held_within_bound,
    no_formats,
    offers,
    offers_any,
    produce,
    raw_empty,
)


def _early_raw_empty() -> dict:
    produced = produce("html_and_text", PROBE_HTML)
    before = consumer_formats()
    raw = raw_empty()
    after = consumer_formats()
    outcome = raw.get("report") or {}
    return step(
        "1_early_raw_empty_clipboard_leaves_no_formats",
        produced.get("returncode") == 0
        and offers(before.get("formats"), HTML_TEXT_FORMATS)
        and outcome.get("emptied") is True
        and outcome.get("closed") is True
        and no_formats(after),
        producer=produced,
        consumer_before=before,
        raw_empty=raw,
        consumer_after=after,
    )


def _produced_then_child_clear(name, producer, payload, offered) -> dict:
    produced = produce(producer, payload)
    before = consumer_formats()
    cleared = child_clear()
    return cleared_step(
        name,
        consumer_formats,
        no_formats,
        held=produced.get("returncode") == 0 and offered(before.get("formats")),
        clears=(cleared,),
        producer=produced,
        consumer_before=before,
        child_clear=cleared,
    )


def _file_list_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="clipboard-clear-probe-") as raw:
        listed = Path(raw) / "clear probe file.txt"
        listed.write_text("clear probe file\n", encoding="utf-8")
        result = _produced_then_child_clear(
            "4_file_list_producer_then_child_clear_reads_empty",
            "file_list",
            str(listed),
            lambda formats: offers(formats, (CF_HDROP,)),
        )
        result["file_path"] = str(listed)
        result["file_existed"] = listed.is_file()
        result["ok"] = result["ok"] and result["file_existed"]
        return result


def _clear_twice() -> dict:
    first = child_clear()
    second = child_clear()
    return cleared_step(
        "6_clear_twice_on_cleared_succeeds",
        consumer_formats,
        no_formats,
        clears=(first, second),
        first=first,
        second=second,
    )


def _probe() -> list[dict]:
    return [
        _early_raw_empty(),
        _produced_then_child_clear(
            "2_html_and_text_producer_then_child_clear_reads_empty",
            "html_and_text",
            PROBE_HTML,
            lambda formats: offers(formats, HTML_TEXT_FORMATS),
        ),
        _produced_then_child_clear(
            "3_image_producer_then_child_clear_reads_empty",
            "image_only",
            "",
            lambda formats: offers_any(formats, (CF_DIB, CF_DIBV5, CF_BITMAP)),
        ),
        _file_list_case(),
        _produced_then_child_clear(
            "5_custom_format_producer_then_child_clear_reads_empty",
            "custom_format",
            b"clear probe custom bytes",
            lambda formats: offers(formats, (CUSTOM_FORMAT,)),
        ),
        _clear_twice(),
        held_past_bound(),
        held_within_bound(),
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
