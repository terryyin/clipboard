"""Desktop-free checks of the one "cleared" rule every native clear probe uses.

``cleared_step`` is driven with a fake independent listing, its empty
predicate, fake child ``clear()`` records and owner-exit records, so the rule
is pinned without a desktop, a helper or a real clipboard.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import native_clear_support as support  # noqa: E402

EMPTY_LISTING = {"returncode": 1, "stdout": "", "stderr": "empty"}
OFFERED_LISTING = {"returncode": 0, "stdout": "text/html\n", "stderr": ""}
RETURNED = {"returncode": 0, "outcome": {"raised": None}}
RAISED = {
    "returncode": 3,
    "outcome": {"raised": "ClipboardContentError", "message": "failed"},
}
BOUND = {"bound_s": support.OWNER_EXIT_BOUND_S}
EXITED = {"pids": [41], "still_alive": [], "exited": True, "waited_s": 0.1, **BOUND}
SURVIVED = {**EXITED, "still_alive": [41], "exited": False, "waited_s": 5.0}


def _is_empty(listed: dict) -> bool:
    return listed["returncode"] != 0


def _observe(listing=EMPTY_LISTING, reads=None, **kwargs) -> dict:
    found = dict(support.EMPTY_READS if reads is None else reads)
    return support.cleared_step(
        "probe_step",
        lambda: listing,
        _is_empty,
        reader=lambda: found,
        **kwargs,
    )


def test_empty_listing_with_every_reader_absent_is_cleared():
    result = _observe(clears=(RETURNED, RETURNED), owner_exit={**EXITED})

    assert result["ok"] is True
    assert result["step"] == "probe_step"
    assert result["listing_after"] == EMPTY_LISTING
    assert result["classified_empty"] is True
    assert result["reads"] == support.EMPTY_READS
    assert result["owner_exit"]["exited"] is True


def test_non_empty_listing_is_not_cleared():
    result = _observe(listing=OFFERED_LISTING, clears=(RETURNED,))

    assert result["ok"] is False
    assert result["classified_empty"] is False


@pytest.mark.parametrize(
    ("reader", "found"),
    [
        ("paste", {"value": "left over"}),
        ("paste_html", {"value": "<p>left</p>"}),
        ("paste_files", {"value": ["kept.txt"]}),
        ("paste_image", {"value": "RGB (4, 4)"}),
        ("inspect", {"value": {"kinds": ["text"], "formats": ["text/plain"]}}),
    ],
)
def test_a_reader_that_is_not_absent_is_not_cleared(reader, found):
    result = _observe(reads={**support.EMPTY_READS, reader: found}, clears=(RETURNED,))

    assert result["ok"] is False


def test_a_reader_error_is_not_cleared(monkeypatch):
    import clipboard

    def fail():
        raise clipboard.ClipboardContentError("unreadable")

    for name in ("paste_files", "paste_image"):
        monkeypatch.setattr(clipboard, name, lambda: None)
    monkeypatch.setattr(clipboard, "paste", lambda: "")
    monkeypatch.setattr(clipboard, "paste_html", fail)
    monkeypatch.setattr(
        clipboard, "inspect", lambda: type("S", (), {"kinds": (), "formats": ()})()
    )

    reads = support.read_everything()
    result = _observe(reads=reads, clears=(RETURNED,))

    assert reads["paste_html"]["error_type"] == "ClipboardContentError"
    assert result["ok"] is False


@pytest.mark.parametrize(
    "clears", [(RAISED,), (RETURNED, RAISED), ({"error": "TimeoutExpired"},)]
)
def test_a_child_clear_that_raised_is_not_cleared(clears):
    assert _observe(clears=clears)["ok"] is False


@pytest.mark.parametrize(
    "owner_exit",
    [
        SURVIVED,
        {"pids": [], "still_alive": [], "exited": False, "waited_s": 0.0, **BOUND},
        {"pids": [7], "still_alive": [], "exited": True, "waited_s": 5.05, **BOUND},
    ],
)
def test_a_surviving_unfollowed_or_late_owner_is_not_cleared(owner_exit):
    result = _observe(clears=(RETURNED,), owner_exit=owner_exit)

    assert result["ok"] is False
    assert result["owner_exit"] == owner_exit


def test_step_preconditions_that_did_not_hold_are_not_cleared():
    assert _observe(held=False, clears=(RETURNED,))["ok"] is False
