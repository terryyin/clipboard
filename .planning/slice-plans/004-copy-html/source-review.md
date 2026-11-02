# Source review: SEED-001#copy-html

**Launch:** Fresh general-purpose reviewer; source-only; no plan, product, proof, or conversation inheritance.
**Input:** Goal, Scope (required behavior, supported desktops, required restrictions, scope limits / deferred, rejection constraints), and key examples 1–8 from `.planning/seeds/SEED-001-clipboard-true-to-its-name.md#copy-html` only.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Provide an explicit public write API (proposed spelling `copy_html(html, text)`) that accepts a Unicode HTML fragment string and a caller-supplied Unicode plain-text alternative. | slice 1 | observed: `clipboard.copy_html` + `tests/test_copy_html_seam.py::test_copy_html_public_surface` / `test_injected_writer_receives_both_representations` |
| 2 | Publish both the HTML fragment and the plain-text alternative as one clipboard update (one logical offer). | slice 2 | observed: `tests/test_copy_html_contract.py::test_valid_html_and_text_publish_both_in_one_update` (single replace; `kind=html+text`) |
| 3 | On a successful write, leave neither representation overwriting the other: a rich consumer can obtain the HTML and a text consumer can obtain the alternative from that same offer. | slice 2 | observed: same test — `offer["html"]` and `offer["text"]` both present on one offer |
| 4.1 | Reject invalid input before replacing current clipboard contents: wrong types | slice 2 | observed: `test_invalid_args_fail_before_replace` (None/bytes/int); writer not invoked; prior intact |
| 4.2 | Reject invalid input before replacing current clipboard contents: empty HTML with no usable fragment when the contract requires one | slice 2 | observed: `test_invalid_args_fail_before_replace` (empty/whitespace HTML); `_validate_copy_html_args` |
| 5.1 | Failures other than successful dual publication raise an actionable clipboard content error: missing helper | slice 4 | observed: non-Darwin default `ClipboardContentError` names multi-type helper expectation (xclip); `test_unsupported_platform_default_writer_is_content_error` |
| 5.2 | Failures other than successful dual publication raise an actionable clipboard content error: denied access | slice 3 | observed: `test_macos_denied_pasteboard_write_is_content_error` (nonzero osascript / denial-like stderr → `ClipboardContentError`) |
| 5.3 | Failures other than successful dual publication raise an actionable clipboard content error: transfer failure | slice 2 | observed: `test_transfer_failure_raises_actionable_content_error` (`OSError` → `ClipboardContentError`) |
| 5.4 | Failures other than successful dual publication raise an actionable clipboard content error: unsupported session | slice 3 | observed: `test_unsupported_platform_default_writer_is_content_error` + `test_macos_missing_osascript_is_content_error` → `ClipboardContentError` |
| 5.5 | Failures other than successful dual publication raise an actionable clipboard content error: inability to offer both representations together | slice 2 | observed: `test_one_type_only_backend_errors_without_partial_success` / `test_text_only_path_is_not_silent_success` |
| 6.1 | Document platform HTML envelopes and Linux helper dependencies as needed: `xclip` on X11 | slice 7 | |
| 6.2 | Document platform HTML envelopes and Linux helper dependencies as needed: Wayland helpers that can offer multiple MIME types (not a one-type-only path that drops the alternative) | slice 7 | |
| 7 | Keep default automated tests desktop-free via an injectable write backend. | slice 1 | observed: `set_html_clipboard_writer` + `tests/test_copy_html_seam.py` injection/default stub; no desktop required |
| 8 | Native proof uses independent rich and plain-text consumers (not a same-library round-trip alone) and stays explicitly gated. | slice 3 | observed: `scripts/probe_macos_native_copy_html.py` — AppKit HTML + `pbpaste` after writer subprocess exit; gated `CLIPBOARD_NATIVE_PROBE` |
| 9 | Successful dual offers remain pasteable after the writing process exits on each claimed desktop. | slice 3 | observed: probe `writer_exited_before_consume: true` + dual consume success (macOS Aqua); other desktops in slices 4–6 |
| 10 | On Windows, publish interoperable `HTML Format` with correct UTF-8 fragment/context byte offsets for non-ASCII content. | slice 6 | observed: README + `scripts/probe_windows_native_copy_html.py` evidence limit (no Windows session); HTML Format/non-ASCII expectation recorded; `verified: false` |
| 11 | Do not synthesize the plain-text alternative from HTML inside this story. | slice 7 | X11 |
| 12.1 | Claim support for Windows desktop | slice 6 | observed: Windows HTML-write evidence limit (supported target, not verified) |
| 12.2 | Claim support for macOS Aqua | slice 3 | observed: README floors + probe ok on macOS 26.6.2 / 25G83 arm64 |
| 12.3 | Claim support for Linux X11 + a multi-type-capable helper | slice 4 | observed: README explicit X11 HTML-write **evidence limit** (no session/helper here); `scripts/probe_linux_x11_native_copy_html.py` refuses verified |
| 12.4 | Claim support for Linux Wayland + a multi-type-capable helper scoped to the compositor actually proved when one is available | slice 5 | observed: README Wayland HTML-write evidence limit; probe refuses verified; no compositor named as verified |
| 13 | Dual publication and writer-exit success are acceptance requirements on each claimed desktop when a session is available. | slice 3 | observed: macOS session available → probe dual+exit success; Linux/Windows later |
| 14 | When no usable session exists during execution for a claimed desktop, record an explicit unverified/unsupported evidence limit for that desktop rather than claiming verified — never silent success. | slice 3 | observed: README keeps Windows/Linux HTML writes unverified (no silent success); macOS verified only with probe floors |
| 15 | Do not generalize one Wayland compositor’s result to all Wayland environments. | slice 5 | observed: README + probe state no compositor generalization / scoped-to-named-compositor wording |
| 16 | After this work, existing text callers remain compatible (including `VERSION` and text-only callers behaving as before). | slice 7 | |
| 17 | After this work, delivered image APIs remain compatible / unchanged. | slice 7 | |
| 18 | After this work, in-memory `copy` / `paste` / `paste_image` contract tests still pass. | slice 7 | |
| Q1 | WSL, SSH, containers, and headless CI are not additional guaranteed desktops. | slice 7 | Q1 |
| Q2 | Wayland support is scoped to the compositor actually proved when one is available; a single compositor’s result does not imply all Wayland environments. | slice 5 | observed: same README/probe compositor-scoping language; evidence limit (no compositor proved) |
| Q3 | Platform HTML envelopes and Linux helper dependencies are documented as needed (including the X11/`xclip` and multi-type Wayland helper expectations). | slice 7 | |
| Q4 | Native dual-consumer / writer-exit proof remains explicitly gated; default automated tests stay desktop-free via an injectable write backend. | slice 1 | observed: injectable seam + desktop-free seam tests; native gating deferred to probe slices |
| Q5 | Unavailability of a usable session during execution yields an explicit evidence limit, not a verified claim and not silent success. | slice 3 | observed: README explicit unverified for Win/Linux HTML write; macOS only after probe |
| Q6 | The plain-text alternative is caller-supplied; this story does not synthesize it from HTML. | slice 7 | X11 |
| Q7 | Failures other than successful dual publication surface as actionable clipboard content errors (not silent no-op or partial success). | slice 2 | observed: one-type / text-only / transfer-failure contract tests raise `ClipboardContentError` |
| Q8 | Invalid input is rejected before any clipboard replacement (fail-before-replace). | slice 2 | observed: `test_invalid_args_fail_before_replace` — no writer invocations |
| E1 | Unicode HTML fragment with a styled link (or small table) and an explicit matching plain-text alternative → `copy_html(html, text)` succeeds → writing process exits → independent rich editor pastes formatting; text editor pastes the alternative; neither representation alone replaced the other. | slice 3 | observed: probe café styled link; independent HTML + text consumers after exit |
| E2 | Same pattern including non-ASCII characters in fragment and/or surrounding Windows `HTML Format` context → rich consumer pastes the correct fragment (offsets/encoding hold); text consumer pastes the Unicode alternative. | slice 6 | observed: evidence limit — non-ASCII HTML Format case required for future verification; not claimed on this host |
| E3 | Clipboard currently holds ordinary text (or a prior image) → `copy_html` succeeds → subsequent independent pastes see the new HTML and text alternatives, not the superseded offer as the sole content. | slice 2 | observed: `test_successful_write_replaces_prior_sole_content` (text and image seeds → dual offer) |
| E4 | Empty or non-string HTML / text arguments that violate the public contract → actionable error before any clipboard replacement; prior offer remains. | slice 2 | observed: `test_invalid_args_fail_before_replace` |
| E5 | Session or helper cannot offer HTML and plain text together (e.g. one-type-only helper path) → actionable failure; no silent text-only “success”. | slice 2 | observed: `test_one_type_only_backend_errors_without_partial_success` / `test_text_only_path_is_not_silent_success` |
| E6 | Missing Linux helper or denied/unavailable clipboard access → actionable error; no silent empty success. | slice 4 | observed: default platform error actionable (names helpers); X11 probe exits non-zero with `verified: false` / evidence_limit |
| E7 | Windows, macOS Aqua, Linux X11, and/or Linux Wayland session available → same dual-consumer + writer-exit success with floors recorded for the named compositor/helper; if a session is unavailable during execution, that desktop keeps an explicit evidence limit instead of a verified claim. | slice 3 | observed: macOS branch verified with floors; Win/Linux evidence limits retained in README (slices 4–6 close or refresh) |
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
