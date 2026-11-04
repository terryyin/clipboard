Usage
-----

Text (no optional extras):

::

   import clipboard
   clipboard.copy("abc")
   text = clipboard.paste()

``copy(text)`` replaces the clipboard with exactly ``text``; ``paste()``
returns exactly the text the clipboard offers, as a ``str``. Unicode and emoji,
multiline strings, leading/trailing whitespace, and ``""`` survive unchanged
in both directions, including on macOS when the Python process has no UTF-8
locale (launchd, cron, IDE-spawned). Text written stays pasteable after the
Python process exits: on Linux a background helper (``xclip`` / ``wl-copy``)
keeps owning the selection, and Windows and macOS hand the text to the system;
delegated paths (below) carry no lifetime promise. Persistence across logout
or reboot is not promised.

``paste()`` returns ``""`` for ordinary absence (an empty clipboard, or one
with no text representation such as image-only); it never returns ``None``.
Native line endings pass through untranslated in both directions: text copied
by a Windows application comes back with ``\r\n``, so use
``paste().splitlines()`` as the portable way to split lines. ``copy("")``
promises only that ``paste()`` then returns ``""``; whether other
representations remain is platform behavior (Windows and ``wl-copy --clear``
empty the clipboard; macOS and ``xclip`` leave an empty text offer).
Non-``str`` arguments keep pyperclip's ``str()`` coercion: ``copy(42)``
copies ``"42"``.

A ``str`` containing ``"\x00"`` (Windows ``CF_UNICODETEXT`` would silently
truncate it) or one that cannot be UTF-8 encoded (a lone surrogate such as
``"\ud800"``) raises ``clipboard.ClipboardContentError`` **before** the
clipboard is replaced. Every other text failure also raises
``ClipboardContentError`` naming the cause, never a fabricated ``""`` or a
silent no-op write; when an underlying helper or pyperclip error exists it is
the exception's ``__cause__``:

* missing helper: the message names ``xclip`` (X11) / ``wl-clipboard``
  (Wayland) with an install hint;
* no visible desktop session: Linux with neither ``DISPLAY`` nor
  ``WAYLAND_DISPLAY`` set;
* a display or compositor that no longer answers (a dead ``DISPLAY``, a
  stale ``WAYLAND_DISPLAY``), quoting the helper's own message;
* a stalled clipboard owner or a clipboard held by another process;
* helper exit failure, undecodable helper output, or another transfer
  failure.

