"""Linux X11 file-list copy writer: background ``xclip`` ``text/uri-list`` owner.

The body is one percent-encoded ``file://`` URI per path (``Path.as_uri()``,
directories included, no trailing slash added), each line CRLF-terminated as
RFC 2483 asks, fed on stdin to ``xclip -selection clipboard -t text/uri-list``.
That ``xclip`` forks a background owner in its own session, so the offer stays
pasteable after Python exits (the ``copy_image`` / text writer lifetime).

Missing ``DISPLAY`` or ``xclip`` raises ``ClipboardContentError`` with an
install hint before any helper starts, so the clipboard is untouched. The
writer returns only once CLIPBOARD lists ``text/uri-list`` in ``TARGETS`` and
serves exactly the written body (a previous file-manager owner may list the
same type); helper exit, launch failure, or no such offer within the bound
raises ``ClipboardContentError`` — never silent success.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from clipboard._desktop import _xclip_targets_lenient
from clipboard._errors import ClipboardContentError
from clipboard._text_native_linux import (
    _helper_log,
    _helper_log_suffix,
    _install_hint,
    _remaining,
)
from clipboard._text_native_x11 import _stop_owner

_URI_LIST = "text/uri-list"
_XCLIP_URI_LIST_WRITE_CMD = ["xclip", "-selection", "clipboard", "-t", _URI_LIST]
_XCLIP_URI_LIST_READ_CMD = ["xclip", "-selection", "clipboard", "-o", "-t", _URI_LIST]
# One bound across launch, TARGETS polling and read-back (text writer's 10 s).
_X11_FILES_WRITE_TIMEOUT_S = 10.0
_X11_FILES_READBACK_TIMEOUT_S = 2.0
_X11_FILES_POLL_INTERVAL_S = 0.05


def _error(detail: str) -> ClipboardContentError:
    return ClipboardContentError(
        f"Linux X11 clipboard file-list write failed: {detail}"
    )


def _xclip_missing_detail() -> str:
    return f"xclip was not found on PATH; {_install_hint('xclip', 'xclip')}"


def _uri_list_body(paths: list[str]) -> bytes:
    """``text/uri-list`` bytes: percent-encoded ASCII URIs, CRLF after each."""
    return "".join(f"{Path(path).as_uri()}\r\n" for path in paths).encode("ascii")


def _require_session() -> None:
    """Fail before any helper runs, so the current clipboard stays as it was."""
    if not os.environ.get("DISPLAY"):
        raise _error(
            "no X11 display (DISPLAY is unset); run inside an X11 session, or "
            "inject a writer with set_files_clipboard_writer for tests"
        )
    if shutil.which("xclip") is None:
        raise _error(
            f"{_xclip_missing_detail()} "
            f"(`{' '.join(_XCLIP_URI_LIST_WRITE_CMD)}` owns the offer)"
        )


def _start_owner(body: bytes, log) -> subprocess.Popen:
    try:
        proc = subprocess.Popen(
            _XCLIP_URI_LIST_WRITE_CMD,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=log,
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        raise _error(_xclip_missing_detail()) from exc
    except OSError as exc:
        raise _error(f"could not run xclip ({exc})") from exc
    assert proc.stdin is not None
    try:
        proc.stdin.write(body)
        proc.stdin.close()
    except BrokenPipeError:
        pass  # xclip already exited; its status and stderr say why below.
    return proc


def _owner_serves(body: bytes, deadline: float) -> bool:
    """Whether ``TARGETS`` lists ``text/uri-list`` and it is exactly ``body``."""
    if _URI_LIST.encode() not in _xclip_targets_lenient().splitlines():
        return False
    try:
        result = subprocess.run(
            _XCLIP_URI_LIST_READ_CMD,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=_remaining(deadline, _X11_FILES_READBACK_TIMEOUT_S),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout == body


def _x11_files_clipboard_writer(paths: list[str]) -> None:
    """Replace CLIPBOARD with one ``text/uri-list`` offer of ``paths``."""
    _require_session()
    body = _uri_list_body(paths)
    command = " ".join(_XCLIP_URI_LIST_WRITE_CMD)
    deadline = time.monotonic() + _X11_FILES_WRITE_TIMEOUT_S
    # stderr goes to an unlinked file, never a pipe the background owner holds.
    with tempfile.TemporaryFile() as log:
        proc = _start_owner(body, log)
        while True:
            status = proc.poll()
            if status not in (None, 0):
                error = _error(
                    f"{command} exited with status {status}" + _helper_log_suffix(log)
                )
                raise error from subprocess.CalledProcessError(
                    status, _XCLIP_URI_LIST_WRITE_CMD, None, _helper_log(log)
                )
            if _owner_serves(body, deadline):
                return
            if time.monotonic() >= deadline:
                _stop_owner(proc)
                raise _error(
                    f"{command} did not offer the file list as {_URI_LIST} in "
                    f"TARGETS within the {_X11_FILES_WRITE_TIMEOUT_S:g}s bound"
                    + _helper_log_suffix(log)
                ) from subprocess.TimeoutExpired(
                    _XCLIP_URI_LIST_WRITE_CMD, _X11_FILES_WRITE_TIMEOUT_S
                )
            time.sleep(_X11_FILES_POLL_INTERVAL_S)
