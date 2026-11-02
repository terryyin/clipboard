# Source review — SEED-001#inspect-formats

**Launch:** Fresh general-purpose reviewer (no conversation inheritance); source-only
inputs; read no other project files; change nothing.
**Input:** Story section Goal, Scope (required behavior, supported desktops,
required restrictions, scope limits/deferred, rejection constraints), and Key
examples 1–7 from
`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#inspect-formats`.
No human amendments.
**Reviewer agent:** 27bfddc3-7443-4f63-8ede-97a0d19be450

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | Python application and automation developers can learn what the current clipboard offer contains through an explicit non-mutating inspect API, instead of inferring availability from an empty paste() string or by retrieving every payload. | slice 7 | |
| 2 | Inspection reports which library-understood content kinds are present. | slice 2 | observed: tests/test_inspect_contract.py::test_html_and_text_offer_reports_both_kinds_and_native_ids kinds |
| 3 | Inspection reports which native format identifiers are offered. | slice 2 | observed: tests/test_inspect_contract.py::test_html_and_text_offer_reports_both_kinds_and_native_ids formats |
| 4 | Mixed offers (for example HTML + text) report each present kind and the corresponding native identifiers. | slice 2 | observed: tests/test_inspect_contract.py::test_html_and_text_offer_reports_both_kinds_and_native_ids mixed kinds+ids |
| 5 | Empty offer, content present without a given kind, and unavailable/denied access remain distinguishable where the native platform permits that distinction. | slice 2 | observed: tests/test_inspect_contract.py::test_empty_and_access_failure_remain_distinguishable |
| 6 | Inspection does not replace, clear, or reserve the offer. | slice 2 | observed: tests/test_inspect_contract.py::test_inspect_does_not_mutate_fake_offer_model |
| 7 | Inspection does not claim that every listed format can be decoded. | slice 7 | |
| 8 | Add an explicit public inspect API (proposed spelling inspect()). | slice 1 | observed: clipboard.inspect in clipboard package; tests/test_inspect_seam.py::test_inspect_public_surface |
| 9 | The API returns a structured snapshot of the current clipboard offer. | slice 2 | observed: tests/test_inspect_contract.py success paths return ClipboardOfferSnapshot |
| 10 | The snapshot includes the set of library-understood kinds currently present among the fixed vocabulary {text, image, html, files} when native formats map to them. | slice 2 | observed: clipboard/_offer.py snapshot_from_native_formats + contract kind asserts |
| 11.1 | Native format identifiers include Windows format names/ids. | slice 6 | |
| 11.2 | Native format identifiers include macOS pasteboard types / UTIs. | slice 3 | |
| 11.3 | Native format identifiers include Linux MIME types. | slice 4 | |
| 12 | Native format identifiers include identifiers for types this library cannot yet decode. | slice 2 | observed: undecodable com.example.undecodable retained in formats (HTML+text and file-list tests) |
| 13 | An empty clipboard yields an empty-kinds / empty-or-documented-empty formats snapshot, not an access error. | slice 2 | observed: tests/test_inspect_contract.py::test_empty_offer_yields_empty_snapshot_not_error |
| 14.1 | Denied/unavailable access raises ClipboardContentError rather than a fabricated empty snapshot. | slice 2 | observed: tests/test_inspect_contract.py::test_access_denied_raises_clipboard_content_error_not_empty |
| 14.2 | Missing Linux helper required to enumerate raises ClipboardContentError rather than a fabricated empty snapshot. | slice 4 | |
| 14.3 | Transfer failure while enumerating raises ClipboardContentError rather than a fabricated empty snapshot. | slice 2 | observed: tests/test_inspect_contract.py::test_enumeration_transfer_failure_raises_clipboard_content_error |
| 15 | The call leaves the clipboard unchanged. | slice 2 | observed: tests/test_inspect_contract.py::test_inspect_does_not_mutate_fake_offer_model |
| 16 | The call must not fetch representation payloads solely to decide kind presence when the platform can enumerate types without a body read. | slice 2 | observed: tests/test_inspect_contract.py::test_kinds_derived_from_type_list_alone_not_payload_presence |
| 17 | Document that the result is a snapshot subject to races: another application may replace the offer before a later read. | slice 7 | |
| 18 | Default automated tests stay desktop-free via an injectable inspect backend. | slice 1 | observed: set_clipboard_inspector + tests/test_inspect_seam.py desktop-free fakes |
| 19 | Native proof uses an independent producer and stays explicitly gated. | slice 3 | |
| 20 | Document Linux helper dependencies for enumeration (xclip / wl-paste -l or equivalent) and supported desktop setup. | slice 7 | |
| 21 | No clipboard[images] requirement for this story. | slice 1 | observed: inspect() docstring + tests/test_inspect_seam.py::test_inspect_importable_without_images_extra |
| 22.1 | Supported desktop: Windows desktop. | slice 6 | |
| 22.2 | Supported desktop: macOS Aqua. | slice 3 | |
| 22.3 | Supported desktop: Linux X11 + helper able to list CLIPBOARD targets. | slice 4 | |
| 22.4 | Supported desktop: Linux Wayland + helper able to list offered MIME types, scoped to the compositor actually proved when one is available. | slice 5 | |
| 23 | WSL, SSH, containers, and headless CI are not additional guaranteed desktops. | slice 7 | |
| 24 | Independent-producer success is an acceptance requirement on each claimed desktop when a session is available. | slice 3 | |
| 25 | When no usable session exists during execution, record an explicit unverified/unsupported evidence limit for that desktop rather than claiming verified — never silent success. | slice 3 | |
| 26 | Do not generalize one Wayland compositor's result to all Wayland environments. | slice 5 | |
| 27 | Do not overload paste() / copy() to return format metadata. | slice 1 | observed: separate clipboard.inspect; copy/paste remain pyperclip re-exports |
| 28 | Do not treat access failure as an empty clipboard. | slice 2 | observed: access-denied / missing-helper tests raise ClipboardContentError not empty |
| 29 | Do not bypass OS pasteboard / clipboard authorization. | slice 3 | |
| 30 | Do not replace, clear, or rewrite clipboard contents as part of inspection. | slice 2 | observed: tests/test_inspect_contract.py::test_inspect_does_not_mutate_fake_offer_model |
| 31 | Do not claim that listing a native format means a successful later paste_* decode. | slice 7 | |
| 32 | Do not hang the caller indefinitely waiting on a contended clipboard. | slice 3 | |
| 33 | Do not conflate “this process cannot access the clipboard” with “the offer has no text/image/html/files.” | slice 2 | observed: tests/test_inspect_contract.py::test_empty_and_access_failure_remain_distinguishable |
| 34 | Denied/unavailable access must not yield a successful empty snapshot. | slice 2 | observed: tests/test_inspect_contract.py::test_access_denied_raises_clipboard_content_error_not_empty |
| 35 | A successful inspect must not mutate the offer. | slice 2 | observed: tests/test_inspect_contract.py::test_inspect_does_not_mutate_fake_offer_model |
| 36 | Silent success on an unproved desktop is forbidden. | slice 3 | |
| 37 | Kind membership must not require fetching full payloads when type enumeration alone is sufficient. | slice 2 | observed: payload_fetches == [] in type-list / HTML+text / image / file-list tests |
| 38 | Independent browser or rich editor copies HTML + plain text → inspect() reports kinds including html and text, plus native HTML and text identifiers; later independent consumer can still obtain the same offer; payloads not required solely for the report when types enumerate. | slice 2 | observed: tests/test_inspect_contract.py::test_html_and_text_offer_reports_both_kinds_and_native_ids |
| 39 | Clipboard holds only an image → kinds include image and not text/html; native image identifier(s) appear; paste() emptiness is not the sole signal for image availability. | slice 2 | observed: tests/test_inspect_contract.py::test_image_only_offer_reports_image_without_text_or_html |
| 40 | Clipboard is empty → snapshot with no kinds and no native formats (or documented empty equivalent); not ClipboardContentError. | slice 2 | observed: tests/test_inspect_contract.py::test_empty_offer_yields_empty_snapshot_not_error |
| 41 | Native file-list present that the library cannot yet paste → kinds include files and native file-list identifier(s) among formats; no filesystem read. | slice 2 | observed: tests/test_inspect_contract.py::test_file_list_native_id_reports_files_without_filesystem_read |
| 42 | Missing Linux enumeration helper or denied/unavailable access → ClipboardContentError with actionable message; not successful empty snapshot. | slice 2 | observed: tests/test_inspect_contract.py::test_missing_helper_message_is_actionable_not_empty_success |
| 43 | Windows, macOS Aqua, Linux X11, and/or Linux Wayland session available → independent-producer inspect success with floors; if session unavailable, explicit evidence limit instead of verified claim. | slice 3 | |
| 44.1 | After this work, in-memory copy / paste / paste_image / copy_html / (when present) paste_html contract tests still pass. | slice 7 | |
| 44.2 | VERSION and text-only callers behave as before. | slice 7 | |
| 44.3 | inspect does not require clipboard[images]. | slice 1 | observed: tests/test_inspect_seam.py::test_inspect_importable_without_images_extra |
