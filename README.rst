clipboard
=========

A cross platform clipboard library for Python (Windows, macOS, Linux). Text
``copy`` / ``paste`` follow this package's own contract: it owns the macOS
and Linux helper paths, uses pyperclip's Windows backend, and delegates other
environments to pyperclip; richer APIs sit beside them.

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
background owner serves exactly the written bytes); on macOS each
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

Image read/write needs the optional ``images`` extra (Pillow):

::

   import clipboard
   from PIL import Image

   image = clipboard.paste_image()  # Pillow Image, or None when none is offered
   clipboard.copy_image(Image.new("RGB", (8, 8), (255, 0, 0)))

``paste_image`` leaves the clipboard unchanged. Ordinary absence (text-only,
empty, or file-list offer) returns ``None``. Access, missing-helper, transfer,
or malformed-image failures raise ``clipboard.ClipboardImageError`` (not
``None``). ``copy_image`` publishes one static Pillow raster (non-RGB(A)
converted); invalid input raises ``ClipboardImageError`` **before** replacing
contents; helper/access/transfer failure raises (no silent success). Calling
either without the extra raises ``ImportError``.

HTML dual-offer write (no ``clipboard[images]`` required):

::

   import clipboard
   clipboard.copy_html(
       '<a href="https://example.com"><b>café</b></a>',
       'café → https://example.com',
   )

``copy_html(html, text)`` requires both Unicode arguments; the library does not
synthesize text from HTML. Invalid args raise
``clipboard.ClipboardContentError`` **before** replacing contents. Success
publishes HTML and plain text together; inability to offer both, missing
helpers, denied access, transfer failure, or an unsupported session raises
``ClipboardContentError`` — never silent text-only success. On macOS Aqua the
default writer uses ``NSPasteboard`` HTML + string via ``osascript``. Elsewhere
the default path raises until a dual-offer writer exists; Linux/Windows HTML
writes remain evidence-limited (below) — an evidence limit is not proof a
native writer is present.

Inspect the current offer (kinds + native format ids; no ``clipboard[images]``):

::

   import clipboard
   snap = clipboard.inspect()
   # snap.kinds: frozenset among {text, image, html, files}
   # snap.formats: platform-native type / UTI / MIME / format names

``inspect()`` returns a ``ClipboardOfferSnapshot``: library ``kinds`` mapped
from known native ids, plus the full ``formats`` list (undecodable ids stay
listed). Listing a format does **not** promise a later ``paste_*`` / decode
will succeed. An empty offer yields empty ``kinds`` / ``formats`` — not an
error. Denied access, missing helper, or enumeration failure raises
``ClipboardContentError`` (never a fabricated empty success; not
``ClipboardImageError``). Inspection does not replace, clear, or reserve the
clipboard. The snapshot is a point-in-time view and can race with other
writers. Linux helpers: X11 ``xclip -selection clipboard -o -t TARGETS``;
Wayland ``wl-paste -l`` (verified claims stay **named-compositor-scoped**).
On Linux an unowned X11 CLIPBOARD (``xclip``'s no-owner error, in either its
``target TARGETS not available`` or ``There is no owner for the`` wording) and
a nothing-copied Wayland selection (``Nothing is copied`` / ``No selection``)
give an empty snapshot; any other helper failure still raises. WSL, SSH, containers, and headless CI are not additional guaranteed desktops
for ``inspect``.

To read the HTML fragment of a selection another application copied (for
example a browser or rich editor), call ``paste_html``:

::

   import clipboard

   html = clipboard.paste_html()  # fragment str, or None when no HTML is offered
   if html is not None:
       print(html)  # e.g. '<a href="https://example.com"><b>café</b></a>'

``paste_html()`` returns the Unicode HTML **fragment** of the copied selection
when the clipboard offers HTML, and ``None`` when no HTML is offered (text-only,
empty, image-only, or file-list clipboard). An HTML offer whose fragment is
empty returns ``""``, not ``None``. Denied or unavailable access, a missing
helper, a timeout or a clipboard held by another process, transfer failure, or
a malformed envelope or invalid encoding raise
``clipboard.ClipboardContentError`` (not ``ClipboardImageError``) — never
``None`` and never a fabricated fragment. Helper calls are bounded (about
10 s); on Windows a busy clipboard is retried for about 1 s.

The read never changes, clears, or takes ownership of the clipboard: another
consumer still sees the same offer afterwards. The markup is returned verbatim
as a string: it is never executed, linked resources are never fetched, and
local paths in it are never opened. HTML is never synthesized from plain text
or RTF; ``paste()`` keeps returning plain text.

