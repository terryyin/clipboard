clipboard
=========

A cross platform clipboard operation library of Python. Works for Windows, Mac and Linux.

Well, as I was trying to implement this, I realize that everything is included in pyperclip already: https://pypi.python.org/pypi/pyperclip/

But anyway, `clipboard` is a better name. You are free to choose:-) I might add more features to it.

Usage
-----

Text copy and paste (no optional extras required):

::

   import clipboard
   clipboard.copy("abc")  # now the clipboard content will be string "abc"
   text = clipboard.paste()  # text will have the content of clipboard

To read or write a static raster image on the clipboard as a Pillow ``Image``,
install the optional ``images`` extra (Pillow) and call ``paste_image`` /
``copy_image``:

::

   import clipboard
   from PIL import Image

   image = clipboard.paste_image()  # Pillow Image, or None when none is offered
   clipboard.copy_image(Image.new("RGB", (8, 8), (255, 0, 0)))

``paste_image`` leaves clipboard contents unchanged. Ordinary absence (text-only
clipboard, empty clipboard, or a file-reference / filename-list offer) returns
``None``. Access, missing-helper, transfer, or malformed-image failures raise
``clipboard.ClipboardImageError`` instead of returning ``None``.

``copy_image`` publishes one static raster offer (Pillow ``Image`` only; open
path/bytes yourself first). Non-RGB(A) modes are converted to a transferable
RGB or RGBA raster before the offer; animated / multi-frame / path overloads
are out of scope. Invalid or unloadable input raises
``clipboard.ClipboardImageError`` **before** replacing current clipboard
contents. Missing helper, denied access, transfer failure, or an unsupported
session raise ``ClipboardImageError`` (no silent success). A successful write
replaces prior text and image representations for that clipboard. Calling
``paste_image`` or ``copy_image`` without the extra raises ``ImportError``.

To publish an HTML fragment with a matching plain-text alternative as one
clipboard offer, call ``copy_html``:

::

   import clipboard
   clipboard.copy_html(
       '<a href="https://example.com"><b>café</b></a>',
       'café → https://example.com',
   )

``copy_html(html, text)`` requires the caller to supply both a Unicode HTML
fragment and a matching plain-text alternative; the library does not synthesize
text from HTML. Invalid arguments are rejected with
``clipboard.ClipboardContentError`` **before** replacing clipboard contents.
Success means both representations are published together as one offer: a rich
consumer can obtain HTML and a text-only consumer can obtain the alternative.
Inability to offer both together, missing helpers, denied access, transfer
failure, or an unsupported session raises ``ClipboardContentError`` — never a
silent text-only "success". Sequential single-format writes are not a dual
offer.

On macOS Aqua the default writer uses the system pasteboard
(``NSPasteboard`` HTML + string types via ``osascript``). On other platforms
the default path raises ``ClipboardContentError`` until a dual-offer writer is
available; Linux and Windows HTML writes remain evidence-limited rather than
verified (see below) — do not read an evidence limit as proof that a native
writer is already present for that desktop.

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

Installation
------------

Install from PyPI with ``python -m pip install clipboard``. This checkout
supports Python 3.10 and newer. Text ``copy`` / ``paste`` need a working desktop
clipboard backend on Linux; see the
`pyperclip documentation <https://pyperclip.readthedocs.io/>`_.

For ``paste_image`` and ``copy_image``, install the optional extra so Pillow is
available:

::

   python -m pip install 'clipboard[images]'

``copy_html`` and ``paste_html`` do **not** require the ``clipboard[images]``
extra.

On Linux, image clipboard **reads** also need a helper on ``PATH``:

* X11: ``xclip``
* Wayland: ``wl-paste`` (from wl-clipboard)

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

For Linux HTML + plain-text **writes**, a helper must be able to offer
**multiple** MIME types together (not a one-type-only path that drops the
alternative):

* X11: multi-type-capable ``xclip`` (or equivalent) offering ``text/html`` and
  ``text/plain`` on CLIPBOARD together
* Wayland: a multi-type-capable helper (for example ``wl-copy``) on a **named**
  compositor; do not generalize one compositor's result to all Wayland
  environments

