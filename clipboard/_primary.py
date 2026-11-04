"""Linux PRIMARY selection text contract (``copy_primary`` / ``paste_primary``).

PRIMARY is the select-and-middle-click selection of Linux desktops. These
operations reach PRIMARY only: CLIPBOARD is never read or written, and every
case where PRIMARY cannot be reached raises ``ClipboardContentError`` instead
of falling back to CLIPBOARD (a fallback would overwrite what the user
copied). Session choice follows the text rule of ``copy`` / ``paste``
(``_desktop_text._text_session_owner``), but only the owned paths serve
PRIMARY: X11 through ``xclip -selection primary`` and Wayland through
wl-clipboard's ``--primary`` (a compositor wl-clipboard reports without
primary-selection support raises). pyperclip (``xsel``, Klipper, Qt) is
never used, nor are its internal ``primary=`` flags. The injected ``copy`` /
``paste`` seams (``set_text_clipboard_writer`` / ``_reader``) are
deliberately not consulted.
"""

from __future__ import annotations

from clipboard import (
    _desktop_text,
    _platform,
    _text_native_wayland,
    _text_native_wayland_writer,
    _text_native_x11,
)
from clipboard._errors import ClipboardContentError, _call_content_backend
from clipboard._text import _validate_copy_text
from clipboard._text_native_linux import (
    _NO_CLIPBOARD_FALLBACK,
    _PRIMARY,
    _install_hint,
)

_PLATFORM_NAMES = {"darwin": "macOS", "win32": "Windows"}


def _unavailable(predicate: str) -> ClipboardContentError:
    """``"the primary selection <predicate>"``, stating that there is no fallback."""
    return ClipboardContentError(
        f"the primary selection {predicate}; {_NO_CLIPBOARD_FALLBACK}"
    )


# Owned text paths that also serve PRIMARY, by text session owner:
# (writer, reader), each called with ``_PRIMARY``.
_PRIMARY_PATHS = {
    _desktop_text._TEXT_OWNER_X11: (
        _text_native_x11._x11_text_clipboard_writer,
        _text_native_x11._x11_text_clipboard_reader,
    ),
    _desktop_text._TEXT_OWNER_WAYLAND: (
        _text_native_wayland_writer._wayland_text_clipboard_writer,
        _text_native_wayland._wayland_text_clipboard_reader,
    ),
}


def _primary_session() -> str:
    """The text owner serving PRIMARY (X11 or Wayland); raise otherwise.

    Runs no helper and no pyperclip: only the session variables, ``PATH``
    and ``/proc/version`` are consulted. A Wayland-only session without
    both wl-clipboard helpers raises from ``_text_session_owner`` (naming
    ``wl-copy`` / ``wl-paste`` and wl-clipboard).
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
    if owner in _PRIMARY_PATHS:
        return owner
    if _desktop_text._is_wsl():
        raise _unavailable("is not available on WSL (Linux under Windows)")
    # Linux X11 whose text would go through pyperclip (no xclip on PATH).
    raise _unavailable(
        "on Linux X11 needs xclip, which was not found on PATH (pyperclip's "
        f"xsel / Klipper / Qt fallbacks are not used); "
        f"{_install_hint('xclip', 'xclip')}"
    )


def _primary_writer(text: str) -> None:
    writer, _reader = _PRIMARY_PATHS[_primary_session()]
    writer(text, _PRIMARY)


def _primary_reader() -> str:
    _writer, reader = _PRIMARY_PATHS[_primary_session()]
    return reader(_PRIMARY)


def copy_primary(text) -> None:
    """Replace the Linux PRIMARY selection with ``text``; CLIPBOARD is untouched.

    Input rules are those of ``copy``: non-``str`` values via ``str()``, and
    text containing ``"\\x00"`` or not UTF-8 encodable is rejected before
    PRIMARY is replaced. Linux X11 through ``xclip`` and Wayland through
    ``wl-copy --primary`` (confirmed by an exact ``wl-paste --primary``
    read-back); the text stays pasteable by middle-click after Python
    exits. Raises ``ClipboardContentError`` wherever PRIMARY cannot be
    reached (macOS, Windows, WSL, other platforms, no desktop session, X11
    without ``xclip``, Wayland without wl-clipboard, a compositor
    wl-clipboard reports without primary-selection support) and for any
    helper failure; never falls back to CLIPBOARD.
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
