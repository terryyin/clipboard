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
* Primary selection ``copy_primary`` / ``paste_primary`` on Linux X11, by
  ``scripts/probe_linux_x11_native_primary.py`` (wrapper
  ``tests/test_primary_native_linux_x11.py``, run under ``xvfb-run -a`` as a
  step of gated job ``native-linux-x11-text``, run 41799207621; xclip 0.13,
  also observed locally under Xvfb on Ubuntu 24.04). Independent background
  ``xclip -selection primary|clipboard -i`` producers and
  ``xclip -selection primary|clipboard -o`` consumers; every library call
  runs in a child Python that exits first. Steps: a fresh, unowned PRIMARY
  reads ``""`` (xclip 0.13 reports ``Error: target TARGETS not available``);
  different PRIMARY and CLIPBOARD owners are read apart by
  ``paste_primary()`` / ``paste()``; a child's ``copy_primary`` is read by
  the independent PRIMARY consumer after it exits while CLIPBOARD is
  unchanged; a child's ``copy`` leaves PRIMARY unchanged; a refused
  ``copy_primary("a\x00b")`` leaves PRIMARY readable; and with a ``PATH``
  holding ``xsel`` but no ``xclip``, ``paste()`` still reads CLIPBOARD
  through pyperclip while both PRIMARY calls raise naming ``xclip`` within
  the bound. Evidence limits: a headless Xvfb CI session, not an owner-held
  desktop; real middle-click pastes in terminals or toolkits, GNOME, KDE,
  XWayland bridging of PRIMARY, and clipboard managers that sync PRIMARY
  with CLIPBOARD are unobserved.
* Primary selection ``copy_primary`` / ``paste_primary`` on Linux Wayland
  (Sway), by ``scripts/probe_linux_wayland_native_primary.py`` (wrapper
  ``tests/test_primary_native_linux_wayland.py``, run in its own fresh
  headless Sway as a step of gated job ``native-linux-wayland-text``, run
  41803370471; Sway 1.11, wl-clipboard 2.2.1; also observed locally on
  headless Sway 1.9 with wl-clipboard 2.2.1 on Ubuntu 24.04). Independent
  ``wl-copy [--primary] --type text/plain;charset=utf-8`` producers and
  ``wl-paste [--primary] -n`` consumers; every library call runs in a child
  Python (no ``DISPLAY``) that exits first. Steps: a fresh, unselected
  PRIMARY reads ``""`` (wl-paste reports ``Nothing is copied``); different
  PRIMARY and CLIPBOARD offers are read apart by ``paste_primary()`` /
  ``paste()``; a child's ``copy_primary`` is read by the independent
  ``wl-paste --primary -n`` after it exits while ``wl-paste -n`` still gives
  the CLIPBOARD text; a child's ``copy`` leaves PRIMARY unchanged; a refused
  ``copy_primary("a\x00b")`` leaves PRIMARY readable; a child's
  ``copy_primary("")`` leaves PRIMARY reading ``""``; and with a ``PATH``
  lacking ``wl-paste`` both PRIMARY calls raise naming wl-clipboard within
  the bound. Evidence limits: Sway only (the compositor is not
  generalized); GNOME, KDE and other compositors, XWayland bridging of
  PRIMARY, real middle-click pastes, and clipboard managers or desktop
  settings that sync PRIMARY with CLIPBOARD (a newer offer by that program)
  are unobserved. A native compositor without primary-selection support is
  unobserved too: the unsupported report is classified from wl-clipboard
  2.2.1's own wording in desktop-free tests only. Sway's
  ``primary_selection disabled`` is not such a compositor for wl-clipboard:
  one local Sway 1.9 observation saw ``wl-copy --primary`` exit 0 with the
  write dropped and reads saying ``Nothing is copied`` (``copy_primary``'s
  read-back turns that into an error, and ``paste_primary`` reads ``""``),
  while another saw the primary-selection protocol withdrawn but PRIMARY
  still written and read through wlroots data-control.
* Image **reads**: macOS Aqua verified (``scripts/probe_macos_native_paste_image.py``).
  Windows / X11 / Wayland reads remain evidence-limited (no usable session in
  that verification); do not generalize Wayland from X11 or an unstated compositor.
