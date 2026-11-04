"""Linux Wayland file-list copy writer: ``wl-copy --type text/uri-list``.

The body is byte-identical to the X11 writer's (shared ``_uri_list_body``: one
percent-encoded ``file://`` URI per path, CRLF-terminated), handed to
``wl-copy --type text/uri-list`` through the shared owner launcher (an
unlinked temp-file stdin, never a pipe). wl-copy forks a background server
that keeps serving the selection after Python exits (the Wayland text / image
lifetime).

Missing ``WAYLAND_DISPLAY`` or a missing ``wl-copy`` / ``wl-paste`` raises
``ClipboardContentError`` (with an install hint for the helpers) before any
helper starts, so the clipboard is untouched. The writer returns only once
``wl-paste --list-types`` lists ``text/uri-list`` and
``wl-paste --type text/uri-list --no-newline`` reads back exactly the written
body (a previous owner may already offer the same type). A wl-copy exit,
launch failure or stall, or no such offer within the bound raises
``ClipboardContentError`` quoting wl-copy's stderr (where a compositor that
cannot be reached or refuses the selection says why) — never silent success
and never a text-only fallback.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time

from clipboard._desktop import (
    _WL_PASTE_LIST_TYPES_HTML_CMD,
    _helper_stderr_detail,
    _start_helper_owner,
)
from clipboard._errors import ClipboardContentError
from clipboard._files_offer import _uri_list_body
from clipboard._text_native_linux import (
    _helper_log,
    _helper_log_suffix,
    _install_hint,
    _remaining,
)

_URI_LIST = "text/uri-list"
_PACKAGE = "wl-clipboard"
_WL_COPY_URI_LIST_CMD = ["wl-copy", "--type", _URI_LIST]
_WL_PASTE_URI_LIST_READ_CMD = ["wl-paste", "--type", _URI_LIST, "--no-newline"]
_LIST_TYPES_CMD = list(_WL_PASTE_LIST_TYPES_HTML_CMD)
# One bound across wl-copy, list-types polling and read-back (text writer's 10 s).
_WAYLAND_FILES_WRITE_TIMEOUT_S = 10.0
_WAYLAND_FILES_READBACK_TIMEOUT_S = 2.0
_WAYLAND_FILES_POLL_INTERVAL_S = 0.05
# wl-clipboard's stderr when WAYLAND_DISPLAY names no reachable compositor.
_NO_COMPOSITOR = "Failed to connect to a Wayland server"


def _error(detail: str) -> ClipboardContentError:
    return ClipboardContentError(
        f"Linux Wayland clipboard file-list write failed: {detail}"
    )


def _missing_detail(helper: str) -> str:
    return f"{helper} was not found on PATH; {_install_hint(helper, _PACKAGE)}"


def _require_session() -> None:
    """Fail before any helper runs, so the current clipboard stays as it was."""
    if not os.environ.get("WAYLAND_DISPLAY"):
        raise _error(
            "unsupported session: no Wayland compositor (WAYLAND_DISPLAY is "
            "unset); run inside a Wayland session, or inject a writer with "
            "set_files_clipboard_writer for tests"
        )
    for helper in ("wl-copy", "wl-paste"):
        if shutil.which(helper) is None:
            raise _error(
                f"{_missing_detail(helper)} (`{' '.join(_WL_COPY_URI_LIST_CMD)}` "
                "owns the offer and wl-paste confirms it)"
            )


def _exit_error(status: int, log) -> ClipboardContentError:
    command = " ".join(_WL_COPY_URI_LIST_CMD)
    stderr = _helper_log(log)
    prefix = (
        "unsupported session: no usable Wayland compositor at "
        f"WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY')!r}; "
        if _NO_COMPOSITOR.encode() in stderr
        else ""
    )
    error = _error(
        f"{prefix}{command} exited with status {status}" + _helper_log_suffix(log)
    )
    error.__cause__ = subprocess.CalledProcessError(
        status, _WL_COPY_URI_LIST_CMD, None, stderr
    )
    return error


def _run_wl_copy(body: bytes, deadline: float, log) -> None:
    """Run wl-copy's foreground part (it forks the serving background part)."""
    try:
        proc = _start_helper_owner(_WL_COPY_URI_LIST_CMD, body, log)
    except FileNotFoundError as exc:
        raise _error(_missing_detail("wl-copy")) from exc
    except OSError as exc:
        raise _error(f"could not run wl-copy ({exc})") from exc
    try:
        proc.wait(timeout=_remaining(deadline, _WAYLAND_FILES_WRITE_TIMEOUT_S))
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        raise _error(
            f"{' '.join(_WL_COPY_URI_LIST_CMD)} did not finish within the "
            f"{_WAYLAND_FILES_WRITE_TIMEOUT_S:g}s bound (compositor stalled or "
            "not answering)" + _helper_log_suffix(log)
        ) from exc
    if proc.returncode != 0:
        raise _exit_error(proc.returncode, log)


def _run_wl_paste(cmd: list[str], deadline: float):
    """One bounded wl-paste run; ``(result, None)`` or ``(None, why it failed)``."""
    try:
        result = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=_remaining(deadline, _WAYLAND_FILES_READBACK_TIMEOUT_S),
        )
    except subprocess.TimeoutExpired:
        return None, f"{' '.join(cmd)} did not answer"
    except OSError as exc:
        return None, f"could not run {cmd[0]} ({exc})"
    if result.returncode != 0:
        detail = _helper_stderr_detail(result)
        return None, f"{' '.join(cmd)} exited with status {result.returncode}" + (
            f": {detail}" if detail else ""
        )
    return result, None


def _selection_serves(body: bytes, deadline: float) -> str | None:
    """``None`` once the selection offers exactly ``body``; else what was seen."""
    listing, why = _run_wl_paste(_LIST_TYPES_CMD, deadline)
    if listing is None:
        return why
    raw = (listing.stdout or b"").decode("utf-8", "replace")
    listed = [line.strip() for line in raw.splitlines() if line.strip()]
    if _URI_LIST not in listed:
        return f"{_URI_LIST} not listed (listed: {', '.join(listed) or 'nothing'})"
    read, why = _run_wl_paste(_WL_PASTE_URI_LIST_READ_CMD, deadline)
    if read is None:
        return why
    if read.stdout != body:
        return (
            f"{_URI_LIST} read back {len(read.stdout)} bytes that differ from "
            f"the {len(body)} written"
        )
    return None


def _wayland_files_clipboard_writer(paths: list[str]) -> None:
    """Replace the Wayland selection with one ``text/uri-list`` offer of ``paths``."""
    _require_session()
    body = _uri_list_body(paths)
    deadline = time.monotonic() + _WAYLAND_FILES_WRITE_TIMEOUT_S
    # stderr goes to an unlinked file, never a pipe the background server holds.
    with tempfile.TemporaryFile() as log:
        _run_wl_copy(body, deadline, log)
        while True:
            seen = _selection_serves(body, deadline)
            if seen is None:
                return
            if time.monotonic() >= deadline:
                raise _error(
                    f"{' '.join(_WL_COPY_URI_LIST_CMD)} did not offer the file "
                    f"list within the {_WAYLAND_FILES_WRITE_TIMEOUT_S:g}s bound "
                    f"(last check: {seen})" + _helper_log_suffix(log)
                ) from subprocess.TimeoutExpired(
                    _WL_COPY_URI_LIST_CMD, _WAYLAND_FILES_WRITE_TIMEOUT_S
                )
            time.sleep(_WAYLAND_FILES_POLL_INTERVAL_S)
