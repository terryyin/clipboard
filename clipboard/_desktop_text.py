"""Plain-text desktop session selection, in pyperclip 1.11.0's order.

Sibling of ``_desktop`` (which keeps the image / HTML / file-list session
rules and helper listing): this rule is text-only and deliberately distinct
from ``_desktop._is_linux_wayland`` and ``_desktop._linux_wayland_without_x11``.
"""

from __future__ import annotations

import importlib.util
import os
import shutil

from clipboard import _platform
from clipboard._errors import ClipboardContentError

# Text session owners (see ``_text_session_owner``).
_TEXT_OWNER_PYPERCLIP = "pyperclip"
_TEXT_OWNER_MACOS = "macos"
_TEXT_OWNER_X11 = "x11"
_TEXT_OWNER_WAYLAND = "wayland"

_PROC_VERSION_PATH = "/proc/version"

_TEXT_HELPER_INSTALL_HINT = (
    "install xclip for X11 (e.g. `sudo apt-get install xclip`) or "
    "wl-clipboard for Wayland (e.g. `sudo apt-get install wl-clipboard`) "
    "and ensure it is on PATH"
)


def _read_proc_version() -> str:
    """``/proc/version`` text, or ``""`` when it cannot be read."""
    try:
        with open(_PROC_VERSION_PATH, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _qt_binding_installed() -> bool:
    """True when pyperclip's Qt fallback (``qtpy`` or ``PyQt5``) is importable.

    Uses ``find_spec`` so deciding never imports Qt itself.
    """
    for name in ("qtpy", "PyQt5"):
        try:
            if importlib.util.find_spec(name) is not None:
                return True
        except (ImportError, ValueError):
            continue
    return False


def _text_session_owner() -> str:
    """Name the plain-text backend for this session, in pyperclip 1.11.0's
    ``determine_clipboard`` order so no working user changes mechanism.

    Text rule, distinct from ``_is_linux_wayland`` and
    ``_linux_wayland_without_x11``: Wayland is chosen only when
    ``WAYLAND_DISPLAY`` is set *and* both ``wl-copy`` and ``wl-paste`` are on
    PATH (``XDG_SESSION_TYPE`` is ignored); otherwise a set ``DISPLAY`` picks
    X11 (``xclip``), then pyperclip's xsel / Klipper / Qt fallbacks.

    Windows, WSL (``/proc/version`` mentions ``microsoft``), non-Linux
    platforms, and X11 without ``xclip`` but with a pyperclip fallback return
    ``_TEXT_OWNER_PYPERCLIP``. Raises ``ClipboardContentError`` when Linux
    shows no desktop session or a session without any text helper.
    """
    platform = _platform.current()
    if platform == "win32":
        return _TEXT_OWNER_PYPERCLIP
    if platform == "darwin":
        return _TEXT_OWNER_MACOS
    if not platform.startswith("linux"):
        return _TEXT_OWNER_PYPERCLIP
    if "microsoft" in _read_proc_version().lower():
        return _TEXT_OWNER_PYPERCLIP
    wayland = os.environ.get("WAYLAND_DISPLAY")
    display = os.environ.get("DISPLAY")
    if wayland and shutil.which("wl-copy") and shutil.which("wl-paste"):
        return _TEXT_OWNER_WAYLAND
    if display:
        if shutil.which("xclip"):
            return _TEXT_OWNER_X11
        if (
            shutil.which("xsel")
            or (shutil.which("klipper") and shutil.which("qdbus"))
            or _qt_binding_installed()
        ):
            return _TEXT_OWNER_PYPERCLIP
        raise ClipboardContentError(
            "missing Linux clipboard text helper: DISPLAY is set but no "
            f"clipboard helper was found on PATH; {_TEXT_HELPER_INSTALL_HINT}"
        )
    if wayland:
        raise ClipboardContentError(
            "missing Linux clipboard text helper: WAYLAND_DISPLAY is set but "
            "wl-copy and wl-paste were not both found on PATH; "
            f"{_TEXT_HELPER_INSTALL_HINT}"
        )
    raise ClipboardContentError(
        "no desktop session is visible: neither DISPLAY nor WAYLAND_DISPLAY "
        "is set, so the Linux text clipboard cannot be reached (run inside an "
        "X11 or Wayland session, or forward one)"
    )
