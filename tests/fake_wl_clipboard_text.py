"""In-memory Wayland selection and wl-clipboard helpers standing in for ``subprocess``.

``FakeWayland.run`` answers ``wl-paste --list-types`` and ``wl-paste -n -t T``
like wl-clipboard 2.x (``Nothing is copied`` / ``No suitable type of content
copied`` on stderr, exit 1); ``FakeWayland.popen`` returns a ``FakeWlCopy``
whose foreground part sets (or clears) the selection, exits with a given
status and stderr, or stalls past the bound.
"""

import subprocess

# What wl-copy 2.x lists for a text type: the type plus its generic family.
WL_COPY_TEXT_FAMILY = (
    "text/plain;charset=utf-8",
    "text/plain",
    "TEXT",
    "STRING",
    "UTF8_STRING",
)


class FakeWlCopy:
    def __init__(self, wayland, cmd, stdin, stderr):
        self.wayland = wayland
        self.cmd = cmd
        self.stdin = stdin
        self.log = stderr
        self.returncode = None
        self.input = None
        self.killed = False

    def communicate(self, input=None, timeout=None):
        assert 0 < timeout <= 10.0
        self.input = input
        self.wayland.communicate_timeouts.append(timeout)
        if self.wayland.stalls:
            raise subprocess.TimeoutExpired(self.cmd, timeout)
        if self.wayland.copy_exit is not None:
            status, stderr = self.wayland.copy_exit
            self.log.write(stderr)
            self.returncode = status
            return None, None
        if "--clear" in self.cmd:
            self.wayland.offers = None
        else:
            self.wayland.offers = dict.fromkeys(WL_COPY_TEXT_FAMILY, input)
        self.returncode = 0
        return None, None

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        self.returncode = -9
        return self.returncode


class FakeWayland:
    def __init__(self):
        self.offers = None  # None: nothing is copied
        self.calls = []
        self.run_error = None
        self.run_failure = None  # (returncode, stderr) for every run
        self.popen_error = None
        self.popens = []
        self.copy_exit = None  # (status, stderr) for wl-copy's foreground part
        self.stalls = False
        self.communicate_timeouts = []

    def run(self, cmd, *, stdin, capture_output, check, timeout):
        assert stdin is subprocess.DEVNULL
        assert capture_output is True and check is False
        assert 0 < timeout <= 10.0
        self.calls.append({"cmd": cmd, "timeout": timeout})
        if self.run_error is not None:
            raise self.run_error
        if self.run_failure is not None:
            returncode, stderr = self.run_failure
            return subprocess.CompletedProcess(cmd, returncode, b"", stderr)
        if not self.offers:
            return self._fail(cmd, b"Nothing is copied\n")
        if cmd == ["wl-paste", "--list-types"]:
            listing = "".join(f"{t}\n" for t in self.offers)
            return subprocess.CompletedProcess(cmd, 0, listing.encode(), b"")
        assert cmd[:3] == ["wl-paste", "-n", "-t"] and len(cmd) == 4
        if cmd[3] not in self.offers:
            return self._fail(cmd, b"No suitable type of content copied\n")
        return subprocess.CompletedProcess(cmd, 0, self.offers[cmd[3]], b"")

    @staticmethod
    def _fail(cmd, stderr):
        return subprocess.CompletedProcess(cmd, 1, b"", stderr)

    def popen(self, cmd, *, stdin, stdout, stderr, start_new_session):
        assert stdout is subprocess.DEVNULL
        assert hasattr(stderr, "write") and start_new_session is True
        if self.popen_error is not None:
            raise self.popen_error
        proc = FakeWlCopy(self, cmd, stdin, stderr)
        self.popens.append(proc)
        return proc
