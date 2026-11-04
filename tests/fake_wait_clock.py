"""Fake monotonic clock, scripted observations and cancel for wait tests.

The wait's clock and sleep are ``clipboard._wait`` attributes; the fake clock
advances only when the wait sleeps (or an observation is made to take time),
so deadlines are exact.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import clipboard
from clipboard import _wait

EMPTY = clipboard.ClipboardOfferSnapshot(kinds=frozenset(), formats=())
IMAGE = clipboard.ClipboardOfferSnapshot(
    kinds=frozenset({"image"}), formats=("public.png", "public.tiff")
)
TEXT = clipboard.ClipboardOfferSnapshot(
    kinds=frozenset({"text"}), formats=("public.utf8-plain-text",)
)
START = 100.0


class _OnlyIsSet:
    def is_set(self) -> bool:
        return False


# ``(named, options)``: every wait rejects these before observing, naming
# ``named``; shared because one loop owns timeout / interval / cancel rules.
INVALID_WAIT_OPTIONS = [
    ("timeout", {"timeout": -1}),
    ("timeout", {"timeout": -0.001}),
    ("timeout", {"timeout": math.nan}),
    ("timeout", {"timeout": math.inf}),
    ("timeout", {"timeout": -math.inf}),
    ("timeout", {"timeout": True}),
    ("timeout", {"timeout": False}),
    ("timeout", {"timeout": "1"}),
    ("timeout", {"timeout": None}),
    ("interval", {"timeout": 1, "interval": 0}),
    ("interval", {"timeout": 1, "interval": 0.0}),
    ("interval", {"timeout": 1, "interval": -0.5}),
    ("interval", {"timeout": 1, "interval": math.nan}),
    ("interval", {"timeout": 1, "interval": math.inf}),
    ("interval", {"timeout": 1, "interval": True}),
    ("interval", {"timeout": 1, "interval": "0.5"}),
    ("interval", {"timeout": 1, "interval": None}),
    ("cancel", {"timeout": 1, "cancel": object()}),
    ("cancel", {"timeout": 1, "cancel": _OnlyIsSet()}),
    ("cancel", {"timeout": 1, "cancel": True}),
]


def option_id(value) -> str | None:
    """Readable pytest ids for ``INVALID_WAIT_OPTIONS`` rows."""
    return repr(value) if not isinstance(value, dict) else None


def no_plain_sleep(seconds: float) -> None:
    """``_wait._sleep`` stand-in proving a given cancel is the only pause."""
    raise AssertionError(f"plain sleep({seconds}) used while cancel was given")


class FakeClock:
    """Monotonic time that moves only when slept on (or advanced)."""

    def __init__(self) -> None:
        self.now = START
        self.sleeps: list[float] = []
        self.overshoot = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds + self.overshoot


class Scripted:
    """Scripted observation results (offers or texts); records the clock time
    of each call. The last result repeats; an exception result is raised."""

    def __init__(self, clock: FakeClock, *results, cost=0.0):
        self.clock = clock
        self.results = list(results)
        self.cost = cost
        self.calls: list[float] = []

    def __call__(self):
        self.calls.append(self.clock.now)
        self.clock.now += self.cost
        index = min(len(self.calls), len(self.results)) - 1
        result = self.results[index]
        if isinstance(result, BaseException):
            raise result
        return result


class FakeCancel:
    """Duck-typed cancel (``is_set`` / ``wait``) on the fake clock."""

    def __init__(self, clock: FakeClock, *, set_on_wait: int | None = None):
        self.clock = clock
        self.set_on_wait = set_on_wait
        self.waits: list[float] = []
        self.flag = False

    def is_set(self) -> bool:
        return self.flag

    def wait(self, timeout=None) -> bool:
        self.waits.append(timeout)
        if self.set_on_wait is not None and len(self.waits) >= self.set_on_wait:
            self.flag = True
            return True
        self.clock.now += timeout
        return False


def install_fake_clock(monkeypatch) -> FakeClock:
    """Drive ``clipboard._wait`` with a fresh ``FakeClock``."""
    fake = FakeClock()
    monkeypatch.setattr(_wait, "_monotonic", fake.monotonic)
    monkeypatch.setattr(_wait, "_sleep", fake.sleep)
    return fake


def _installer(clock: FakeClock, seam) -> Callable[..., Scripted]:
    def install(*results, **kwargs) -> Scripted:
        fake = Scripted(clock, *results, **kwargs)
        seam(fake)
        return fake

    return install


def inspector_installer(clock: FakeClock) -> Callable[..., Scripted]:
    """Return ``install(*offers, cost=...)`` injecting a scripted inspector."""
    return _installer(clock, clipboard.set_clipboard_inspector)


def reader_installer(clock: FakeClock) -> Callable[..., Scripted]:
    """Return ``install(*texts, cost=...)`` injecting a scripted text reader."""
    return _installer(clock, clipboard.set_text_clipboard_reader)


def assert_capped_pauses(pauses, calls, *, interval, deadline, cost=0.0):
    """Every pause is ``min(interval, remaining)`` and strictly positive."""
    assert pauses
    for pause, observed_at in zip(pauses, calls[: len(pauses)], strict=True):
        remaining = deadline - (observed_at + cost)
        assert pause == min(interval, remaining)
        assert pause > 0