* Image **writes** ``copy_image``: macOS Aqua verified (26.6.2 / 25G83 / Darwin
  25.6.0, Pillow 11.3.0, Python 3.13, arm64; RGBA preserved;
  ``scripts/probe_macos_native_copy_image.py``). Linux X11 verified under gated
  GHA ``native-linux-x11-copy-image`` (Xvfb + ``xclip``, Python 3.13 / Pillow
  11.3.0; headless CI, not owner desktop); a stalled X11 owner or Wayland
  compositor is proved by desktop-free stand-ins only
  (``tests/test_copy_image_x11_write_stall.py``,
  ``tests/test_copy_image_wayland_write_stall.py``).
  Wayland verified **only** under
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
  ``NSStringPboardType`` listed, and a following ``clear()`` left none. An
  independent JXA producer's file URL (``writeObjects`` of an ``NSURL`` for
  an existing temp file, listed as ``public.file-url``,
  ``NSFilenamesPboardType``, ``Apple URL pasteboard type`` and related
  types) and, separately, an unknown ``com.example.clipboard-probe`` type
  alone were each emptied to no types by a child ``clear()``, with
  ``paste_files()`` ``None`` and every reader absent. Evidence limits: whether a macOS privacy prompt appeared on screen is
  unobserved (the probe cannot capture the screen); every ``clear()``
  finished within its bound without blocking. Linux Wayland (``wl-copy
  --clear``) **verified** in CI run 41651498162:
  ``scripts/probe_linux_wayland_native_clear.py``
  (wrapper ``tests/test_clear_native_linux_wayland.py``, job
  ``native-linux-wayland-clear``) on headless Sway 1.11 with wl-clipboard
  2.2.1 on ``ubuntu-26.04`` first records the raw ``wl-copy --clear`` against
  an independent ``text/html`` owner, then has independent ``wl-copy``
  producers of ``text/html`` and ``text/plain;charset=utf-8`` and a
  ``copy_image()`` owner each followed by a child ``clear()``, ``clear()``
  twice, and a ``PATH`` without ``wl-copy``. Each time ``wl-paste -l`` then
  said ``Nothing is copied``, every reader read absence, the library's
  background ``wl-copy`` image owner exited within 5 s, and the ``PATH``
  case raised ``ClipboardContentError`` naming ``wl-clipboard``. CI run
  41658893626 steps 8-9 add an independent ``wl-copy --type text/uri-list`` producer of a
  ``file://`` URI naming an existing temp file and an unknown
  ``application/x-clipboard-probe`` type, each followed by a child
  ``clear()``; both then read nothing copied and ``paste_files()`` ``None``.
  Evidence limits: other Wayland
  compositors, and desktops with clipboard managers (GNOME, KDE Plasma /
  Klipper) that may re-offer a saved entry, are unverified. Linux X11
  (libX11 ``XSetSelectionOwner``) is **verified** in CI run 41654014945 by
  ``scripts/probe_linux_x11_native_clear.py`` (wrapper
  ``tests/test_clear_native_linux_x11.py``, job ``native-linux-x11-clear``)
  on a fresh Xvfb 2:21.1.22 with xclip 0.13 on ``ubuntu-26.04``: the raw
  ``ctypes`` ``XSetSelectionOwner(None)`` from a separate process against an
  independent ``xclip -t text/html`` owner, then an independent ``xclip``
  ``text/html`` producer and a ``copy_image()`` owner each followed by a
  child ``clear()``, ``clear()`` twice, and a ``DISPLAY`` naming no server.
  The raw call left ``XGetSelectionOwner`` at 0 and the ``xclip`` owner
  exited; after each library ``clear()`` ``xclip -o -t TARGETS`` reported no
  owner, every reader read absence, and the library's background ``xclip``
  image owner exited within 5 s; the dead ``DISPLAY`` raised
  ``ClipboardContentError`` naming ``DISPLAY=':1987'``. CI run 41658893626
  steps 7-8 add an independent ``xclip -t text/uri-list`` owner of a ``file://``
  URI naming an existing temp file and an unknown
  ``application/x-clipboard-probe`` owner, each followed by a child
  ``clear()``; both then read no owner, the producer exited, and
  ``paste_files()`` was ``None``. Evidence limits: real X11 desktops, and those with
  clipboard managers that may re-offer a saved entry, are unverified.
  Windows desktop (user32 ``EmptyClipboard``) is **verified** in CI run
  41658893626 on GitHub ``windows-latest`` (image ``win25-vs2026``
  20261030.294.1, Windows 10.0.26100 ServerDatacenter; job ``native-windows-clear``;
  ``scripts/probe_windows_native_clear.py``, wrapper
  ``tests/test_clear_native_windows.py``, which records the runner image and
  Windows version and fails, never skips, on an evidence limit). It first
  records a raw ``OpenClipboard(NULL)`` / ``EmptyClipboard`` from a separate
  process against an independent PowerShell / .NET HTML + text offer, then
  has independent producers of HTML + text, an image, a ``CF_HDROP`` file
  list naming an existing temp file, and only an unknown registered
  ``ClipboardProbe.Custom`` format each followed by a child ``clear()``, after
  which an independent ``EnumClipboardFormats`` consumer must list no formats
  and every reader must read absence; then ``clear()`` twice, a holder
  process keeping the clipboard open past the 15 s bound (``clear()`` must
  raise naming the held clipboard and the prior formats must remain), and a
  holder releasing within the bound (``clear()`` must succeed). All eight
  steps held: each ``clear()`` left no formats; the held case raised after
  15.1 s with ``last_error=5`` and ``HTML Format`` / ``CF_UNICODETEXT`` (13)
  were still listed after release. Evidence limits: Win+V clipboard history and cloud clipboard
  copies are not erased or checked.
