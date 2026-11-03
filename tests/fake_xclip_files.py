"""In-memory X11 CLIPBOARD standing in for ``subprocess`` in copy_files tests.

``FakeX11Files.run`` answers ``xclip -o -t T`` like xclip 0.13 (``target T not
available`` on stderr, exit 1, ``TARGETS`` listing otherwise);
``FakeX11Files.popen`` starts a ``FakeUriListOwner`` that takes CLIPBOARD with
the ``text/uri-list`` body already on its stdin file after ``delay`` helper
runs, exits early, or never offers. No display, helper, or real clipboard is
touched.
"""

from __future__ import annotations

import subprocess

URI_LIST = "text/uri-list"


class FakeUriListOwner:
    """A forking ``xclip -t text/uri-list``: stdin file body, then background owner."""

    def __init__(self, x11, stderr, data: bytes):
        self.x11 = x11
        self.log = stderr
        self.pid = 5151
        self.status = None
        self.data = data
        if self.x11.owner_exit is not None:
            self._exit()
        elif not self.x11.never_offers:
            self.status = 0  # xclip forks; its background child owns CLIPBOARD
            self.x11.pending = (self.x11.delay, self.data)

    def _exit(self):
        status, stderr = self.x11.owner_exit
        self.log.write(stderr)
        self.status = status

    def poll(self):
        return self.status


class FakeX11Files:
    def __init__(self):
        self.offers = None  # None: CLIPBOARD has no owner
        self.calls = []
        self.popen_error = None
        self.popens = []
        self.owner_exit = None  # (status, stderr) when the owner dies early
        self.never_offers = False
        self.delay = 0
        self.pending = None
        self.killed = []

    def run(self, cmd, **kwargs):
        assert kwargs["capture_output"] is True and kwargs["check"] is False
        assert 0 < kwargs["timeout"] <= 10.0
        self.calls.append(cmd)
        if self.pending is not None:
            delay, data = self.pending
            if delay <= 0:
                self.offers, self.pending = {URI_LIST: data}, None
            else:
                self.pending = (delay - 1, data)
        if self.offers is None:
            return self._fail(cmd, b"Error: target TARGETS not available\n")
        target = cmd[-1]
        if target == "TARGETS":
            listing = "\n".join(["TARGETS", *self.offers]) + "\n"
            return subprocess.CompletedProcess(cmd, 0, listing.encode(), b"")
        if target not in self.offers:
            return self._fail(cmd, f"Error: target {target} not available\n".encode())
        return subprocess.CompletedProcess(cmd, 0, self.offers[target], b"")

    @staticmethod
    def _fail(cmd, stderr):
        return subprocess.CompletedProcess(cmd, 1, b"", stderr)

    def popen(self, cmd, *, stdin, stdout, stderr, start_new_session):
        # Writer feeds an unlinked temp file, never a pipe Python would block on.
        assert stdin is not subprocess.PIPE and hasattr(stdin, "read")
        assert stdout is subprocess.DEVNULL
        # Never a pipe the background owner would inherit and hold open.
        assert hasattr(stderr, "write") and stderr is not subprocess.PIPE
        assert start_new_session is True
        if self.popen_error is not None:
            raise self.popen_error
        body = stdin.read()
        owner = FakeUriListOwner(self, stderr, body)
        self.popens.append({"cmd": cmd, "owner": owner})
        return owner