On Windows, a successful dual offer uses interoperable ``HTML Format`` (UTF-8
fragment/context byte offsets, including non-ASCII) plus Unicode text in the
same update. Windows and macOS need a usable desktop clipboard / pasteboard
session; rich clipboard writes are not guaranteed under WSL, SSH, containers,
or headless CI.

Image **writes** via ``copy_image`` on Linux need:

* X11: ``xclip`` (publishes ``image/png`` on CLIPBOARD; ``xclip -quiet`` may
  keep a background owner so the offer stays pasteable after the writing
  process exits)
* Wayland: ``wl-copy`` (from wl-clipboard; publishes ``image/png``; may keep a
  background owner so the offer stays pasteable after the writing process
  exits)

Windows and macOS need a usable desktop clipboard / pasteboard session; image read/write and rich clipboard writes are not guaranteed under WSL, SSH, containers, or headless CI.

Evidence / verified platforms:

* macOS Aqua pasteboard image reads have been verified with an independent
  producer via the gated native probe (``CLIPBOARD_NATIVE_PROBE=1`` /
  ``scripts/probe_macos_native_paste_image.py``).
* Windows desktop, Linux X11 + ``xclip``, and Linux Wayland + ``wl-paste``
  image reads remain supported targets but are each evidence-limited
  (unverified / unsupported for native proof): no usable desktop clipboard
  session for those environments was available during image-read
  verification. Do not treat any of them as natively verified from that
  work, and do not generalize a Wayland claim from X11 or an unstated
  compositor.
* macOS Aqua pasteboard image **writes** via ``copy_image`` have been verified
  with an independent consumer (``PIL.ImageGrab.grabclipboard`` after the writing
  process exits) at floors macOS 26.6.2 (build 25G83) / Darwin 25.6.0, Pillow
  11.3.0, Python 3.13, arm64 Aqua; RGBA alpha was preserved in that probe.
  Re-run with ``CLIPBOARD_NATIVE_PROBE=1`` /
  ``scripts/probe_macos_native_copy_image.py`` to refresh floors on another host.
* Linux X11 image **writes** via ``copy_image`` (``xclip``) have been verified
  under gated GitHub Actions job ``native-linux-x11-copy-image`` on
  ``ubuntu-latest`` with Xvfb + ``xclip`` (independent consumer ``xclip -o``
  ``image/png`` after writer exit) at floors Python 3.13 / Pillow 11.3.0; the
  venue is headless CI with Xvfb, not an owner-held desktop. Opaque writer-exit
  succeeded; the RGBA case is exercised in the same probe (preserve-or-drop
  recorded there).
* Linux Wayland image **writes** via ``copy_image`` (``wl-copy``) have been
  verified **only** under gated GitHub Actions job
  ``native-linux-wayland-copy-image`` on ``ubuntu-latest`` with the named
  compositor **Sway** (``WLR_BACKENDS=headless``, ``wl-clipboard``; independent
  consumer ``wl-paste -t image/png`` after writer exit) at floors Python 3.13 /
  Pillow 11.3.0; do not generalize that result to other Wayland compositors.
  Opaque writer-exit succeeded; the RGBA case is exercised in the same probe
  (preserve-or-drop recorded there).
