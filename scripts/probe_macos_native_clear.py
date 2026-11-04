#!/usr/bin/env python3
"""Independent-producer probe: macOS Aqua offer → child clipboard.clear().

**Independent** producers (osascript / AppKit, not clipboard.*) place an
HTML+text dual offer and, separately, a PNG-only offer on the general
pasteboard. A **child** Python process calls ``clipboard.clear()`` and exits
(``native_clear_support.child_clear``). Each case then ends in the shared
``native_clear_support.cleared_step`` rule: an **independent** consumer (JXA
``NSPasteboard types``, a different script stack from the library's
AppleScriptObjC) lists no types, ``pbpaste`` (a second independent consumer)
prints nothing, and this process's public readers read absence. Also probes
``clear()`` twice on a cleared pasteboard (two child clears) and the
``copy("")`` versus ``clear()`` contrast. Then an independent JXA producer
writes a ``public.file-url`` (``NSURL fileURLWithPath:`` of an existing temp
file) and, separately, only an unknown ``com.example.clipboard-probe`` type;
each is followed by a child ``clear()`` and the same rule.

Privacy prompts: the probe cannot see the screen. It records the screen-lock
state, whether each child ``clear()`` finished within its bound (from the
child records), and how long it took; an on-screen prompt stays an evidence
limit unless the operator watched the screen.

Prints one JSON object on stdout. Exit 0 when every case passes. Requires
darwin and ``clipboard[images]`` (for ``paste_image``). Does not run under
default pytest. **Replaces the live clipboard.**
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from macos_native_clear_support import (
    copy_empty_in_child,
    independent_listing,
    list_types_independent,
    no_offer,
    produce_custom_type_independent,
    produce_file_url_independent,
    session_state,
)
from macos_native_inspect_support import (
    produce_html_text_independent,
    produce_image_only_independent,
)
from native_clear_support import CHILD_TIMEOUT_S, child_clear, cleared_step
from native_probe_common import macos_environment, require_darwin_and_images

CLEAR_RECORD_KEYS = ("child_clear", "first", "second")


def _cleared(name: str, *, held: bool = True, clears: tuple, **observed) -> dict:
    """The shared "cleared" rule on the JXA listing + ``pbpaste``."""
    result = cleared_step(
        name, independent_listing, no_offer, held=held, clears=clears, **observed
    )
    result["case"] = result.pop("step")
    return result


def _produced_case(name: str, produce, expected: tuple[str, ...]) -> dict:
    produce()
    before = list_types_independent()
    produced_ok = all(t in before["types"] for t in expected)
    cleared = child_clear()
    return _cleared(
        name,
        held=produced_ok,
        clears=(cleared,),
        types_before=before["types"],
        change_count_before=before["changeCount"],
        produced_ok=produced_ok,
        child_clear=cleared,
    )


def _twice_case() -> dict:
    first = child_clear()
    second = child_clear()
    return _cleared(
        "clear_twice_on_cleared", clears=(first, second), first=first, second=second
    )


def _copy_empty_contrast_case() -> dict:
    copy_child = copy_empty_in_child()
    after_copy = list_types_independent()
    has_text_type = "public.utf8-plain-text" in after_copy["types"]
    cleared = child_clear()
    return _cleared(
        "copy_empty_vs_clear",
        held=copy_child.get("returncode") == 0 and has_text_type,
        clears=(cleared,),
        child_copy_empty=copy_child,
        types_after_copy_empty=after_copy["types"],
        copy_empty_left_text_offer=has_text_type,
        child_clear=cleared,
    )


CUSTOM_UTI = "com.example.clipboard-probe"


def _file_url_case() -> dict:
    with tempfile.TemporaryDirectory(prefix="clipboard-clear-probe-") as raw:
        listed = Path(raw) / "clear probe file.txt"
        listed.write_text("clear probe file\n", encoding="utf-8")
        case = _produced_case(
            "file_url",
            lambda: produce_file_url_independent(str(listed)),
            ("public.file-url",),
        )
        case["file_path"] = str(listed)
        case["file_existed"] = listed.is_file()
        case["ok"] = case["ok"] and case["file_existed"]
        return case


def _custom_type_case() -> dict:
    return _produced_case(
        "unknown_custom_type",
        lambda: produce_custom_type_independent(CUSTOM_UTI, "clear probe bytes"),
        (CUSTOM_UTI,),
    )


def _within_bound(cases: list[dict]) -> bool:
    runs = [case[key] for case in cases for key in CLEAR_RECORD_KEYS if key in case]
    return bool(runs) and all(
        "error" not in run and run["elapsed_s"] <= CHILD_TIMEOUT_S for run in runs
    )


def main() -> None:
    require_darwin_and_images()
    import clipboard

    for reset in (
        clipboard.set_text_clipboard_writer,
        clipboard.set_text_clipboard_reader,
        clipboard.set_html_clipboard_reader,
        clipboard.set_clipboard_inspector,
        clipboard.set_files_clipboard_reader,
        clipboard.set_clipboard_clearer,
    ):
        reset(None)
    session_before = session_state()
    cases = [
        _produced_case(
            "html_and_text",
            produce_html_text_independent,
            ("public.html", "public.utf8-plain-text"),
        ),
        _produced_case("png_only", produce_image_only_independent, ("public.png",)),
        _twice_case(),
        _copy_empty_contrast_case(),
        _file_url_case(),
        _custom_type_case(),
    ]
    session_after = session_state()
    env = macos_environment(
        producer=(
            "osascript AppKit NSPasteboardTypeHTML + NSPasteboardTypeString; "
            "osascript AppKit NSPasteboardTypePNG; JXA writeObjects NSURL "
            "file URL and setData:forType: com.example.clipboard-probe "
            "(independent of clipboard.*)"
        ),
        library_under_test="clipboard.clear() in a child Python that exits",
        type_consumer="osascript -l JavaScript NSPasteboard.generalPasteboard.types",
        text_consumer="pbpaste",
        helper="osascript + pbpaste (macOS built-in)",
    )
    ok = all(case["ok"] for case in cases)
    report = {
        "ok": ok,
        "environment": env,
        "floors": {
            "macos_product": env["macos_product"],
            "macos_build": env["macos_build"],
            "machine": env["machine"],
            "method": "osascript AppKit NSPasteboard clearContents (general)",
        },
        "session": {"before": session_before, "after": session_after},
        "cases": {case["case"]: case for case in cases},
        "privacy_prompt": {
            "every_child_clear_finished_within_bound": _within_bound(cases),
            "bound_s": CHILD_TIMEOUT_S,
            "on_screen_prompt": (
                "not observable by this probe; evidence limit unless the "
                "operator watched the screen"
            ),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
