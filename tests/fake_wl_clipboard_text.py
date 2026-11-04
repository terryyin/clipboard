"""In-memory Wayland selections and wl-clipboard helpers standing in for ``subprocess``.

Each selection has its own offers: ``FakeWayland.offers`` is the regular
selection (CLIPBOARD; ``None``: nothing is copied) and ``FakeWayland.primary``
is PRIMARY, reached by argv carrying ``--primary``. ``FakeWayland.run``
answers ``wl-paste [--primary] --list-types`` and ``wl-paste [--primary] -n
-t T`` like wl-clipboard 2.x (``Nothing is copied`` / ``No suitable type of
content copied`` on stderr, exit 1); ``FakeWayland.popen`` returns a
``FakeWlCopy`` whose foreground part sets (or clears) its selection, exits
with a given status and stderr, or stalls past the bound.
``primary_unsupported`` makes every ``--primary`` run report wl-clipboard
2.2.1's unsupported wording (exit 1); ``drops_primary`` makes
``wl-copy --primary`` exit 0 without changing PRIMARY (Sway with
``primary_selection disabled``). ``install_wayland_text_session`` routes
``subprocess`` to a new fake in a Wayland-only text session.
"""

import subprocess

from fake_pyperclip import FakePyperclip

PRIMARY_UNSUPPORTED = b"The compositor does not seem to support primary selection\n"

# What wl-copy 2.x lists for a text type: the type plus its generic family.
WL_COPY_TEXT_FAMILY = (
    "text/plain;charset=utf-8",
    "text/plain",
    "TEXT",
    "STRING",
    "UTF8_STRING",
)


def text_offer(text):
    """What wl-copy offers for ``text``: its UTF-8 bytes under the text family."""
    return dict.fromkeys(WL_COPY_TEXT_FAMILY, text.encode())


def install_wayland_text_session(text_session, monkeypatch):
    """A ``FakeWayland`` serving ``subprocess`` in a Wayland-only text session
    (pyperclip faked as ``fake.pyperclip`` to show it is never used)."""
    fake = FakeWayland()
    monkeypatch.setattr(subprocess, "run", fake.run)
    monkeypatch.setattr(subprocess, "Popen", fake.popen)
    text_session("linux", {"WAYLAND_DISPLAY": "wayland-0"}, ("wl-copy", "wl-paste"))
    fake.pyperclip = FakePyperclip(monkeypatch)
    return fake


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
        selection = self.wayland.selection(self.cmd)
        if self.wayland.copy_exit is not None:
            status, stderr = self.wayland.copy_exit
            self.log.write(stderr)
            self.returncode = status
            return None, None
        if selection == "primary" and self.wayland.primary_unsupported:
            self.log.write(PRIMARY_UNSUPPORTED)
            self.returncode = 1
            return None, None
        self.returncode = 0
        if selection == "primary" and self.wayland.drops_primary:
            return None, None
        if "--clear" in self.cmd:
            self.wayland.selections[selection] = None
        else:
            self.wayland.selections[selection] = dict.fromkeys(
                WL_COPY_TEXT_FAMILY, input
            )
        return None, None

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        self.returncode = -9
        return self.returncode


class FakeWayland:
    def __init__(self):
        self.selections = {"clipboard": None, "primary": None}  # None: nothing
        self.primary_unsupported = False
        self.drops_primary = False
        self.calls = []
        self.run_error = None
        self.run_failure = None  # (returncode, stderr) for every run
        self.popen_error = None
        self.popens = []
        self.copy_exit = None  # (status, stderr) for wl-copy's foreground part
        self.stalls = False
        self.communicate_timeouts = []

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

    def only_primary_ran(self):
        """Whether every wl-paste run and wl-copy start carried ``--primary``."""
        return all("--primary" in c["cmd"] for c in self.calls) and all(
            "--primary" in proc.cmd for proc in self.popens
        )

    @staticmethod
    def selection(cmd):
        return "primary" if "--primary" in cmd else "clipboard"

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
        selection = self.selection(cmd)
        flags = ["--primary"] if selection == "primary" else []
        if selection == "primary" and self.primary_unsupported:
            return self._fail(cmd, PRIMARY_UNSUPPORTED)
        offers = self.selections[selection]
        if not offers:
            return self._fail(cmd, b"Nothing is copied\n")
        if cmd == ["wl-paste", *flags, "--list-types"]:
            listing = "".join(f"{t}\n" for t in offers)
            return subprocess.CompletedProcess(cmd, 0, listing.encode(), b"")
        assert cmd[: 3 + len(flags)] == ["wl-paste", *flags, "-n", "-t"], cmd
        assert len(cmd) == 4 + len(flags), cmd
        if cmd[-1] not in offers:
            return self._fail(cmd, b"No suitable type of content copied\n")
        return subprocess.CompletedProcess(cmd, 0, offers[cmd[-1]], b"")

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
