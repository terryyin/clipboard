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
(README Evidence); delivered `paste_html` fragment reads (no extra) with
macOS Aqua verified by a real browser producer and Linux X11 (Xvfb CI),
Wayland (Sway CI) and Windows (`windows-latest` CI) verified with named
independent helper producers, browser interoperability there unobserved
(2026-11-02).

**Affects:** Later file and further rich-content stories should follow the same
explicit-API + optional-extra shape unless evidence forces a revision.
