#!/usr/bin/env python3
"""Independent-producer probe: macOS file-list pasteboard → clipboard.paste_files().

Creates two local files (Unicode + spaces), places them on the pasteboard via
osascript ``NSFilenamesPboardType`` (Finder-equivalent independent producer —
not ``paste_files`` / same-library round-trip), then consumes with
``paste_files()`` using the Darwin default reader. Proves non-mutation via a
second ``paste_files()`` and an independent AppKit re-read, and proves no
filesystem open/modify via mtime/size floors.

Prints one JSON object on stdout. Exit 0 on success; non-zero on failure.
Requires darwin. Does not run under default pytest.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from native_probe_common import die, macos_environment

# Contended pasteboard must not hang the probe indefinitely.
_OSASCRIPT_TIMEOUT_S = 30


def _escape_as_literal(path: str) -> str:
    return path.replace("\\", "\\\\").replace('"', '\\"')


def _place_filenames_on_pasteboard(paths: list[str]) -> None:
    """Independent producer: AppKit filename list, not this library."""
    lines = [
        'use framework "AppKit"',
        'use framework "Foundation"',
        "use scripting additions",
        ("set pb to current application's NSPasteboard's generalPasteboard()"),
        "pb's clearContents()",
        "set arr to current application's NSMutableArray's array()",
    ]
    for path in paths:
        lines.append(f'arr\'s addObject:"{_escape_as_literal(path)}"')
    lines.extend(
        [
            ("set fnameType to current application's NSFilenamesPboardType"),
            "pb's declareTypes:{fnameType} owner:(missing value)",
            "set ok to pb's setPropertyList:arr forType:fnameType",
            (
                "if ok is false then error "
                '"NSPasteboard refused NSFilenamesPboardType offer"'
            ),
            'return "ok"',
        ]
    )
    with tempfile.TemporaryDirectory(prefix="clipboard-files-probe-write-") as raw:
        script_path = Path(raw) / "place_files.applescript"
        script_path.write_text("\n".join(lines), encoding="utf-8")
        try:
            result = subprocess.run(
                ["osascript", str(script_path)],
                capture_output=True,
                text=True,
                timeout=_OSASCRIPT_TIMEOUT_S,
                check=False,
            )
        except subprocess.TimeoutExpired:
            die("osascript pasteboard write timed out")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        die(f"osascript pasteboard write failed: {detail}")


def _independent_filenames_consumer() -> list[str] | None:
    """Re-read NSFilenamesPboardType without clipboard.paste_files."""
    script = "\n".join(
        [
            'use framework "AppKit"',
            'use framework "Foundation"',
            "use scripting additions",
            ("set pb to current application's NSPasteboard's generalPasteboard()"),
            (
                "set names to pb's propertyListForType:"
                "(current application's NSFilenamesPboardType)"
            ),
            'if names is missing value then return "NONE"',
            (
                "set jsonData to current application's "
                "NSJSONSerialization's dataWithJSONObject:names "
                "options:0 |error|:(missing value)"
            ),
            ('if jsonData is missing value then error "JSON encode failed"'),
            (
                "set jsonStr to (current application's NSString's "
                "alloc()'s initWithData:jsonData encoding:"
                "(current application's NSUTF8StringEncoding))"
            ),
            "return jsonStr as text",
        ]
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=_OSASCRIPT_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        die("independent filenames consumer timed out")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        die(f"independent filenames consumer failed: {detail}")
    out = (result.stdout or "").strip()
    if not out or out == "NONE":
        return None
    try:
        paths = json.loads(out)
    except json.JSONDecodeError as exc:
        die(f"independent consumer returned non-JSON: {out!r}: {exc}")
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        die(f"independent consumer returned unexpected shape: {paths!r}")
    return paths


def _stat_floor(path: Path) -> dict:
    st = path.stat()
    return {"size": st.st_size, "mtime_ns": st.st_mtime_ns}


def main() -> None:
    if sys.platform != "darwin":
        die(f"probe requires macOS (darwin); got {sys.platform!r}")

    try:
        import clipboard
    except ImportError as exc:
        die(f"missing clipboard import: {exc}")

    with tempfile.TemporaryDirectory(prefix="clipboard-macos-files-probe-") as raw:
        tmpdir = Path(raw)
        first = tmpdir / "plain.txt"
        second = tmpdir / "café space.txt"
        first.write_text("alpha\n", encoding="utf-8")
        second.write_text("bravo\n", encoding="utf-8")
        expected = [str(first.resolve()), str(second.resolve())]
        before = {p: _stat_floor(Path(p)) for p in expected}

        clipboard.set_files_clipboard_reader(None)
        _place_filenames_on_pasteboard(expected)

        first_paste = clipboard.paste_files()
        second_paste = clipboard.paste_files()
        independent = _independent_filenames_consumer()
        after = {p: _stat_floor(Path(p)) for p in expected}

    files_unchanged = before == after
    paths_ok = first_paste == expected
    preservative = first_paste == second_paste and first_paste is not None
    independent_ok = independent == expected
    ok = paths_ok and preservative and independent_ok and files_unchanged

    env = macos_environment(
        pasteboard_method=(
            "osascript AppKit NSFilenamesPboardType "
            "(Finder-equivalent independent producer)"
        ),
        consumer=("clipboard.paste_files() with set_files_clipboard_reader(None)"),
    )
    floors = {
        "macos_product": env["macos_product"],
        "macos_build": env["macos_build"],
        "os_release": env["os_release"],
        "machine": env["machine"],
        "python": env["python"],
        "method": env["pasteboard_method"],
    }
    report = {
        "ok": ok,
        "environment": env,
        "floors": floors,
        "expected_paths": expected,
        "first_paste": first_paste,
        "second_paste": second_paste,
        "independent_consumer": independent,
        "preservative": preservative,
        "independent_still_sees_offer": independent_ok,
        "files_unchanged": files_unchanged,
        "set_files_clipboard_reader": None,
        "commitments": {
            "independent_producer": (
                "osascript NSFilenamesPboardType "
                "(Finder-equivalent; not paste_files round-trip)"
            ),
            "consumer": "clipboard.paste_files() default Darwin reader",
            "non_mutation": (
                "second paste_files + independent AppKit filenames re-read"
            ),
            "no_filesystem_side_effects": (
                "mtime_ns/size unchanged on referenced files"
            ),
            "authorization": "normal macOS pasteboard; no entitlement bypass",
            "unicode_and_spaces": "café space.txt included in offer",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