Envelope behavior differs per desktop:

* **Windows:** the registered ``HTML Format`` is cut at its UTF-8
  ``StartFragment`` / ``EndFragment`` byte offsets. The ``Version`` /
  ``StartHTML`` header block, ``SourceURL``, and the unselected surrounding
  context are never returned. A ``StartHTML`` that points into the header (the
  shape PowerShell ``Set-Clipboard -AsHtml`` writes) is tolerated because the
  fragment offsets still delimit a trustworthy fragment. Envelopes whose
  offsets do not match their bytes — for example .NET Framework
  ``Clipboard.SetText(..., Html)`` / ``Set-Clipboard -AsHtml``
  with non-ASCII text, which those APIs write as ANSI — raise
  ``ClipboardContentError``.
* **macOS:** the pasteboard's ``public.html`` body is returned as offered,
  including a leading ``<meta charset='utf-8'>`` that browsers such as Chrome
  prepend.
* **Linux (X11 and Wayland):** the ``text/html`` body is returned as offered.
  It is decoded as UTF-8; a UTF-16 byte-order mark is honoured; trailing NUL
  terminators are stripped, and any other NUL is refused with
  ``ClipboardContentError`` rather than guessing the encoding.

The default reader is chosen per platform; Installation lists what each
desktop needs and the Linux Wayland / X11 session rule. Other platforms raise
``ClipboardContentError``.

Out of scope for ``paste_html``: returning the surrounding context, the
``SourceURL``, or other producer metadata; full-document import; RTF or
attributed-string conversion; arbitrary MIME or binary reads; the X11 PRIMARY
selection; and format inspection. Supported desktops are Windows, macOS Aqua,
Linux X11, and Linux Wayland (Sway verified); WSL, SSH sessions, containers,
and headless CI are not guaranteed desktops.

For desktop-free tests, inject a fake reader with
``clipboard.set_html_clipboard_reader(reader)`` and restore the default with
``clipboard.set_html_clipboard_reader(None)``. A reader takes no arguments and
returns ``None`` when no HTML is offered; the offer values it returns
otherwise are package-private test plumbing, not public API.

File-list read (no ``clipboard[images]`` required):

::

   import clipboard
   paths = clipboard.paste_files()  # ordered list[str], or None

``paste_files()`` returns an ordered ``list[str]`` of local filesystem paths
when a native file-list offer yields at least one local reference, or ``None``
for ordinary absence (empty clipboard; plain text — including path-looking
text; image-only; HTML-only; only non-local URIs). Access, missing Linux
helper, transfer, or malformed file-list metadata raises
``clipboard.ClipboardContentError`` — never ``None`` or fabricated paths. The
read does not mutate the clipboard and performs no open, copy, move, delete,
or existence check on referenced paths. Cut/move companion markers are
ignored for library behavior. Do not overload ``paste()`` / ``copy()`` for
file lists. Supported desktops: Windows Explorer ``CF_HDROP``; macOS Aqua
Finder file-URL / filename types; Linux X11 + ``xclip`` ``text/uri-list``
from a **named** file manager; Linux Wayland + ``wl-paste`` ``text/uri-list``
from a **named** FM on a **named** compositor. WSL, SSH, containers, and
headless CI are not additional guaranteed desktops.

File-list copy, so a desktop file manager can paste the files (no
``clipboard[images]`` required):

::

   import clipboard
   clipboard.copy_files(["out/report final.pdf", "out/données é.csv"])
   # the script may exit; the user pastes copies of both in a file manager

``copy_files(paths)`` takes an ordered, non-empty iterable of ``str`` /
``os.PathLike`` local paths to existing files or directories and replaces the
current clipboard with one native file-list offer. Relative paths are made
absolute against the current directory at call time, without resolving
symlinks (working directory ``/home/u/proj``: ``copy_files(["out/a.txt"])``
offers ``/home/u/proj/out/a.txt``); order and duplicates pass through. The
offer is marked **copy**, not cut: a file manager pastes copies and leaves the
sources in place (Windows sets ``Preferred DropEffect`` to copy; the macOS and
Linux offers carry no cut marker). It returns ``None``.

Invalid input — an empty iterable (which would clear the clipboard), a bare
``str`` / ``bytes`` (wrap one path in a list), a non-path item, or a path that
does not exist at call time — raises ``clipboard.ClipboardContentError``
naming the problem **before** the clipboard is replaced, so earlier text
stays pasteable. A missing helper, no usable desktop session, denied access,
or transfer failure also raises ``ClipboardContentError``; there is no
text-only fallback and no silent success.

