# Source review: SEED-001#copy-html

**Launch:** Fresh general-purpose reviewer; source-only; no plan, product, proof, or conversation inheritance.
**Input:** Goal, Scope (required behavior, supported desktops, required restrictions, scope limits / deferred, rejection constraints), and key examples 1–8 from `.planning/seeds/SEED-001-clipboard-true-to-its-name.md#copy-html` only.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Provide an explicit public write API (proposed spelling `copy_html(html, text)`) that accepts a Unicode HTML fragment string and a caller-supplied Unicode plain-text alternative. | slice 1 | observed: `clipboard.copy_html` + `tests/test_copy_html_seam.py::test_copy_html_public_surface` / `test_injected_writer_receives_both_representations` |
| 2 | Publish both the HTML fragment and the plain-text alternative as one clipboard update (one logical offer). | slice 2 | |
| 3 | On a successful write, leave neither representation overwriting the other: a rich consumer can obtain the HTML and a text consumer can obtain the alternative from that same offer. | slice 2 | |
| 4.1 | Reject invalid input before replacing current clipboard contents: wrong types | slice 2 | |
| 4.2 | Reject invalid input before replacing current clipboard contents: empty HTML with no usable fragment when the contract requires one | slice 2 | |
| 5.1 | Failures other than successful dual publication raise an actionable clipboard content error: missing helper | slice 4 | |
| 5.2 | Failures other than successful dual publication raise an actionable clipboard content error: denied access | slice 3 | |
| 5.3 | Failures other than successful dual publication raise an actionable clipboard content error: transfer failure | slice 2 | |
| 5.4 | Failures other than successful dual publication raise an actionable clipboard content error: unsupported session | slice 3 | |
| 5.5 | Failures other than successful dual publication raise an actionable clipboard content error: inability to offer both representations together | slice 2 | |
| 6.1 | Document platform HTML envelopes and Linux helper dependencies as needed: `xclip` on X11 | slice 7 | |
| 6.2 | Document platform HTML envelopes and Linux helper dependencies as needed: Wayland helpers that can offer multiple MIME types (not a one-type-only path that drops the alternative) | slice 7 | |
| 7 | Keep default automated tests desktop-free via an injectable write backend. | slice 1 | observed: `set_html_clipboard_writer` + `tests/test_copy_html_seam.py` injection/default stub; no desktop required |
| 8 | Native proof uses independent rich and plain-text consumers (not a same-library round-trip alone) and stays explicitly gated. | slice 3 | |
| 9 | Successful dual offers remain pasteable after the writing process exits on each claimed desktop. | slice 3 | |
| 10 | On Windows, publish interoperable `HTML Format` with correct UTF-8 fragment/context byte offsets for non-ASCII content. | slice 6 | |
| 11 | Do not synthesize the plain-text alternative from HTML inside this story. | slice 7 | X11 |
| 12.1 | Claim support for Windows desktop | slice 6 | |
| 12.2 | Claim support for macOS Aqua | slice 3 | |
| 12.3 | Claim support for Linux X11 + a multi-type-capable helper | slice 4 | |
| 12.4 | Claim support for Linux Wayland + a multi-type-capable helper scoped to the compositor actually proved when one is available | slice 5 | |
| 13 | Dual publication and writer-exit success are acceptance requirements on each claimed desktop when a session is available. | slice 3 | |
| 14 | When no usable session exists during execution for a claimed desktop, record an explicit unverified/unsupported evidence limit for that desktop rather than claiming verified — never silent success. | slice 3 | |
| 15 | Do not generalize one Wayland compositor’s result to all Wayland environments. | slice 5 | |
| 16 | After this work, existing text callers remain compatible (including `VERSION` and text-only callers behaving as before). | slice 7 | |
| 17 | After this work, delivered image APIs remain compatible / unchanged. | slice 7 | |
| 18 | After this work, in-memory `copy` / `paste` / `paste_image` contract tests still pass. | slice 7 | |
| Q1 | WSL, SSH, containers, and headless CI are not additional guaranteed desktops. | slice 7 | Q1 |
| Q2 | Wayland support is scoped to the compositor actually proved when one is available; a single compositor’s result does not imply all Wayland environments. | slice 5 | |
| Q3 | Platform HTML envelopes and Linux helper dependencies are documented as needed (including the X11/`xclip` and multi-type Wayland helper expectations). | slice 7 | |
| Q4 | Native dual-consumer / writer-exit proof remains explicitly gated; default automated tests stay desktop-free via an injectable write backend. | slice 1 | observed: injectable seam + desktop-free seam tests; native gating deferred to probe slices |
| Q5 | Unavailability of a usable session during execution yields an explicit evidence limit, not a verified claim and not silent success. | slice 3 | |
| Q6 | The plain-text alternative is caller-supplied; this story does not synthesize it from HTML. | slice 7 | X11 |
| Q7 | Failures other than successful dual publication surface as actionable clipboard content errors (not silent no-op or partial success). | slice 2 | |
| Q8 | Invalid input is rejected before any clipboard replacement (fail-before-replace). | slice 2 | |
| E1 | Unicode HTML fragment with a styled link (or small table) and an explicit matching plain-text alternative → `copy_html(html, text)` succeeds → writing process exits → independent rich editor pastes formatting; text editor pastes the alternative; neither representation alone replaced the other. | slice 3 | |
| E2 | Same pattern including non-ASCII characters in fragment and/or surrounding Windows `HTML Format` context → rich consumer pastes the correct fragment (offsets/encoding hold); text consumer pastes the Unicode alternative. | slice 6 | |
| E3 | Clipboard currently holds ordinary text (or a prior image) → `copy_html` succeeds → subsequent independent pastes see the new HTML and text alternatives, not the superseded offer as the sole content. | slice 2 | |
| E4 | Empty or non-string HTML / text arguments that violate the public contract → actionable error before any clipboard replacement; prior offer remains. | slice 2 | |
| E5 | Session or helper cannot offer HTML and plain text together (e.g. one-type-only helper path) → actionable failure; no silent text-only “success”. | slice 2 | |
| E6 | Missing Linux helper or denied/unavailable clipboard access → actionable error; no silent empty success. | slice 4 | |
| E7 | Windows, macOS Aqua, Linux X11, and/or Linux Wayland session available → same dual-consumer + writer-exit success with floors recorded for the named compositor/helper; if a session is unavailable during execution, that desktop keeps an explicit evidence limit instead of a verified claim. | slice 3 | |
| E8 | After this work, in-memory `copy` / `paste` / `paste_image` contract tests still pass; `VERSION` and text-only callers behave as before; image APIs remain unchanged. | slice 7 | |
| X1 | Do not overload `copy()` / `paste()` to accept or return HTML. | slice 1 | observed: `copy`/`paste` remain pyperclip re-exports; HTML write is separate `copy_html` |
| X2 | Do not treat two sequential text (or text-then-HTML) writes as fulfilling this story. | slice 7 | X2 |
| X3 | Do not bypass OS pasteboard / clipboard authorization. | slice 7 | X3 |
| X4 | Do not leave only one of the two promised representations after claiming success. | slice 7 | X4 |
| X5 | Do not hang the caller indefinitely waiting to serve clipboard data. | slice 7 | X5 |
| X6 | Do not execute markup, fetch remote resources, or promise pixel-identical layout across applications. | slice 7 | X6 |
| X7.1 | Deferred: automatic HTML-to-text conversion | slice 7 | X7.1 |
| X7.2 | Deferred: reading HTML (`SEED-001#read-html`) | slice 7 | X7.2 |
| X7.3 | Deferred: RTF or other rich formats | slice 7 | X7.3 |
| X7.4 | Deferred: full HTML documents as a distinct contract from fragments | slice 7 | X7.4 |
| X7.5 | Deferred: embedded resource packaging | slice 7 | X7.5 |
| X7.6 | Deferred: bundling GUI toolkits or `win32clipboard` as a required public dependency | slice 7 | X7.6 |
| X7.7 | Deferred: making default pytest / CI require a real desktop | slice 7 | X7.7 |
| X7.8 | Deferred: expanding beyond the four-desktop set | slice 7 | X7.8 |
| X7.9 | Deferred: inventing rollback/atomicity guarantees beyond fail-before-replace | slice 7 | X7.9 |
| X7.10 | Deferred: same-library HTML round-trip as sole native proof | slice 7 | X7.10 |
| X8 | A call that cannot publish HTML and plain text together must not replace current content with a partial offer presented as success | slice 7 | X8 |
| X9 | Silent success on an unproved desktop is forbidden. | slice 7 | X9 |
| X10 | Sequential single-format writes claiming dual success are forbidden. | slice 7 | X10 |

## Comparison notes (slice 1)

| Id | Source-expected | Actual observation | Owner |
| --- | --- | --- | --- |
| 1 | Explicit public `copy_html(html, text)` | Present; injectable path receives both strings | slice 1 accepted |
| 7 | Desktop-free injectable write backend | `set_html_clipboard_writer` + seam tests | slice 1 accepted |
| Q4 | Gated native; desktop-free defaults | Seam desktop-free; native still planned | slice 1 accepted for injectable half |
| X1 | Do not overload `copy`/`paste` | Unchanged re-exports; separate API | slice 1 accepted |
| remaining | Later slices / exclusions | Allocated; not claimed by Structure seam | as in table |
