"""Clear-probe steps shared by the Linux X11 and Wayland ``clear`` probes.

A ``LinuxDesktop`` names what differs between the two desktops: the owner
helper's process name (``xclip`` / ``wl-copy``), the independent listing
(``xclip -o -t TARGETS`` / ``wl-paste -l``) with its empty-clipboard
predicate (no owner / nothing copied), the bounded wait until a type is
offered, and the independent producer of one type. Every step below ends in
``native_clear_support.cleared_step``; the producer and ``copy_image``
steps follow the background owner process they leave and require it to exit
after the child ``clear()`` on both desktops. Desktop-only steps (raw early
mechanism, dead ``DISPLAY``, ``PATH`` without ``wl-copy``) stay in each
desktop's probe.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from native_clear_support import (
    child_clear,
    child_python,
    cleared_step,
    helper_pids,
    wait_pids_exit,
)

HTML_TYPE = "text/html"
HTML_BODY = b"<p><b>clear probe</b> html</p>"
URI_LIST_TYPE = "text/uri-list"
UNKNOWN_TYPE = "application/x-clipboard-probe"
UNKNOWN_BODY = b"clear probe custom bytes"
COPY_IMAGE_CHILD = """
from PIL import Image
import clipboard

clipboard.copy_image(Image.new("RGB", (4, 4), (255, 0, 0)))
"""


@dataclass(frozen=True)
class LinuxDesktop:
    """One Linux desktop's clipboard helpers, as the shared steps use them."""

    owner: str
    listing: Callable[[], dict]
    is_empty: Callable[[dict], bool]
    wait_offered: Callable[[str], dict]
    produce: Callable[[str, bytes], dict]

    def cleared(self, name: str, **kwargs) -> dict:
        return cleared_step(name, self.listing, self.is_empty, **kwargs)


def fresh_reads_empty(desktop: LinuxDesktop, name: str, observed: dict) -> dict:
    """Step 1: a clipboard nobody has offered anything on reads absence."""
    result = desktop.cleared(name)
    observed["fresh_listing"] = result["listing_after"]
    return result


def _owner_then_child_clear(
    desktop: LinuxDesktop,
    name: str,
    mime_type: str,
    start: Callable[[], dict],
    *,
    started_as: str,
    owners_as: str,
) -> dict:
    """``start`` leaves a background owner of ``mime_type``; child clear ends it."""
    before = helper_pids(desktop.owner)
    started = start()
    offered = desktop.wait_offered(mime_type)
    owners = helper_pids(desktop.owner, argv_contains=mime_type) - before
    cleared = child_clear()
    owner_exit = wait_pids_exit(owners)
    return desktop.cleared(
        name,
        held=started.get("returncode") == 0 and offered["offered"] and bool(owners),
        clears=(cleared,),
        owner_exit=owner_exit,
        **{
            started_as: started,
            "offered_before": offered,
            owners_as: sorted(owners),
            "child_clear": cleared,
        },
    )


def producer_then_child_clear(
    desktop: LinuxDesktop, name: str, mime_type: str, body: bytes
) -> dict:
    """An independent producer's background owner of one type, then child clear."""
    return _owner_then_child_clear(
        desktop,
        name,
        mime_type,
        lambda: desktop.produce(mime_type, body),
        started_as="producer",
        owners_as="producer_owner_pids",
    )


def file_list_producer_then_child_clear(desktop: LinuxDesktop, name: str) -> dict:
    """``text/uri-list`` naming an existing temp file, then child clear."""
    with tempfile.TemporaryDirectory(prefix="clipboard-clear-probe-") as raw:
        listed = Path(raw) / "clear probe file.txt"
        listed.write_text("clear probe file\n", encoding="utf-8")
        body = (listed.as_uri() + "\r\n").encode("ascii")
        result = producer_then_child_clear(desktop, name, URI_LIST_TYPE, body)
        result["file_uri"] = listed.as_uri()
        result["file_existed"] = listed.is_file()
        result["ok"] = (
            result["ok"]
            and result["file_uri"].startswith("file:///")
            and result["file_existed"]
        )
        return result


def copy_image_owner_ends(desktop: LinuxDesktop, name: str) -> dict:
    """A child's ``copy_image()`` owner ends after a child ``clear()``."""
    return _owner_then_child_clear(
        desktop,
        name,
        "image/png",
        lambda: child_python(COPY_IMAGE_CHILD),
        started_as="copy_image_child",
        owners_as="library_owner_pids",
    )


def clear_twice_on_cleared(desktop: LinuxDesktop, name: str) -> dict:
    """``clear()`` twice on the already cleared clipboard succeeds."""
    first = child_clear()
    second = child_clear()
    return desktop.cleared(name, clears=(first, second), first=first, second=second)
