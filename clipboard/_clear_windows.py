"""Windows desktop clear: user32 ``EmptyClipboard`` removes every format.

Reuses inspect's ``user32`` loader and bounded ``OpenClipboard(NULL)`` retry
(``clipboard._offer_windows``, 15 s), so a momentary holder does not fail the
clear and a holder past the bound raises instead of hanging. Opening with a
``NULL`` window is enough here: ``EmptyClipboard`` then leaves no owner and no
format, and this module never sets data afterwards. ``CloseClipboard`` always
runs once the clipboard is open.
"""

from __future__ import annotations

from clipboard import _offer_windows
from clipboard._errors import ClipboardContentError

_OPERATION = "clearing the clipboard; nothing was cleared"
_SEAM = "a clearer with set_clipboard_clearer"


def _empty_failed(ctypes, code: int) -> ClipboardContentError:
    detail = f"Win32 error {code}"
    if code:
        detail += f": {ctypes.FormatError(code).strip()}"
    return ClipboardContentError(
        f"Windows clipboard clear failed: EmptyClipboard failed ({detail}; "
        f"last_error={code}); clear needs an interactive Windows desktop "
        "session with clipboard access"
    )


def _windows_clipboard_clearer() -> None:
    """Leave the Windows clipboard with no format at all; return ``None``.

    ``OpenClipboard`` still failing at the bound (clipboard held by another
    process, or access denied) and ``EmptyClipboard`` failing (with its
    ``GetLastError`` code) raise ``ClipboardContentError``.
    """
    user32, ctypes = _offer_windows._load_user32()
    _offer_windows._open_clipboard_bounded(
        user32, ctypes, operation=_OPERATION, seam=_SEAM
    )
    try:
        if not user32.EmptyClipboard():
            raise _empty_failed(ctypes, ctypes.get_last_error())
    finally:
        user32.CloseClipboard()