The offer stays pasteable after the Python process exits: macOS and Windows
hand it to the system clipboard; on Linux a background helper (``xclip`` /
``wl-copy``) keeps serving it, so it lasts only as long as that helper or the
desktop session. Persistence across logout or reboot is not promised.

The offer is a **reference, not a snapshot**: the library neither locks nor
copies the files, and a file manager copies what exists when the user pastes.
If ``out/a.txt`` is deleted after a successful ``copy_files``, pasting makes
the file manager report or skip the missing item in its own way; nothing is
raised in Python and no other file is touched.

Native offers: macOS Aqua one ``NSPasteboard`` file-URL item per path (via
``osascript`` / AppKit); Windows desktop ``CF_HDROP`` plus ``Preferred
DropEffect`` copy (``ctypes``, no pywin32); Linux one ``text/uri-list`` of
``file://`` URIs, served by ``xclip`` on X11 or ``wl-copy`` on Wayland. The
helpers serve one type per owner, so the GNOME ``x-special/gnome-copied-files``
convention is not also offered. As for ``paste_files``, a Linux session uses
Wayland only when ``WAYLAND_DISPLAY`` is set without an X11 ``DISPLAY``.
Other platforms raise ``ClipboardContentError`` naming the platform. Out of
scope for ``copy_files``: a plain-text alternative in the same offer, cut /
move, virtual or promised files, non-``file:`` URIs, the X11 PRIMARY
selection, and WSL, SSH sessions, containers, or headless CI as guaranteed
desktops.

For desktop-free tests, inject a fake writer with
``clipboard.set_files_clipboard_writer(writer)`` and restore the default with
``clipboard.set_files_clipboard_writer(None)``. The writer receives one
already validated ``list[str]`` of absolute paths and must publish it as one
copy offer or raise.

Clear the clipboard (no ``clipboard[images]`` required):

::

   import clipboard
   clipboard.clear()

``clear()`` removes every representation from the current clipboard, so it
holds no offer at all: afterwards ``paste()`` returns ``""``, ``paste_html()``,
``paste_image()`` and ``paste_files()`` return ``None``, ``inspect()`` is
empty, and other applications see no types. It returns ``None``. Clearing an
already empty clipboard, or clearing twice in a row, succeeds. This is not the
same as ``copy("")``, which on macOS and ``xclip`` leaves an empty text offer
behind (a ``public.utf8-plain-text`` type on macOS). Failures (no usable
session, a helper or native call failing, a timeout) raise
``clipboard.ClipboardContentError``.

Platforms: macOS Aqua clears the general pasteboard with ``NSPasteboard
clearContents`` through the built-in ``osascript`` (bounded at 15 s; see
Evidence). Linux Wayland runs ``wl-copy --clear`` (bounded at 10 s), which
needs ``wl-clipboard`` on ``PATH``; a missing ``wl-copy`` raises
``ClipboardContentError`` naming ``wl-clipboard``. A session with both
``DISPLAY`` and ``WAYLAND_DISPLAY`` clears the Wayland selection. On Linux
with neither ``DISPLAY`` nor ``WAYLAND_DISPLAY``, ``clear()`` raises
``ClipboardContentError`` saying no desktop session is visible. Linux X11 and
Windows desktop clears are not available yet: there ``clear()`` raises
``ClipboardContentError`` saying the native clearer is not available on that
platform.

Boundary: ``clear()`` acts once on the current clipboard. A later offer is a
newer copy, not a failed clear, and is not detected: another application
copying, a clipboard manager re-offering its saved entry (for example KDE
Klipper's "prevent empty clipboard" or compositor clipboard persistence), or
a sync service. ``clear()`` does not erase OS clipboard history, clipboard
managers' saved entries, cloud or Universal Clipboard copies, or other
devices, and it claims no secure deletion of the former contents. On macOS it
clears only the general pasteboard, not the Find pasteboard or other named
pasteboards; the X11 PRIMARY selection is out of scope.

For desktop-free tests, inject a fake with
``clipboard.set_clipboard_clearer(clearer)`` and restore the default with
``clipboard.set_clipboard_clearer(None)``. The clearer takes no arguments and
must leave the clipboard with no offer at all or raise.

Installation
------------

``python -m pip install clipboard`` (Python 3.10+). Text needs nothing extra
on Windows or macOS. On Linux text needs a desktop session and a helper on
``PATH``: ``xclip`` for X11 (for example ``apt install xclip``) or
``wl-clipboard`` (``wl-copy`` and ``wl-paste``) for Wayland (for example
``apt install wl-clipboard``); without ``xclip``, an X11 session may still
use pyperclip's ``xsel`` / Klipper / Qt fallbacks (see
`pyperclip <https://pyperclip.readthedocs.io/>`_; unverified). Images:
``python -m pip install 'clipboard[images]'``. ``copy_html``, ``paste_html``,
``paste_files``, ``copy_files``, and ``inspect`` do **not** need that extra.

