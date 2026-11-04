"""Linux PRIMARY selection text contract (``copy_primary`` / ``paste_primary``).

PRIMARY is the select-and-middle-click selection of Linux desktops. These
operations reach PRIMARY only: CLIPBOARD is never read or written, and every
case where PRIMARY cannot be reached raises ``ClipboardContentError`` instead
of falling back to CLIPBOARD (a fallback would overwrite what the user
copied). Session choice follows the text rule of ``copy`` / ``paste``
(``_desktop_text._text_session_owner``), but only the owned X11 ``xclip``
path serves PRIMARY: pyperclip (``xsel``, Klipper, Qt) is never used, nor
are its internal ``primary=`` flags. The injected ``copy`` / ``paste`` seams
(``set_text_clipboard_writer`` / ``_reader``) are deliberately not consulted.
"""

from __future__ import annotations

from clipboard import _desktop_text, _platform, _text_native_x11
from clipboard._errors import ClipboardContentError, _call_content_backend
from clipboard._text import _validate_copy_text
from clipboard._text_native_linux import _install_hint

_PLATFORM_NAMES = {"darwin": "macOS", "win32": "Windows"}


def _unavailable(predicate: str) -> ClipboardContentError:
    """``"the primary selection <predicate>"``, stating that there is no fallback."""
    return ClipboardContentError(
        f"the primary selection {predicate}; the ordinary clipboard is not used instead"
    )


def _x11_primary_session() -> None:
    """Return when PRIMARY is reachable through ``xclip``; raise otherwise.

    Runs no helper and no pyperclip: only the session variables, ``PATH``
    and ``/proc/version`` are consulted.
    """
    platform = _platform.current()
    if not platform.startswith("linux"):
        name = _PLATFORM_NAMES.get(platform, platform)
        raise _unavailable(
            f"is not available on {name} ({platform}): PRIMARY is a Linux X11 / "
            "Wayland selection"
        )
    try:
        owner = _desktop_text._text_session_owner()
    except ClipboardContentError as exc:
        raise _unavailable(f"cannot be reached: {exc}") from exc
    if owner == _desktop_text._TEXT_OWNER_X11:
        return
    if owner == _desktop_text._TEXT_OWNER_WAYLAND:
        raise _unavailable("is not yet supported on Wayland")
    if _desktop_text._is_wsl():
        raise _unavailable("is not available on WSL (Linux under Windows)")
    # Linux X11 whose text would go through pyperclip (no xclip on PATH).
    raise _unavailable(
        "on Linux X11 needs xclip, which was not found on PATH (pyperclip's "
        f"xsel / Klipper / Qt fallbacks are not used); "
        f"{_install_hint('xclip', 'xclip')}"
    )


def _primary_writer(text: str) -> None:
    _x11_primary_session()
    _text_native_x11._x11_text_clipboard_writer(text, _text_native_x11._PRIMARY)


def _primary_reader() -> str:
    _x11_primary_session()
    return _text_native_x11._x11_text_clipboard_reader(_text_native_x11._PRIMARY)


def copy_primary(text) -> None:
    """Replace the Linux PRIMARY selection with ``text``; CLIPBOARD is untouched.

    Input rules are those of ``copy``: non-``str`` values via ``str()``, and
    text containing ``"\\x00"`` or not UTF-8 encodable is rejected before
    PRIMARY is replaced. Linux X11 through ``xclip`` (the text stays
    pasteable by middle-click after Python exits). Raises
    ``ClipboardContentError`` wherever PRIMARY cannot be reached (macOS,
    Windows, WSL, other platforms, no desktop session, X11 without
    ``xclip``, Wayland for now) and for any helper failure; never falls back
    to CLIPBOARD.
    """
    validated = _validate_copy_text(text)
    _call_content_backend("primary selection text write", _primary_writer, validated)


def paste_primary() -> str:
    """Return the Linux PRIMARY selection's text (``""`` when nothing is
    selected or the owner offers no text, never ``None``); CLIPBOARD is never
    read.

    Line endings are returned untranslated. Raises ``ClipboardContentError``
    where ``copy_primary`` does.
    """
    return _call_content_backend("primary selection text read", _primary_reader)
