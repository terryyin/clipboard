clipboard
=========

A cross platform clipboard library for Python (Windows, macOS, Linux). Text
``copy`` / ``paste`` re-export pyperclip; richer APIs sit beside them.

Usage
-----

Text (no optional extras):

::

   import clipboard
   clipboard.copy("abc")
   text = clipboard.paste()

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
WSL, SSH, containers, and headless CI are not additional guaranteed desktops
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

Installation
------------

``python -m pip install clipboard`` (Python 3.10+). Text needs a working
desktop clipboard backend on Linux; see
`pyperclip <https://pyperclip.readthedocs.io/>`_. Images:
``python -m pip install 'clipboard[images]'``. ``copy_html``, ``paste_html``,
``paste_files``, and ``inspect`` do **not** need that extra.

Linux image **reads**: X11 ``xclip``; Wayland ``wl-paste``. Linux file-list
**reads** (``paste_files``): X11 ``xclip -o -selection clipboard -t
text/uri-list``; Wayland ``wl-paste -t text/uri-list`` (missing helper →
``ClipboardContentError``, not silent ``None``). Linux HTML **writes** need a
multi-MIME helper (X11 multi-type ``xclip``; Wayland e.g. ``wl-copy`` on a
**named** compositor — do not generalize). Linux image **writes**: X11
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
  exit 2). Re-run on owner-held desktops to replace limits.
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
and the X11, Wayland, and Windows ``paste_html`` probes are separate gated jobs.

Publishing
----------

A matching version tag runs checks and publishes via PyPI Trusted Publishing,
then a GitHub release. Configure the ``pypi`` environment and trusted
publisher first. See
`the release guide <https://github.com/terryyin/clipboard/blob/master/docs/releasing.md>`_.
