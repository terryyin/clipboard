#!/usr/bin/env python3
"""Observe helper-made file offers pasted by Thunar in an isolated X11 session.

This is an interoperability experiment, not a copy_files API test. Run inside
dbus-run-session + xvfb-run with Openbox, xclip, xdotool and Thunar installed.
It writes JSON and desktop logs to CLIPBOARD_PROBE_ARTIFACTS (default: artifacts).
Only the named X11/Thunar environment is covered; a URI-list timeout records
"no copies observed", not a claim about every Linux file manager.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

from linux_x11_thunar_support import (
    PASTE_WAIT,
    assert_copies,
    require_isolated_thunar_session,
    run,
    thunar_window,
    x11_floors,
)

URI_LIST = "text/uri-list"
GNOME_FILES = "x-special/gnome-copied-files"


def _offer(mime: str, source: Path, names: dict[str, bytes], log) -> dict:
    uris = [str((source / name).as_uri()) for name in names]
    body = (
        "\r\n".join(uris) + "\r\n" if mime == URI_LIST else "copy\n" + "\n".join(uris)
    )
    # Default xclip forks its owner. Wait for the writing command to exit;
    # do not capture the background owner's inherited stdout/stderr pipes.
    writer = run(
        "xclip",
        "-selection",
        "clipboard",
        "-t",
        mime,
        input=body.encode("utf-8"),
        stdout=subprocess.DEVNULL,
        stderr=log,
    )
    deadline = time.monotonic() + 5
    targets = ""
    while time.monotonic() < deadline:
        available = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o", "-t", "TARGETS"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if available.returncode == 0:
            targets = available.stdout.strip()
            if mime in targets.splitlines():
                break
        time.sleep(0.1)
    assert mime in targets.splitlines(), f"requested MIME not offered: {targets}"
    protocol_targets = {"TARGETS", "TIMESTAMP", "MULTIPLE", "SAVE_TARGETS"}
    assert set(targets.splitlines()) - protocol_targets == {mime}, targets
    actual = run(
        "xclip", "-selection", "clipboard", "-o", "-t", mime, capture_output=True
    ).stdout
    assert actual == body.encode("utf-8"), (
        "independent clipboard read differs from the published body"
    )
    return {
        "mime": mime,
        "targets": targets.splitlines(),
        "writer_returncode": writer.returncode,
        "writer_exited_before_paste": True,
        "payload": body,
    }


def _round(root: Path, label: str, mime: str, log) -> dict:
    source = root / f"source-{label}"
    destination = root / f"destination-{label}"
    source.mkdir()
    destination.mkdir()
    expected = {"report final.txt": b"first file\n", "données é.csv": b"a,b\n1,2\n"}
    for name, content in expected.items():
        (source / name).write_bytes(content)

    with thunar_window(destination, log) as window:
        report = _offer(mime, source, expected, log)
        # The offer alone must not manufacture a successful paste. Exercise
        # the very same oracle before sending any Paste keystroke.
        time.sleep(0.3)
        assert not list(destination.iterdir()), "setup unexpectedly copied files"
        try:
            assert_copies(source, destination, expected)
        except AssertionError:
            report["no_paste_control_rejected_by_copy_assertions"] = True
        else:
            raise AssertionError("copy assertions accepted an empty destination")

        run("xdotool", "key", "--clearmodifiers", "Escape")
        run("xdotool", "key", "--clearmodifiers", "ctrl+v")
        deadline = time.monotonic() + PASTE_WAIT
        while time.monotonic() < deadline:
            if all((destination / name).is_file() for name in expected):
                break
            time.sleep(0.1)
        entries = sorted(p.name for p in destination.iterdir())
        if entries:
            assert_copies(source, destination, expected)
            outcome = "copies verified"
        else:
            for name, content in expected.items():
                assert (source / name).read_bytes() == content, (
                    f"source changed: {name}"
                )
            outcome = "no copies observed"
        report.update(
            label=label,
            outcome=outcome,
            destination_entries=entries,
            sources_unchanged=True,
            paste_action="Thunar destination window: xdotool ctrl+v",
            observation_timeout_seconds=PASTE_WAIT,
            window=window,
        )
        return report


def main() -> None:
    artifacts = Path(os.environ.get("CLIPBOARD_PROBE_ARTIFACTS", "artifacts")).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    report: dict = {"ok": False, "rounds": []}
    try:
        require_isolated_thunar_session()
        report["environment"] = x11_floors()
        with tempfile.TemporaryDirectory(prefix="clipboard-thunar-") as raw:
            with (artifacts / "thunar.log").open("w") as log:
                for label, mime in (
                    ("positive-before", GNOME_FILES),
                    ("uri-list", URI_LIST),
                    ("positive-after", GNOME_FILES),
                ):
                    result = _round(Path(raw), label, mime, log)
                    report["rounds"].append(result)
                    if mime == GNOME_FILES:
                        assert result["outcome"] == "copies verified", (
                            f"positive control failed: {label}; inspect thunar.log"
                        )
        report["ok"] = True
        report["evidence_limit"] = (
            "Helper-made offers only, not the unimplemented copy_files API; "
            "Thunar in this X11/Xvfb session only. Wayland and other file managers "
            "remain unverified. No copies observed is a bounded observation."
        )
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        (artifacts / "file-manager-offers.json").write_text(serialized + "\n")
        print(serialized)
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
