"""Desktop-free proofs for ``clipboard.wait_for_text_change`` outcomes.

The text is observed through public ``paste()`` with a scripted reader
injected by ``set_text_clipboard_reader``; a fake clock (``fake_wait_clock``)
makes deadlines exact. The first observation is the baseline. Failures and
argument validation live in ``test_wait_for_text_change_failures.py``.
"""

from __future__ import annotations

import threading
import time

import pytest
from fake_wait_clock import (
    START,
    FakeCancel,
    assert_capped_pauses,
    install_fake_clock,
    no_plain_sleep,
    reader_installer,
)

import clipboard
from clipboard import _wait


@pytest.fixture
def clock(monkeypatch):
    return install_fake_clock(monkeypatch)


@pytest.fixture
def reader(clock, restore_text_clipboard):
    return reader_installer(clock)


def test_new_text_after_the_baseline_is_returned(clock, reader):
    fake = reader("old", "old", "new")

    assert clipboard.wait_for_text_change(timeout=30) == "new"
    assert fake.calls == [START, START + 0.5, START + 1.0]
    assert clock.sleeps == [0.5, 0.5]


def test_clearing_then_identical_recopy_is_not_a_change(clock, reader):
    fake = reader("old", "", "old")
    deadline = START + 2.0

    assert clipboard.wait_for_text_change(timeout=2, interval=0.5) is None
    assert fake.calls == [START + step * 0.5 for step in range(5)]
    assert max(fake.calls) <= deadline
    assert_capped_pauses(clock.sleeps, fake.calls, interval=0.5, deadline=deadline)


def test_clearing_then_new_text_returns_the_new_text(clock, reader):
    reader("old", "", "", "new")

    assert clipboard.wait_for_text_change(timeout=10) == "new"


def test_offer_without_text_keeps_waiting(clock, reader):
    """A reader returning ``None`` (no text offered) reads as ``""``."""
    fake = reader("old", None, None, "fresh")

    assert clipboard.wait_for_text_change(timeout=10) == "fresh"
    assert len(fake.calls) == 4


def test_empty_baseline_returns_the_first_copied_text(clock, reader):
    fake = reader("", "", "copied")

    assert clipboard.wait_for_text_change(timeout=10) == "copied"
    assert len(fake.calls) == 3


def test_unchanged_text_until_the_deadline_returns_none(clock, reader):
    fake = reader("same")
    deadline = START + 1.25

    assert clipboard.wait_for_text_change(timeout=1.25, interval=0.5) is None
    assert fake.calls == [START, START + 0.5, START + 1.0, START + 1.25]
    assert clock.sleeps == [0.5, 0.5, 0.25]
    assert_capped_pauses(clock.sleeps, fake.calls, interval=0.5, deadline=deadline)


def test_slow_reads_return_by_timeout_plus_one_observation(clock, reader):
    fake = reader("same", cost=0.3)
    deadline = START + 1.0

    assert clipboard.wait_for_text_change(timeout=1, interval=0.5) is None
    assert all(at <= deadline for at in fake.calls)
    assert clock.now <= deadline + fake.cost
    assert_capped_pauses(
        clock.sleeps, fake.calls, interval=0.5, deadline=deadline, cost=0.3
    )


def test_timeout_zero_reads_only_the_baseline(clock, reader):
    fake = reader("old", "new")

    assert clipboard.wait_for_text_change(timeout=0) is None
    assert fake.calls == [START]
    assert clock.sleeps == []


def test_cancel_set_from_another_thread_ends_the_wait_promptly(
    monkeypatch, restore_text_clipboard
):
    """Real clock and Event: a 30 s interval is cut short by the setter."""
    monkeypatch.setattr(_wait, "_sleep", no_plain_sleep)
    calls = []

    def same() -> str:
        calls.append(time.monotonic())
        return "old"

    clipboard.set_text_clipboard_reader(same)
    before = threading.active_count()
    event = threading.Event()
    setter = threading.Thread(target=lambda: (time.sleep(0.2), event.set()))
    started = time.monotonic()
    setter.start()

    result = clipboard.wait_for_text_change(timeout=60, interval=30, cancel=event)

    elapsed = time.monotonic() - started
    setter.join(5)
    assert result is None
    assert elapsed < 10
    assert len(calls) == 1
    assert threading.active_count() == before


def test_cancel_wait_is_the_pause_and_set_cancel_stops_reading(clock, reader):
    fake = reader("old")
    cancel = FakeCancel(clock, set_on_wait=2)

    assert clipboard.wait_for_text_change(timeout=10, cancel=cancel) is None
    assert cancel.waits == [0.5, 0.5]
    assert fake.calls == [START, START + 0.5]
    assert clock.sleeps == []


def test_cancel_already_set_returns_none_without_reading(clock, reader):
    fake = reader("old", "new")
    event = threading.Event()
    event.set()

    assert clipboard.wait_for_text_change(timeout=5, cancel=event) is None
    assert fake.calls == []


def test_unset_cancel_still_returns_the_changed_text(clock, reader):
    reader("old", "new")
    cancel = FakeCancel(clock)

    assert clipboard.wait_for_text_change(timeout=5, cancel=cancel) == "new"
    assert cancel.waits == [0.5]


def test_wait_starts_no_thread(clock, reader):
    reader("old", "old", "new")
    before = threading.active_count()

    assert clipboard.wait_for_text_change(timeout=5) == "new"
    assert threading.active_count() == before
