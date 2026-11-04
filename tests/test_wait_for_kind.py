"""Desktop-free proofs for ``clipboard.wait_for_kind`` outcomes and pauses.

A fake clock (``fake_wait_clock``) makes deadlines exact. Cancellation from
another thread uses a real ``threading.Event`` on the real clock with a
generous bound. Failures and argument validation live in
``test_wait_for_kind_failures.py``.
"""

from __future__ import annotations

import threading
import time

import pytest
from fake_wait_clock import (
    EMPTY,
    IMAGE,
    START,
    TEXT,
    FakeCancel,
    assert_capped_pauses,
    inspector_installer,
    install_fake_clock,
    no_plain_sleep,
)

import clipboard
from clipboard import _wait


@pytest.fixture
def clock(monkeypatch):
    return install_fake_clock(monkeypatch)


@pytest.fixture
def inspector(clock, restore_clipboard_inspector):
    return inspector_installer(clock)


def test_kind_appearing_after_several_observations_returns_that_snapshot(
    clock, inspector
):
    fake = inspector(EMPTY, EMPTY, IMAGE)

    result = clipboard.wait_for_kind("image", timeout=30)

    assert result is IMAGE
    assert fake.calls == [START, START + 0.5, START + 1.0]
    assert clock.sleeps == [0.5, 0.5]


def test_kind_already_offered_returns_at_once_after_one_observation(clock, inspector):
    fake = inspector(TEXT)

    assert clipboard.wait_for_kind("text", timeout=5) is TEXT
    assert fake.calls == [START]
    assert clock.sleeps == []


def test_other_kinds_do_not_satisfy_the_wait(clock, inspector):
    both = clipboard.ClipboardOfferSnapshot(
        kinds=frozenset({"html", "text"}), formats=("text/html", "text/plain")
    )
    fake = inspector(TEXT, IMAGE, both)

    assert clipboard.wait_for_kind("html", timeout=10, interval=1) is both
    assert len(fake.calls) == 3


def test_deadline_returns_none_with_no_observation_after_it(clock, inspector):
    fake = inspector(EMPTY)
    deadline = START + 1.25

    assert clipboard.wait_for_kind("html", timeout=1.25, interval=0.5) is None
    assert fake.calls == [START, START + 0.5, START + 1.0, START + 1.25]
    assert clock.sleeps == [0.5, 0.5, 0.25]
    assert max(fake.calls) <= deadline
    assert_capped_pauses(clock.sleeps, fake.calls, interval=0.5, deadline=deadline)


def test_sleep_overshooting_the_deadline_starts_no_further_observation(
    clock, inspector
):
    clock.overshoot = 1.0
    fake = inspector(EMPTY)

    assert clipboard.wait_for_kind("text", timeout=1, interval=0.5) is None
    assert fake.calls == [START]
    assert clock.sleeps == [0.5]


def test_slow_observation_returns_by_timeout_plus_one_observation(clock, inspector):
    fake = inspector(EMPTY, cost=0.3)
    deadline = START + 1.0

    assert clipboard.wait_for_kind("text", timeout=1, interval=0.5) is None
    assert all(at <= deadline for at in fake.calls)
    assert clock.now <= deadline + fake.cost
    assert_capped_pauses(
        clock.sleeps, fake.calls, interval=0.5, deadline=deadline, cost=0.3
    )


def test_timeout_zero_observes_exactly_once_without_sleeping(clock, inspector):
    fake = inspector(EMPTY)

    assert clipboard.wait_for_kind("text", timeout=0) is None
    assert fake.calls == [START]
    assert clock.sleeps == []


def test_timeout_zero_still_returns_an_offered_kind(clock, inspector):
    inspector(IMAGE)

    assert clipboard.wait_for_kind("image", timeout=0) is IMAGE


def test_cancel_set_from_another_thread_ends_the_wait_promptly(
    monkeypatch, restore_clipboard_inspector
):
    """Real clock and Event: a 30 s interval is cut short by the setter."""
    monkeypatch.setattr(_wait, "_sleep", no_plain_sleep)
    calls = []

    def empty() -> clipboard.ClipboardOfferSnapshot:
        calls.append(time.monotonic())
        return EMPTY

    clipboard.set_clipboard_inspector(empty)
    before = threading.active_count()
    event = threading.Event()
    setter = threading.Thread(target=lambda: (time.sleep(0.2), event.set()))
    started = time.monotonic()
    setter.start()

    result = clipboard.wait_for_kind("text", timeout=60, interval=30, cancel=event)

    elapsed = time.monotonic() - started
    setter.join(5)
    assert result is None
    assert elapsed < 10
    assert len(calls) == 1
    assert threading.active_count() == before


def test_cancel_wait_is_the_pause_and_set_cancel_stops_observing(clock, inspector):
    fake = inspector(EMPTY)
    cancel = FakeCancel(clock, set_on_wait=3)
    deadline = START + 1.25

    assert (
        clipboard.wait_for_kind("text", timeout=1.25, interval=0.5, cancel=cancel)
        is None
    )
    assert cancel.waits == [0.5, 0.5, 0.25]
    assert fake.calls == [START, START + 0.5, START + 1.0]
    assert clock.sleeps == []
    assert_capped_pauses(cancel.waits, fake.calls, interval=0.5, deadline=deadline)


def test_cancel_already_set_returns_none_without_observing(clock, inspector):
    fake = inspector(TEXT)
    event = threading.Event()
    event.set()

    assert clipboard.wait_for_kind("text", timeout=5, cancel=event) is None
    assert fake.calls == []
    assert clock.sleeps == []


def test_unset_cancel_still_returns_the_offered_kind(clock, inspector):
    inspector(EMPTY, IMAGE)
    cancel = FakeCancel(clock)

    assert clipboard.wait_for_kind("image", timeout=5, cancel=cancel) is IMAGE
    assert cancel.waits == [0.5]


def test_wait_starts_no_thread(clock, inspector):
    inspector(EMPTY, EMPTY, TEXT)
    before = threading.active_count()

    assert clipboard.wait_for_kind("text", timeout=5) is TEXT
    assert threading.active_count() == before