Linux image **reads**: X11 ``xclip``; Wayland ``wl-paste``. Linux file-list
**reads** (``paste_files``): X11 ``xclip -o -selection clipboard -t
text/uri-list``; Wayland ``wl-paste -t text/uri-list`` (missing helper →
``ClipboardContentError``, not silent ``None``). Linux file-list **writes**
(``copy_files``): X11 ``xclip`` (for example ``apt install xclip``) and a
usable ``DISPLAY``; Wayland ``wl-copy`` and ``wl-paste`` from
``wl-clipboard`` (for example ``apt install wl-clipboard``); the helper keeps
running in the background as the offer's owner, and a missing helper raises
``ClipboardContentError`` with an install hint before the clipboard is
replaced. Linux HTML **writes** need a multi-MIME helper (X11 multi-type
``xclip``; Wayland e.g. ``wl-copy`` on a **named** compositor — do not
generalize). Linux image **writes**: X11
``xclip`` / Wayland ``wl-copy`` (may keep a background owner). Windows/macOS
need a usable desktop session; rich/image/file-list APIs are not guaranteed
under WSL, SSH, containers, or headless CI.

HTML **reads** via ``paste_html`` need:

* Linux X11: ``xclip`` on ``PATH`` (for example ``apt install xclip``) and a
  usable X11 display (``DISPLAY``); it lists CLIPBOARD ``TARGETS`` and then
  requests ``text/html``
* Linux Wayland: ``wl-paste`` from wl-clipboard on ``PATH`` (for example
  ``apt install wl-clipboard``) and a compositor that gives ``wl-paste``
  clipboard access (data-control); only Sway is verified
* macOS: nothing extra; the built-in ``osascript`` in a logged-in Aqua session
* Windows: nothing extra; ``ctypes`` from the standard library (no pywin32)

A Linux session counts as Wayland when ``XDG_SESSION_TYPE`` is ``wayland`` or
``WAYLAND_DISPLAY`` is set; otherwise ``paste_html`` uses X11. A missing helper
or display raises ``ClipboardContentError``.

Evidence / verified platforms (native probes gated via
``CLIPBOARD_NATIVE_PROBE=1``; default tests are in-memory):

