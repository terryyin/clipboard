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
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

URI_LIST = "text/uri-list"
GNOME_FILES = "x-special/gnome-copied-files"
PASTE_WAIT = 8


def _run(*args: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, timeout=15, **kwargs)


def _output(*args: str) -> str:
    return _run(*args, capture_output=True, text=True).stdout.strip()


def _assert_copies(source: Path, destination: Path, expected: dict[str, bytes]) -> None:
    assert sorted(p.name for p in destination.iterdir()) == sorted(expected), (
        f"destination entries differ: {list(destination.iterdir())}"
    )
    for name, content in expected.items():
        assert (destination / name).read_bytes() == content, f"copy differs: {name}"
        assert (source / name).read_bytes() == content, f"source changed: {name}"


def _wait_window(destination: Path, launched: subprocess.Popen) -> str:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        status = launched.poll()
        if status not in (None, 0):
            raise RuntimeError(
                f"Thunar exited with status {status}; inspect thunar.log"
            )
        result = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--class", "Thunar"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"window search failed: {result.stderr}")
        for window in result.stdout.splitlines():
            title = _output("xdotool", "getwindowname", window)
            if destination.name in title:
                return window
        time.sleep(0.1)
    raise RuntimeError(f"Thunar destination window did not appear: {destination}")


def _offer(mime: str, source: Path, names: dict[str, bytes], log) -> dict:
    uris = [str((source / name).as_uri()) for name in names]
    body = (
        "\r\n".join(uris) + "\r\n" if mime == URI_LIST else "copy\n" + "\n".join(uris)
    )
    # Default xclip forks its owner. Wait for the writing command to exit;
    # do not capture the background owner's inherited stdout/stderr pipes.
    writer = _run(
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
    actual = _run(
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

    launched = subprocess.Popen(
        ["thunar", str(destination)],
        stdout=log,
        stderr=log,
    )
    try:
        window = _wait_window(destination, launched)
        _run("xdotool", "windowactivate", "--sync", window)
        _run("xdotool", "windowfocus", "--sync", window)
        report = _offer(mime, source, expected, log)
        # The offer alone must not manufacture a successful paste. Exercise
        # the very same oracle before sending any Paste keystroke.
        time.sleep(0.3)
        assert not list(destination.iterdir()), "setup unexpectedly copied files"
        try:
            _assert_copies(source, destination, expected)
        except AssertionError:
            report["no_paste_control_rejected_by_copy_assertions"] = True
        else:
            raise AssertionError("copy assertions accepted an empty destination")

        _run("xdotool", "key", "--clearmodifiers", "Escape")
        _run("xdotool", "key", "--clearmodifiers", "ctrl+v")
        deadline = time.monotonic() + PASTE_WAIT
        while time.monotonic() < deadline:
            if all((destination / name).is_file() for name in expected):
                break
            time.sleep(0.1)
        entries = sorted(p.name for p in destination.iterdir())
        if entries:
            _assert_copies(source, destination, expected)
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
    finally:
        # This probe requires its own D-Bus/X11 session, so quitting Thunar
        # cannot close a user's file-manager window.
        _run("thunar", "--quit", stdout=log, stderr=log)
        launched.wait(timeout=10)


def main() -> None:
    artifacts = Path(os.environ.get("CLIPBOARD_PROBE_ARTIFACTS", "artifacts")).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    report: dict = {"ok": False, "rounds": []}
    try:
        assert sys.platform.startswith("linux"), "Linux is required"
        assert os.environ.get("CLIPBOARD_NATIVE_PROBE") == "1", (
            "native gate is required"
        )
        assert os.environ.get("CLIPBOARD_FILE_MANAGER_ISOLATED") == "1", (
            "explicit isolated file-manager session acknowledgement is required"
        )
        assert os.environ.get("DISPLAY"), "DISPLAY is required"
        assert os.environ.get("DBUS_SESSION_BUS_ADDRESS"), "isolated D-Bus is required"
        for executable in ("thunar", "xclip", "xdotool"):
            assert shutil.which(executable), f"missing required helper: {executable}"
        xclip_version = _run("xclip", "-version", capture_output=True, text=True)
        report["environment"] = {
            "os": platform.system(),
            "kernel": platform.release(),
            "distribution": Path("/etc/os-release").read_text(),
            "python": platform.python_version(),
            "thunar": _output("thunar", "--version"),
            "xclip": (xclip_version.stdout + xclip_version.stderr).strip(),
            "xdotool": _output("xdotool", "--version"),
            "desktop_packages": _output(
                "dpkg-query",
                "--show",
                "--showformat=${Package} ${Version}\n",
                "xvfb",
                "openbox",
            ),
            "display": os.environ["DISPLAY"],
            "session": "X11 / Xvfb / Openbox / isolated D-Bus",
        }
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
