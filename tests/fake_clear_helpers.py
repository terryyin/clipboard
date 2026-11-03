"""Scripted ``subprocess.run`` stand-ins for the native ``clear()`` adapters.

``FakeClearHelper`` answers or raises like ``osascript``;
``FakeWlCopyClear`` answers ``wl-copy --clear`` (stderr written to the
clearer's file) and routes any other command to ``x11_child``, because
``_clear_wayland`` and ``_clear_x11`` share one ``subprocess`` module;
``FakeX11ClearChild`` answers the libX11 clear child with its one JSON
outcome line.
"""

import json
import subprocess


class FakeClearHelper:
    """Stand-in for ``subprocess.run``: records calls, answers or raises."""

    def __init__(self, *, returncode=0, stdout="ok\n", stderr="", raises=None):
        self.result = subprocess.CompletedProcess([], returncode, stdout, stderr)
        self.raises = raises
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if self.raises is not None:
            raise self.raises
        return self.result


class FakeWlCopyClear(FakeClearHelper):
    """``wl-copy`` with stderr to a file; other commands go to ``x11_child``.

    ``x11_child`` defaults to ``None``, which fails the test: the session must
    not reach the X11 clearer.
    """

    x11_child = None

    def __call__(self, args, **kwargs):
        if args[:1] != ["wl-copy"]:
            if self.x11_child is None:
                raise AssertionError("this session must not run the X11 clear child")
            return self.x11_child(args, **kwargs)
        self.calls.append((args, kwargs))
        if self.raises is not None:
            raise self.raises
        if self.result.stderr:
            kwargs["stderr"].write(self.result.stderr.encode())
        return subprocess.CompletedProcess(args, self.result.returncode)


class FakeX11ClearChild(FakeClearHelper):
    """The libX11 clear child: ``outcome`` is its JSON stdout line."""

    def __init__(self, *, outcome=None, **kwargs):
        stdout = "" if outcome is None else json.dumps(outcome) + "\n"
        kwargs.setdefault("stdout", stdout)
        super().__init__(**kwargs)
