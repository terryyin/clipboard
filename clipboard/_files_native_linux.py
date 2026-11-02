"""Linux X11 / Wayland file-list clipboard readers (xclip / wl-paste)."""

from __future__ import annotations

import os
import shutil
import subprocess

from ._errors import ClipboardContentError

# Contended clipboard must not hang callers indefinitely (commitment 78).
_NATIVE_FILES_READ_TIMEOUT_S = 30
# Authoritative xclip argv for CLIPBOARD text/uri-list (docs/errors reuse this).
_XCLIP_TEXT_URI_LIST = (
    "-o",
    "-selection",
    "clipboard",
    "-t",
    "text/uri-list",
)
# Authoritative wl-paste argv for text/uri-list (docs/errors reuse this).
_WL_PASTE_TEXT_URI_LIST = (
    "-t",
    "text/uri-list",
)


def _linux_wayland_without_x11() -> bool:
    """True when only a Wayland session is advertised (X11 reader not selected)."""
    return bool(os.environ.get("WAYLAND_DISPLAY")) and not bool(
        os.environ.get("DISPLAY")
    )


def _xclip_uri_list_invocation() -> str:
    return "xclip " + " ".join(_XCLIP_TEXT_URI_LIST)


def _linux_x11_helper_missing_message() -> str:
    return (
        "clipboard file-list read failed: Linux X11 session/helper unavailable "
        "(need DISPLAY and xclip on PATH to request text/uri-list on CLIPBOARD "
        f"via `{_xclip_uri_list_invocation()}`); inject a reader "
        "with set_files_clipboard_reader for tests"
    )


def _wl_paste_uri_list_invocation() -> str:
    return "wl-paste " + " ".join(_WL_PASTE_TEXT_URI_LIST)


def _linux_wayland_helper_missing_message() -> str:
    return (
        "clipboard file-list read failed: Linux Wayland session/helper unavailable "
        "(need WAYLAND_DISPLAY and wl-paste on PATH to request text/uri-list "
        f"via `{_wl_paste_uri_list_invocation()}` on a named compositor); inject a "
        "reader with set_files_clipboard_reader for tests"
    )


def _uri_list_target_absent(stderr: str, stdout: str) -> bool:
    """Whether helper failure looks like ordinary missing text/uri-list offer."""
    detail = f"{stderr}\n{stdout}".lower()
    markers = (
        "not available",
        "no data types",
        "error: target",
        "cannot convert",
        "nothing is copied",
        "no mime",
    )
    return any(marker in detail for marker in markers)


def _run_uri_list_helper(
    helper: str,
    argv_tail: tuple[str, ...],
    *,
    timeout_detail: str,
    transfer_failed_detail: str,
) -> object:
    """Run a Linux helper for ``text/uri-list``; return structured offer or None."""
    try:
        result = subprocess.run(
            [helper, *argv_tail],
            capture_output=True,
            text=True,
            timeout=_NATIVE_FILES_READ_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClipboardContentError(
            f"clipboard file-list read failed: {timeout_detail}"
        ) from exc
    except OSError as exc:
        raise ClipboardContentError(f"clipboard file-list read failed: {exc}") from exc

    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if result.returncode != 0:
        if _uri_list_target_absent(stderr, stdout):
            return None
        detail = (stderr or stdout).strip()
        raise ClipboardContentError(
            "clipboard file-list read failed"
            + (f": {detail}" if detail else f": {transfer_failed_detail}")
        )

    if not stdout.strip():
        return None
    # Structured shape so paste_files uses the shared uri-list normalizer.
    return {"kind": "uri-list", "uri_list": stdout}


def _linux_x11_files_clipboard_reader() -> object:
    """Read ``text/uri-list`` from X11 CLIPBOARD via ``xclip`` (read-only).

    Returns a structured ``uri-list`` offer for ``_normalize_files_offer`` (same
    ``file://`` decode as the in-memory contract). Ordinary absence of that
    target is ``None``. Missing ``DISPLAY`` / ``xclip`` raises
    ``ClipboardContentError`` (never silent ``None``). Does not clear or rewrite
    CLIPBOARD and does not open referenced files. Cut/move companion types are
    not requested (ignored for library behavior).
    """
    display = os.environ.get("DISPLAY") or ""
    xclip = shutil.which("xclip")
    if not display or not xclip:
        raise ClipboardContentError(_linux_x11_helper_missing_message())

    return _run_uri_list_helper(
        xclip,
        _XCLIP_TEXT_URI_LIST,
        timeout_detail="xclip text/uri-list read timed out",
        transfer_failed_detail="xclip text/uri-list transfer failed",
    )


def _linux_wayland_files_clipboard_reader() -> object:
    """Read ``text/uri-list`` via ``wl-paste`` on Wayland (read-only).

    Returns a structured ``uri-list`` offer for ``_normalize_files_offer`` (same
    ``file://`` decode as the in-memory contract). Ordinary absence of that
    target is ``None``. Missing ``WAYLAND_DISPLAY`` / ``wl-paste`` raises
    ``ClipboardContentError`` (never silent ``None``). Does not clear or rewrite
    the clipboard and does not open referenced files. Cut/move companion types
    are not requested (ignored for library behavior). Success is scoped to the
    compositor actually proved when one is available — never generalized.
    """
    wayland = os.environ.get("WAYLAND_DISPLAY") or ""
    wl_paste = shutil.which("wl-paste")
    if not wayland or not wl_paste:
        raise ClipboardContentError(_linux_wayland_helper_missing_message())

    return _run_uri_list_helper(
        wl_paste,
        _WL_PASTE_TEXT_URI_LIST,
        timeout_detail="wl-paste text/uri-list read timed out",
        transfer_failed_detail="wl-paste text/uri-list transfer failed",
    )
