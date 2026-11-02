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

``copy_html`` does **not** require the ``clipboard[images]`` extra.

On Linux, image clipboard **reads** also need a helper on ``PATH``:

* X11: ``xclip``
* Wayland: ``wl-paste`` (from wl-clipboard)

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
* macOS Aqua ``paste_files`` verified with independent ``osascript`` / ``NSFilenamesPboardType`` producer (Unicode+spaces; not library round-trip), AppKit re-read non-mutation, files untouched; floors macOS 26.6.2 (25G83) / Darwin 25.6.0 / arm64 (``scripts/probe_macos_native_paste_files.py``; ``CLIPBOARD_NATIVE_PROBE=1`` / ``tests/test_paste_files_native_macos.py``).

Default automated tests use an in-memory backend and do not exercise a real
desktop clipboard; native probes stay explicitly gated and are not part of the
default suite. The X11 and Wayland image-write probes are separate gated jobs,
not part of the default matrix pytest.

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
