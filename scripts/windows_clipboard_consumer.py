#!/usr/bin/env python3
"""Independent Windows clipboard consumer for the gated paste_html probe.

Plain ctypes (not ``clipboard``'s reader), run as a separate process. Prints
JSON: the offered format names/ids, the raw ``HTML Format`` bytes (base64, or
``null``) and ``GetClipboardSequenceNumber``; ``open_error`` when the
clipboard cannot be opened. With ``--text`` it also reports ``text``, the
``CF_UNICODETEXT`` string up to its NUL (``null`` when not offered). Reads
only: never empties or sets the clipboard.
"""

import base64
import ctypes
import json
import sys
import time

HANDLE = ctypes.c_void_p
CF_UNICODETEXT = 13


def main() -> None:
    u = ctypes.WinDLL("user32", use_last_error=True)
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    u.OpenClipboard.argtypes = [HANDLE]
    u.GetClipboardData.argtypes = [ctypes.c_uint]
    u.GetClipboardData.restype = HANDLE
    u.EnumClipboardFormats.argtypes = [ctypes.c_uint]
    u.EnumClipboardFormats.restype = ctypes.c_uint
    u.GetClipboardFormatNameW.argtypes = [ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_int]
    u.GetClipboardSequenceNumber.restype = ctypes.c_uint32
    for function in (k.GlobalLock, k.GlobalUnlock, k.GlobalSize):
        function.argtypes = [HANDLE]
    k.GlobalLock.restype = HANDLE
    k.GlobalSize.restype = ctypes.c_size_t
    html_format = u.RegisterClipboardFormatW("HTML Format")
    for _ in range(20):
        if u.OpenClipboard(None):
            break
        time.sleep(0.1)
    else:
        print(json.dumps({"open_error": ctypes.get_last_error()}))
        return
    try:
        formats, fmt = [], 0
        while fmt := u.EnumClipboardFormats(fmt):
            name = ctypes.create_unicode_buffer(256)
            got = u.GetClipboardFormatNameW(fmt, name, 256)
            formats.append(name.value if got else fmt)
        raw, handle = None, u.GetClipboardData(html_format)
        if handle:
            pointer = k.GlobalLock(handle)
            try:
                data = ctypes.string_at(pointer, k.GlobalSize(handle))
                raw = base64.b64encode(data).decode("ascii")
            finally:
                k.GlobalUnlock(handle)
        report = {"formats": formats, "html": raw}
        if "--text" in sys.argv[1:]:
            report["text"], handle = None, u.GetClipboardData(CF_UNICODETEXT)
            if handle:
                pointer = k.GlobalLock(handle)
                try:
                    report["text"] = ctypes.wstring_at(pointer)
                finally:
                    k.GlobalUnlock(handle)
        report["seq"] = u.GetClipboardSequenceNumber()
    finally:
        u.CloseClipboard()
    print(json.dumps(report))


if __name__ == "__main__":
    main()