* Text ``copy`` / ``paste``, each desktop proved with independent producers
  and consumers in other processes and a ``copy()`` in a child Python that
  exits before the consumer reads (sample ``"  héllo 👋 ﾃｽﾄ\nline 2 "``):

  * macOS Aqua **verified** on the owner's desktop by
    ``scripts/probe_macos_native_text.py`` (wrapper
    ``tests/test_text_native_macos.py``; independent ``osascript`` and
    ``pbpaste`` producers / consumers): exact round trips both ways, a child
    Python with an empty environment copied and pasted exactly, ``copy("")``
    read ``""``, a refused ``copy("a\x00b")`` left the prior text readable,
    and cleared and image-only pasteboards read ``""``. Floors: macOS 26.6.2
    (build 25G83) / Darwin 25.6.0, arm64, Python 3.13.17. Evidence limits: a
    macOS "Paste from Other Apps" privacy denial is unobserved and may make
    ``pbpaste`` return ``""`` with exit 0, so ``paste()`` could return
    ``""`` rather than raise; ``pbcopy`` / ``pbpaste`` in an SSH session into
    macOS (no WindowServer access) are unobserved.
  * Linux X11 **verified** under gated GitHub Actions job
    ``native-linux-x11-text`` (runs 41471306541 and 41473939537; Ubuntu
    26.04.1, Xvfb ``2:21.1.22-1ubuntu1.3``, xclip 0.13, Python 3.13.14;
    independent ``xclip -i`` producers and ``xclip -o`` consumer): exact
    round trips, ``copy("")`` read ``""``, a ``STRING``-only owner read as
    Latin-1, image-only and unowned clipboards read ``""``, a dead display made both operations raise in under 0.1 s quoting
    ``Error: Can't open display``, and ``PATH`` without ``xclip`` gave the
    install hint. A stalled owner is proved by desktop-free tests only.
  * Linux Wayland **verified only** under gated job
    ``native-linux-wayland-text`` (run 41478592764) with the named compositor
    **Sway** 1.11 and ``wl-clipboard`` 2.2.1 (Ubuntu 26.04.1, Python 3.13.14;
    independent ``wl-copy`` producers and ``wl-paste`` consumer): exact round
    trips, ``copy("")`` read ``""``, image-only and cleared selections read
    ``""``, a stale ``WAYLAND_DISPLAY`` made both
    operations raise quoting ``Failed to connect to a Wayland server``, and
    ``PATH`` without ``wl-paste`` gave the install hint. Other Wayland
    compositors are unverified.
  * Windows **verified** under gated job ``native-windows-text`` (run
    41484980894; Windows Server 2025 Datacenter 10.0.26100, Windows PowerShell
    5.1.26100 and PowerShell 7.6.7, Python 3.13.16, pyperclip 1.11.0;
    independent PowerShell ``Set-Clipboard`` / ``Get-Clipboard``, .NET
    ``SetImage``, ctypes reader, and classic Notepad 10.0.26100.32860): a
    ``Set-Clipboard`` producer of ``"  héllo 👋 ﾃｽﾄ\r\nline 2 "`` made
    ``paste()`` return it exactly with ``\r\n``; a child's
    ``copy("héllo 👋\nline 2")`` exited and ``Get-Clipboard -Raw`` read it
    exactly, stored LF-only (no translation); Notepad pastes that LF-only
    text as two lines, while array-form ``Get-Clipboard`` (both PowerShells)
    splits only on CRLF and reports it as one line;
    ``copy("")`` left ``Get-Clipboard`` empty and ``paste()`` ``""``;
    image-only read ``""`` with ``inspect()`` kinds ``image``; a clipboard
    held open by another process made ``paste()`` raise
    ``ClipboardContentError`` (cause ``PyperclipWindowsException``) after
    about 0.5 s, and it succeeded after release.

  The Linux and Windows venues are headless CI runner sessions, not
  owner-held desktops. Unverified: delegated paths (``xsel``, Klipper, Qt,
  WSL), Cygwin, SSH sessions,
  containers, headless environments other than those jobs, and remote
  desktops. Re-run with ``CLIPBOARD_NATIVE_PROBE=1`` and
  ``tests/test_text_native_macos.py``,
  ``tests/test_text_native_linux_x11.py`` (under ``xvfb-run -a``),
  ``tests/test_text_native_linux_wayland.py`` (inside Sway), or
  ``tests/test_text_native_windows.py``; each wrapper runs its
  ``scripts/probe_*_native_text.py`` probe and fails rather than skips on an
  evidence limit.
* Image **reads**: macOS Aqua verified (``scripts/probe_macos_native_paste_image.py``).
  Windows / X11 / Wayland reads remain evidence-limited (no usable session in
  that verification); do not generalize Wayland from X11 or an unstated compositor.
* Image **writes** ``copy_image``: macOS Aqua verified (26.6.2 / 25G83 / Darwin
  25.6.0, Pillow 11.3.0, Python 3.13, arm64; RGBA preserved;
  ``scripts/probe_macos_native_copy_image.py``). Linux X11 verified under gated
  GHA ``native-linux-x11-copy-image`` (Xvfb + ``xclip``, Python 3.13 / Pillow
  11.3.0; headless CI, not owner desktop). Wayland verified **only** under
  ``native-linux-wayland-copy-image`` with named compositor **Sway** (do not
  generalize). Windows writes: evidence limit (Darwin checkout; GHA Windows is
  headless pytest only).
* ``copy_html``: macOS Aqua dual-offer verified (``scripts/probe_macos_native_copy_html.py``,
  26.6.2 / 25G83 / arm64, ``osascript`` / AppKit). Linux X11 / Wayland (named
  compositor only) / Windows HTML Format: evidence limits here (Darwin; probes
  exit 2 with ``evidence_limit`` / ``verified: false``).
