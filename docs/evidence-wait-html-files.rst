Evidence (waits, HTML, and files)
--------------------------------

* ``wait_for_kind`` / ``wait_for_text_change``: macOS Aqua **verified**
  on 2026-11-05 (commit ``abb4de8``) on the owner's unlocked console
  session by the gated probe ``scripts/probe_macos_native_wait.py``
  (wrapper ``tests/test_wait_native_macos.py``; no images extra), which
  exited 0 with ``ok`` true, no evidence limit and no failed steps on two
  consecutive runs. It runs the same four steps as the other desktops
  (shared ``scripts/native_wait_support.py``) with an independent
  ``pbcopy`` producer (``LANG=en_US.UTF-8``) on a freshly cleared
  pasteboard and the library in a child Python. On the recorded run,
  ``wait_for_kind("text", timeout=20)`` saw no kinds twice, then
  ``"text"`` and returned that snapshot (``public.utf8-plain-text`` /
  ``NSStringPboardType``) 0.37 s after the producer finished;
  ``wait_for_kind("html", timeout=1)`` with nothing copied returned
  ``None`` after 1.0 s; ``wait_for_text_change(timeout=20)`` returned the
  second independently copied text 0.01 s after its producer finished; and
  after ``clear()`` and an identical recopy ``wait_for_text_change(timeout=3)``
  observed the old text, ``""`` twice, then the old text again and returned
  ``None`` at 3.0 s. The longest single observation was 0.20 s. Floors:
  macOS 26.6.2 (build 25G83) / Darwin 25.6.0, arm64, Python 3.13.17, 0.5 s
  interval. Earlier runs on the same machine stopped at an evidence limit
  (exit 2) because the screen was locked; the probe refuses a locked or
  off-console session, and such an exit is not verification. Evidence
  limits: kinds other than text are not observed for the waits themselves
  (they rely on ``inspect``'s evidence above), and other macOS versions or
  producers than ``pbcopy`` are not observed.
* ``wait_for_kind`` / ``wait_for_text_change``: Linux X11 under Xvfb,
  Linux Wayland under headless Sway and Windows desktop **verified** in
  CI run 41798644132 (commit ``bf48f2c``) by the gated probes
  ``scripts/probe_{linux_x11,linux_wayland,windows}_native_wait.py``
  (wrappers ``tests/test_wait_native_{linux_x11,linux_wayland,windows}.py``,
  jobs ``native-linux-x11-wait``, ``native-linux-wayland-wait`` and
  ``native-windows-wait``, which fail on an evidence limit). They run the
  same four steps as the macOS probe (shared
  ``scripts/native_wait_support.py``) with an independent producer on a
  freshly cleared clipboard: ``xclip -selection clipboard -i`` (xclip 0.13,
  Xvfb 21.1.22, Ubuntu 26.04), ``wl-copy`` with no ``--type`` (wl-clipboard
  2.2.1, Sway 1.11, Ubuntu 26.04) and Windows PowerShell 5.1
  ``Set-Clipboard`` (Windows Server 2025, build 26100, runner image
  win25-vs2026). On each, ``wait_for_kind("text", timeout=20)`` saw
  no kinds, then ``"text"`` after the copy and returned that snapshot
  (X11 ``TARGETS`` / ``UTF8_STRING``; Wayland ``text/plain`` and four more
  types; Windows ``CF_UNICODETEXT`` with ``CF_TEXT`` / ``CF_OEMTEXT`` /
  ``CF_LOCALE``) within 0.5 s of the producer finishing;
  ``wait_for_kind("html", timeout=1)`` with nothing copied returned
  ``None`` after 1.0 s; ``wait_for_text_change(timeout=20)`` returned the
  second independently copied text; and after ``clear()`` and an identical
  recopy ``wait_for_text_change(timeout=3)`` observed ``""`` then the old
  text again and returned ``None`` at 3.0 s. Evidence limits: other
  compositors, GNOME / KDE, interactive Windows sessions, and kinds other
  than text (``image``, ``html``, ``files``) are not observed for the waits
  themselves; they rely on ``inspect``'s evidence above.
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
  library) reads the offer. A further offer-level round (no file-manager paste)
  copies a relative file path, a directory, and the same file again from a
  child whose cwd is the source folder; the independent consumer and
  ``paste_files()`` must read three absolute paths in that order.
  ``paste_files()`` agreement is recorded only as a consistency check, not as
  interoperability proof. A file-manager paste is claimed only where one was
  observed; one file manager or compositor is not generalized to others.

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
