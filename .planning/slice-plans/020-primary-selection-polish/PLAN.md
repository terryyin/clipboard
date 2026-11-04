# Plan: Correct PRIMARY wording and probe evidence

**Identity:** SEED-001#primary-selection-polish
**Source:** [Correct PRIMARY wording and probe evidence](../../seeds/SEED-001-clipboard-true-to-its-name.md#primary-selection-polish)
**Source review:** [source-review.md](source-review.md)
**Provenance:** execution retrospective of SEED-001#primary-selection
(commits f823f1d, 15252dd, 0abf1a4 from base 68e5ea9; CI runs 41799207621
and 41803370471 green). Original contract and plan, recoverable from
before-cleanup commit 7c9e2546ff4e664bba661a39a57b92d7e5edd4ed:
`.planning/seeds/SEED-001-clipboard-true-to-its-name.md#primary-selection`
(key examples 1–9 and the required restriction "Unsupported never falls back
to CLIPBOARD") and `.planning/slice-plans/017-primary-selection/PLAN.md`.

## Findings (current at 0abf1a4)

1. `clipboard/_primary.py` `copy_primary` reuses `clipboard/_text.py`
   `_validate_copy_text`, whose messages say "clipboard text write
   rejected …" / "clipboard text write failed: cannot convert …"; every other
   PRIMARY error names "primary selection" (`_text_native_linux` subjects).
   A rejected `copy_primary("a\x00b")` (example 9) therefore reads as a
   CLIPBOARD write.
2. `clipboard/_primary.py` `_primary_session`: with `DISPLAY` and
   `WAYLAND_DISPLAY` set, wl-clipboard incomplete, no `xclip`, and `xsel` /
   Qt present, the owner is pyperclip and the error names only `xclip`,
   never wl-clipboard.
3. `scripts/probe_linux_wayland_native_primary.py` step names
   `7_path_without_wl_paste_names_wl_clipboard_within_bound` (example 7 is
   macOS / Windows; this is the example 8 analogue) and
   `5_child_copy_primary_empty_reads_empty` (not example 5), mirrored in
   `tests/test_primary_native_linux_wayland.py` `STEPS`.
4. README Wayland PRIMARY Evidence bullet names no CI run; the X11 bullet
   cites 41799207621; the Sway run is 41803370471.
5. `tests/test_primary_wayland_failures.py` module docstring and
   `tests/fake_wl_clipboard_text.py` `drops_primary` state that Sway with
   `primary_selection disabled` drops writes as fact; README and
   `clipboard/_text_native_wayland_writer.py` record that two observations
   conflict.
6. `scripts/probe_linux_x11_native_primary.py` copies the X11 evidence-limit
   reason chain a third time (also `probe_linux_x11_native_{text,clear}.py`);
   Wayland gained `evidence_limit()` in
   `scripts/linux_wayland_native_text_support.py` but
   `probe_linux_wayland_native_{clear,paste_html}.py` keep their inline copy.

Out of scope (pre-existing, not this execution's residue): the duplicated
headless-Sway launch block across Wayland workflows; `_clear_wayland.py`'s own
`wl-copy --clear` runner.

## Settled premises (preparation workspace observation)

1. `copy_primary("a\x00b")` raises
   `"clipboard text write rejected: text contains a NUL character…"` —
   contains `"clipboard"`, not `"primary selection"` (uv run in this
   checkout). Slice 1 consumes this for the rejection-wording change.
2. With `DISPLAY` and `WAYLAND_DISPLAY` set and `PATH` carrying only a
   stub `xsel` (no `xclip`, no wl-clipboard), `copy_primary("x")` raises
   naming `xclip` and "Linux X11" only — no wl-clipboard mention (same
   run). Slice 1 consumes this for the mixed-session message.
3. Probe/wrapper step ids, README Wayland PRIMARY bullet (no run id),
   Sway-disabled wording in the failure test / fake, and the duplicated
   X11 / remaining Wayland evidence-limit chains are present in the
   named files at this revision; rename, cite, reword and share as
   planned. No early probe: native CI after publish owns green
   Wayland/X11 PRIMARY jobs.

## Preserved promises and constraints

- All behavior of `copy` / `paste` / `copy_primary` / `paste_primary`
  except error text; CLIPBOARD error wording and argv byte-for-byte
  (`copy`'s "clipboard text write rejected" text stays for `copy`).
- No fallback from PRIMARY to CLIPBOARD or pyperclip.
- Probe wrappers assert only exit, `ok`, ordered steps and environment
  floors (AGENTS.md); evidence-limit outcomes (exit 2 / CI failure) stay the
  same for every probe.
- Tests assert error type plus named subject / platform / helper, not copied
  wording (AGENTS.md).

## Outside-in proof

| Finding | Observable signal | Slice |
| --- | --- | --- |
| 1 | `tests/test_primary_x11.py` / `tests/test_primary_wayland.py` rejected-text tests also assert "primary selection" in the message; `tests/test_text_*` `copy` rejection tests unchanged | 1 |
| 2 | New desktop-free case in `tests/test_primary_unavailable.py`: mixed session, incomplete wl-clipboard, xsel only → error names both `xclip` and wl-clipboard, nothing runs | 1 |
| 3 | Renamed steps in probe and wrapper `STEPS`; CI `native-wayland-text.yml` PRIMARY step passes | 1 |
| 4, 5 | README and docstring text | 1 |
| 6 | Shared X11 `evidence_limit` in `scripts/linux_x11_native_text_support.py` used by the three X11 probes; the two remaining Wayland probes use `evidence_limit()`; each probe still exits 2 with `evidence_limit` off its desktop (local smoke) and the native CI jobs stay green | 1 |
| Regression | `nix develop -c make check`, `make lint-workflows`; CI native jobs green on the published revision | 1 |

## Ordered slices

### 1. Name the primary selection everywhere and align PRIMARY probe evidence
Type: Behavior
Status: done
Proof: as the table; local `nix develop -c make check` and
`nix develop -c make lint-workflows`; native proof owned by CI on push.

Behavior: rejected `copy_primary` input and the mixed-session missing-helper
error name the primary selection (and wl-clipboard where `WAYLAND_DISPLAY`
is set); probe step names, README run id and test docs match the story
examples and the recorded observations; evidence-limit rules have one home
per desktop. `copy` messages and all other behavior unchanged.

## Plan refinement and concerns

Slice-plan refinement was not needed: one Behavior slice owns the whole
bounded correction outcome, proof maps 1:1 to the six key examples, and
no independent second outcome or Structure-only seam remains. This review
identified no remaining slice-specific concern.

## Learnings

- Empty-string Wayland PRIMARY probe step has no seed example number; renamed
  to `empty_copy_primary_reads_empty` (dropped false `5_`) while the missing-
  helper step is `8_…` for the example 8 analogue.
- Post-change refactor stopped on pre-existing `README.rst` oversize (1016 /
  250). Developer authorized option 1 packaging split: Usage / Installation /
  Evidence / Development moved under `docs/*.rst` (each ≤250); short
  `README.rst` landing keeps `pyproject.toml` `readme`; Evidence run
  `41803370471` lives in `docs/evidence-text-primary-clear.rst`.

## Accepted proof (slice 1)

- Desktop-free: `nix develop -c make check` (770 passed, 33 skipped);
  `nix develop -c make lint-workflows`; focused primary + copy wording suites.
- Live: `copy("a\\x00b")` still "clipboard text write rejected…";
  `copy_primary` names "primary selection".
- Mixed-session: `test_mixed_session_incomplete_wl_clipboard_with_xsel_names_both_helpers`.
- evidence_limit Darwin smoke: five X11/Wayland probes exit 2 with
  `evidence_limit`.
- Native CI on published revision `90a8e7b` (run 41928637574) success,
  including Native Linux Wayland text copy/paste (Sway) and Native Linux X11
  text copy/paste (Xvfb).
