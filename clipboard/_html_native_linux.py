"""Linux X11 HTML clipboard reader (``xclip`` requesting ``text/html``)."""

from __future__ import annotations

import subprocess

from ._errors import ClipboardContentError
from ._html_envelope import _fragment_offer, _HtmlOffer

# Bounded so a contended or wedged CLIPBOARD owner never hangs the caller:
# xclip otherwise waits for the owner's SelectionNotify indefinitely.
_X11_HTML_READ_TIMEOUT_SECONDS = 10.0
_X11_HTML_TARGET = "text/html"
# xclip's stderr (``Error: target TARGETS not available``, exit 1) when the
# TARGETS conversion yields no property. That happens when CLIPBOARD has no
# owner (ICCCM owners must answer TARGETS), i.e. an empty clipboard. A missing
# display reports ``Can't open display`` instead and stays an error.
_XCLIP_NO_TARGETS = "target TARGETS not available"


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


def _stderr_text(result: subprocess.CompletedProcess[bytes]) -> str:
    return (result.stderr or b"").decode("utf-8", "replace").strip()


def _exit_error(
    target: str, result: subprocess.CompletedProcess[bytes]
) -> ClipboardContentError:
    detail = _stderr_text(result)
    return _x11_html_read_error(
        f"xclip -t {target} exited with status {result.returncode}"
        + (f": {detail}" if detail else "")
    )


def _linux_x11_html_clipboard_reader() -> _HtmlOffer | None:
    """Read CLIPBOARD's ``text/html`` via ``xclip -o`` without taking ownership.

    Lists TARGETS first: ``None`` when CLIPBOARD has no owner (empty) or its
    owner does not offer ``text/html`` (text-only, image-only, file-list).
    Otherwise returns the raw ``text/html`` bytes as a fragment offer, left
    for ``clipboard._html_envelope`` to decode.
    """
    targets = _run_xclip_output("TARGETS")
    if targets.returncode != 0:
        if _XCLIP_NO_TARGETS in _stderr_text(targets):
            return None
        raise _exit_error("TARGETS", targets)
    offered = {line.strip() for line in (targets.stdout or b"").splitlines()}
    if _X11_HTML_TARGET.encode("ascii") not in offered:
        return None
    html = _run_xclip_output(_X11_HTML_TARGET)
    if html.returncode != 0:
        # Advertised but not delivered: an unreadable offer, not absence.
        raise _exit_error(_X11_HTML_TARGET, html)
    return _fragment_offer(html.stdout or b"")
