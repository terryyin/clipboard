"""Linux HTML clipboard readers: X11 (``xclip``) and Wayland (``wl-paste``)."""

from __future__ import annotations

import subprocess

from clipboard._desktop import (
    _HTML_LISTING_TIMEOUT_S,
    _helper_stderr_detail,
    _wl_paste_list_types_html,
    _xclip_targets_html,
)
from clipboard._errors import ClipboardContentError
from clipboard._html_envelope import _fragment_offer, _HtmlOffer

# Bounded so a contended or wedged CLIPBOARD owner never hangs the caller:
# xclip otherwise waits for the owner's SelectionNotify indefinitely.
# Listing uses the same bound via ``_desktop._HTML_LISTING_TIMEOUT_S``.
_X11_HTML_READ_TIMEOUT_SECONDS = _HTML_LISTING_TIMEOUT_S
_LINUX_HTML_TYPE = "text/html"


def _x11_html_read_error(detail: str) -> ClipboardContentError:
    return ClipboardContentError(
        f"Linux X11 HTML clipboard read failed: {detail}; paste_html needs a "
        "usable X11 session (DISPLAY) and xclip on PATH (install it, e.g. "
        "`apt install xclip`)"
    )


def _run_xclip_output(target: str) -> subprocess.CompletedProcess[bytes]:
    """Run ``xclip -selection clipboard -o -t <target>`` (read only, bounded)."""
    try:
        return subprocess.run(
            ["xclip", "-selection", "clipboard", "-o", "-t", target],
            capture_output=True,
            check=False,
            timeout=_X11_HTML_READ_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise _x11_html_read_error(
            f"xclip did not answer {target} within "
            f"{_X11_HTML_READ_TIMEOUT_SECONDS:g}s (CLIPBOARD owner contended "
            "or stalled)"
        ) from exc
    except FileNotFoundError as exc:
        raise _x11_html_read_error("xclip was not found on PATH") from exc
    except OSError as exc:
        raise _x11_html_read_error(f"could not run xclip ({exc})") from exc


def _exit_detail(command: str, result: subprocess.CompletedProcess[bytes]) -> str:
    """``<command> exited with status N[: stderr]`` for a failed helper run."""
    detail = _helper_stderr_detail(result)
    return f"{command} exited with status {result.returncode}" + (
        f": {detail}" if detail else ""
    )


def _offers_html(listing: subprocess.CompletedProcess[bytes]) -> bool:
    """Whether a helper's one-type-per-line listing has exactly ``text/html``."""
    offered = {line.strip() for line in (listing.stdout or b"").splitlines()}
    return _LINUX_HTML_TYPE.encode("ascii") in offered


def _exit_error(
    target: str, result: subprocess.CompletedProcess[bytes]
) -> ClipboardContentError:
    return _x11_html_read_error(_exit_detail(f"xclip -t {target}", result))


def _list_xclip_targets_for_html() -> subprocess.CompletedProcess[bytes] | None:
    """TARGETS via desktop; wrap helper faults with X11 HTML read errors."""
    try:
        return _xclip_targets_html()
    except subprocess.TimeoutExpired as exc:
        raise _x11_html_read_error(
            f"xclip did not answer TARGETS within "
            f"{_X11_HTML_READ_TIMEOUT_SECONDS:g}s (CLIPBOARD owner contended "
            "or stalled)"
        ) from exc
    except FileNotFoundError as exc:
        raise _x11_html_read_error("xclip was not found on PATH") from exc
    except OSError as exc:
        raise _x11_html_read_error(f"could not run xclip ({exc})") from exc


def _linux_x11_html_clipboard_reader() -> _HtmlOffer | None:
    """Read CLIPBOARD's ``text/html`` via ``xclip -o`` without taking ownership.

    Lists TARGETS first: ``None`` when CLIPBOARD has no owner (empty) or its
    owner does not offer ``text/html`` (text-only, image-only, file-list).
    Otherwise returns the raw ``text/html`` bytes as a fragment offer, left
    for ``clipboard._html_envelope`` to decode.
    """
    targets = _list_xclip_targets_for_html()
    if targets is None:
        return None
    if targets.returncode != 0:
        raise _exit_error("TARGETS", targets)
    if not _offers_html(targets):
        return None
    html = _run_xclip_output(_LINUX_HTML_TYPE)
    if html.returncode != 0:
        # Advertised but not delivered: an unreadable offer, not absence.
        raise _exit_error(_LINUX_HTML_TYPE, html)
    return _fragment_offer(html.stdout or b"")


# --- Linux Wayland: ``wl-paste`` (wl-clipboard) requesting ``text/html`` ---

# Bounded so a stalled source client or compositor never hangs the caller.
# Listing uses the same bound via ``_desktop._HTML_LISTING_TIMEOUT_S``.
_WAYLAND_HTML_READ_TIMEOUT_SECONDS = _HTML_LISTING_TIMEOUT_S


def _wayland_html_read_error(detail: str) -> ClipboardContentError:
    return ClipboardContentError(
        f"Linux Wayland HTML clipboard read failed: {detail}; paste_html needs "
        "a usable Wayland session (WAYLAND_DISPLAY) on a compositor that "
        "offers clipboard access to wl-paste, and wl-paste from wl-clipboard "
        "on PATH (install it, e.g. `apt install wl-clipboard`)"
    )


def _run_wl_paste(args: list[str], what: str) -> subprocess.CompletedProcess[bytes]:
    """Run ``wl-paste <args>`` (read only, bounded, stdin from /dev/null)."""
    try:
        return subprocess.run(
            ["wl-paste", *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=_WAYLAND_HTML_READ_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise _wayland_html_read_error(
            f"wl-paste did not answer {what} within "
            f"{_WAYLAND_HTML_READ_TIMEOUT_SECONDS:g}s (selection source or "
            "compositor stalled)"
        ) from exc
    except FileNotFoundError as exc:
        raise _wayland_html_read_error("wl-paste was not found on PATH") from exc
    except OSError as exc:
        raise _wayland_html_read_error(f"could not run wl-paste ({exc})") from exc


def _wl_paste_exit_error(
    what: str, result: subprocess.CompletedProcess[bytes]
) -> ClipboardContentError:
    return _wayland_html_read_error(_exit_detail(f"wl-paste {what}", result))


def _list_wl_paste_types_for_html() -> subprocess.CompletedProcess[bytes] | None:
    """``--list-types`` via desktop; wrap helper faults with Wayland HTML errors."""
    try:
        return _wl_paste_list_types_html()
    except subprocess.TimeoutExpired as exc:
        raise _wayland_html_read_error(
            f"wl-paste did not answer --list-types within "
            f"{_WAYLAND_HTML_READ_TIMEOUT_SECONDS:g}s (selection source or "
            "compositor stalled)"
        ) from exc
    except FileNotFoundError as exc:
        raise _wayland_html_read_error("wl-paste was not found on PATH") from exc
    except OSError as exc:
        raise _wayland_html_read_error(f"could not run wl-paste ({exc})") from exc


def _linux_wayland_html_clipboard_reader() -> _HtmlOffer | None:
    """Read the Wayland clipboard's ``text/html`` via ``wl-paste`` (read only).

    Lists the offer's MIME types first: ``None`` when nothing is copied or no
    type is exactly ``text/html`` (text-only, image-only, file-list).
    Otherwise returns the raw ``text/html`` bytes (``--no-newline``, so none
    is appended) as a fragment offer, left for ``clipboard._html_envelope``.
    Never runs wl-copy, so the selection is never taken or replaced.
    """
    types = _list_wl_paste_types_for_html()
    if types is None:
        return None
    if types.returncode != 0:
        raise _wl_paste_exit_error("--list-types", types)
    if not _offers_html(types):
        return None
    html = _run_wl_paste(
        ["--no-newline", "--type", _LINUX_HTML_TYPE], f"--type {_LINUX_HTML_TYPE}"
    )
    if html.returncode != 0:
        # Listed but not delivered (or cleared in between): not absence.
        raise _wl_paste_exit_error(f"--type {_LINUX_HTML_TYPE}", html)
    return _fragment_offer(html.stdout or b"")
