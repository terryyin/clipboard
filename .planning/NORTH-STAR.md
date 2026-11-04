# North Star

Temporary direction for consequential choices that are not yet Accepted ADRs.
Retire each topic into a maintained home when the product still needs the rule.

## Rich clipboard content beside text re-exports

New clipboard content operations (images first) stay as **explicit APIs** next
to the existing pyperclip `copy` / `paste` re-exports. They do not overload
`paste()`. Optional packaging extras declare content-stack dependencies (for
images: Pillow via `clipboard[images]`; Linux helpers documented, not bundled).
A thin contract layer normalizes platform offers into one absence / value /
failure model. In-memory fakes prove the contract in CI; native
interoperability needs independent producers and documented evidence limits.

**Evidence:** SEED-001 Shared Boundaries; delivered `paste_image` /
`clipboard[images]` contract (2026-11-02); delivered `copy_image` write path
with macOS Aqua verified, Linux X11 (Xvfb CI) and Wayland (Sway CI) writer-exit
proofs, Windows write evidence-limited (2026-11-02); delivered `copy_html`
HTML+plain-text dual-offer with macOS Aqua verified and Windows / Linux X11 /
Wayland HTML writes evidence-limited (2026-11-02); delivered `inspect()`
kinds+formats offer snapshot with injectable backend, macOS Aqua independent-
producer verification, and Windows / Linux X11 / Wayland inspect evidence-
limited on Darwin (2026-11-02); delivered `paste_files`
local file-list read (no `clipboard[images]` required) with macOS Aqua
Finder-equivalent verification and Windows / Linux X11 / Wayland reads
evidence-limited (2026-11-02); domain research reuse of
Pillow `ImageGrab.grabclipboard`; macOS Aqua image reads independently
verified; Windows, X11+`xclip`, and Wayland+`wl-paste` image reads documented
with explicit evidence limits when no usable native session was available
(`docs/evidence-*.rst`); delivered `paste_html` fragment reads (no extra) with
macOS Aqua verified by a real browser producer and Linux X11 (Xvfb CI),
Wayland (Sway CI) and Windows (`windows-latest` CI) verified with named
independent helper producers, browser interoperability there unobserved
(2026-11-02); delivered `copy_files` local file-list copy offers (no
`clipboard[images]` required, validation before replacing, copy not cut,
reference not snapshot) with native offers read by independent consumers
after the writer exits on macOS Aqua (local probe), Windows
(`windows-latest` CI), X11 (Xvfb CI) and Wayland (Sway CI), file-manager
paste verified only with the Explorer shell Paste verb (Windows CI) and
Thunar (X11 CI), and Finder and Wayland file-manager paste evidence-limited
(`docs/evidence-*.rst`) (2026-11-03).

**Text (delivered 2026-11-03, SEED-001#portable-text):** `copy` / `paste` keep
their names and pyperclip stays a dependency, but they are no longer bare
re-exports: the package owns their contract (exact `str`, `""` absence,
NUL / unencodable refusal before replacing, `ClipboardContentError` with the
cause) and the default macOS (`pbcopy` / `pbpaste` with a UTF-8 locale), X11
(`xclip`), and Wayland (wl-clipboard) paths, because pyperclip 1.11.0
discards Linux helper failures and inherits a locale that corrupts macOS
text; Windows keeps pyperclip's bounded `CF_UNICODETEXT` backend, and
pyperclip remains the delegate for WSL and unowned environments with failure
translation only. Verified with independent producers / consumers on macOS
Aqua (local probe), X11 (Xvfb CI), Wayland (Sway CI), and Windows
(`windows-latest` CI); delegated paths unverified (`docs/evidence-*.rst`).

**Clear (delivered 2026-11-03):** explicit `clear()` (no extra) leaves no
offer at all, unlike `copy("")`, with native clears on macOS Aqua
(`clearContents`), Wayland (`wl-copy --clear`), X11 (libX11
`XSetSelectionOwner(None)`) and Windows (`EmptyClipboard`). Each was verified
with independent producers of text, HTML, image, file list and unknown types
and independent consumers: macOS by local probe, X11 / Sway /
`windows-latest` in CI. An unowned or nothing-copied Linux clipboard now reads
as an empty `inspect()` snapshot (`docs/evidence-*.rst`).

**Affects:** Later file and further rich-content stories should follow the same
explicit-API + optional-extra shape unless evidence forces a revision.
