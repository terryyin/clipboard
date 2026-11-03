#!/usr/bin/env python3
"""Independent-producer probe: macOS Aqua offer → child clipboard.clear().

**Independent** producers (osascript / AppKit, not clipboard.*) place an
HTML+text dual offer and, separately, a PNG-only offer on the general
pasteboard. A **child** Python process calls ``clipboard.clear()`` and exits.
An **independent** consumer (JXA ``NSPasteboard types``, a different script
stack from the library's AppleScriptObjC) then lists the types, and ``pbpaste``
reads text. This process's public readers run afterwards as a consistency
check. Also probes ``clear()`` twice on a cleared pasteboard and the
``copy("")`` versus ``clear()`` contrast. Then an independent JXA producer
writes a ``public.file-url`` (``NSURL fileURLWithPath:`` of an existing temp
file) and, separately, only an unknown ``com.example.clipboard-probe`` type;
each is followed by a child ``clear()``, the independent type list is empty
and ``paste_files()`` is ``None``.

Privacy prompts: the probe cannot see the screen. It records the screen-lock
state, whether each child ``clear()`` finished within its bound, and how long
it took; an on-screen prompt stays an evidence limit unless the operator
watched the screen.

Prints one JSON object on stdout. Exit 0 when every case passes. Requires
darwin and ``clipboard[images]`` (for ``paste_image``). Does not run under
default pytest. **Replaces the live clipboard.**
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from macos_native_clear_support import (
    CHILD_TIMEOUT_S,
    clear_in_child,
    copy_empty_in_child,
    list_types_independent,
    produce_custom_type_independent,
    produce_file_url_independent,
    session_state,
)
from macos_native_inspect_support import (
    consume_text_independent,
    produce_html_text_independent,
    produce_image_only_independent,
)
from native_probe_common import macos_environment, require_darwin_and_images


def readers_in_parent() -> dict:
    """Consistency check through this process's public readers."""
    import clipboard

    for reset in (
        clipboard.set_html_clipboard_reader,
        clipboard.set_clipboard_inspector,
        clipboard.set_files_clipboard_reader,
    ):
        reset(None)
    snap = clipboard.inspect()
    html = clipboard.paste_html()
    text = clipboard.paste()
    files = clipboard.paste_files()
    image = clipboard.paste_image()
    return {
        "inspect_kinds": sorted(snap.kinds),
        "inspect_formats": list(snap.formats),
        "paste_html_is_none": html is None,
        "paste": text,
        "paste_files_is_none": files is None,
        "paste_image_is_none": image is None,
    }


def _empty_after(readers: dict, types: dict, pbpaste: str) -> bool:
    return (
        types["types"] == []
        and pbpaste == ""
        and readers["inspect_kinds"] == []
        and readers["inspect_formats"] == []
        and readers["paste_html_is_none"]
        and readers["paste"] == ""
        and readers["paste_files_is_none"]
        and readers["paste_image_is_none"]
    )


def _produced_case(name: str, produce, expected: tuple[str, ...]) -> dict:
    produce()
    before = list_types_independent()
    produced_ok = all(t in before["types"] for t in expected)
    child = clear_in_child()
    after = list_types_independent()
    pbpaste = consume_text_independent()
    readers = readers_in_parent()
    ok = produced_ok and _empty_after(readers, after, pbpaste)
    return {
        "case": name,
        "ok": ok,
        "types_before": before["types"],
        "produced_ok": produced_ok,
        "child_clear": child,
        "types_after": after["types"],
        "change_count": [before["changeCount"], after["changeCount"]],
        "pbpaste_after": pbpaste,
        "readers_after": readers,
    }


def _twice_case() -> dict:
    child = clear_in_child(times=2)
    after = list_types_independent()
    return {
        "case": "clear_twice_on_cleared",
        "ok": after["types"] == [],
        "child_clear": child,
        "types_after": after["types"],
    }


def _copy_empty_contrast_case() -> dict:
    copy_child = copy_empty_in_child()
    after_copy = list_types_independent()
    clear_child = clear_in_child()
    after_clear = list_types_independent()
    has_text_type = "public.utf8-plain-text" in after_copy["types"]
    ok = has_text_type and after_clear["types"] == []
    return {
        "case": "copy_empty_vs_clear",
        "ok": ok,
        "child_copy_empty": copy_child,
        "types_after_copy_empty": after_copy["types"],
        "copy_empty_left_text_offer": has_text_type,
        "child_clear": clear_child,
        "types_after_clear": after_clear["types"],
    }


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


def main() -> None:
    require_darwin_and_images()
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
            "every_child_clear_finished_within_bound": True,
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
