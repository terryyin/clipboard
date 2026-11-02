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

To recover local paths from a file-manager clipboard offer, call
``paste_files`` (no ``clipboard[images]`` extra required):

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
or existence check on referenced paths; returned paths are not promised to
still exist or be readable. Cut/move companion markers
(``PreferredDropEffect``, ``x-special/gnome-copied-files`` “cut”,
``application/x-kde-cutselection``, equivalents) are ignored for library
behavior: paths are still returned when references are offered; the library
never moves, deletes, or reissues cut as move. Do not overload ``paste()`` /
``copy()`` for file lists.

Supported desktops for this API: Windows Explorer (or equivalent)
``CF_HDROP``; macOS Aqua Finder (or equivalent) file-URL / filename pasteboard
types; Linux X11 + ``xclip`` requesting ``text/uri-list`` on CLIPBOARD from a
**named** file manager; Linux Wayland + ``wl-paste`` requesting
``text/uri-list`` (or equivalent) from a **named** file manager on the
**named** compositor actually proved. WSL, SSH, containers, and headless CI
are not additional guaranteed desktops. See Evidence for verified floors vs
explicit limits.

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

``copy_html`` and ``paste_files`` do **not** require ``clipboard[images]``.

On Linux, helpers on ``PATH``:

* Image **reads**: X11 ``xclip``; Wayland ``wl-paste`` (wl-clipboard)
* File-list **reads** (``paste_files`` / ``text/uri-list``): X11
  ``xclip -o -selection clipboard -t text/uri-list``; Wayland
  ``wl-paste -t text/uri-list`` (missing helper → ``ClipboardContentError``,
  not silent ``None``)
* HTML + plain-text **writes**: a helper that offers **multiple** MIME types
  together — X11 multi-type ``xclip`` (``text/html`` + ``text/plain``); Wayland
  multi-type helper (for example ``wl-copy``) on a **named** compositor (do not
  generalize one compositor)
* Image **writes** (``copy_image``): X11 ``xclip`` (``image/png``; ``-quiet`` may
  keep a background owner); Wayland ``wl-copy`` (same)

On Windows, a successful HTML dual offer uses interoperable ``HTML Format``
(UTF-8 fragment/context byte offsets, including non-ASCII) plus Unicode text
in the same update. Windows and macOS need a usable desktop clipboard /
pasteboard session; image read/write, rich writes, and file-list reads are not
guaranteed under WSL, SSH, containers, or headless CI.

Evidence / verified platforms (``CLIPBOARD_NATIVE_PROBE=1``; default tests are
in-memory / desktop-free). An evidence limit is never a verified claim or
silent success for that desktop:

* Images **read**: macOS Aqua verified (independent producer;
  ``scripts/probe_macos_native_paste_image.py``). Windows, Linux X11+``xclip``,
  and Linux Wayland+``wl-paste`` remain evidence-limited (no usable session
  during image-read verification); do not generalize Wayland from X11 or an
  unstated compositor.
* Images **write** (``copy_image``): macOS Aqua verified (independent
  ``ImageGrab.grabclipboard`` after writer exit; floors macOS 26.6.2 build
  25G83 / Darwin 25.6.0 / Pillow 11.3.0 / Python 3.13 arm64; RGBA preserved;
  ``scripts/probe_macos_native_copy_image.py``). Linux X11 verified under gated
  GHA ``native-linux-x11-copy-image`` (ubuntu-latest Xvfb+``xclip``; floors
  Python 3.13 / Pillow 11.3.0; CI venue, not owner desktop). Linux Wayland
  verified **only** under gated GHA ``native-linux-wayland-copy-image`` with
  named compositor **Sway** (do not generalize). Windows write: explicit
  evidence limit (Darwin checkout; GHA ``windows-latest`` is headless pytest
  only). Image-write acceptance is not Windows-only (issue #5).
* HTML dual-offer (``copy_html``): macOS Aqua verified (independent rich +
  text consumers; floors ProductVersion 26.6.2 Build 25G83 arm64;
  ``scripts/probe_macos_native_copy_html.py``). Linux X11 / Wayland / Windows:
  evidence limits here (Darwin; helpers/session missing) —
  ``scripts/probe_{linux_x11,linux_wayland,windows}_native_copy_html.py``
  record ``verified: false`` (Wayland also ``compositor_generalization:
  false``; Windows requires a non-ASCII case for future verification).
* ``paste_files``: macOS Aqua **verified** (independent ``osascript`` /
  ``NSFilenamesPboardType``; Unicode+spaces; non-mutation; floors macOS
  26.6.2 / Darwin 25.6.0 / arm64;
  ``scripts/probe_macos_native_paste_files.py``). Linux X11 (``xclip``
  ``text/uri-list`` after a **named** FM), Linux Wayland (``wl-paste``
  ``text/uri-list`` on a **named** compositor after a **named** FM), and
  Windows (Explorer ``CF_HDROP``) are **evidence limits** here (Darwin; no
  session/helpers) — never verified; do not generalize one FM or compositor.
  Probes ``scripts/probe_{linux_x11,linux_wayland,windows}_native_paste_files.py``
  exit 2 with ``verified: false`` (X11 ``file_manager_generalization: false``;
  Wayland ``compositor_generalization: false``).

Native probes are not part of the default suite. X11/Wayland image-write
probes are separate gated jobs, not matrix pytest.

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
directly. Do not install project dependencies into the system Python environment.

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
