"""Desktop-free checks of the CI readiness wait for a headless compositor.

A socket alone is not readiness: the wait needs a ``wl-paste --list-types``
round trip that lists an offer or reports nothing copied. ``subprocess.run``,
the socket, the clock and sleep are all fakes.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import await_wayland_compositor as readiness  # noqa: E402


class FakeSocket:
    def __init__(self, appears_after: int = 0):
        self.checks = 0
        self.appears_after = appears_after

    def is_socket(self):
        self.checks += 1
        return self.checks > self.appears_after

    def __str__(self):
        return "/run/wayland-1"


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def runner(*answers):
    """``subprocess.run`` fake: each call takes the next answer (last repeats)."""
    calls = []

    def run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        answer = answers[min(len(calls), len(answers)) - 1]
        if isinstance(answer, BaseException):
            raise answer
        returncode, stderr = answer
        return subprocess.CompletedProcess(cmd, returncode, "", stderr)

    return run, calls


def wait(socket, run, clock, deadline_s=30.0):
    return readiness.await_compositor(
        socket, deadline_s=deadline_s, run=run, clock=clock, sleep=clock.sleep
    )


def test_nothing_copied_answer_is_ready_without_selecting_anything():
    run, calls = runner((1, "Nothing is copied\n"))

    assert wait(FakeSocket(), run, Clock()) is None
    assert [cmd for cmd, _ in calls] == [["wl-paste", "--list-types"]]
    assert calls[0][1]["timeout"] == readiness.ATTEMPT_TIMEOUT_S


def test_a_listed_offer_is_ready():
    run, _ = runner((0, ""))

    assert wait(FakeSocket(), run, Clock()) is None


def test_no_round_trip_is_tried_before_the_socket_exists():
    socket = FakeSocket(appears_after=3)
    run, calls = runner((1, "Nothing is copied"))

    assert wait(socket, run, Clock()) is None
    assert socket.checks == 4
    assert len(calls) == 1


def test_a_stalled_compositor_is_retried_until_it_answers():
    stalled = subprocess.TimeoutExpired(["wl-paste"], readiness.ATTEMPT_TIMEOUT_S)
    run, calls = runner(stalled, (1, "Failed to connect to a Wayland server"), (0, ""))

    assert wait(FakeSocket(), run, Clock()) is None
    assert len(calls) == 3


def test_deadline_returns_the_last_reason():
    run, _ = runner((1, "Failed to connect to a Wayland server"))

    reason = wait(FakeSocket(), run, Clock(), deadline_s=1.0)

    assert "Failed to connect to a Wayland server" in reason


def test_deadline_without_a_socket_names_the_socket():
    run, calls = runner((0, ""))

    reason = wait(FakeSocket(appears_after=10**6), run, Clock(), deadline_s=1.0)

    assert "/run/wayland-1" in reason
    assert calls == []
