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

Installation
------------

``python -m pip install clipboard`` (Python 3.10+). Text needs a working
desktop clipboard backend on Linux; see
`pyperclip <https://pyperclip.readthedocs.io/>`_. Images:
``python -m pip install 'clipboard[images]'``. ``copy_html`` and ``inspect``
do **not** need that extra.

Linux image **reads**: X11 ``xclip``; Wayland ``wl-paste``. Linux HTML
**writes** need a multi-MIME helper (X11 multi-type ``xclip``; Wayland e.g.
``wl-copy`` on a **named** compositor — do not generalize). Linux image
**writes**: X11 ``xclip`` / Wayland ``wl-copy`` (may keep a background owner).
Windows/macOS need a usable desktop session; rich/image APIs are not
guaranteed under WSL, SSH, containers, or headless CI.

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
are separate gated jobs.

Publishing
----------

A matching version tag runs checks and publishes via PyPI Trusted Publishing,
then a GitHub release. Configure the ``pypi`` environment and trusted
publisher first. See
`the release guide <https://github.com/terryyin/clipboard/blob/master/docs/releasing.md>`_.