* ``inspect()``: macOS Aqua verified with independent AppKit producer
  (HTML+text; image-only when feasible), matching kinds/UTIs, then independent
  consumer (non-mutation); floors ``scripts/probe_macos_native_inspect.py``
  26.6.2 / 25G83 / arm64, ``NSPasteboard`` ``types()`` (no payload fetch).
  Linux X11 (needs ``DISPLAY`` + ``xclip`` TARGETS), Wayland (``WAYLAND_DISPLAY``
  + ``wl-paste -l``, compositor-scoped), and Windows (``ctypes`` / ``user32``
  ``EnumClipboardFormats``, no ``win32clipboard``): evidence limits here
  (Darwin); probes ``scripts/probe_linux_x11_native_inspect.py``,
  ``scripts/probe_linux_wayland_native_inspect.py``,
  ``scripts/probe_windows_native_inspect.py`` record ``evidence_limit`` /
  ``verified: false`` (Wayland also ``compositor_generalization: false``;
  exit 2). Re-run on owner-held desktops to replace limits. Empty Linux
  CLIPBOARD → empty ``inspect()``, ``paste_html()`` / ``paste_files()``
  ``None`` (and ``paste()`` ``""``, ``paste_image()`` ``None``) **verified**
  in CI on ``ubuntu-26.04`` (image 20261025.179.1): a fresh Xvfb
  2:21.1.22-1ubuntu1.3 with xclip 0.13 (``native-linux-x11-clear``; xclip
  TARGETS exit 1, stderr ``Error: target TARGETS not available``) and a fresh
  headless Sway 1.11 with wl-clipboard 2.2.1 (``native-linux-wayland-clear``;
  ``wl-paste -l`` exit 1, stderr ``Nothing is copied``). The newer xclip
  wording ``There is no owner for the`` and wl-paste ``No selection`` are
  covered by desktop-free tests only.
* ``clear()``: macOS Aqua **verified** by ``scripts/probe_macos_native_clear.py``
  (wrapper ``tests/test_clear_native_macos.py``, run with ``--extra images``)
  on the owner's unlocked console session, macOS 26.6.2 (build 25G83) /
  Darwin 25.6.0, arm64, Python 3.13.17, Pillow 11.3.0. Independent
  ``osascript`` / AppKit producers offered HTML + text (``public.html``,
  ``Apple HTML pasteboard type``, ``public.utf8-plain-text``,
  ``NSStringPboardType``) and, separately, a PNG (listed as ``public.png``,
  ``Apple PNG pasteboard type``, ``public.tiff``, ``NeXT TIFF v4.0 pasteboard
  type``); a child Python called ``clear()`` and exited (about 0.3 s); an
  independent JXA ``NSPasteboard types`` listing was then empty, ``pbpaste``
  printed nothing, and the probe's own ``paste()`` was ``""``,
  ``paste_html()`` / ``paste_image()`` / ``paste_files()`` were ``None`` and
  ``inspect()`` had no kinds or formats. ``clear()`` twice on the cleared
  pasteboard succeeded; ``copy("")`` left ``public.utf8-plain-text`` and
  ``NSStringPboardType`` listed, and a following ``clear()`` left none.
  Evidence limits: whether a macOS privacy prompt appeared on screen is
  unobserved (the probe cannot capture the screen); every ``clear()``
  finished within its bound without blocking. Linux Wayland (``wl-copy
  --clear``) **pending CI**: ``scripts/probe_linux_wayland_native_clear.py``
  (wrapper ``tests/test_clear_native_linux_wayland.py``, job
  ``native-linux-wayland-clear``) on headless Sway 1.11 with wl-clipboard
  2.2.1 on ``ubuntu-26.04`` first records the raw ``wl-copy --clear`` against
  an independent ``text/html`` owner, then has independent ``wl-copy``
  producers of ``text/html`` and ``text/plain;charset=utf-8`` and a
  ``copy_image()`` owner each followed by a child ``clear()``, ``clear()``
  twice, and a ``PATH`` without ``wl-copy``. Evidence limits: other Wayland
  compositors, and desktops with clipboard managers (GNOME, KDE Plasma /
  Klipper) that may re-offer a saved entry, are unverified. Linux X11 and
  Windows clears are not available yet.
