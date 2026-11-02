#!/usr/bin/env python3
"""Independent Windows clipboard holder for the gated text probe.

Plain ctypes in a separate process (not ``clipboard`` or pyperclip). Opens the
clipboard with its own hidden ``STATIC`` window, not ``OpenClipboard(NULL)``:
win32k lets another ``OpenClipboard(NULL)`` (pyperclip's ``paste``) reopen a
clipboard opened with NULL, and that caller's ``CloseClipboard`` then ends the
hold. Prints one JSON line ``{"ready": true, "hwnd": ..., "open_window": ...}``
once it holds the clipboard (``GetOpenClipboardWindow()`` is its window),
keeps it open for ``argv[1]`` seconds while pumping messages, re-checks
``GetOpenClipboardWindow()`` just before release, closes it and prints
``{"released": true, ...}``. Prints ``{"ready": false, ...}`` when it never
gets the clipboard within 5 s. Never empties or sets the clipboard.
"""

import ctypes
import json
import sys
import time
from ctypes import wintypes

PM_REMOVE = 0x0001


def _say(**fields) -> None:
    print(json.dumps(fields), flush=True)


def _user32():
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.CreateWindowExW.argtypes = [
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.HWND,
        wintypes.HMENU,
        wintypes.HINSTANCE,
        wintypes.LPVOID,
    ]
    u.CreateWindowExW.restype = wintypes.HWND
    u.DestroyWindow.argtypes = [wintypes.HWND]
    u.DestroyWindow.restype = wintypes.BOOL
    u.OpenClipboard.argtypes = [wintypes.HWND]
    u.OpenClipboard.restype = wintypes.BOOL
    u.CloseClipboard.argtypes = []
    u.CloseClipboard.restype = wintypes.BOOL
    u.GetOpenClipboardWindow.argtypes = []
    u.GetOpenClipboardWindow.restype = wintypes.HWND
    msg_args = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT]
    u.PeekMessageW.argtypes = msg_args + [wintypes.UINT, wintypes.UINT]
    u.PeekMessageW.restype = wintypes.BOOL
    u.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    u.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    u.DispatchMessageW.restype = ctypes.c_ssize_t
    return u


def _pump(u, seconds: float) -> None:
    msg = wintypes.MSG()
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        while u.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            u.TranslateMessage(ctypes.byref(msg))
            u.DispatchMessageW(ctypes.byref(msg))
        time.sleep(min(0.02, max(0.0, end - time.monotonic())))


def _open_window(u) -> int:
    return u.GetOpenClipboardWindow() or 0


def main() -> None:
    hold = float(sys.argv[1])
    u = _user32()
    hwnd = u.CreateWindowExW(0, "STATIC", None, 0, 0, 0, 0, 0, None, None, None, None)
    if not hwnd:
        _say(ready=False, create_window_error=ctypes.get_last_error())
        return
    try:
        deadline = time.monotonic() + 5
        while not u.OpenClipboard(hwnd):
            if time.monotonic() > deadline:
                _say(
                    ready=False,
                    hwnd=hwnd,
                    open_error=ctypes.get_last_error(),
                    open_window=_open_window(u),
                )
                return
            time.sleep(0.05)
        opened = time.monotonic()
        at_ready = _open_window(u)
        try:
            _say(
                ready=True,
                hold_seconds=hold,
                hwnd=hwnd,
                open_window=at_ready,
                holds_at_ready=at_ready == hwnd,
            )
            _pump(u, hold)
            before = _open_window(u)
        finally:
            closed = u.CloseClipboard()
            close_error = 0 if closed else ctypes.get_last_error()
        _say(
            released=True,
            held_seconds=round(time.monotonic() - opened, 3),
            open_window_before_release=before,
            holds_before_release=before == hwnd,
            close_ok=bool(closed),
            close_error=close_error,
        )
    finally:
        u.DestroyWindow(hwnd)


if __name__ == "__main__":
    main()
