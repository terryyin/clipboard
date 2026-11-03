#!/usr/bin/env python3
"""Independent-consumer probe: clipboard.copy_files → Windows CF_HDROP + Explorer.

1. Two sources whose names contain Unicode and spaces are copied by the public
   ``copy_files`` (default writer) in a child Python process that **exits**.
2. An independent consumer, Windows PowerShell 5.1 under ``-STA`` (not this
   library), reads ``[Windows.Forms.Clipboard]::GetFileDropList()``,
   ``Get-Clipboard -Format FileDropList`` and the ``Preferred DropEffect``
   stream; the paths must equal the absolute sources in order and the effect
   must be 1 (DROPEFFECT_COPY). It re-reads at seconds after writer exit, so
   the offer is shown held by the system rather than by the dead writer (the
   clipboard sequence number must differ from before the write; whether it
   stays constant across rechecks is recorded). ``paste_files()`` agreement
   is recorded as a consistency check only.
3. Explorer shell paste: ``Shell.Application`` ``NameSpace(dest).Self``
   ``InvokeVerb("Paste")`` (falling back to the folder's own ``Paste`` verb)
   must create copies in an empty temporary folder; the destination bytes must
   equal the sources and the sources must be unchanged.
4. A further offer-level round: from a child whose cwd is the source folder,
   ``copy_files(["report final.pdf", "a dir", "report final.pdf"])`` (relative
   file, directory, duplicate). The same PowerShell CF_HDROP consumer must
   read three absolute paths in that order with drop effect 1; ``paste_files()``
   agrees. No Explorer paste for this round (a duplicate would collide).

Prints one JSON object (floors included). Exit 0 only when every observation
held; 1 when one failed or could not be made; 2 off Windows or without
Windows PowerShell. Overwrites the clipboard. Not run by default pytest.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from copy_files_native_probe_support import paste_files_consistency
from windows_native_copy_files_support import (
    consumer_ok,
    copy_in_exiting_child,
    independent_consumer,
    relative_directory_duplicate_round,
    sequence_number,
    shell_paste,
)

SOURCE_NAMES = ("report final.pdf", "données é.csv")
SOURCE_BODIES = (b"%PDF-1.4 probe report\n", "col,é\n1,données\n".encode())
# Seconds after writer exit at which the independent consumer re-reads.
RECHECKS_S = (0, 5, 10)


def _fingerprint(path: Path) -> dict:
    st = path.stat()
    return {
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def recheck_after_exit(paths: list[str]) -> list[dict]:
    start = time.monotonic()
    rechecks = []
    for mark in RECHECKS_S:
        delay = start + mark - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        seen = independent_consumer()
        rechecks.append(
            {
                "t_s": round(time.monotonic() - start, 1),
                "ok": consumer_ok(seen, paths),
                "sequence_number": seen.get("sequence_number"),
                "error": seen.get("error"),
            }
        )
    return rechecks


def windows_floors() -> dict:
    from windows_native_text_support import windows_floors as text_floors

    floors = text_floors()
    floors["shell"] = "Shell.Application (explorer shell COM) paste verb"
    return floors


def _limit(reason: str) -> int:
    print(json.dumps({"ok": False, "evidence_limit": True, "reason": reason}))
    return 2


def main() -> int:
    if sys.platform != "win32":
        return _limit(f"probe requires a Windows desktop; got {sys.platform!r}")
    if shutil.which("powershell.exe") is None:
        return _limit("Windows PowerShell (powershell.exe) not found")

    with tempfile.TemporaryDirectory(prefix="clipboard-copy-files-probe-") as raw:
        tmp = Path(raw).resolve()  # long names, not an 8.3 short TEMP path
        source_dir, dest = tmp / "sources", tmp / "dest"
        source_dir.mkdir()
        dest.mkdir()
        sources = []
        for name, body in zip(SOURCE_NAMES, SOURCE_BODIES, strict=True):
            (source_dir / name).write_bytes(body)
            sources.append(source_dir / name)
        paths = [os.path.abspath(p) for p in sources]
        before = {p.name: _fingerprint(p) for p in sources}
        sequence_before = sequence_number()

        writer = copy_in_exiting_child(paths)
        rechecks = recheck_after_exit(paths)
        independent = independent_consumer()
        pasted = paste_files_consistency()
        paste = shell_paste(sources, dest)
        # After Explorer paste: a duplicate would collide in a file-manager paste.
        relative_round = relative_directory_duplicate_round(source_dir)
        after = {p.name: _fingerprint(p) for p in sources}

    sequences = {r["sequence_number"] for r in rechecks}
    sequences.add(independent.get("sequence_number"))
    observations = {
        "writer_exited_ok": writer.get("exited") is True
        and writer.get("returncode") == 0,
        "independent_paths_equal": consumer_ok(independent, paths),
        "offer_held_after_exit": all(r["ok"] for r in rechecks)
        and None not in sequences
        and sequence_before not in sequences,
        "paste_files_agrees": pasted["value"] == paths,
        "shell_paste_copies_match": paste["copies_match"],
        "sources_unchanged": before == after,
        "relative_directory_duplicate_writer_exited_ok": relative_round[
            "writer_exited_ok"
        ],
        "relative_directory_duplicate_independent_paths_equal": relative_round[
            "independent_paths_equal"
        ],
        "relative_directory_duplicate_paste_files_agrees": relative_round[
            "paste_files_agrees"
        ],
    }
    failed = [name for name, held in observations.items() if not held]
    report = {
        "ok": not failed,
        "failed_observations": failed,
        "observations": observations,
        "expected_paths": paths,
        "writer": writer,
        "sequence_before": sequence_before,
        # Recorded, not gated: one value means no other writer replaced it.
        "sequence_stable_after_exit": len(sequences) == 1,
        "rechecks_after_exit": rechecks,
        "independent": independent,
        "paste_files": pasted,
        "shell_paste": paste,
        "relative_directory_duplicate": relative_round,
        "sources_before": before,
        "sources_after": after,
        "floors": windows_floors(),
        "commitments": {
            "writer": (
                "clipboard.copy_files default writer: ctypes CF_HDROP wide "
                "DROPFILES + Preferred DropEffect DWORD 1"
            ),
            "writer_exit": "copy_files ran in a child Python that exited first",
            "independent_consumer": (
                "Windows PowerShell -STA Windows.Forms Clipboard.GetFileDropList, "
                "Get-Clipboard -Format FileDropList, Preferred DropEffect stream"
            ),
            "relative_directory_duplicate": (
                "further offer: relative file + directory + duplicate from "
                "source cwd; PowerShell CF_HDROP; no Explorer paste"
            ),
            "file_manager": "Shell.Application folder Paste verb (Explorer shell)",
            "consistency_only": "paste_files() agreement is not interop proof",
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