* macOS Aqua HTML **reads** via ``paste_html`` (default reader: the
  pasteboard's ``public.html`` type via built-in ``osascript`` / AppKit) have
  been verified with an independent **browser** producer: Google Chrome
  156.0.8078.74 copied a Unicode styled-link selection (context left
  unselected) from a local page, ``paste_html()`` returned that selection's
  markup, and an independent consumer afterwards saw the same offer with an
  unchanged ``changeCount``; text-only, image-only and file-list offers
  returned ``None``. Floors: macOS 26.6.2 (build 25G83) / Darwin 25.6.0,
  Python 3.13, arm64 Aqua. Re-run with ``CLIPBOARD_NATIVE_PROBE=1`` /
  ``scripts/probe_macos_native_paste_html.py`` to refresh floors on another
  host.
* Linux X11 HTML **reads** via ``paste_html`` (default reader: ``xclip
  -selection clipboard -o`` listing ``TARGETS``, then requesting
  ``text/html``; a missing ``xclip`` or display raises
  ``ClipboardContentError``) have been verified with an independent **helper**
  producer under gated GitHub Actions job ``native-linux-x11-paste-html`` on
  ``ubuntu-latest`` (Ubuntu 26.04 image 20261025.179) with Xvfb + ``xclip``
  0.13: an independent ``xclip -t text/html -i`` producer offered a non-ASCII
  fragment, ``paste_html()`` returned it exactly, a later independent ``xclip
  -o`` consumer saw the same bytes, and text-only, image-only and unowned
  clipboards returned ``None``. Floors: Python 3.13, xclip 0.13. That helper
  is **not** a browser or rich editor, so browser / rich-editor
  interoperability on X11 remains unobserved; the venue is headless CI with
  Xvfb, not an owner-held desktop.
* Linux Wayland HTML **reads** via ``paste_html`` (default reader in a Wayland
  session: ``wl-paste --list-types``, then ``wl-paste --no-newline --type
  text/html``; an empty clipboard returns ``None``, while a missing
  ``wl-paste`` or no reachable compositor raises ``ClipboardContentError``)
  have been verified with an independent **helper** producer **only** under
  gated GitHub Actions job ``native-linux-wayland-paste-html`` on
  ``ubuntu-latest`` (Ubuntu 26.04) with the named compositor **Sway** 1.11
  (``WLR_BACKENDS=headless``) and ``wl-clipboard`` 2.2.1: an independent
  ``wl-copy --type text/html`` producer offered a non-ASCII fragment,
  ``paste_html()`` returned it exactly, a later independent ``wl-paste``
  consumer saw the same bytes, and text-only, image-only and cleared
  clipboards returned ``None`` (``wl-paste`` reports "Nothing is copied").
  Floors: Python 3.13, Sway 1.11, wl-clipboard 2.2.1. That helper is **not** a
  browser or rich editor, so browser / rich-editor interoperability on Wayland
  remains unobserved; the venue is headless CI, not an owner-held desktop; the
  result covers Sway only and does not generalize to other Wayland
  compositors.
* Windows desktop HTML **reads** via ``paste_html`` (default reader: the
  registered ``HTML Format`` through user32 / kernel32 via ``ctypes``, no
  pywin32; the fragment is cut at the envelope's UTF-8 ``StartFragment`` /
  ``EndFragment`` byte offsets; ``OpenClipboard`` is retried for about 1 s
  while another process holds the clipboard, then ``ClipboardContentError``)
  have been verified with an independent **helper** producer under gated
  GitHub Actions job ``native-windows-paste-html`` on ``windows-latest``
  (Windows Server 2025, 10.0.26100; Windows PowerShell 5.1.26100, .NET CLR
  4.0.30319.42000): an independent PowerShell / .NET ``DataObject`` +
  ``MemoryStream`` producer placed a UTF-8 byte-offset envelope with a
  non-ASCII fragment and non-ASCII unselected context, ``paste_html()``
  returned only the fragment (no headers or context), an independent
  ``ctypes`` consumer in another process saw the same bytes and sequence
  number afterwards, and text-only, image-only and cleared clipboards returned
  ``None``. Floors: Python 3.13, Windows 10.0.26100. That helper builds the
  envelope by hand and is **not** a browser or rich editor, so browser /
  rich-editor interoperability on Windows remains unobserved; the venue is a
  CI runner session, not an owner-held desktop. On that .NET Framework,
  ``Clipboard.SetText(..., Html)`` and ``Set-Clipboard -AsHtml`` wrote the
  non-ASCII content as ANSI so their offsets no longer matched the bytes;
  ``paste_html`` raised ``ClipboardContentError`` for them rather than return
  a guessed fragment.
* ``paste_files``: macOS Aqua **verified** (independent ``osascript`` /
  ``NSFilenamesPboardType``; Unicode+spaces; non-mutation; floors macOS
  26.6.2 / Darwin 25.6.0 / arm64;
  ``scripts/probe_macos_native_paste_files.py``). Linux X11 (``xclip``
  ``text/uri-list`` after a **named** FM), Linux Wayland (``wl-paste``
  ``text/uri-list`` on a **named** compositor after a **named** FM), and
  Windows (Explorer ``CF_HDROP``) are **evidence limits** here (Darwin; no
  session/helpers) — never verified; do not generalize one FM or compositor.
  Probes ``scripts/probe_{linux_x11,linux_wayland,windows}_native_paste_files.py``
  exit 2 with ``verified: false``.
* ``copy_files``: each desktop was checked with two sources whose names
  contain Unicode and spaces, copied by the public ``copy_files`` in a child
  Python process that **exits** before an independent consumer (not this
  library) reads the offer. ``paste_files()`` agreement is recorded only as a
  consistency check, not as interoperability proof. A file-manager paste is
  claimed only where one was observed; one file manager or compositor is not
  generalized to others.

  * macOS Aqua **offer verified; Finder paste not observed** by
    ``scripts/probe_macos_native_copy_files.py`` (wrapper
    ``tests/test_copy_files_native_macos.py``): an independent ``osascript``
    consumer read ``public.file-url`` items equal to the absolute paths, in
    order, after the writer exited and again on rechecks; a refused copy
    (missing path) left the prior text readable via ``pbpaste``. Floors:
    macOS 26.6.2 (build 25G83) / Darwin 25.6.0, arm64, Python 3.13.17.
    Evidence limit: Finder Paste of this offer is **unobserved** (developer
    rounds pasted nothing, cause unexplained, and one round ran against a
    locked screen), so pasting into Finder is not a verified claim.
  * Windows **verified** under gated job ``native-windows-copy-files`` (run
    41561268655; ``windows-latest`` image win25-vs2026 20261030.294.1,
    Windows NT 10.0.26100, Windows PowerShell 5.1.26100.33648, Python
    3.13.17, AMD64): an independent PowerShell consumer read the exact
    ``CF_HDROP`` path list and ``Preferred DropEffect`` 1 (copy) after the
    writer exited, with rechecks at 0 / 5 / 10 s, and the Explorer shell's
    ``Shell.Application`` Paste verb copied both files byte-equal into a
    folder with the sources unchanged. Evidence limit: that is the Explorer
    shell verb in a CI runner session, not a paste in an interactive Explorer
    window on an owner-held desktop.
  * Linux X11 **verified with Thunar only** under gated job
    ``native-linux-x11-copy-files`` (run 41562962489; Ubuntu 24.04.5 LTS,
    Thunar 4.18.8, xclip 0.13, Python 3.13.14, Xvfb with Openbox): an
    independent ``xclip`` read the exact CRLF ``text/uri-list`` body after
    the writer exited, with rechecks; Thunar Paste copied both files
    byte-equal with the sources unchanged; with ``xclip`` off ``PATH``,
    ``copy_files`` raised ``ClipboardContentError`` with the install hint and
    the prior text survived. Other X11 file managers (GNOME Files, Dolphin,
    and so on) are unverified; the venue is headless CI, not an owner-held
    desktop.
  * Linux Wayland **offer verified only on Sway; no file-manager paste
    observed** under gated job ``native-linux-wayland-copy-files`` (run
    41564513429; headless **Sway** 1.9, ``wl-clipboard`` 2.2.1, Ubuntu
    24.04, Python 3.13.14): an independent ``wl-paste`` read the exact body
    after the writer exited, with rechecks; with ``wl-copy`` off ``PATH``,
    ``copy_files`` raised with the install hint and the prior text survived.
    Evidence limit: a Thunar-on-Sway paste attempt pasted nothing (cause
    undiagnosed), so pasting into any Wayland file manager is not a verified
    claim, and other compositors are unverified.

  Re-run with ``CLIPBOARD_NATIVE_PROBE=1`` and
  ``tests/test_copy_files_native_{macos,windows,linux_x11,linux_wayland}.py``;
  each runs its ``scripts/probe_*_native_copy_files.py`` probe. The earlier
  helper-only Thunar format experiment is recorded in
  ``docs/file-manager-offers.md``.

Development
-----------

Nix flakes (`Nix <https://nixos.org/download/>`_), like Lizard: ``flake.lock``
pins Python 3.13, uv, Make, actionlint; ``uv.lock`` pins deps.

::

   nix develop
   make deps check lint-workflows build test-package

Or ``nix develop -c make check``. Without Nix: Python 3.13 + uv + same Make
targets. Windows: ``uv sync --locked``, ``uv run --locked --extra images
pytest``, ``uv run --locked ruff check .``. Do not install into system Python.
GHA covers Nix plus Python 3.10–3.14, installs wheel/sdist outside the tree,
and uses an in-memory clipboard (no desktop). X11/Wayland image-write probes
and the X11, Wayland, and Windows ``paste_html``, ``copy_files``, and text
probes are separate gated jobs.

Publishing
----------

A matching version tag runs checks and publishes via PyPI Trusted Publishing,
then a GitHub release. Configure the ``pypi`` environment and trusted
publisher first. See
`the release guide <https://github.com/terryyin/clipboard/blob/master/docs/releasing.md>`_.
