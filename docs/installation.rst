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
generalize). Linux image **writes**: X11 ``xclip`` (for example ``apt
install xclip``), which keeps running in the background as the image's
owner; ``copy_image`` returns once it serves the PNG. Wayland ``wl-copy``
from ``wl-clipboard`` (for example ``apt install wl-clipboard``), whose
background part keeps serving the image; ``copy_image`` returns once its
foreground part exits. Both share one 10 s bound, and a missing ``xclip`` /
``wl-copy`` raises ``ClipboardImageError`` with an install hint before the
clipboard is replaced. Windows/macOS
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
