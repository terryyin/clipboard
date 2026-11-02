# What a Python clipboard library should provide

Research date: 2026-11-02. This is product discovery, not a backend design or
a claim that native interoperability has been tested.

## Recommendation

Make `clipboard` a small, dependable bridge between Python and the user's
desktop clipboard. Preserve `copy`, `paste`, and `VERSION`; add explicit
operations for ordinary clipboard content and state. Terry's stated direction
is to make the project true to its name, with **images and rich content first**.
The selected stories are in
[SEED-001](../seeds/SEED-001-clipboard-true-to-its-name.md).

The first useful outcome is reading an image copied by an ordinary desktop
application. Next come image writing and HTML exchange with a plain-text
alternative. A self-round-trip is insufficient: another application must
produce or consume the data. Platform reliability belongs inside each outcome.

## Current project and actual demand

The inspected published repository baseline is
[`b5bb52f`](https://github.com/terryyin/clipboard/tree/b5bb52f6179851ab839555af79c8992f558eae02).
`clipboard.py` re-exports pyperclip's text `copy` and `paste` and declares
`VERSION = "0.0.5"`. The project requires Python 3.10+, depends on
`pyperclip>=1.8.2,<2`, and already has packaging, release, and Python/OS CI
work. Its clipboard round-trip tests substitute an in-memory backend; they
prove the public wrapper contract, not native desktop behavior.

There is direct historical demand for
[reading copied images](https://github.com/terryyin/clipboard/issues/2) and
[writing images from Linux](https://github.com/terryyin/clipboard/issues/5).
[Unicode trouble](https://github.com/terryyin/clipboard/issues/1) was reported
against Python 2.7; it motivates a Unicode contract but is not evidence of a
current Python 3 defect. The
[wheel request](https://github.com/terryyin/clipboard/issues/7) should not become
a duplicate packaging story: the current source already builds and tests wheel
and source distributions. Issue requests are demand signals, not verified
current failures.

## Domain model

The clipboard is an offer of typed representations, sometimes of several
items. It is not a universally available string variable. Windows supports
multiple representations of one selection; macOS supports multiple pasteboard
items and typed data. One HTML selection can offer both styled HTML and plain
text. Repeated text writes cannot substitute for publishing both together.
[Windows formats](https://learn.microsoft.com/en-us/windows/win32/dataxchg/clipboard-formats),
[Apple NSPasteboard](https://developer.apple.com/documentation/appkit/nspasteboard).

The recommended public behavior distinguishes these situations:

- The clipboard has no selection or contains no readable representation.
- It has data, but not the requested kind, such as an image without text.
- It has a requested representation with a valid empty value.
- Access is unavailable, denied, busy, timed out, or failed during transfer.

Do not reinterpret any of the last category as empty clipboard content.
Where a native backend cannot distinguish two states, expose that limitation
rather than inventing certainty. Inspecting types is a snapshot; another
application can replace the selection before it is read.

## Platform differences that change the product promise

| Environment | Evidence and consequence |
| --- | --- |
| Windows desktop | Unicode text, DIB/DIBV5 images, and file lists are distinct native formats. Copying PNG bytes under an arbitrary label does not establish interoperability with image applications. [Standard formats](https://learn.microsoft.com/en-us/windows/win32/dataxchg/standard-clipboard-formats). |
| Windows HTML | The registered `HTML Format` representation uses UTF-8 with byte offsets identifying the fragment and context. Non-ASCII HTML must be tested against another application. [HTML format](https://learn.microsoft.com/en-us/windows/win32/dataxchg/html-clipboard-format). |
| Windows access | Another process can hold the clipboard open. Calls need bounded failure behavior and must release acquired native resources. [OpenClipboard](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-openclipboard). |
| macOS | Pasteboards carry images, URLs, strings, and attributed content. Current AppKit also exposes per-app pasteboard access policy, including ask and deny. Respect OS prompts and denial; do not silently switch mechanisms to evade them. Exact behavior for each supported OS release and Python host remains to be observed. [NSPasteboard](https://developer.apple.com/documentation/appkit/nspasteboard), [access policy](https://developer.apple.com/documentation/appkit/nspasteboard/accessbehavior-swift.enum?language=objc). |
| Linux X11 | PRIMARY and CLIPBOARD serve different user workflows. Ownership and a serving event loop affect whether data remains available. File-manager conventions differ. A functioning toolkit is evidence of feasibility, not a required dependency. [Qt clipboard notes](https://doc.qt.io/qt-6/qclipboard.html). |
| Linux X11 after writer exit | The clipboard-manager specification defines a handoff through SAVE_TARGETS. Persistence is an ownership/lifetime concern, not clipboard history. [Clipboard Manager specification](https://wiki.freedesktop.org/www/ClipboardManager/). |
| Linux Wayland | Core clipboard offers are seat- and focus-related. The newer `ext-data-control` extension enables privileged clipboard management, but its presence and authorization are compositor-specific. Do not promise all Wayland desktops from one compositor's result. [Core protocol](https://wayland.freedesktop.org/docs/html/apa.html#protocol-spec-wl_data_device), [upstream extension](https://github.com/wayland-mirror/wayland-protocols/blob/main/staging/ext-data-control/ext-data-control-v1.xml). |
| Linux command helpers | `wl-copy` serves in the background by default; `wl-paste` can enumerate/request MIME types. Newline behavior, selection choice, and watch support matter. Required helper versions/protocols must be recorded when a story is refined. [Upstream manual](https://github.com/bugaevc/wl-clipboard/blob/master/data/wl-clipboard.1). |
| WSL, SSH, containers, headless CI | These are execution environments, not additional guaranteed desktop clipboards. WSL has a Windows bridge in current pyperclip; a remote Python process cannot assume it controls the local user's clipboard. Preserve working inherited text behavior and report missing access; broad remote bridging is deferred. [Pyperclip source](https://github.com/asweigart/pyperclip/blob/master/src/pyperclip/__init__.py). |

For new content support, the intended platform set is Windows desktop, macOS,
Linux X11, and Linux Wayland. Refinement must name concrete supported OS,
desktop/compositor, helper, and Python combinations. A generic OS label does
not settle support. Missing permissions/protocols need an actionable outcome,
not a blanket claim of successful support.

## Core capabilities and boundaries

| Capability | Necessary behavior | Selection |
| --- | --- | --- |
| Read images | Recover actual static raster pixels; distinguish images from file paths and URLs; handle native image representations. | First story. |
| Write images | Other desktop applications can paste the image; preserve dimensions and supported transparency; remain usable after the writing script exits. | Second story. |
| Write HTML | Publish the HTML fragment and an explicit matching Unicode text alternative in the same clipboard update. | Third story. |
| Read HTML | Recover the offered fragment without rendering, executing markup, or downloading linked resources; distinguish HTML absence from a read failure. | Fourth story. |
| Inspect state and formats | Report offered kinds and native format identifiers without changing data; distinguish unavailable access; state staleness and known limits. | Selected. |
| Read/write file references | Exchange structured local file references with file managers; do not treat arbitrary newline text as files or perform filesystem operations. | Two selected stories. |
| Text and availability | Preserve the existing text API; specify Unicode, whitespace/newlines, empty and invalid input; give bounded actionable failures. | Selected, plus compatibility in every story. |
| Clear | Remove every offered representation in the selected clipboard; repeat safely; make no promise to erase OS history or another application's saved copy. | Selected. |
| Wait for content | Wait for an available supported kind or a changed value with timeout/cancellation and documented observation limits. | Selected. |
| Linux PRIMARY | Explicit opt-in to the selection; keep default operations on CLIPBOARD and report unsupported selection access. | Selected last. |
| RTF and arbitrary typed bytes | Useful later extensions for document/desktop developers; MIME names, Windows registered formats, and macOS UTIs are not interchangeable labels. | Deferred until image/HTML interoperability and demand justify the next bounded story. |
| Snapshot/restore, sensitive hints | Useful later, but restoring must avoid overwriting a newer copy; history/cloud exclusion is platform-specific. | Deferred; no false secure-erasure or race-free guarantee. |
| CLI, async streams, history, sync, mobile | A CLI may be convenient; the others broaden the product considerably. None is needed to establish the initial desktop library promise. | Deferred. |

These are product recommendations from the sources and user direction, not
claims that all competing libraries implement these semantics.

## Existing solutions and the strongest smaller alternative

**Pyperclip** is a good existing text solution to reuse where it meets the
contract. Current upstream source identifies version 1.11.0, contains Wayland
and WSL text backends, and has no `waitForPaste` or `waitForNewPaste` definitions.
Its old documentation still describes those waits, so do not simply promise to
re-export them. The project already permits current 1.x versions; an upgrade
alone does not add image or rich-content APIs.
[Current source](https://github.com/asweigart/pyperclip/blob/master/src/pyperclip/__init__.py),
[older wait documentation](https://pyperclip.readthedocs.io/en/latest/).

**Pillow ImageGrab** can read clipboard images on Windows, macOS, and Linux;
Linux requires `wl-paste` or `xclip`. On Windows its result can instead be a
filename list. It is a plausible reusable piece for image reading, not evidence
that writing, HTML, or uniform semantics are already solved.
[ImageGrab documentation](https://pillow.readthedocs.io/en/stable/reference/ImageGrab.html#PIL.ImageGrab.grabclipboard).

**PyClip** advertises binary and text clipboard access, clearing, a CLI, and
X11/Wayland backends. Its documentation explicitly notes additional Windows
formats and loss of arbitrary binary data with macOS's pbcopy/pbpaste backend.
Evaluate its actual native format interoperability before considering reuse.
[Upstream README](https://github.com/spyoungtech/pyclip).

**Qt** demonstrates text, images, MIME data, clearing, and selection support in
a mature cross-platform API. It also carries GUI lifecycle obligations. It is a
reference and reuse candidate when already present in an application, not a
decision to require a GUI toolkit for every script.
[QClipboard](https://doc.qt.io/qt-6/qclipboard.html).

The strongest smaller alternative is documenting recipes that combine
pyperclip, Pillow, and native helpers. That can satisfy an expert's isolated
task quickly. It leaves each consumer responsible for installation, differing
empty/error results, native format negotiation, rich-content alternatives, and
writer lifetime. It therefore falls short of the requested cohesive `clipboard`
library. Reusing those tools internally remains open; rewriting their working
behavior is not the product goal.

## Proof and remaining uncertainty

Each selected story needs its own automated contract coverage and native
interoperability evidence appropriate to its promise. Cross-process tests must
include an independent producer or consumer; same-library round trips can
hide a shared encoding mistake. Writes need a writer-exit case, replacement by
another application, and resource cleanup. Reads must leave offered content
unchanged. Image comparisons concern decoded pixels and documented conversion
limits, not identical PNG byte encodings. Rich-copy proof includes a rich target
and a plain-text target after one write.

Keep deterministic in-memory tests; add native proof where required by the
story rather than replacing them or creating a preparatory testing project.
The existing CI matrix is not native clipboard coverage. No desktop probes
were run during this research and no user clipboard was read or modified.

Refinement must settle supported native combinations, image input/output
shapes and conversion limits, explicit absence/error results, HTML fragment
context, and successful-write lifetime. Backend choices, public API spellings,
dependency extras, and OS minimums remain design work. If a selected story is
larger than its L hypothesis, split on an independently useful user outcome
while retaining the cross-platform direction.