* Windows desktop remains a supported write target, but image **writes** via
  ``copy_image`` are **unverified**: no usable Windows desktop session was
  available during ``SEED-001#write-images`` execution (developer checkout is
  Darwin; GitHub Actions ``windows-latest`` matrix jobs are headless pytest
  only and are not a desktop clipboard probe venue). This is an explicit
  evidence limit — not a verified claim. Image-write story acceptance is
  **not** Windows-only: Linux X11 (Xvfb CI) and Wayland (Sway CI) writer-exit
  proofs above are required and already observed (issue #5); Windows remains
  evidence-limited beside them.
* macOS Aqua HTML + plain-text dual-offer writes via ``copy_html`` have been
  verified with independent rich (``NSPasteboardTypeHTML``) and text
  (``pbpaste``) consumers after the writing process exits. Floors recorded by
  ``scripts/probe_macos_native_copy_html.py`` on this work: macOS
  ProductVersion 26.6.2, BuildVersion 25G83, machine arm64 (Apple Silicon),
  method ``osascript`` / AppKit ``NSPasteboardTypeHTML`` +
  ``NSPasteboardTypeString``. Re-run with ``CLIPBOARD_NATIVE_PROBE=1`` /
  the probe script to refresh floors on another host.
* Linux X11 HTML + plain-text dual-offer writes via ``copy_html`` are an
  explicit **evidence limit** on this execution host: no usable X11 session
  with a multi-type-capable helper (for example ``xclip`` offering
  ``text/html`` and ``text/plain`` together) was available (Darwin checkout;
  ``xclip`` not on ``PATH``). Do not treat X11 HTML write as verified.
  ``scripts/probe_linux_x11_native_copy_html.py`` records
  ``evidence_limit`` / ``verified: false`` (exit 2) rather than silent
  success. Re-run that gated X11 dual-consumer probe on an owner-held X11
  session to replace this limit.
* Linux Wayland HTML + plain-text dual-offer writes via ``copy_html`` are an
  explicit **evidence limit** on this execution host: no usable Wayland
  session with a multi-type-capable helper on a **named** compositor was
  available (Darwin checkout; ``wl-copy`` / ``wl-paste`` not on ``PATH``;
  ``WAYLAND_DISPLAY`` unset). Do not treat Wayland HTML write as verified,
  and do not generalize any future single-compositor result to all Wayland
  environments. ``scripts/probe_linux_wayland_native_copy_html.py`` records
  ``evidence_limit`` / ``verified: false`` /
  ``compositor_generalization: false`` (exit 2) rather than silent success.
  Re-run that gated Wayland dual-consumer probe on an owner-held Wayland
  session to replace this limit for that compositor only.
* Windows desktop HTML + Unicode text dual-offer writes via ``copy_html``
  (interoperable ``HTML Format`` with UTF-8 fragment/context byte offsets for
  non-ASCII content) are an explicit **evidence limit** on this execution
  host: no usable Windows desktop session was available (Darwin checkout).
  Do not treat Windows HTML write as verified.
  ``scripts/probe_windows_native_copy_html.py`` records
  ``evidence_limit`` / ``verified: false`` /
  ``non_ascii_case_required_for_verification: true`` (exit 2) rather than
  silent success. Re-run that gated Windows dual-consumer probe on an
  owner-held Windows desktop to replace this limit, including a non-ASCII
  fragment/context case.
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

Default automated tests use an in-memory backend and do not exercise a real
desktop clipboard; native probes stay explicitly gated and are not part of the
default suite. The X11 and Wayland image-write probes and the X11, Wayland,
and Windows ``paste_html`` probes are separate gated jobs, not part of the
default matrix pytest. A headless CI venue is evidence for the recorded floors
only; it is not a guaranteed desktop.

Development
-----------

The development environment uses `Nix <https://nixos.org/download/>`_ with flakes
enabled, like the neighboring Lizard project. ``flake.lock`` pins Python 3.13,
uv, Make, and actionlint. ``pyproject.toml`` declares Python dependencies and
``uv.lock`` pins their resolved versions.

::

   nix develop
   make deps            # sync the locked Python environment
   make check           # Ruff lint, format check, and pytest
   make lint-workflows  # GitHub Actions validation with actionlint
   make build           # wheel, sdist, and strict package metadata checks
   make test-package    # build and test installation of both distributions

For a single command, use ``nix develop -c make check``. Without Nix, install
Python 3.13 and uv, then use the same Make targets; actionlint is needed for
``make lint-workflows``. Windows contributors can run ``uv sync --locked``,
``uv run --locked --extra images pytest``, and ``uv run --locked ruff check .``
directly.
Do not install project dependencies into the system Python environment.

GitHub Actions checks the Nix environment and tests Python 3.10–3.14, including
Windows and macOS at the supported version boundaries. Package checks install
both the wheel and source archive outside the source tree. Tests use an
in-memory clipboard backend and do not require desktop clipboard access.

Publishing
----------

Pushing a matching version tag runs checks and publishes through PyPI Trusted
Publishing, followed by a GitHub release. Maintainers must first configure the
``pypi`` environment and trusted publisher. See
`the release guide <https://github.com/terryyin/clipboard/blob/master/docs/releasing.md>`_
for setup, approval, and release steps.
