"""macOS observers for the copy_files probe: osascript consumer, pbcopy/pbpaste.

Independent of this library: JXA reads ``public.file-url`` items; ``pbcopy`` /
``pbpaste`` hold prior text. The child-Python writer uses the default
``copy_files`` writer after clearing the writer seam.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

from copy_files_native_probe_support import (
    ensure_repo_on_pythonpath,
    prepare_relative_directory_duplicate,
)
from native_probe_common import die

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAMES = ("report final.pdf", "données é.csv")
SOURCE_BODIES = (b"%PDF-1.4 probe report\n", "col,é\n1,données\n".encode())
PRIOR_TEXT = "keep"
MISSING = "missing.txt"
_HELPER_TIMEOUT_S = 30
PROBE_RECHECKS_S = (0, 5, 10, 20)
LEAVE_OFFER_RECHECKS_S = (0, 10, 30, 60)
ACCESS_BEHAVIORS = {0: "default", 1: "ask", 2: "alwaysAllow", 3: "alwaysDeny"}

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


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
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


def independent_file_url_consumer() -> dict:
    result = run(["osascript", "-l", "JavaScript", "-e", _CONSUMER_JXA])
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


def pbcopy(text: str) -> None:
    result = run(["pbcopy"], input=text)
    if result.returncode != 0:
        die(f"independent producer pbcopy failed: {result.stderr.strip()}")


def pbpaste() -> str:
    result = run(["pbpaste"])
    if result.returncode != 0:
        die(f"independent consumer pbpaste failed: {result.stderr.strip()}")
    return result.stdout


def write_sources(directory: Path) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, body in zip(SOURCE_NAMES, SOURCE_BODIES, strict=True):
        target = directory / name
        target.write_bytes(body)
        paths.append(str(target.absolute()))
    return paths


def fingerprint(path: str) -> dict:
    st = os.stat(path)
    return {
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
    }


def copy_in_exiting_child(paths: list[str], *, cwd: Path | str | None = None) -> dict:
    """Run public copy_files with the default writer in a child that exits."""
    code = textwrap.dedent(
        """
        import sys
        import clipboard
        clipboard.set_files_clipboard_writer(None)
        clipboard.copy_files(sys.argv[1:])
        """
    )
    result = run(
        [sys.executable, "-c", code, *paths],
        cwd=ROOT if cwd is None else cwd,
        env=ensure_repo_on_pythonpath(None, ROOT),
    )
    if result.returncode != 0:
        die(f"copy_files child failed: {(result.stderr or result.stdout).strip()}")
    return {"returncode": result.returncode, "exited": True}


def missing_path_keeps_prior_text(existing: str, workdir: Path) -> dict:
    import clipboard

    pbcopy(PRIOR_TEXT)
    before = pbpaste()
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
    after = pbpaste()
    return {
        "prior_text_before": before,
        "error": error,
        "error_names_missing": error is not None and MISSING in error,
        "prior_text_after": after,
        "prior_text_survived": before == PRIOR_TEXT and after == PRIOR_TEXT,
    }


def recheck_after_exit(paths: list[str], schedule: tuple[int, ...]) -> list[dict]:
    start = time.monotonic()
    rechecks = []
    for mark in schedule:
        delay = start + mark - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        seen = independent_file_url_consumer()
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


def offer_held(rechecks: list[dict]) -> bool:
    first = rechecks[0]["change_count"]
    return all(
        r["change_count"] == first
        and "public.file-url" in r["types"]
        and r["paths_equal"]
        for r in rechecks
    )


def copy_and_observe(paths: list[str], schedule: tuple[int, ...]) -> dict:
    import clipboard

    before = {p: fingerprint(p) for p in paths}
    change_before = independent_file_url_consumer()["change_count"]
    writer = copy_in_exiting_child(paths)
    rechecks = recheck_after_exit(paths, schedule)
    observed = independent_file_url_consumer()
    clipboard.set_files_clipboard_reader(None)
    pasted = clipboard.paste_files()
    after = {p: fingerprint(p) for p in paths}
    return {
        "writer": writer,
        "change_count_before": change_before,
        "rechecks_after_exit": rechecks,
        "offer_held_after_exit": offer_held(rechecks)
        and observed["change_count"] == rechecks[0]["change_count"],
        "independent": observed,
        "independent_paths_equal": observed["paths"] == paths,
        "paste_files": pasted,
        "paste_files_agrees": pasted == paths,
        "sources_before": before,
        "sources_after": after,
        "sources_unchanged": before == after,
    }


def relative_directory_duplicate_round(source: Path) -> dict:
    """Offer-level: relative file + directory + duplicate → absolute paths."""
    import clipboard

    relative, expected = prepare_relative_directory_duplicate(source)
    writer = copy_in_exiting_child(relative, cwd=source)
    observed = independent_file_url_consumer()
    clipboard.set_files_clipboard_reader(None)
    pasted = clipboard.paste_files()
    return {
        "relative_args": relative,
        "cwd": str(source),
        "expected_paths": expected,
        "writer": writer,
        "independent": observed,
        "independent_paths_equal": observed["paths"] == expected,
        "paste_files": pasted,
        "paste_files_agrees": pasted == expected,
    }
