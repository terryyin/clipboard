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

To read a static raster image from the clipboard as a Pillow ``Image``, install
the optional ``images`` extra (Pillow) and call ``paste_image``:

::

   import clipboard
   image = clipboard.paste_image()  # Pillow Image, or None when none is offered

``paste_image`` leaves clipboard contents unchanged. Ordinary absence (text-only
clipboard, empty clipboard, or a file-reference / filename-list offer) returns
``None``. Access, missing-helper, transfer, or malformed-image failures raise
``clipboard.ClipboardImageError`` instead of returning ``None``. Calling
``paste_image`` without the extra raises ``ImportError``.

Installation
------------

Install from PyPI with ``python -m pip install clipboard``. This checkout
supports Python 3.10 and newer. Text ``copy`` / ``paste`` need a working desktop
clipboard backend on Linux; see the
`pyperclip documentation <https://pyperclip.readthedocs.io/>`_.

For ``paste_image``, install the optional extra so Pillow is available:

::

   python -m pip install 'clipboard[images]'

On Linux, image clipboard reads also need a helper on ``PATH``:

* X11: ``xclip``
* Wayland: ``wl-paste`` (from wl-clipboard)

Image **writes** via ``copy_image`` on Linux need:

* X11: ``xclip`` (publishes ``image/png`` on CLIPBOARD; ``xclip -quiet`` may
  keep a background owner so the offer stays pasteable after the writing
  process exits)
* Wayland: ``wl-copy`` (from wl-clipboard; publishes ``image/png``; may keep a
  background owner so the offer stays pasteable after the writing process
  exits)

Windows and macOS need a usable desktop clipboard / pasteboard session; image
reading is not guaranteed under WSL, SSH, containers, or headless CI.

Evidence / verified platforms: macOS Aqua pasteboard image **reads** have been
verified with an independent producer in this project's native probe work.
macOS Aqua pasteboard image **writes** via ``copy_image`` have been verified
with an independent consumer (``PIL.ImageGrab.grabclipboard`` after the writing
process exits) at floors macOS 26.6.2 (build 25G83) / Darwin 25.6.0, Pillow
11.3.0, Python 3.13, arm64 Aqua; RGBA alpha was preserved in that probe.
Linux X11 image **writes** via ``copy_image`` (``xclip``) have been verified
under gated GitHub Actions job ``native-linux-x11-copy-image`` on
``ubuntu-latest`` with Xvfb + ``xclip`` (independent consumer ``xclip -o``
``image/png`` after writer exit) at floors Python 3.13 / Pillow 11.3.0; the
venue is headless CI with Xvfb, not an owner-held desktop. Opaque writer-exit
succeeded; the RGBA case is exercised in the same probe (preserve-or-drop
recorded there). Linux Wayland image **writes** via ``copy_image`` (``wl-copy``)
have been verified **only** under gated GitHub Actions job
``native-linux-wayland-copy-image`` on ``ubuntu-latest`` with the named
compositor **Sway** (``WLR_BACKENDS=headless``, ``wl-clipboard``; independent
consumer ``wl-paste -t image/png`` after writer exit) at floors Python 3.13 /
Pillow 11.3.0; do not generalize that result to other Wayland compositors.
Opaque writer-exit succeeded; the RGBA case is exercised in the same probe
(preserve-or-drop recorded there). Windows desktop remains a supported write
target, unverified pending a later ``SEED-001#write-images`` probe or
evidence limit. Windows and Linux image **reads** remain unverified pending
``SEED-001#read-images-native``. Default automated tests use an in-memory
backend and do not exercise a real desktop clipboard; the X11 and Wayland
write probes are separate gated jobs, not part of the default matrix pytest.

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
