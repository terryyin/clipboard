File lists, clear, and waits
---------------------------

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
``DISPLAY`` and ``WAYLAND_DISPLAY`` clears the Wayland selection. Linux X11
(``DISPLAY`` only) gives up the ``CLIPBOARD`` selection with libX11
``XSetSelectionOwner(CLIPBOARD, None, CurrentTime)`` through ``ctypes``, in
a child process bounded at 10 s; it needs nothing beyond libX11 (``libx11-6``
on Debian / Ubuntu), which ``xclip`` already requires, and leaves the
PRIMARY selection untouched. A missing libX11 raises
``ClipboardContentError`` naming ``libx11-6``, and a ``DISPLAY`` that cannot
be opened raises one naming ``DISPLAY`` and its value. The X11 child runs
``clipboard/_x11_relinquish.py`` with ``sys.executable``, so it needs an
ordinary Python installation: a frozen application (``sys.frozen`` set, as
PyInstaller, cx_Freeze and py2exe do) or a package imported from an archive
(the helper is not a file on disk) raises ``ClipboardContentError`` naming
that condition and ``set_clipboard_clearer`` before any child starts; such
apps install their own clearer with ``clipboard.set_clipboard_clearer``.
The Wayland, macOS and Windows clearers are unaffected. On Linux with neither
``DISPLAY`` nor ``WAYLAND_DISPLAY``, ``clear()`` raises
``ClipboardContentError`` saying no desktop session is visible. Windows
desktop calls user32 ``EmptyClipboard`` through ``ctypes`` (no
``win32clipboard``) after ``OpenClipboard``, retrying the open for up to
15 s while another process holds the clipboard, and always closes it again.
A clipboard still held at the end of that bound raises
``ClipboardContentError`` naming ``OpenClipboard``, the clipboard as held by
another process (or access denied), the ``last_error`` code, and that nothing
was cleared; the prior contents stay. An ``EmptyClipboard`` failure raises one
with its ``GetLastError`` code and message. Platforms without a desktop
clipboard this package knows raise ``ClipboardContentError`` saying the
native clearer is not available on that platform.

Boundary: ``clear()`` acts once on the current clipboard. A later offer is a
newer copy, not a failed clear, and is not detected: another application
copying, a clipboard manager re-offering its saved entry (for example KDE
Klipper's "prevent empty clipboard" or compositor clipboard persistence), or
a sync service. ``clear()`` does not erase OS clipboard history (such as the
Windows Win+V clipboard history), clipboard managers' saved entries, cloud
clipboard (Windows) or Universal Clipboard (Apple) copies, or other
devices, and it claims no secure deletion of the former contents. On macOS it
clears only the general pasteboard, not the Find pasteboard or other named
pasteboards; the X11 PRIMARY selection is out of scope.

For desktop-free tests, inject a fake with
``clipboard.set_clipboard_clearer(clearer)`` and restore the default with
``clipboard.set_clipboard_clearer(None)``. The clearer takes no arguments and
must leave the clipboard with no offer at all or raise.

Waiting for content (no ``clipboard[images]`` required):

::

   import threading
   import clipboard

   snapshot = clipboard.wait_for_kind("image", timeout=30)
   if snapshot is None:
       print("nothing copied in time")

   stop = threading.Event()  # another thread may call stop.set()
   clipboard.wait_for_kind("text", timeout=60, interval=1, cancel=stop)

   new_text = clipboard.wait_for_text_change(timeout=30)
   if new_text is None:
       print("no new text copied in time")

``wait_for_kind(kind, *, timeout, interval=0.5, cancel=None)`` waits until
the clipboard offers ``kind`` (``"text"``, ``"image"``, ``"html"`` or
``"files"``) and returns the ``ClipboardOfferSnapshot`` that showed it. It is
a **state** wait: each observation is one ``inspect()``, so it reads no
payload, needs no images extra and leaves the clipboard unchanged, and when
the kind is already offered it returns at once after one observation. A
caller who needs content copied *after* the call uses ``wait_for_text_change``
(for text) or clears the clipboard first.

``wait_for_text_change(*, timeout, interval=0.5, cancel=None)`` is a
**change** wait on text. Its first observation is one ``paste()``, kept as
the baseline; each later observation is one ``paste()``, and the first
observed text that is non-empty and differs from the baseline is returned.
Clearing (``paste()`` reads ``""``) or an offer with no text (an image only,
say) is not a change: the wait continues, and a text different from the
baseline copied afterwards is returned. It keeps only the baseline, logs no
text, runs wherever ``paste`` runs (every ``paste`` backend, including
pyperclip delegation) with ``paste``'s session selection and errors, and
honours ``set_text_clipboard_reader`` fakes.

Outcomes (both waits):

* the kind is observed / changed text is observed: the snapshot / text is
  returned;
* the deadline passes: ``None``. ``timeout`` is required, in seconds on a
  monotonic clock, and must be a non-negative finite number; ``timeout=0``
  observes exactly once, and for ``wait_for_text_change`` that one
  observation is the baseline read, so it returns ``None``. The baseline
  read counts against the deadline like any other observation;
* ``cancel`` is set: ``None``, with no further observation. ``cancel`` is a
  ``threading.Event`` or any object with ``is_set()`` and ``wait(seconds)``;
  the pause between observations waits on it, so setting it from another
  thread ends the wait without waiting out the interval;
* an observation fails: the ``ClipboardContentError`` from ``inspect()`` or
  ``paste()``, including the baseline read (no
  desktop session, missing helper, denied access, helper failure or timeout,
  a platform where ``inspect`` is not available) is raised at once and never
  retried, so a timeout or cancellation (``None``) is never mistaken for a
  failure. An empty clipboard is absence, not failure (``inspect`` lists no
  kinds, ``paste`` reads ``""``), and the wait keeps observing;
* an invalid argument (an unknown ``kind`` for ``wait_for_kind``; a negative, NaN, infinite,
  boolean or non-numeric ``timeout``; an ``interval`` that is not a positive
  finite number; a ``cancel`` without ``is_set`` / ``wait``) raises
  ``ClipboardContentError`` before the clipboard is observed.

``KeyboardInterrupt`` propagates. Each wait runs in the calling thread and
starts no thread or helper of its own. ``wait_for_kind`` runs wherever
``inspect`` runs, with ``inspect``'s session selection and errors, and
honours ``set_clipboard_inspector`` fakes.

Observation limits: the waits poll, they are not change notifications. They
pause ``min(interval, time left)`` between observations (``interval`` must
be positive, so they never busy-spin helper processes), and a kind or a text
that is offered and withdrawn between two observations is missed.
``wait_for_text_change`` compares observed values, not copy events: an
identical recopy of the baseline text (even after a clear) is not a change,
and only the last value seen at an observation counts. No new observation
starts after the deadline; one already running finishes within its
operation's own helper bound, so a wait returns no later than ``timeout``
plus one observation. On macOS one ``inspect()`` runs
``osascript`` and has taken from about 0.2 s to over 1 s on the owner's
machine, so a kind is seen up to about one interval plus two observations
after it is copied (one observation may have started just before the copy).
