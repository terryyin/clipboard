"""In-memory X11 selections and xclip owners standing in for ``subprocess``.

Each selection (``-selection clipboard`` / ``-selection primary``) has its own
offers: ``FakeX11.offers`` is CLIPBOARD (``None``: no owner) and
``FakeX11.primary`` is PRIMARY. ``FakeX11.run`` answers
``xclip -selection S -o -t T`` like xclip 0.13 (``target T not available`` on
stderr, exit 1); ``FakeX11.popen`` starts a ``FakeOwner`` that takes the
selection named in its argv with the text already on its stdin file after
``delay`` read-backs, exits early, or never offers.
"""

import subprocess


class FakeOwner:
    """A background ``xclip -i``: takes its selection after ``delay`` read-backs."""

    def __init__(self, x11, stderr, data: bytes, selection: str):
        self.x11 = x11
        self.log = stderr
        self.pid = 4242
        self.status = None
        self.data = data
        if self.x11.owner_exit is not None:
            self._exit()
        elif not self.x11.never_offers:
            self.status = 0  # xclip forks; its background child owns CLIPBOARD
            self.x11.pending = (selection, self.x11.delay, self.data)

    def _exit(self):
        status, stderr = self.x11.owner_exit
        self.log.write(stderr)
        self.status = status

    def poll(self):
        return self.status


class FakeX11:
    def __init__(self):
        self.selections = {"clipboard": None, "primary": None}  # None: no owner
        self.calls = []
        self.run_error = None
        self.run_failure = None  # (returncode, stderr) for every run
        self.popen_error = None
        self.popens = []
        self.owner_exit = None  # (status, stderr) when the owner dies early
        self.never_offers = False
        self.delay = 0
        self.pending = None
        self.killed = []

    @property
    def offers(self):
        return self.selections["clipboard"]

    @offers.setter
    def offers(self, offers):
        self.selections["clipboard"] = offers

    @property
    def primary(self):
        return self.selections["primary"]

    @primary.setter
    def primary(self, offers):
        self.selections["primary"] = offers

    @staticmethod
    def _selection(cmd):
        assert cmd[:2] == ["xclip", "-selection"], cmd
        return cmd[2]

    def run(self, cmd, *, stdin, capture_output, check, timeout):
        assert stdin is subprocess.DEVNULL
        assert capture_output is True and check is False
        assert 0 < timeout <= 10.0
        self.calls.append({"cmd": cmd, "timeout": timeout})
        if self.pending is not None:
            selection, delay, data = self.pending
            if delay <= 0:
                self.selections[selection] = {"UTF8_STRING": data}
                self.pending = None
            else:
                self.pending = (selection, delay - 1, data)
        if self.run_error is not None:
            raise self.run_error
        if self.run_failure is not None:
            returncode, stderr = self.run_failure
            return subprocess.CompletedProcess(cmd, returncode, b"", stderr)
        offers = self.selections[self._selection(cmd)]
        if offers is None:
            return self._fail(cmd, b"Error: target TARGETS not available\n")
        target = cmd[-1]
        if target == "TARGETS":
            listing = "\n".join(["TARGETS", *offers]) + "\n"
            return subprocess.CompletedProcess(cmd, 0, listing.encode(), b"")
        if target not in offers:
            return self._fail(cmd, f"Error: target {target} not available\n".encode())
        return subprocess.CompletedProcess(cmd, 0, offers[target], b"")

    @staticmethod
    def _fail(cmd, stderr):
        return subprocess.CompletedProcess(cmd, 1, b"", stderr)

    def popen(self, cmd, *, stdin, stdout, stderr, start_new_session):
        # Writer feeds an unlinked temp file, never a pipe Python would block on.
        assert stdin is not subprocess.PIPE and hasattr(stdin, "read")
        assert stdout is subprocess.DEVNULL
        assert hasattr(stderr, "write") and start_new_session is True
        if self.popen_error is not None:
            raise self.popen_error
        owner = FakeOwner(self, stderr, stdin.read(), self._selection(cmd))
        self.popens.append({"cmd": cmd, "owner": owner})
        return owner
