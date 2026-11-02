#!/usr/bin/env python3
"""Notepad as an independent consumer of the current Windows clipboard text.

Plain ctypes in a separate process (not ``clipboard`` or pyperclip). Launches
``notepad.exe``, finds its new top-level ``Notepad`` window and its text child
(classic ``Edit``, or Store Notepad's ``RichEditD2DPT``), sends ``WM_PASTE`` to
that child (Notepad reads the clipboard itself), then reads
``EM_GETLINECOUNT`` and ``WM_GETTEXT``, and terminates Notepad without saving.

Prints one JSON object: ``notepad_path``, ``window_pid``, ``window_class``,
``edit_class``, ``line_count``, ``text``. When Notepad cannot be driven it
prints ``{"unavailable": "<reason>", ...}`` instead, so a missing observation
is never confused with a one-line result. Reads the clipboard only.
"""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import signal
import subprocess
import time
from ctypes import wintypes

WM_GETTEXT, WM_GETTEXTLENGTH, WM_PASTE = 0x000D, 0x000E, 0x0302
EM_GETLINECOUNT = 0x00BA
SMTO_ABORTIFHUNG = 0x0002
EDIT_CLASSES = ("Edit", "RichEditD2DPT")
WAIT_SECONDS = 20.0

# CFUNCTYPE only so the module imports off Windows for checks.
ENUM_PROC = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)(
    wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
)


def _user32():
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.EnumWindows.argtypes = [ENUM_PROC, wintypes.LPARAM]
    u.EnumChildWindows.argtypes = [wintypes.HWND, ENUM_PROC, wintypes.LPARAM]
    u.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    u.GetWindowThreadProcessId.restype = wintypes.DWORD
    u.SendMessageTimeoutW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    u.SendMessageTimeoutW.restype = ctypes.c_ssize_t
    return u


def _class(u, hwnd) -> str:
    name = ctypes.create_unicode_buffer(256)
    u.GetClassNameW(hwnd, name, 256)
    return name.value


def _top_notepads(u) -> set[int]:
    found: set[int] = set()

    def visit(hwnd, _):
        if _class(u, hwnd) == "Notepad":
            found.add(hwnd)
        return True

    u.EnumWindows(ENUM_PROC(visit), 0)
    return found


def _edit_child(u, top):
    found: list[tuple[int, str]] = []

    def visit(hwnd, _):
        cls = _class(u, hwnd)
        if cls in EDIT_CLASSES:
            found.append((hwnd, cls))
            return False
        return True

    u.EnumChildWindows(top, ENUM_PROC(visit), 0)
    return found[0] if found else (None, None)


def _send(u, hwnd, msg, wparam=0, lparam=0):
    result = ctypes.c_size_t()
    ok = u.SendMessageTimeoutW(
        hwnd, msg, wparam, lparam, SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
    )
    return result.value if ok else None


def _pid(u, hwnd) -> int:
    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _find(u, before: set[int]):
    """New top-level Notepad window with a text child, or ``(None, None, None)``."""
    deadline = time.monotonic() + WAIT_SECONDS
    while time.monotonic() < deadline:
        for top in _top_notepads(u) - before:
            edit, cls = _edit_child(u, top)
            if edit:
                return top, edit, cls
        time.sleep(0.2)
    return None, None, None


def observe(u, report: dict, kill: list[int]) -> None:
    """Fill ``report``; every Notepad pid to terminate is added to ``kill``."""
    before = _top_notepads(u)
    proc = subprocess.Popen([report["notepad_path"]])
    report["launched_pid"] = proc.pid
    kill.append(proc.pid)
    top, edit, cls = _find(u, before)
    if not top:
        report["unavailable"] = f"no new Notepad window with {EDIT_CLASSES} child"
        return
    report.update(window_pid=_pid(u, top), window_class=_class(u, top))
    report["edit_class"] = cls
    kill.append(report["window_pid"])
    time.sleep(0.5)
    if _send(u, edit, WM_PASTE) is None:
        report["unavailable"] = (
            f"WM_PASTE to {cls} timed out ({ctypes.get_last_error()})"
        )
        return
    time.sleep(0.5)
    length = _send(u, edit, WM_GETTEXTLENGTH)
    lines = _send(u, edit, EM_GETLINECOUNT)
    if length is None or lines is None:
        report["unavailable"] = f"reading {cls} timed out ({ctypes.get_last_error()})"
        return
    if length == 0:
        report["unavailable"] = f"WM_PASTE left {cls} empty (paste did not land)"
        return
    buf = ctypes.create_unicode_buffer(length + 1)
    _send(u, edit, WM_GETTEXT, length + 1, ctypes.addressof(buf))
    report.update(line_count=lines, text_length=length, text=buf.value)


def main() -> None:
    path = shutil.which("notepad.exe")
    if path is None:
        print(json.dumps({"unavailable": "notepad.exe not on PATH"}))
        return
    u = _user32()
    report: dict = {"notepad_path": path}
    kill: list[int] = []
    try:
        observe(u, report, kill)
    except Exception as exc:  # noqa: BLE001 - recorded for the JSON report
        report["unavailable"] = f"{type(exc).__name__}: {exc}"
    finally:
        for pid in dict.fromkeys(kill):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
    print(json.dumps(report))


if __name__ == "__main__":
    main()
