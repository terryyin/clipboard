"""Bounded, cancellable waits over clipboard observations.

One observation loop (``_observe_until``) owns the deadline, cancellation and
sleep rules; each public wait supplies its observation and predicate (kind
membership through ``inspect``; changed text against a baseline through
``paste``, where the baseline is the loop's first observation). The
loop runs in the calling thread on a monotonic clock, starts no thread or
helper of its own, and lets every observation failure propagate at once.
``_monotonic`` and ``_sleep`` are module attributes so desktop-free tests can
drive the loop with a fake clock.
"""

from __future__ import annotations

import math
import numbers
import time
from collections.abc import Callable
from typing import Protocol, TypeVar, get_args

from clipboard import _offer, _text
from clipboard._errors import ClipboardContentError
from clipboard._offer import ClipboardKind, ClipboardOfferSnapshot

_T = TypeVar("_T")

_KINDS: tuple[str, ...] = get_args(ClipboardKind)

_NO_BASELINE = object()

_monotonic: Callable[[], float] = time.monotonic
_sleep: Callable[[float], object] = time.sleep


class _Cancel(Protocol):
    def is_set(self) -> bool: ...

    def wait(self, timeout: float | None = None) -> bool: ...


def _seconds(name: str, value: object, *, positive: bool) -> float:
    """``value`` as finite seconds (``> 0`` when ``positive``, else ``>= 0``)."""
    rule = "a positive finite number" if positive else "a non-negative finite number"
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ClipboardContentError(
            f"{name} must be {rule} of seconds; got {type(value).__name__} {value!r}"
        )
    seconds = float(value)
    if not math.isfinite(seconds) or seconds < 0 or (positive and seconds == 0):
        raise ClipboardContentError(f"{name} must be {rule} of seconds; got {value!r}")
    return seconds


def _validated_cancel(cancel: object) -> _Cancel | None:
    if cancel is None:
        return None
    if not (
        callable(getattr(cancel, "is_set", None))
        and callable(getattr(cancel, "wait", None))
    ):
        raise ClipboardContentError(
            "cancel must be None or an object with is_set() and wait(seconds), "
            f"such as threading.Event; got {type(cancel).__name__}"
        )
    return cancel  # type: ignore[return-value]


def _observe_until(
    observe: Callable[[], _T],
    satisfied: Callable[[_T], bool],
    *,
    timeout: object,
    interval: object,
    cancel: object,
) -> _T | None:
    """Observe until ``satisfied``; ``None`` at the deadline or on cancel.

    Arguments are validated before the first observation. Each round checks
    ``cancel``, observes, and returns the observation when it satisfies the
    predicate; otherwise it sleeps ``min(interval, remaining)`` (on
    ``cancel.wait`` when given) and observes again only while the deadline
    has not passed. ``timeout=0`` makes exactly one observation. Observation
    failures propagate unchanged and are never retried.
    """
    timeout_s = _seconds("timeout", timeout, positive=False)
    interval_s = _seconds("interval", interval, positive=True)
    event = _validated_cancel(cancel)
    deadline = _monotonic() + timeout_s
    while event is None or not event.is_set():
        observed = observe()
        if satisfied(observed):
            return observed
        remaining = deadline - _monotonic()
        if remaining <= 0:
            return None
        pause = min(interval_s, remaining)
        if event is None:
            _sleep(pause)
        elif event.wait(pause):
            return None
        if _monotonic() > deadline:
            return None
    return None


def wait_for_kind(
    kind: ClipboardKind,
    *,
    timeout: float,
    interval: float = 0.5,
    cancel: _Cancel | None = None,
) -> ClipboardOfferSnapshot | None:
    """Wait until the clipboard offers ``kind``; return that offer snapshot.

    ``kind`` is one of ``"text"``, ``"image"``, ``"html"``, ``"files"``. This
    is a state wait: each observation is one ``inspect()`` (no payload read,
    no ``clipboard[images]``, the clipboard is left unchanged), and the
    first snapshot whose ``kinds`` contain ``kind`` is returned, at once when
    it is already offered. ``timeout`` (required, non-negative finite
    seconds on a monotonic clock) bounds the wait; ``timeout=0`` observes
    once. ``interval`` (positive finite seconds) is the pause between
    observations. ``cancel`` is ``None`` or an object with ``is_set()`` and
    ``wait(seconds)`` such as ``threading.Event``; the pause waits on it, so
    setting it from another thread ends the wait promptly.

    Returns ``None`` at the deadline or once ``cancel`` is set, without
    another observation. Any ``ClipboardContentError`` from ``inspect()``
    (no session, missing helper, denied access, platform not available) is
    raised at once and never retried. An invalid ``kind``, ``timeout``,
    ``interval`` or ``cancel`` raises ``ClipboardContentError`` before the
    clipboard is observed.
    """
    if not isinstance(kind, str) or kind not in _KINDS:
        raise ClipboardContentError(
            f"kind must be one of {', '.join(_KINDS)}; got {kind!r}"
        )
    return _observe_until(
        _offer.inspect,
        lambda snapshot: kind in snapshot.kinds,
        timeout=timeout,
        interval=interval,
        cancel=cancel,
    )


def wait_for_text_change(
    *,
    timeout: float,
    interval: float = 0.5,
    cancel: _Cancel | None = None,
) -> str | None:
    """Wait until the clipboard text changes; return the new text.

    The first observation is one ``paste()``, kept as the baseline; each
    later ``paste()`` is compared with it, and the first observed text that
    is non-empty and differs from the baseline is returned. Clearing (``""``)
    or an offer with no text is not a change, and the wait continues.
    "Changed" compares observed values, not copy events: an identical recopy,
    and values that come and go between two observations, are missed. Only
    the baseline is kept and no text is logged.

    ``timeout``, ``interval`` and ``cancel`` follow ``wait_for_kind``: the
    baseline read is the wait's first observation and counts against the
    deadline, so ``timeout=0`` reads only the baseline and returns ``None``.
    Returns ``None`` at the deadline or once ``cancel`` is set (an
    already-set ``cancel`` reads nothing), without another observation. Any
    ``ClipboardContentError`` from ``paste()``, including the baseline read,
    is raised at once and never retried. An invalid ``timeout``,
    ``interval`` or ``cancel`` raises ``ClipboardContentError`` before the
    clipboard is read.
    """
    baseline: object = _NO_BASELINE

    def changed(text: str) -> bool:
        nonlocal baseline
        if baseline is _NO_BASELINE:
            baseline = text
            return False
        return text != "" and text != baseline

    return _observe_until(
        _text.paste,
        changed,
        timeout=timeout,
        interval=interval,
        cancel=cancel,
    )
