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
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

from native_probe_common import die, macos_environment

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAMES = ("report final.pdf", "données é.csv")
SOURCE_BODIES = (b"%PDF-1.4 probe report\n", "col,é\n1,données\n".encode())
PRIOR_TEXT = "keep"
MISSING = "missing.txt"
# Contended pasteboard must not hang the probe indefinitely.
_HELPER_TIMEOUT_S = 30
# Rechecks after the writer exits: the offer must survive a paste-like delay
# at the same changeCount (data still held by the pasteboard server, not by
# the dead writer). Seconds after writer exit.
PROBE_RECHECKS_S = (0, 5, 10, 20)
LEAVE_OFFER_RECHECKS_S = (0, 10, 30, 60)
# NSPasteboardAccessBehavior: a consumer with ask/deny may see no types while
# changeCount is still readable, which is not evidence that the offer vanished.
ACCESS_BEHAVIORS = {0: "default", 1: "ask", 2: "alwaysAllow", 3: "alwaysDeny"}

# Independent consumer: plain AppKit item read, no clipboard-library code.
_CONSUMER_JXA = """
ObjC.import("AppKit");
var pb = $.NSPasteboard.generalPasteboard;
var items = pb.pasteboardItems;
var urls = [];
var n = items.isNil() ? 0 : Number(items.count);
for (var i = 0; i < n; i++) {
  var s = items.objectAtIndex(i).stringForType("public.file-url");
  urls.push(s.isNil() ? null : s.js);
}
var access = null;
try { access = Number(pb.accessBehavior); } catch (e) { access = null; }
JSON.stringify({change_count: Number(pb.changeCount), file_urls: urls,
  types: ObjC.deepUnwrap(pb.types) || [], access_behavior: access});
"""


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=_HELPER_TIMEOUT_S,
            check=False,
            **kwargs,
        )
    except subprocess.TimeoutExpired:
        die(f"{args[0]} timed out after {_HELPER_TIMEOUT_S}s")
    except OSError as exc:
        die(f"could not run {args[0]}: {exc}")


def _independent_file_url_consumer() -> dict:
    result = _run(["osascript", "-l", "JavaScript", "-e", _CONSUMER_JXA])
    if result.returncode != 0:
        die(f"independent file-URL consumer failed: {result.stderr.strip()}")
    observed = json.loads(result.stdout)
    paths = []
    for url in observed["file_urls"]:
        if url is None:
            paths.append(None)
            continue
        parts = urlsplit(url)
        path = unquote(parts.path) if parts.scheme == "file" else None
        if path and len(path) > 1:
            path = path.rstrip("/")
        paths.append(path)
    observed["paths"] = paths
    return observed


def _pbcopy(text: str) -> None:
    result = _run(["pbcopy"], input=text)
    if result.returncode != 0:
        die(f"independent producer pbcopy failed: {result.stderr.strip()}")


def _pbpaste() -> str:
    result = _run(["pbpaste"])
    if result.returncode != 0:
        die(f"independent consumer pbpaste failed: {result.stderr.strip()}")
    return result.stdout


def _write_sources(directory: Path) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, body in zip(SOURCE_NAMES, SOURCE_BODIES, strict=True):
        target = directory / name
        target.write_bytes(body)
        paths.append(str(target.absolute()))
    return paths


def _fingerprint(path: str) -> dict:
    st = os.stat(path)
    return {
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
    }


def _copy_in_exiting_child(paths: list[str]) -> dict:
    """Run public copy_files with the default writer in a child that exits."""
    code = textwrap.dedent(
        """
        import sys
        import clipboard
        clipboard.set_files_clipboard_writer(None)
        clipboard.copy_files(sys.argv[1:])
        """
    )
    result = _run([sys.executable, "-c", code, *paths], cwd=ROOT)
    if result.returncode != 0:
        die(f"copy_files child failed: {(result.stderr or result.stdout).strip()}")
    return {"returncode": result.returncode, "exited": True}


def _missing_path_keeps_prior_text(existing: str, workdir: Path) -> dict:
    import clipboard

    _pbcopy(PRIOR_TEXT)
    before = _pbpaste()
    clipboard.set_files_clipboard_writer(None)
    previous_cwd = os.getcwd()
    os.chdir(workdir)
    try:
        clipboard.copy_files([existing, MISSING])
    except clipboard.ClipboardContentError as exc:
        error = str(exc)
    else:
        error = None
    finally:
        os.chdir(previous_cwd)
    after = _pbpaste()
    return {
        "prior_text_before": before,
        "error": error,
        "error_names_missing": error is not None and MISSING in error,
        "prior_text_after": after,
        "prior_text_survived": before == PRIOR_TEXT and after == PRIOR_TEXT,
    }


