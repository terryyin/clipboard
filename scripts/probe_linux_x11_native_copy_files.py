#!/usr/bin/env python3
"""Independent-consumer probe: clipboard.copy_files → Linux X11 xclip + Thunar.

Run inside dbus-run-session + xvfb-run with Openbox, xclip, xdotool and Thunar
(the shared isolated desktop; see ``native-linux-x11-copy-files`` in ci.yml).

1. Missing helper: an independent ``xclip -i`` sets prior
   text; the public ``copy_files`` runs in a child Python whose ``PATH`` holds
   no ``xclip`` and must fail with ``ClipboardContentError`` and an install
   hint; an independent ``xclip -o`` still reads the prior text.
2. ``report final.pdf`` and ``données é.csv`` are copied by the public
   ``copy_files`` (default writer) in a child Python that **exits**. An
   independent ``xclip -o -t text/uri-list`` must return exactly the CRLF
   ``file://`` URIs at 0/5/10 s after exit, and ``TARGETS`` must list it.
   ``paste_files()`` agreement is recorded as a consistency check only.
3. Thunar Paste (Ctrl+V in a destination window) must create both copies
   with matching bytes while the sources stay unchanged.

Prints one JSON object (floors included) and writes it, plus ``thunar.log``,
to CLIPBOARD_PROBE_ARTIFACTS. Exit 0 only when every observation held.
Replaces the isolated session's clipboard. Not run by default pytest.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

from linux_x11_native_copy_files_support import (
    CONTENT_ERROR_EXIT,
    URI_LIST,
    copy_in_exiting_child,
    paste_and_verify,
    set_text_independently,
    xclip_read,
    xclip_targets,
)
from linux_x11_thunar_support import (
    require_isolated_thunar_session,
    thunar_window,
    x11_floors,
)

SOURCES = {"report final.pdf": b"%PDF-1.4 probe report\n", "données é.csv": b"a,b\n"}
PRIOR_TEXT = "prior text from an independent producer é"
# Seconds after writer exit at which the independent consumer re-reads.
RECHECKS_S = (0, 5, 10)


def _fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def missing_helper_round(path: str, empty_bin: Path) -> dict:
    """No xclip on PATH → error with hint; prior text untouched."""
    set_text_independently(PRIOR_TEXT)
    env = dict(os.environ, PATH=str(empty_bin))
    writer = copy_in_exiting_child([path], env=env)
    after = xclip_read("UTF8_STRING")
    return {
        "writer": writer,
        "child_path": str(empty_bin),
        "prior_text_after": after["stdout"].decode("utf-8", "replace"),
        "targets_after": xclip_targets(),
    }


def recheck_after_exit(body: bytes) -> list[dict]:
    start = time.monotonic()
    rechecks = []
    for mark in RECHECKS_S:
        delay = start + mark - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        seen = xclip_read(URI_LIST)
        rechecks.append(
            {
                "t_s": round(time.monotonic() - start, 1),
                "ok": seen["returncode"] == 0 and seen["stdout"] == body,
                "targets_list_uri_list": URI_LIST in xclip_targets(),
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


def _owner_processes() -> str:
    """Recorded, not gated: the background owner that holds the offer."""
    try:
        found = subprocess.run(
            ["pgrep", "-af", "xclip"], capture_output=True, text=True, check=False
        )
    except OSError as exc:
        return f"pgrep unavailable: {exc}"
    return found.stdout.strip()


def run_probe(tmp: Path, log) -> dict:
    source, destination, empty_bin = tmp / "sources", tmp / "dest", tmp / "no-xclip"
    for folder in (source, destination, empty_bin):
        folder.mkdir()
    for name, content in SOURCES.items():
        (source / name).write_bytes(content)
    paths = [os.path.abspath(source / name) for name in SOURCES]
    body = "".join(f"{Path(p).as_uri()}\r\n" for p in paths).encode("ascii")
    before = {name: _fingerprint(source / name) for name in SOURCES}

    missing = missing_helper_round(paths[0], empty_bin)
    with thunar_window(destination, log) as window:
        writer = copy_in_exiting_child(paths)
        rechecks = recheck_after_exit(body)
        independent = xclip_read(URI_LIST)
        targets = xclip_targets()
        owners = _owner_processes()
        pasted = paste_files_consistency()
        paste = paste_and_verify(window, source, destination, SOURCES)
    after = {name: _fingerprint(source / name) for name in SOURCES}

    missing_stderr = missing["writer"].get("stderr", "")
    observations = {
        "missing_helper_content_error": missing["writer"].get("returncode")
        == CONTENT_ERROR_EXIT
        and "xclip was not found on PATH" in missing_stderr,
        "missing_helper_install_hint": "apt-get install xclip" in missing_stderr,
        "missing_helper_prior_text_survives": missing["prior_text_after"] == PRIOR_TEXT
        and URI_LIST not in missing["targets_after"],
        "writer_exited_ok": writer.get("exited") is True
        and writer.get("returncode") == 0,
        "independent_body_equal": independent["returncode"] == 0
        and independent["stdout"] == body,
        "targets_list_uri_list": URI_LIST in targets,
        "offer_held_after_exit": all(
            r["ok"] and r["targets_list_uri_list"] for r in rechecks
        ),
        "paste_files_agrees": pasted["value"] == paths,
        "thunar_paste_copies_match": paste["copies_match"],
        "sources_unchanged": before == after,
    }
    failed = [name for name, held in observations.items() if not held]
    return {
        "ok": not failed,
        "failed_observations": failed,
        "observations": observations,
        "expected_paths": paths,
        "expected_body": body.decode("ascii"),
        "missing_helper": missing,
        "writer": writer,
        "rechecks_after_exit": rechecks,
        "independent": {
            "returncode": independent["returncode"],
            "body": independent["stdout"].decode("utf-8", "replace"),
            "stderr": independent["stderr"],
            "targets": targets,
        },
        "xclip_owner_processes": owners,
        "paste_files": pasted,
        "thunar_paste": paste,
        "sources_before": before,
        "sources_after": after,
    }


def main() -> int:
    artifacts = Path(os.environ.get("CLIPBOARD_PROBE_ARTIFACTS", "artifacts")).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    report: dict = {"ok": False}
    try:
        require_isolated_thunar_session()
        report["floors"] = x11_floors()
        with tempfile.TemporaryDirectory(prefix="clipboard-x11-copy-files-") as raw:
            with (artifacts / "thunar.log").open("w") as log:
                report.update(run_probe(Path(raw), log))
        report["commitments"] = {
            "writer": "clipboard.copy_files default writer: background "
            "xclip -selection clipboard -t text/uri-list owner",
            "writer_exit": "copy_files ran in a child Python that exited first",
            "independent_consumer": "xclip -selection clipboard -o -t "
            "text/uri-list and TARGETS, rechecked at 0/5/10 s",
            "file_manager": "Thunar Ctrl+V in its own isolated X11/D-Bus session",
            "consistency_only": "paste_files() agreement is not interop proof",
            "evidence_limit": "Thunar on this Xvfb/Openbox session only; other "
            "file managers and Wayland remain unverified",
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
