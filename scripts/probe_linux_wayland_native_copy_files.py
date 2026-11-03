#!/usr/bin/env python3
"""Independent-consumer probe: clipboard.copy_files → Linux Wayland wl-copy.

Run on a Wayland-only session (``WAYLAND_DISPLAY`` set, ``DISPLAY`` unset) of
headless Sway with wl-clipboard (see ``native-linux-wayland-copy-files`` in
ci.yml).

1. Missing helper: an independent ``wl-copy`` sets prior text; the public
   ``copy_files`` runs in a child Python whose ``PATH`` holds no wl-clipboard
   and must fail with ``ClipboardContentError`` and an install hint; an
   independent ``wl-paste`` still reads the prior text.
2. ``report final.pdf`` and ``données é.csv`` are copied by the public
   ``copy_files`` (default writer) in a child Python that **exits**. An
   independent ``wl-paste --type text/uri-list`` must return exactly the CRLF
   ``file://`` URIs at 0/5/10 s after exit and ``--list-types`` must list it.
   ``paste_files()`` agreement is recorded as a consistency check only.
3. Recorded only (never gating): a Thunar Paste attempt under Sway
   (``GDK_BACKEND=wayland``, Sway IPC focus, ``wtype`` Ctrl+V).

Prints one JSON object (floors included) and writes it, plus ``thunar.log``,
to CLIPBOARD_PROBE_ARTIFACTS. Exit 0 only when every gated observation held.
Replaces the session's Wayland selection. Not run by default pytest.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

from linux_wayland_native_copy_files_support import (
    TEXT_TYPE,
    URI_LIST,
    require_wayland_only_session,
    set_text_independently,
    wayland_floors,
    wl_list_types,
    wl_paste_read,
)
from linux_wayland_thunar_support import attempt_thunar_paste
from linux_x11_native_copy_files_support import (
    CONTENT_ERROR_EXIT,
    copy_in_exiting_child,
)

SOURCES = {"report final.pdf": b"%PDF-1.4 probe report\n", "données é.csv": b"a,b\n"}
PRIOR_TEXT = "prior text from an independent producer é"
# Seconds after writer exit at which the independent consumer re-reads.
RECHECKS_S = (0, 5, 10)


def _fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def missing_helper_round(path: str, empty_bin: Path) -> dict:
    """No wl-clipboard on PATH → error with hint; prior text untouched."""
    set_text_independently(PRIOR_TEXT)
    env = dict(os.environ, PATH=str(empty_bin))
    writer = copy_in_exiting_child([path], env=env)
    after = wl_paste_read(TEXT_TYPE)
    return {
        "writer": writer,
        "child_path": str(empty_bin),
        "prior_text_after": after["stdout"].decode("utf-8", "replace"),
        "types_after": wl_list_types(),
    }


def recheck_after_exit(body: bytes) -> list[dict]:
    start = time.monotonic()
    rechecks = []
    for mark in RECHECKS_S:
        delay = start + mark - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        seen = wl_paste_read(URI_LIST)
        rechecks.append(
            {
                "t_s": round(time.monotonic() - start, 1),
                "ok": seen["returncode"] == 0 and seen["stdout"] == body,
                "types_list_uri_list": URI_LIST in wl_list_types(),
                "error": seen["stderr"] or None,
            }
        )
    return rechecks


def paste_files_consistency() -> dict:
    import clipboard

    clipboard.set_files_clipboard_reader(None)
    try:
        return {"value": clipboard.paste_files(), "error": None}
    except clipboard.ClipboardContentError as exc:
        return {"value": None, "error": str(exc)}


def run_probe(tmp: Path, log) -> dict:
    source, destination, empty_bin = tmp / "sources", tmp / "dest", tmp / "no-wl"
    for folder in (source, destination, empty_bin):
        folder.mkdir()
    for name, content in SOURCES.items():
        (source / name).write_bytes(content)
    paths = [os.path.abspath(source / name) for name in SOURCES]
    body = "".join(f"{Path(p).as_uri()}\r\n" for p in paths).encode("ascii")
    before = {name: _fingerprint(source / name) for name in SOURCES}

    missing = missing_helper_round(paths[0], empty_bin)
    writer = copy_in_exiting_child(paths)
    rechecks = recheck_after_exit(body)
    independent = wl_paste_read(URI_LIST)
    types = wl_list_types()
    pasted = paste_files_consistency()
    thunar = attempt_thunar_paste(source, destination, SOURCES, log)
    after = {name: _fingerprint(source / name) for name in SOURCES}

    missing_stderr = missing["writer"].get("stderr", "")
    observations = {
        "missing_helper_content_error": missing["writer"].get("returncode")
        == CONTENT_ERROR_EXIT
        and "wl-copy was not found on PATH" in missing_stderr,
        "missing_helper_install_hint": "apt-get install wl-clipboard" in missing_stderr,
        "missing_helper_prior_text_survives": missing["prior_text_after"] == PRIOR_TEXT
        and URI_LIST not in missing["types_after"],
        "writer_exited_ok": writer.get("exited") is True
        and writer.get("returncode") == 0,
        "independent_body_equal": independent["returncode"] == 0
        and independent["stdout"] == body,
        "types_list_uri_list": URI_LIST in types,
        "offer_held_after_exit": all(
            r["ok"] and r["types_list_uri_list"] for r in rechecks
        ),
        "paste_files_agrees": pasted["value"] == paths,
        "sources_unchanged": before == after,
    }
    failed = [name for name, held in observations.items() if not held]
    return {
        "ok": not failed,
        "failed_observations": failed,
        "observations": observations,
        # Recorded only; becomes ``thunar_paste_copies_match`` once reliable.
        "recorded_observations": {"thunar_paste_attempt": thunar["copies_match"]},
        "expected_paths": paths,
        "expected_body": body.decode("ascii"),
        "missing_helper": missing,
        "writer": writer,
        "rechecks_after_exit": rechecks,
        "independent": {
            "returncode": independent["returncode"],
            "body": independent["stdout"].decode("utf-8", "replace"),
            "stderr": independent["stderr"],
            "types": types,
        },
        "paste_files": pasted,
        "thunar_paste_attempt": thunar,
        "sources_before": before,
        "sources_after": after,
    }


def main() -> int:
    artifacts = Path(os.environ.get("CLIPBOARD_PROBE_ARTIFACTS", "artifacts")).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    report: dict = {"ok": False}
    try:
        require_wayland_only_session()
        report["floors"] = wayland_floors()
        with tempfile.TemporaryDirectory(prefix="clipboard-wl-copy-files-") as raw:
            with (artifacts / "thunar.log").open("w") as log:
                report.update(run_probe(Path(raw), log))
        report["commitments"] = {
            "writer": "clipboard.copy_files default writer: wl-copy --type "
            "text/uri-list background server, confirmed by wl-paste",
            "writer_exit": "copy_files ran in a child Python that exited first",
            "independent_consumer": "wl-paste --type text/uri-list and "
            "--list-types, rechecked at 0/5/10 s",
            "consistency_only": "paste_files() agreement is not interop proof",
            "evidence_limit": "offer level on headless Sway only; the Thunar "
            "attempt is recorded, not gated; other compositors and file "
            "managers remain unverified",
        }
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        report["ok"] = False
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    (artifacts / "copy-files.json").write_text(serialized + "\n")
    print(serialized)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