def _floors(env: dict) -> dict:
    return {
        "macos_product": env["macos_product"],
        "macos_build": env["macos_build"],
        "darwin_release": env["os_release"],
        "machine": env["machine"],
        "python": env["python"],
        "osascript": shutil.which("osascript"),
        "method": env["write_method"],
    }


def _recheck_after_exit(paths: list[str], schedule: tuple[int, ...]) -> list[dict]:
    """Independent consumer re-reads at seconds-after-writer-exit marks."""
    start = time.monotonic()
    rechecks = []
    for mark in schedule:
        delay = start + mark - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        seen = _independent_file_url_consumer()
        rechecks.append(
            {
                "t_s": round(time.monotonic() - start, 1),
                "change_count": seen["change_count"],
                "types": seen["types"],
                "access_behavior": ACCESS_BEHAVIORS.get(
                    seen["access_behavior"], seen["access_behavior"]
                ),
                "paths_equal": seen["paths"] == paths,
            }
        )
    return rechecks


def _offer_held(rechecks: list[dict]) -> bool:
    first = rechecks[0]["change_count"]
    return all(
        r["change_count"] == first
        and "public.file-url" in r["types"]
        and r["paths_equal"]
        for r in rechecks
    )


def _copy_and_observe(paths: list[str], schedule: tuple[int, ...]) -> dict:
    import clipboard

    before = {p: _fingerprint(p) for p in paths}
    change_before = _independent_file_url_consumer()["change_count"]
    writer = _copy_in_exiting_child(paths)
    rechecks = _recheck_after_exit(paths, schedule)
    observed = _independent_file_url_consumer()
    clipboard.set_files_clipboard_reader(None)
    pasted = clipboard.paste_files()
    after = {p: _fingerprint(p) for p in paths}
    return {
        "writer": writer,
        "change_count_before": change_before,
        "rechecks_after_exit": rechecks,
        "offer_held_after_exit": _offer_held(rechecks)
        and observed["change_count"] == rechecks[0]["change_count"],
        "independent": observed,
        "independent_paths_equal": observed["paths"] == paths,
        "paste_files": pasted,
        "paste_files_agrees": pasted == paths,
        "sources_before": before,
        "sources_after": after,
        "sources_unchanged": before == after,
    }


def _environment() -> dict:
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


def _leave_offer(directory: Path) -> None:
    paths = _write_sources(directory.absolute())
    run = _copy_and_observe(paths, LEAVE_OFFER_RECHECKS_S)
    ok = (
        run["independent_paths_equal"]
        and run["offer_held_after_exit"]
        and run["sources_unchanged"]
    )
    env = _environment()
    report = {
        "ok": ok,
        "mode": "leave-offer",
        "environment": env,
        "floors": _floors(env),
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
        seen = _independent_file_url_consumer()
        seen["access_behavior"] = ACCESS_BEHAVIORS.get(
            seen["access_behavior"], seen["access_behavior"]
        )
        seen["mode"] = "check-offer"
        print(json.dumps(seen, indent=2, sort_keys=True, ensure_ascii=False))
        return
    if args.leave_offer is not None:
        _leave_offer(args.leave_offer)
        return

    with tempfile.TemporaryDirectory(prefix="clipboard-copy-files-probe-") as raw:
        tmpdir = Path(raw)
        paths = _write_sources(tmpdir / "sources")
        missing = _missing_path_keeps_prior_text(paths[0], tmpdir / "sources")
        run = _copy_and_observe(paths, PROBE_RECHECKS_S)

    ok = (
        missing["error_names_missing"]
        and missing["prior_text_survived"]
        and run["independent_paths_equal"]
        and run["offer_held_after_exit"]
        and run["paste_files_agrees"]
        and run["sources_unchanged"]
    )
    env = _environment()
    report = {
        "ok": ok,
        "mode": "probe",
        "environment": env,
        "floors": _floors(env),
        "expected_paths": paths,
        "missing_path": missing,
        **run,
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