Bounds: on Linux each ``paste()`` and each ``copy()`` shares one 10 s bound
across its helper runs (an X11 ``copy()`` returns only once the new
background owner serves exactly the written bytes); on Linux each
``copy_image`` shares the same 10 s bound across starting its helper, handing
it the PNG and confirming the offer (X11: ``image/png`` reads back as exactly
the written PNG; Wayland: ``wl-copy``'s foreground part exits), and past it
raises ``ClipboardImageError`` naming the helper (``xclip`` / ``wl-copy``)
and the bound, quoting the helper's stderr, and stops that owner; on macOS each
``pbcopy`` / ``pbpaste`` run is bounded at 15 s; on Windows pyperclip retries
``OpenClipboard`` for about 0.5 s while another process holds the clipboard
and then raises (no other bound is added there). Delegated paths carry no
bound promise.

The default backend is chosen per call from the current session, in
pyperclip's order (except macOS pyobjc users, below). A mechanism already
resolved in pyperclip (``pyperclip.set_clipboard``, or earlier direct
``pyperclip.copy`` / ``paste`` use in the process) never displaces an owned
backend below; delegate deliberately instead (see below).

* Windows: pyperclip's ``CF_UNICODETEXT`` backend (ctypes);
* macOS Aqua (owned): ``pbcopy`` / ``pbpaste`` run with ``LC_ALL=en_US.UTF-8``
  in the helper's environment (the process environment is not changed).
  macOS users with pyobjc installed now go through ``pbcopy`` / ``pbpaste``
  rather than pyperclip's AppKit path;
* Linux under WSL (``/proc/version`` mentions ``microsoft``): pyperclip's
  ``clip.exe`` / PowerShell bridge;
* Linux Wayland (owned) when ``WAYLAND_DISPLAY`` is set and both ``wl-copy``
  and ``wl-paste`` are on ``PATH``: wl-clipboard, reading the first offered
  text type (``text/plain;charset=utf-8`` first) and writing
  ``text/plain;charset=utf-8``;
* otherwise Linux X11 (owned) when ``DISPLAY`` is set and ``xclip`` is on
  ``PATH``: the CLIPBOARD selection, ``UTF8_STRING`` first, then ``STRING``
  decoded as Latin-1;
* X11 with only ``xsel``, Klipper, or Qt, and other platforms: pyperclip.

Delegated paths (WSL, X11 without ``xclip``, other platforms) get failure translation only — pyperclip errors,
a missing executable, or a non-``str`` result become
``ClipboardContentError``, and a ``None`` result becomes ``""`` — and are
unverified (see Evidence).

**Compatibility note:** a process that selected a mechanism with
``pyperclip.set_clipboard`` (or used pyperclip directly) on macOS, X11 with
``xclip`` or Wayland with wl-clipboard now reaches the owned backend, not that
mechanism. To keep pyperclip there, delegate explicitly, with pyperclip looked
up at call time::

    import pyperclip
    clipboard.set_text_clipboard_writer(lambda text: pyperclip.copy(text))
    clipboard.set_text_clipboard_reader(lambda: pyperclip.paste())

Failures still become ``ClipboardContentError``; pass ``None`` to each setter
to restore default dispatch.

**Compatibility note:** ``copy`` / ``paste`` no longer let
``pyperclip.PyperclipException`` (or ``PyperclipWindowsException``) escape. A
caller catching ``pyperclip.PyperclipException`` must catch
``clipboard.ClipboardContentError`` instead; the pyperclip exception is its
``__cause__``.

For desktop-free tests, or deliberate delegation as above, inject with
``clipboard.set_text_clipboard_writer(writer)`` and
``clipboard.set_text_clipboard_reader(reader)``; pass ``None`` to restore the
default. A writer receives the already validated ``str``; a reader takes no
arguments and returns a ``str`` (or ``None`` when no text is offered).

Linux primary selection (select, then middle-click paste) text, beside the
ordinary clipboard:

::

   clipboard.copy_primary("for middle click")
   selected = clipboard.paste_primary()

``copy_primary(text)`` replaces only the PRIMARY selection, and
``paste_primary()`` reads only PRIMARY; CLIPBOARD is neither read nor
changed, and ``copy`` / ``paste`` keep reaching CLIPBOARD only and leave
PRIMARY as it was. ``copy_primary`` applies ``copy``'s input rules
(``str()`` coercion; ``"\x00"`` or non-UTF-8-encodable text raises
``ClipboardContentError`` before PRIMARY is replaced), and ``paste_primary``
returns ``""`` when nothing is selected or the owner offers no text (never
``None``), with line endings untranslated. On Linux X11 they run
``xclip -selection primary`` (``xclip`` on ``PATH`` is required); on Linux
Wayland they run wl-clipboard's ``wl-copy --primary`` / ``wl-paste --primary``
(``wl-copy`` and ``wl-paste`` on ``PATH`` are required), which works only
where the compositor offers wl-clipboard a primary-selection protocol. Both
share the 10 s bound of ``copy`` / ``paste``; written text stays pasteable
by middle-click after Python exits, served by a background ``xclip`` or by
``wl-copy``'s forked source. On Wayland ``copy_primary`` returns only once
an exact ``wl-paste --primary`` read-back serves the written text, so a
write the compositor drops raises instead of reporting success;
``copy_primary("")`` leaves PRIMARY offering empty text, which reads ``""``.

There is no fallback to CLIPBOARD: wherever PRIMARY cannot be reached, both
raise ``ClipboardContentError`` naming the reason and run no helper or
pyperclip mechanism: "not available" on macOS, Windows, WSL and other
platforms; Linux with no desktop session; X11 without ``xclip`` (even where
``paste()`` still works through pyperclip's ``xsel``, Klipper or Qt) and
Wayland without wl-clipboard, each with an install hint; and a Wayland
compositor for which wl-clipboard reports that primary selection is
unsupported (``The compositor does not seem to support primary selection``,
which is not "nothing selected": that reads ``""``). Other helper failures
and timeouts raise as for ``paste`` / ``copy``, with messages naming the
primary selection. The session is chosen as for ``copy`` / ``paste``:
Wayland when ``WAYLAND_DISPLAY`` is set and both wl-clipboard helpers are on
``PATH``, otherwise X11 with ``DISPLAY``, so a session with both variables
reaches PRIMARY and CLIPBOARD text through the same desktop. ``set_text_clipboard_writer`` /
``set_text_clipboard_reader`` do not apply: an injected text writer or
reader never receives PRIMARY traffic. A clipboard manager or desktop
setting that copies PRIMARY into CLIPBOARD (or back) on its own is a newer
offer by that program, outside this promise.
