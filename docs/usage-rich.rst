Images, HTML, inspect, and paste_html
------------------------------------

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
On Linux an unowned X11 CLIPBOARD (``xclip``'s no-owner error, in either its
``target TARGETS not available`` or ``There is no owner for the`` wording) and
a nothing-copied Wayland selection (``Nothing is copied`` / ``No selection``)
give an empty snapshot; any other helper failure still raises. WSL, SSH, containers, and headless CI are not additional guaranteed desktops
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
