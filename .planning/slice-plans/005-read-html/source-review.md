# Source review: SEED-001#read-html

Launch: fresh general-purpose sub-agent (no conversation inheritance), 2026-11-02, by the execution coordinator.
Input: only the story section "Read HTML fragments copied by desktop applications" (SEED-001 lines 91–267 at b7b6c34), extracted to a temporary file; told to read nothing else and change nothing; return numbered commitments, qualifications, examples, and exclusions without slice ownership.
Reviewer-noted ambiguities: "floors recorded" is undefined; "(or equivalent)" helpers vs. documentation naming only xclip/wl-paste; 4.4 "cannot yield a trustworthy fragment" vs. 22 "corrupt or unparseable".

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| G1 | recover the Unicode HTML fragment of a selection copied by an independent browser or rich editor through clipboard, instead of receiving only plain text | slice 7 | |
| G1.q | Python document and automation developers; producer is an independent browser or rich editor | slice 7 | |
| G2 | when HTML is offered, the returned markup matches the selected fragment | slice 7 | |
| G2.q | (native fragment/context envelopes decoded correctly) | slice 7 | |
| G3 | when only text or no HTML is offered, the call reports ordinary HTML absence | slice 7 | |
| G4 | corrupt native HTML metadata or transfer/access failure reports an actionable error | slice 7 | |
| G5 | the read never changes what remains available for another consumer | slice 7 | |
| 1 | Add an explicit public read API | slice 1 | observed: clipboard/_html.py paste_html (re-exported in clipboard/__init__.py); tests/test_paste_html_seam.py::test_paste_html_public_surface |
| 1.q | (proposed spelling paste_html()) | slice 1 | observed: clipboard.paste_html spelling; tests/test_paste_html_seam.py::test_paste_html_public_surface |
| 2 | returns a Unicode HTML fragment string when the current clipboard offer includes an HTML representation | slice 2 | observed: tests/test_paste_html_contract.py::test_fragment_offer_returns_unicode_fragment (exact CJK/emoji str); tests/test_paste_html_contract.py::test_empty_fragment_offer_returns_empty_string |
| 3 | or ordinary absence (None) when no HTML is offered | slice 2 | observed: tests/test_paste_html_contract.py::test_non_html_offers_return_none (is None) |
| 3.q | (including text-only and empty clipboard) | slice 2 | observed: tests/test_paste_html_contract.py::test_non_html_offers_return_none [empty, text-only] |
| 4 | Failures other than ordinary absence raise ClipboardContentError rather than returning None or a fabricated fragment | slice 2 | observed: tests/test_paste_html_contract.py::test_backend_failures_raise_content_error_not_none; tests/test_paste_html_cf_html.py::test_corrupt_metadata_raises_without_fragment_or_mutation |
| 4.1 | denied/unavailable access | slice 2 | observed: tests/test_paste_html_contract.py::test_backend_failures_raise_content_error_not_none [denied PermissionError, unavailable OSError] |
| 4.2 | missing Linux helper | slice 4 | |
| 4.3 | transfer failure | slice 2 | observed: tests/test_paste_html_contract.py::test_backend_failures_raise_content_error_not_none [transfer BrokenPipeError] |
| 4.4 | malformed native HTML envelope/metadata that cannot yield a trustworthy fragment | slice 2 | observed: tests/test_paste_html_cf_html.py::test_corrupt_metadata_raises_without_fragment_or_mutation (16 cases); tests/test_paste_html_cf_html.py::test_invalid_utf8_inside_fragment_raises; tests/test_paste_html_cf_html.py::test_nul_inside_fragment_range_raises |
| 4.q | Error message is actionable (Goal; Ex. 5) | slice 2 | observed: match= on specific detail in every failure test (e.g. 'missing StartFragment', 'splits a character', 'contains NUL characters') |
| 5 | The read leaves the clipboard unchanged. | slice 2 | observed: tests/html_offer.py::paste_unchanged deep-compares fake representations before/after every success and failure read |
| 6 | Extract the fragment from platform envelopes that wrap selection plus context | slice 2 | observed: tests/test_paste_html_cf_html.py::test_non_ascii_fragment_uses_utf8_byte_offsets; tests/test_paste_html_cf_html.py::test_header_variants_yield_only_the_fragment |
| 6.q | (notably Windows HTML Format UTF-8 byte offsets) | slice 2 | observed: tests/test_paste_html_cf_html.py::test_non_ascii_fragment_uses_utf8_byte_offsets (asserts char-offset slice differs; result equals fragment) |
| 7 | do not return the raw envelope headers as if they were the fragment | slice 2 | observed: tests/test_paste_html_cf_html.py::test_non_ascii_fragment_uses_utf8_byte_offsets asserts no 'Version:'/'StartHTML' in result |
| 8.1 | Never execute markup | slice 2 | observed: tests/test_paste_html_contract.py::test_active_markup_is_returned_verbatim_without_resolving (<script> returned verbatim; subprocess/webbrowser patched to fail) |
| 8.2 | [never] fetch linked resources | slice 2 | observed: tests/test_paste_html_contract.py::test_active_markup_is_returned_verbatim_without_resolving (socket/urlopen patched to fail) |
| 8.3 | [never] open local paths found in markup | slice 2 | observed: tests/test_paste_html_contract.py::test_active_markup_is_returned_verbatim_without_resolving (file:/// href; builtins.open patched to fail) |
| 8.4 | [never] synthesize HTML from plain text | slice 2 | observed: tests/test_paste_html_contract.py::test_non_html_offers_return_none [text-only with markup-like text → None] |
| 8.5 | [never synthesize HTML from] RTF | slice 2 | observed: tests/test_paste_html_contract.py::test_non_html_offers_return_none [text+rtf → None] |
| 9 | Default automated tests stay desktop-free via an injectable read backend | slice 1 | observed: clipboard/_html.py set_html_clipboard_reader; tests/test_paste_html_seam.py::test_injected_reader_value_is_returned, test_injected_reader_absence_is_none, test_reset_reader_restores_default |
| 10 | native proof uses an independent producer (browser or rich editor — not a same-library copy_html round-trip alone) | slice 3 | observed: scripts/probe_macos_native_paste_html.py via tests/test_paste_html_native_macos.py (CLIPBOARD_NATIVE_PROBE=1, macOS 26.6.2/25G83, Chrome 156.0.8078.74): producer kind browser (Chrome select all + copy selection), not copy_html |
| 10.q | and stays explicitly gated | slice 3 | observed: tests/test_paste_html_native_macos.py skipif darwin + CLIPBOARD_NATIVE_PROBE=1; SKIPPED in make check |
| 11.1 | Document Linux helper dependencies for HTML reads: xclip on X11 | slice 7 | |
| 11.2 | Document Linux helper dependencies for HTML reads: wl-paste on Wayland | slice 7 | |
| 11.3 | Document Linux helper dependencies for HTML reads: and supported desktop setup | slice 7 | |
| 12 | No clipboard[images] requirement for this story | slice 1 | observed: tests/test_paste_html_seam.py::test_paste_html_works_without_images_extra (PIL blocked, no PIL in sys.modules) |
| 13.1 | Supported desktop: Windows desktop | slice 6 | |
| 13.2 | Supported desktop: macOS Aqua | slice 3 | observed: scripts/probe_macos_native_paste_html.py via tests/test_paste_html_native_macos.py (CLIPBOARD_NATIVE_PROBE=1, macOS 26.6.2/25G83, Chrome 156.0.8078.74) passed on Aqua arm64; README macOS HTML read evidence bullet |
| 13.3 | Supported desktop: Linux X11 + xclip (or equivalent) able to request text/html on CLIPBOARD | slice 4 | |
| 13.4 | Supported desktop: Linux Wayland + wl-paste (or equivalent) scoped to the compositor actually proved when one is available | slice 5 | |
| 14 | Independent-producer success is an acceptance requirement on each claimed desktop when a session is available | slice 7 | |
| 14.alt | when no usable session exists during execution, record an explicit unverified/unsupported evidence limit for that desktop rather than claiming verified — never silent success | slice 7 | |
| 15 | Do not generalize one Wayland compositor's result to all Wayland environments | slice 5 | |
| 16 | Do not overload paste() / copy() to return or accept HTML | slice 1 | observed: clipboard/__init__.py re-exports pyperclip copy/paste unchanged and adds paste_html separately; full suite tests/test_clipboard.py green |
| 17 | Do not treat ordinary text, file-list, or image-only offers as HTML success | slice 2 | observed: tests/test_paste_html_contract.py::test_non_html_offers_return_none [text-only, image-only, file-list] (fake model); native type lists: G3 |
| 18 | Do not bypass OS pasteboard / clipboard authorization | slice 3 | observed: clipboard/_html_native.py::_macos_html_clipboard_reader uses plain NSPasteboard.generalPasteboard dataForType via osascript; denial → ClipboardContentError (tests/test_paste_html_macos_reader.py::test_helper_failure_is_content_error) |
| 19 | Do not replace, clear, or rewrite clipboard contents as part of the read | slice 2 | observed: tests/html_offer.py::paste_unchanged on every fake read |
| 20 | Do not present envelope headers, full surrounding context HTML, or a synthesized document as the fragment result | slice 2 | observed: tests/test_paste_html_cf_html.py::test_non_ascii_fragment_uses_utf8_byte_offsets (no context, '<html>', '<!--' in result); tests/test_paste_html_cf_html.py::test_byte_offsets_are_authoritative_over_comment_markers |
| 21 | Do not hang the caller indefinitely waiting on a contended clipboard | slice 4 | |
| 22 | Corrupt or unparseable native HTML metadata must not yield a bogus successful fragment | slice 2 | observed: tests/test_paste_html_cf_html.py::test_corrupt_metadata_raises_without_fragment_or_mutation; tests/test_paste_html_contract.py::test_bomless_utf16_fragment_raises |
| 23 | Text-only content must not be turned into HTML by synthesis | slice 2 | observed: tests/test_paste_html_contract.py::test_non_html_offers_return_none [text-only → None, not escaped text] |
| 24 | A successful read must not mutate the clipboard offer | slice 3 | observed: scripts/probe_macos_native_paste_html.py via tests/test_paste_html_native_macos.py (CLIPBOARD_NATIVE_PROBE=1, macOS 26.6.2/25G83, Chrome 156.0.8078.74): independent JXA consumer sees same offer, changeCount 119→119; tests/test_paste_html_macos_reader.py::test_reader_script_only_reads_the_pasteboard |
| 25 | Silent success on an unproved desktop is forbidden | slice 7 | |
| 26 | platform readers must own native HTML envelope decoding (Windows fragment offsets; macOS HTML pasteboard type; Linux text/html MIME) and map them to one absence / fragment / ClipboardContentError model | slice 6 | |
| 27 | reuse ClipboardContentError for HTML read failures — do not overload ClipboardImageError | slice 1 | observed: tests/test_paste_html_seam.py::test_reader_failure_surfaces_as_content_error asserts ClipboardContentError and not ClipboardImageError |
| 28 | platforms that already offer fragment-only text/html return that body directly; fail only when present metadata is unusable; do not invent a mandatory Windows-style envelope on macOS/Linux | slice 2 | observed: tests/test_paste_html_contract.py::test_fragment_offer_without_envelope_is_returned_directly; test_fragment_offer_bom_marked_bytes_decode; test_fragment_offer_invalid_utf8_raises |
| 29 | document per-desktop envelope behavior | slice 7 | |
| E1 | Ex. 1: independent browser/rich editor copies Unicode HTML selection on a supported desktop → paste_html() returns fragment markup for that selection; a later independent consumer can still obtain the same offer | slice 3 | observed: scripts/probe_macos_native_paste_html.py via tests/test_paste_html_native_macos.py (CLIPBOARD_NATIVE_PROBE=1, macOS 26.6.2/25G83, Chrome 156.0.8078.74): paste_html returns Chrome's public.html selection (café → naïve 日本 link, context excluded); later JXA consumer obtains same offer |
| E2 | Ex. 2: Windows HTML Format with fragment/context byte offsets (including non-ASCII) → returned string is the fragment between the offsets, not the Version/StartHTML header block or the unselected surrounding context alone | slice 2 | observed: tests/test_paste_html_cf_html.py::test_non_ascii_fragment_uses_utf8_byte_offsets |
| E3 | Ex. 3: only plain text (or empty / image-only / file-list) → paste_html() returns None; paste() / other readers behave as before | slice 2 | observed: tests/test_paste_html_contract.py::test_non_html_offers_return_none [empty, text-only, image-only, file-list]; make check text/paste_image suites green |
| E4 | Ex. 4: native HTML metadata corrupt or inconsistent (e.g. invalid Windows fragment offsets) → ClipboardContentError; no fabricated fragment; clipboard contents unchanged | slice 2 | observed: tests/test_paste_html_cf_html.py::test_corrupt_metadata_raises_without_fragment_or_mutation (invalid offsets → ClipboardContentError, paste_unchanged) |
| E5 | Ex. 5: missing Linux HTML helper or denied/unavailable access → ClipboardContentError with actionable message; not silent None | slice 4 | |
| E6 | Ex. 6: Windows, macOS Aqua, Linux X11, and/or Wayland session available → independent-producer success with floors recorded for the named compositor/helper; if unavailable, explicit evidence limit instead of verified claim | slice 7 | |
| E7 | Ex. 7: in-memory copy / paste / paste_image / copy_html contract tests still pass; VERSION and text-only callers behave as before; paste_html does not require clipboard[images] | slice 1 | observed: nix develop -c uv run --locked --extra images pytest -q and nix develop -c make check → 82 passed, 6 skipped; make build + make test-package pass after package split (text, paste_image, copy_image, copy_html suites); test_paste_html_works_without_images_extra |
| X1 | Exclusion: WSL, SSH, containers, and headless CI are not additional guaranteed desktops | slice 7 | |
| X2 | Exclusion: public structured return of surrounding context HTML, source URL, or other producer metadata | slice 2 | observed: clipboard/_html_envelope.py returns only the fragment str; tests/test_paste_html_cf_html.py::test_header_variants_yield_only_the_fragment (no SourceURL/context) |
| X3 | Exclusion: RTF / attributed-string conversion | slice 7 | |
| X4 | Exclusion: full-document import as a distinct contract | slice 7 | |
| X5 | Exclusion: arbitrary MIME / typed-binary read | slice 7 | |
| X6 | Exclusion: format inspection (SEED-001#inspect-formats) | slice 7 | |
| X7 | Exclusion: bundling GUI toolkits or win32clipboard as a required public dependency | slice 1 | observed: pyproject.toml dependencies unchanged; paste_html imports nothing new |
| X8 | Exclusion: making default pytest / CI require a real desktop | slice 1 | observed: tests/test_paste_html_seam.py uses only injected readers; default suite runs desktop-free |
| X9 | Exclusion: expanding beyond the four-desktop set | slice 7 | |
| X10 | Exclusion: same-library copy_html round-trip as sole native proof | slice 3 | observed: scripts/probe_macos_native_paste_html.py via tests/test_paste_html_native_macos.py (CLIPBOARD_NATIVE_PROBE=1, macOS 26.6.2/25G83, Chrome 156.0.8078.74) uses Chrome producer; copy_html not used |
| X11 | Exclusion: returning raw platform HTML without fragment extraction | slice 2 | observed: tests/test_paste_html_cf_html.py::test_corrupt_metadata_raises_without_fragment_or_mutation [not-an-envelope raw body raises] |
| X12 | Exclusion: Qt QMimeData / PyClip / GUI toolkit as default stack | slice 1 | observed: no Qt/PyClip import in clipboard/ package |
