"""The libX11 relinquish child (``clipboard/_x11_relinquish.py``).

The library handle is a recording fake; one test runs the real script under
``python -I`` with no ``DISPLAY``, where nothing can be cleared.
"""

import json
import os
import subprocess

import pytest

from clipboard import _clear_x11, _x11_relinquish


class _FakeLibX11:
    """Records the libX11 calls the relinquish sequence makes, in order."""

    DISPLAY = 0x5EED
    CLIPBOARD = 233

    def __init__(self, *, display=DISPLAY, atom=CLIPBOARD):
        self.calls = []

        def record(name, result):
            def call(*args):
                self.calls.append((name, args))
                return result

            return call

        self.XOpenDisplay = record("XOpenDisplay", display)
        self.XInternAtom = record("XInternAtom", atom)
        self.XSetSelectionOwner = record("XSetSelectionOwner", 1)
        self.XSync = record("XSync", 1)
        self.XCloseDisplay = record("XCloseDisplay", 0)


def test_relinquish_sequence_sets_clipboard_owner_to_none():
    lib = _FakeLibX11()
    _x11_relinquish.relinquish_clipboard(lib)
    d, atom = _FakeLibX11.DISPLAY, _FakeLibX11.CLIPBOARD
    assert lib.calls == [
        ("XOpenDisplay", (None,)),
        ("XInternAtom", (d, b"CLIPBOARD", 0)),
        ("XSetSelectionOwner", (d, atom, 0, 0)),
        ("XSync", (d, 0)),
        ("XCloseDisplay", (d,)),
    ]


def test_relinquish_unopenable_display_is_classified_and_calls_nothing_else():
    lib = _FakeLibX11(display=None)
    with pytest.raises(_x11_relinquish.X11Failure) as excinfo:
        _x11_relinquish.relinquish_clipboard(lib)
    assert excinfo.value.kind == "display"
    assert lib.calls == [("XOpenDisplay", (None,))]


def test_relinquish_missing_atom_still_closes_display():
    lib = _FakeLibX11(atom=0)
    with pytest.raises(_x11_relinquish.X11Failure) as excinfo:
        _x11_relinquish.relinquish_clipboard(lib)
    assert excinfo.value.kind == "atom"
    assert [name for name, _ in lib.calls] == [
        "XOpenDisplay",
        "XInternAtom",
        "XCloseDisplay",
    ]


def test_load_libx11_declares_signatures_and_falls_back_to_soname():
    import ctypes

    loaded = []

    def load(name):
        loaded.append(name)
        return _FakeLibX11()

    lib = _x11_relinquish.load_libx11(find_library=lambda name: None, load=load)
    assert loaded == ["libX11.so.6"]
    assert lib.XOpenDisplay.restype is ctypes.c_void_p
    assert lib.XInternAtom.restype is ctypes.c_ulong
    assert lib.XSetSelectionOwner.argtypes == [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
    ]
    assert lib.XSync.argtypes == [ctypes.c_void_p, ctypes.c_int]
    assert lib.XCloseDisplay.argtypes == [ctypes.c_void_p]


def test_load_libx11_missing_names_every_candidate():
    def load(name):
        raise OSError(f"{name}: cannot open shared object file")

    with pytest.raises(_x11_relinquish.X11Failure) as excinfo:
        _x11_relinquish.load_libx11(find_library=lambda name: "libX11.so", load=load)
    assert excinfo.value.kind == "libx11"
    assert "libX11.so:" in excinfo.value.detail
    assert "libX11.so.6:" in excinfo.value.detail


@pytest.mark.parametrize(
    ("load", "exit_code", "outcome"),
    [
        (_FakeLibX11, 0, {"ok": True}),
        (
            lambda: _FakeLibX11(display=None),
            3,
            {"failure": "display", "detail": "XOpenDisplay returned NULL"},
        ),
    ],
    ids=["ok", "display"],
)
def test_relinquish_main_reports_one_json_line(capsys, load, exit_code, outcome):
    assert _x11_relinquish.main(load=load) == exit_code
    assert json.loads(capsys.readouterr().out) == outcome


def test_relinquish_script_runs_standalone_without_a_display():
    """The real child under ``python -I``, no DISPLAY: nothing can be cleared.

    It imports nothing from the package and reports a classified failure:
    libX11 missing (e.g. macOS) or no display to open (Linux with libX11).
    """
    env = {k: v for k, v in os.environ.items() if k != "DISPLAY"}
    result = subprocess.run(
        _clear_x11._relinquish_command(),
        env=env,
        cwd="/",
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 3, result.stderr
    assert json.loads(result.stdout)["failure"] in {"libx11", "display"}
