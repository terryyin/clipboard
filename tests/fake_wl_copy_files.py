"""In-memory Wayland selection standing in for ``subprocess`` in copy_files tests.

``FakeWaylandFiles.popen`` returns a ``FakeWlCopyFiles`` whose foreground part
takes the ``text/uri-list`` body on stdin and exits (status 0, or a scripted
status and stderr, or stalls past the bound); its background server takes the
selection after ``delay`` wl-paste runs, never, or with ``served`` bytes in
place of the body. ``FakeWaylandFiles.run`` answers ``wl-paste --list-types``
and ``wl-paste --type T --no-newline`` like wl-clipboard 2.x (``Nothing is
copied`` / ``No suitable type of content copied`` on stderr, exit 1). No
compositor, helper, or real clipboard is touched.
"""

from __future__ import annotations

import subprocess

URI_LIST = "text/uri-list"
LIST_TYPES = ["wl-paste", "--list-types"]
READ = ["wl-paste", "--type", URI_LIST, "--no-newline"]


class FakeWlCopyFiles:
    def __init__(self, wayland, cmd, stderr):
        self.wayland = wayland
        self.cmd = cmd
        self.log = stderr
        self.input = None
        self.timeout = None
        self.returncode = None
        self.killed = False

    def communicate(self, input=None, timeout=None):
        wayland = self.wayland
        assert 0 < timeout <= 10.0
        self.input, self.timeout = input, timeout
        if wayland.stalls:
            raise subprocess.TimeoutExpired(self.cmd, timeout)
        if wayland.copy_exit is not None:
            status, stderr = wayland.copy_exit
            self.log.write(stderr)
            self.returncode = status
            return None, None
        if wayland.server_stderr:
            self.log.write(wayland.server_stderr)
        if not wayland.never_offers:
            served = input if wayland.served is None else wayland.served
            wayland.pending = (wayland.delay, served)
        self.returncode = 0
        return None, None

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        self.returncode = -9
        return self.returncode


class FakeWaylandFiles:
    def __init__(self):
        self.offers = None  # None: nothing is copied
        self.calls = []
        self.popens = []
        self.popen_error = None
        self.copy_exit = None  # (status, stderr) for wl-copy's foreground part
        self.server_stderr = b""
        self.stalls = False
        self.never_offers = False
        self.served = None  # bytes the server offers instead of the body
        self.delay = 0
        self.pending = None
        self.run_failure = None  # (returncode, stderr) for every wl-paste run

    def run(self, cmd, *, stdin, capture_output, check, timeout):
        assert stdin is subprocess.DEVNULL
        assert capture_output is True and check is False
        assert 0 < timeout <= 2.0
        self.calls.append(cmd)
        if self.pending is not None:
            delay, served = self.pending
            if delay <= 0:
                self.offers, self.pending = {URI_LIST: served}, None
            else:
                self.pending = (delay - 1, served)
        if self.run_failure is not None:
            returncode, stderr = self.run_failure
            return subprocess.CompletedProcess(cmd, returncode, b"", stderr)
        if not self.offers:
            return self._fail(cmd, b"Nothing is copied\n")
        if cmd == LIST_TYPES:
            listing = "".join(f"{name}\n" for name in self.offers)
            return subprocess.CompletedProcess(cmd, 0, listing.encode(), b"")
        assert cmd == READ, cmd
        if URI_LIST not in self.offers:
            return self._fail(cmd, b"No suitable type of content copied\n")
        return subprocess.CompletedProcess(cmd, 0, self.offers[URI_LIST], b"")

    @staticmethod
    def _fail(cmd, stderr):
        return subprocess.CompletedProcess(cmd, 1, b"", stderr)

    def popen(self, cmd, *, stdin, stdout, stderr, start_new_session):
        assert stdin is subprocess.PIPE and stdout is subprocess.DEVNULL
        # Never a pipe the background server would inherit and hold open.
        assert hasattr(stderr, "write") and stderr is not subprocess.PIPE
        assert start_new_session is True
        if self.popen_error is not None:
            raise self.popen_error
        proc = FakeWlCopyFiles(self, cmd, stderr)
        self.popens.append(proc)
        return proc
