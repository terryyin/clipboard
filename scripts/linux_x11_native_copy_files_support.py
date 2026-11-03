"""X11 observers for the copy_files probe: xclip consumer/producer, Thunar paste.

Everything here is independent of this library: ``xclip`` reads and writes
CLIPBOARD, and Thunar pastes through the shared isolated-desktop harness
(``linux_x11_thunar_support``: window wait and copy assertions).
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import time
from pathlib import Path

from copy_files_native_probe_support import (
    ensure_repo_on_pythonpath,
    paste_files_consistency,
    prepare_relative_directory_duplicate,
    uri_list_body,
)
from linux_x11_thunar_support import PASTE_WAIT, assert_copies, run

ROOT = Path(__file__).resolve().parents[1]
URI_LIST = "text/uri-list"
CHILD_TIMEOUT_S = 60
# Exit status the child uses for an expected ClipboardContentError.
CONTENT_ERROR_EXIT = 3


def xclip_read(target: str) -> dict:
    """Independent ``xclip -o -t target`` read of CLIPBOARD (raw bytes)."""
    result = subprocess.run(
        ["xclip", "-selection", "clipboard", "-o", "-t", target],
        capture_output=True,
        timeout=15,
        check=False,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr.decode("utf-8", "replace").strip(),
    }


def xclip_targets() -> list[str]:
    seen = xclip_read("TARGETS")
    if seen["returncode"] != 0:
        return []
    return seen["stdout"].decode("ascii", "replace").split()


def set_text_independently(text: str) -> None:
    """Make an independent ``xclip -i`` (forking owner) hold ``text``."""
    run(
        "xclip",
        "-selection",
        "clipboard",
        "-i",
        input=text.encode("utf-8"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if xclip_read("UTF8_STRING")["stdout"] == text.encode("utf-8"):
            return
        time.sleep(0.1)
    raise RuntimeError("independent xclip producer did not publish the prior text")


def copy_in_exiting_child(
    paths: list[str],
    *,
    env: dict | None = None,
    cwd: Path | str | None = None,
) -> dict:
    """Run public copy_files (default writer) in a child Python that exits.

    ``cwd`` defaults to the repo root. Relative-path rounds pass the probe's
    source folder so ``copy_files`` resolves against that directory.
    """
    code = textwrap.dedent(
        f"""
        import sys
        import clipboard
        clipboard.set_files_clipboard_writer(None)
        try:
            clipboard.copy_files(sys.argv[1:])
        except clipboard.ClipboardContentError as exc:
            print(exc, file=sys.stderr)
            raise SystemExit({CONTENT_ERROR_EXIT})
        """
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code, *paths],
            cwd=ROOT if cwd is None else cwd,
            env=ensure_repo_on_pythonpath(env, ROOT),
            capture_output=True,
            text=True,
            timeout=CHILD_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"exited": False, "error": f"child timed out after {CHILD_TIMEOUT_S}s"}
    return {
        "exited": True,
        "returncode": result.returncode,
        "stderr": result.stderr.strip()[-2000:],
    }


def relative_directory_duplicate_round(source: Path) -> dict:
    """Offer-level: relative file + directory + duplicate → absolute URI list."""
    relative, expected = prepare_relative_directory_duplicate(source)
    body = uri_list_body(expected)
    writer = copy_in_exiting_child(relative, cwd=source)
    independent = xclip_read(URI_LIST)
    targets = xclip_targets()
    pasted = paste_files_consistency()
    return {
        "relative_args": relative,
        "cwd": str(source),
        "expected_paths": expected,
        "expected_body": body.decode("ascii"),
        "writer": writer,
        "independent": {
            "returncode": independent["returncode"],
            "body": independent["stdout"].decode("utf-8", "replace"),
            "stderr": independent["stderr"],
            "targets": targets,
        },
        "paste_files": pasted,
        "writer_exited_ok": writer.get("exited") is True
        and writer.get("returncode") == 0,
        "independent_body_equal": independent["returncode"] == 0
        and independent["stdout"] == body,
        "targets_list_uri_list": URI_LIST in targets,
        "paste_files_agrees": pasted["value"] == expected,
    }


def paste_and_verify(
    window: str, source: Path, destination: Path, expected: dict[str, bytes]
) -> dict:
    """Ctrl+V in Thunar's window; report whether both copies match."""
    # The offer alone must not manufacture a successful paste.
    assert not list(destination.iterdir()), "setup unexpectedly copied files"
    try:
        assert_copies(source, destination, expected)
    except AssertionError:
        control_rejected = True
    else:
        raise AssertionError("copy assertions accepted an empty destination")
    run("xdotool", "windowactivate", "--sync", window)
    run("xdotool", "key", "--clearmodifiers", "Escape")
    run("xdotool", "key", "--clearmodifiers", "ctrl+v")
    deadline = time.monotonic() + PASTE_WAIT
    while time.monotonic() < deadline:
        if all((destination / name).is_file() for name in expected):
            break
        time.sleep(0.1)
    try:
        assert_copies(source, destination, expected)
        copies_match, error = True, None
    except AssertionError as exc:
        copies_match, error = False, str(exc)
    return {
        "window": window,
        "no_paste_control_rejected_by_copy_assertions": control_rejected,
        "destination_entries": sorted(p.name for p in destination.iterdir()),
        "copies_match": copies_match,
        "error": error,
        "paste_action": "Thunar destination window: xdotool ctrl+v",
        "observation_timeout_seconds": PASTE_WAIT,
    }
