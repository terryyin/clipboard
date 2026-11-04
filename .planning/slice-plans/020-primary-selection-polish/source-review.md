# Source review: SEED-001#primary-selection-polish

**Launch:** Fresh general-purpose reviewer; no conversation inheritance; no
plan, return, product, or proof. Input: Goal, Scope, key examples, and scope
limits from
`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#primary-selection-polish`
only. Human amendments: none.

## Reviewer return (verbatim commitments)

**1.** `copy_primary` / `paste_primary` error messages always name the primary selection and never say "clipboard".

- *Qualification:* Limited to error text; no other behavior change (see exclusions).

**2.** `copy_primary` input-rejection messages name the primary selection (never "clipboard").

**3.** `copy` rejection wording stays "clipboard".

**4.** With both `DISPLAY` and `WAYLAND_DISPLAY` set, incomplete wl-clipboard, no `xclip`, and a pyperclip owner present, PRIMARY calls:
- **4.1** name both `xclip` and wl-clipboard in the error;
- **4.2** run nothing (neither PRIMARY nor CLIPBOARD is read or replaced).

**5.** Wayland PRIMARY probe and wrapper step names / step ids match the primary-selection story’s example numbers (not misnumbered CLIPBOARD-text residue such as `5_…` / `7_…`).

**6.** The Wayland PRIMARY README Evidence bullet cites CI run `41803370471` (beside the X11 bullet’s `41799207621`).

**7.** `tests/test_primary_wayland_failures.py` and `tests/fake_wl_clipboard_text.py` describe Sway `primary_selection disabled` as recorded conflicting observations (one drop, one write-through), matching README — not as settled fact that writes are dropped.

**8.** Evidence-limit helper usage:
- **8.1** The three X11 text / clear / PRIMARY probes share one `evidence_limit` helper;
- **8.2** The remaining Wayland clear / `paste_html` probes use the existing `evidence_limit()`.

**9.** Off an X11-only or Wayland session, each of those probes still exits `2` with `evidence_limit` from the shared helper for that desktop.

**10.** Maintainers’ native PRIMARY evidence has step names, run ids, and test documentation that match the story examples (correcting residue from SEED-001#primary-selection).

### Journey examples (E1–E6)

As in the seed key examples 1–6 (NUL rejection; mixed-session helpers; Wayland step ids; README run id; Sway conflicting observations; shared evidence_limit exit 2).

### Exclusions

**X1–X5** as in the seed Scope limits (error text only; no CLIPBOARD/pyperclip fallback; wrappers assert exit/`ok`/steps/floors; evidence-limit outcomes unchanged; Sway drop not stated as fact).

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| 1 | `copy_primary` / `paste_primary` error messages always name the primary selection and never say "clipboard". | slice 1 | observed: clipboard/_primary.py _unavailable subjects; clipboard/_text.py _validate_copy_text(subject="primary selection"); PRIMARY errors name primary selection as write/read target |
| 2 | `copy_primary` input-rejection messages name the primary selection (never "clipboard"). | slice 1 | observed: clipboard/_text.py subject for copy_primary; tests/test_primary_{x11,wayland}.py rejected-text asserts + test_primary_unavailable validation assert primary selection |
| 3 | `copy` rejection wording stays "clipboard". | slice 1 | observed: clipboard/_text.py default subject="clipboard"; live copy NUL rejection still "clipboard text write rejected"; focused text suites green |
| 4.1 | With both DISPLAY and WAYLAND_DISPLAY set, incomplete wl-clipboard, no xclip, and a pyperclip owner present, PRIMARY calls name both xclip and wl-clipboard in the error. | slice 1 | observed: clipboard/_primary.py mixed WAYLAND_DISPLAY branch; tests/test_primary_unavailable.py test_mixed_session_incomplete_wl_clipboard_with_xsel_names_both_helpers asserts xclip and wl-clipboard |
| 4.2 | With both DISPLAY and WAYLAND_DISPLAY set, incomplete wl-clipboard, no xclip, and a pyperclip owner present, PRIMARY calls run nothing (neither PRIMARY nor CLIPBOARD is read or replaced). | slice 1 | observed: same mixed-session test with nothing_runs; _both_raise for copy_primary and paste_primary |
| 5 | Wayland PRIMARY probe and wrapper step names / step ids match the primary-selection story’s example numbers (not misnumbered CLIPBOARD-text residue such as `5_…` / `7_…`). | slice 1 | observed: scripts/probe_linux_wayland_native_primary.py + tests/test_primary_native_linux_wayland.py STEPS: empty_copy_primary_reads_empty and 8_path_without_wl_paste_names_wl_clipboard_within_bound |
| 6 | The Wayland PRIMARY README Evidence bullet cites CI run 41803370471 (beside the X11 bullet’s 41799207621). | slice 1 | observed: docs/evidence-text-primary-clear.rst Wayland PRIMARY Evidence bullet cites run 41803370471 (moved from README.rst in authorized packaging split) |
| 7 | `tests/test_primary_wayland_failures.py` and `tests/fake_wl_clipboard_text.py` describe Sway `primary_selection disabled` as recorded conflicting observations (one drop, one write-through), matching README — not as settled fact that writes are dropped. | slice 1 | observed: tests/test_primary_wayland_failures.py docstring and tests/fake_wl_clipboard_text.py drops_primary: conflicting observations drop vs write-through |
| 8.1 | The three X11 text / clear / PRIMARY probes share one `evidence_limit` helper. | slice 1 | observed: scripts/linux_x11_native_text_support.py evidence_limit(); probe_linux_x11_native_{text,clear,primary}.py call it |
| 8.2 | The remaining Wayland clear / paste_html probes use the existing `evidence_limit()`. | slice 1 | observed: scripts/probe_linux_wayland_native_{clear,paste_html}.py import evidence_limit from linux_wayland_native_text_support |
| 9 | Off an X11-only or Wayland session, each of those probes still exits 2 with `evidence_limit` from the shared helper for that desktop. | slice 1 | observed: Darwin: five probes exit 2 with evidence_limit true reason not Linux (platform darwin) |
| 10 | Maintainers’ native PRIMARY evidence has step names, run ids, and test documentation that match the story examples (correcting residue from SEED-001#primary-selection). | slice 1 | observed: step renames, README run id, and Sway docs together; native desktop green deferred to CI after publish as planned |
