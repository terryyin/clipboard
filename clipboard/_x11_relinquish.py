"""Relinquish the X11 CLIPBOARD selection through libX11 (stdlib only).

``clipboard._clear_x11`` runs this file as a standalone script in a child
Python (``python -I <this file>``), so a wedged X connection or a libX11
error handler that exits the process cannot hang or kill the caller. It
imports nothing from the ``clipboard`` package.

The sequence is ``XOpenDisplay(NULL)`` (uses ``DISPLAY``),
``XInternAtom(display, "CLIPBOARD", False)``,
``XSetSelectionOwner(display, CLIPBOARD, None, CurrentTime)``,
``XSync(display, False)`` and ``XCloseDisplay``. Setting the owner to
``None`` makes the X server send the current owner ``SelectionClear``, so
CLIPBOARD has no owner (and no offer) afterwards. ``XSync`` is a round trip:
the server has processed the request before the child reports success, and
an X protocol error reaches the default error handler (stderr, exit 1)
rather than being lost. PRIMARY is untouched.

The child prints one JSON line: ``{"ok": true}`` (exit 0) or
``{"failure": "libx11" | "display" | "atom", "detail": ...}`` (exit 3).
"""

from __future__ import annotations

import ctypes
import ctypes.util
import json

_LIBX11_FALLBACK = "libX11.so.6"
_CLIPBOARD = b"CLIPBOARD"
_NONE_WINDOW = 0  # X11 ``None``
_CURRENT_TIME = 0  # X11 ``CurrentTime``
_FALSE = 0
FAILURE_EXIT = 3


class X11Failure(Exception):
    """A classified failure: ``kind`` is ``libx11``, ``display`` or ``atom``."""

    def __init__(self, kind: str, detail: str) -> None:
        super().__init__(detail)
        self.kind = kind
        self.detail = detail


def _declare(lib) -> None:
    """Declare the C signatures (``Display*`` as a pointer, XIDs as ulong)."""
    lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    lib.XOpenDisplay.restype = ctypes.c_void_p
    lib.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    lib.XInternAtom.restype = ctypes.c_ulong
    lib.XSetSelectionOwner.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
    ]
    lib.XSetSelectionOwner.restype = ctypes.c_int
    lib.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.XSync.restype = ctypes.c_int
    lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    lib.XCloseDisplay.restype = ctypes.c_int


def load_libx11(find_library=ctypes.util.find_library, load=ctypes.CDLL):
    """libX11 with declared signatures; ``X11Failure("libx11")`` if absent."""
    names = []
    found = find_library("X11")
    if found:
        names.append(found)
    if _LIBX11_FALLBACK not in names:
        names.append(_LIBX11_FALLBACK)
    errors = []
    for name in names:
        try:
            lib = load(name)
        except OSError as exc:
            errors.append(f"{name}: {exc}")
            continue
        _declare(lib)
        return lib
    raise X11Failure("libx11", "; ".join(errors))


def relinquish_clipboard(lib) -> None:
    """Set the CLIPBOARD owner to ``None`` on the ``DISPLAY`` server."""
    display = lib.XOpenDisplay(None)
    if not display:
        raise X11Failure("display", "XOpenDisplay returned NULL")
    try:
        atom = lib.XInternAtom(display, _CLIPBOARD, _FALSE)
        if not atom:
            raise X11Failure("atom", "XInternAtom(CLIPBOARD) returned None")
        lib.XSetSelectionOwner(display, atom, _NONE_WINDOW, _CURRENT_TIME)
        lib.XSync(display, _FALSE)
    finally:
        lib.XCloseDisplay(display)


def main(load=load_libx11) -> int:
    try:
        relinquish_clipboard(load())
    except X11Failure as exc:
        print(json.dumps({"failure": exc.kind, "detail": exc.detail}))
        return FAILURE_EXIT
    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
