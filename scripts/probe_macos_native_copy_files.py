#!/usr/bin/env python3
"""Independent-consumer probe: clipboard.copy_files → macOS file-URL pasteboard.

Default run (temporary sources, removed afterwards):

1. Seed example 2 natively: an independent producer (``pbcopy``) sets the
   text ``keep``; in-process ``copy_files([existing, "missing.txt"])`` must
   raise ``ClipboardContentError`` naming ``missing.txt``; an independent
   consumer (``pbpaste``) must still return ``keep``.
2. Seed example 1 offer level: two sources whose names contain Unicode and
   spaces are copied by the public ``copy_files`` in a child Python process
   that **exits**; an independent ``osascript`` consumer (not this library)
   reads each pasteboard item's ``public.file-url`` and the decoded paths must
   equal the absolute source paths, in order, and must still do so at the
   same changeCount on rechecks up to 20 s after the writer exited (60 s in
   ``--leave-offer`` mode). ``paste_files()`` agreement is
   recorded as a consistency check only. Sources must be unchanged.
3. A further offer-level round (default probe only): from a child whose cwd is
   the source folder, ``copy_files(["report final.pdf", "a dir",
   "report final.pdf"])`` (relative file, directory, duplicate). The same
   independent ``osascript`` consumer must read three absolute paths in that
   order; ``paste_files()`` agrees. No Finder paste for this round.

``--leave-offer DIR`` writes the two sources into DIR, copies them the same
way, checks the offer with the independent consumer for 60 s, and leaves both
the files and the offer in place for a developer-operated Finder paste.
``--check-offer`` only reports what the independent consumer sees now
(changeCount, types, file URLs, and this process's pasteboard access policy).

Prints one JSON object on stdout. Exit 0 on success; non-zero on failure.
Requires darwin. Does not run under default pytest.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from macos_native_copy_files_support import (
    ACCESS_BEHAVIORS,
    LEAVE_OFFER_RECHECKS_S,
    PROBE_RECHECKS_S,
    copy_and_observe,
    independent_file_url_consumer,
    missing_path_keeps_prior_text,
    relative_directory_duplicate_round,
    write_sources,
)
from native_probe_common import die, macos_environment


def floors(env: dict) -> dict:
    return {
        "macos_product": env["macos_product"],
        "macos_build": env["macos_build"],
        "darwin_release": env["os_release"],
        "machine": env["machine"],
        "python": env["python"],
        "osascript": shutil.which("osascript"),
        "method": env["write_method"],
    }


def environment() -> dict:
    return macos_environment(
        write_method=(
            "clipboard.copy_files default writer → osascript JXA AppKit "
            "NSPasteboard clearContents + writeObjects: file NSURLs"
        ),
        consumer=(
            "osascript JXA pasteboardItems stringForType public.file-url "
            "(independent of clipboard library)"
        ),
    )


def leave_offer(directory: Path) -> None:
    paths = write_sources(directory.absolute())
    run = copy_and_observe(paths, LEAVE_OFFER_RECHECKS_S)
    ok = (
        run["independent_paths_equal"]
        and run["offer_held_after_exit"]
        and run["sources_unchanged"]
    )
    env = environment()
    report = {
        "ok": ok,
        "mode": "leave-offer",
        "environment": env,
        "floors": floors(env),
        "expected_paths": paths,
        **run,
        "next": (
            "Offer left on the pasteboard. In Finder, open a different folder "
            "and press Cmd+V; expect copies of both files and these sources "
            "unchanged (compare size/mtime_ns/sha256). Before and after the "
            "paste, run this probe with --check-offer from the same terminal "
            "and compare change_count, types, and access_behavior."
        ),
        "final_change_count": run["rechecks_after_exit"][-1]["change_count"],
        "final_types": run["rechecks_after_exit"][-1]["types"],
    }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if not ok:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--leave-offer",
        metavar="DIR",
        type=Path,
        help="write the sources into DIR and leave their offer on the pasteboard",
    )
    parser.add_argument(
        "--check-offer",
        action="store_true",
        help="only print what the independent consumer sees now (no writes)",
    )
    args = parser.parse_args()

    if sys.platform != "darwin":
        die(f"probe requires macOS (darwin); got {sys.platform!r}")
    try:
        import clipboard  # noqa: F401
    except ImportError as exc:
        die(f"missing clipboard import: {exc}")

    if args.check_offer:
        seen = independent_file_url_consumer()
        seen["access_behavior"] = ACCESS_BEHAVIORS.get(
            seen["access_behavior"], seen["access_behavior"]
        )
        seen["mode"] = "check-offer"
        print(json.dumps(seen, indent=2, sort_keys=True, ensure_ascii=False))
        return
    if args.leave_offer is not None:
        leave_offer(args.leave_offer)
        return

    with tempfile.TemporaryDirectory(prefix="clipboard-copy-files-probe-") as raw:
        tmpdir = Path(raw)
        source = tmpdir / "sources"
        paths = write_sources(source)
        missing = missing_path_keeps_prior_text(paths[0], source)
        run = copy_and_observe(paths, PROBE_RECHECKS_S)
        relative_round = relative_directory_duplicate_round(source)

    ok = (
        missing["error_names_missing"]
        and missing["prior_text_survived"]
        and run["independent_paths_equal"]
        and run["offer_held_after_exit"]
        and run["paste_files_agrees"]
        and run["sources_unchanged"]
        and relative_round["independent_paths_equal"]
        and relative_round["paste_files_agrees"]
        and relative_round["writer"]["exited"] is True
    )
    env = environment()
    report = {
        "ok": ok,
        "mode": "probe",
        "environment": env,
        "floors": floors(env),
        "expected_paths": paths,
        "missing_path": missing,
        **run,
        "relative_directory_duplicate": relative_round,
        "commitments": {
            "independent_consumer": (
                "osascript JXA public.file-url per pasteboard item "
                "(not clipboard.paste_files)"
            ),
            "writer_exit": "copy_files ran in a child Python that exited first",
            "held_after_exit": (
                "independent rechecks at PROBE_RECHECKS_S see the same "
                "changeCount, public.file-url, and paths"
            ),
            "relative_directory_duplicate": (
                "further offer: relative file + directory + duplicate from "
                "source cwd; osascript public.file-url; no Finder paste"
            ),
            "prior_text": "pbcopy producer / pbpaste consumer (not this library)",
            "consistency_only": "paste_files() agreement is not interop proof",
            "authorization": "normal macOS pasteboard; no entitlement bypass",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
