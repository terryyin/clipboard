"""macOS Aqua plain-text clipboard: owned ``pbcopy`` / ``pbpaste`` path.

Both helpers run with the caller's environment plus ``LC_ALL=en_US.UTF-8``:
without a UTF-8 locale (e.g. a process started with ``env -i``) they map
non-ASCII through the C locale and corrupt it, while a forced UTF-8 locale
moves exact UTF-8 bytes both ways. ``os.environ`` itself is never changed.
Bytes pass untranslated (no newline conversion); a cleared pasteboard reads
``""`` because ``pbpaste`` exits 0 with empty output.
"""

from __future__ import annotations

import os
import subprocess

from clipboard._desktop import _helper_stderr_detail
from clipboard._errors import ClipboardContentError

# Bounded like ``_offer_macos`` so a contended pasteboard cannot hang forever.
_MACOS_TEXT_READ_TIMEOUT_S = 15.0
_MACOS_TEXT_WRITE_TIMEOUT_S = 15.0
_MACOS_TEXT_LOCALE = "en_US.UTF-8"
_PBPASTE_CMD = ("pbpaste",)
_PBCOPY_CMD = ("pbcopy",)


def _macos_text_helper_env() -> dict[str, str]:
    """Child environment: a copy of the current one with a UTF-8 ``LC_ALL``."""
    env = dict(os.environ)
    env["LC_ALL"] = _MACOS_TEXT_LOCALE
    return env


def _run_macos_text_helper(
    cmd: tuple[str, ...], operation: str, timeout: float, stdin: bytes | None
) -> bytes:
    """Run ``pbcopy`` / ``pbpaste``; every failure is ``ClipboardContentError``."""
    helper = cmd[0]
    try:
        result = subprocess.run(
            list(cmd),
            input=stdin,
            capture_output=True,
            check=False,
            timeout=timeout,
            env=_macos_text_helper_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise ClipboardContentError(
            f"macOS clipboard text {operation} timed out ({helper}, limit "
            f"{timeout:g}s); pasteboard may be contended"
        ) from exc
    except FileNotFoundError as exc:
        raise ClipboardContentError(
            f"macOS clipboard text {operation} failed: {helper} was not found "
            f"on PATH (it ships with macOS in /usr/bin): {exc}"
        ) from exc
    except OSError as exc:
        raise ClipboardContentError(
            f"macOS clipboard text {operation} failed ({helper}): {exc}"
        ) from exc
    if result.returncode != 0:
        detail = _helper_stderr_detail(result)
        cause = subprocess.CalledProcessError(
            result.returncode, list(cmd), result.stdout, result.stderr
        )
        raise ClipboardContentError(
            f"macOS clipboard text {operation} failed ({helper} exited "
            f"{result.returncode})" + (f": {detail}" if detail else "")
        ) from cause
    return result.stdout or b""


def _macos_text_clipboard_reader() -> str:
    """Return the pasteboard's plain text exactly (``""`` when none)."""
    raw = _run_macos_text_helper(_PBPASTE_CMD, "read", _MACOS_TEXT_READ_TIMEOUT_S, None)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ClipboardContentError(
            f"macOS clipboard text read failed: pbpaste output is not UTF-8 ({exc})"
        ) from exc


def _macos_text_clipboard_writer(text: str) -> None:
    """Replace the pasteboard with exactly ``text`` (already validated)."""
    _run_macos_text_helper(
        _PBCOPY_CMD, "write", _MACOS_TEXT_WRITE_TIMEOUT_S, text.encode("utf-8")
    )
