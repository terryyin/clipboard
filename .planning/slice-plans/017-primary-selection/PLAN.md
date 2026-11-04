# Plan: Use the Linux primary selection explicitly

**Identity:** SEED-001#primary-selection
**Source:** [Use the Linux primary selection explicitly](../../seeds/SEED-001-clipboard-true-to-its-name.md#primary-selection)
**Source review:** [source-review.md](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Add `copy_primary(text)` / `paste_primary()` beside `copy` / `paste`: they
read and write only the Linux PRIMARY selection (X11 through `xclip`, Wayland
through wl-clipboard `--primary`), leave CLIPBOARD unchanged, and raise
`ClipboardContentError` everywhere PRIMARY cannot be reached instead of
falling back to CLIPBOARD. Scope, required restriction and its reason, and
key examples 1–9 are in the seed section; this plan adds none.

**Excluded** (seed scope limits): rich data, `inspect` / `clear` of PRIMARY,
SECONDARY, macOS Find pasteboard, synchronization, multi-seat, waits, a
public PRIMARY injection seam.

## Assumptions and direction

- Follows the North Star topic: explicit new API beside `copy` / `paste`,
  same absence / value / failure model as `paste` (`""` absence, input
  rules of `copy`), fakes in default CI, native claims only with independent
  producers / consumers and stated evidence limits. No revision needed. No
  ADR store exists; no Accepted ADR constrains this plan.
- **PFE.** Reuse, not new machinery: the owned Linux text paths
  `clipboard/_text_native_x11.py` and `clipboard/_text_native_wayland.py`
  already do TARGETS / `--list-types` first reads, ICCCM decoding,
  no-owner / nothing-copied absence, the bounded background owner with
  exact read-back (X11) and the bounded `wl-copy` foreground (Wayland).
  **Change:** the selection becomes a parameter of those paths (CLIPBOARD
  stays the default and its argv stays byte-for-byte the same, since tests
  assert argv); `_desktop` gains the PRIMARY TARGETS / `--list-types`
  commands beside the CLIPBOARD ones (shared listing rules stay in
  `_desktop`, AGENTS.md). Session choice reuses
  `_desktop_text._text_session_owner`, but a `pyperclip` owner on Linux X11
  (no `xclip`) raises naming `xclip` instead of delegating; pyperclip 1.11's
  internal `primary=` flags are not public API and are not used.
  `_validate_copy_text` is shared with `copy`. **Gap:** no PRIMARY
  operation exists today.
- The public contract lives in a new `clipboard/_primary.py` (one concept:
  the PRIMARY text contract and its dispatch), exported from
  `clipboard/__init__.py` and `__all__`. It never reads
  `_text._text_clipboard_writer` / `_reader`, so an injected text seam never
  receives PRIMARY traffic (seed scope). Desktop-free tests fake the helpers
  (`clipboard.subprocess`, `shutil.which`, `fake_platform`), as
  `tests/test_text_x11.py` / `tests/test_text_wayland.py` do.
- Error wording names the selection ("primary selection") so a PRIMARY
  failure is never mistaken for a CLIPBOARD one; tests assert error type and
  named platform / helper, not copied wording (AGENTS.md).
- Preparation checkout: Darwin 25.6.0, no `xclip`, `wl-clipboard` or X
  server. All Linux native proof runs in GitHub Actions after a branch push
  (`ci.yml` runs on every branch push): Xvfb + `xclip 0.13` and Sway 1.11 +
  `wl-clipboard 2.2.1` (`ubuntu-latest`, observed in run 41778191888).
- Local gates (AGENTS.md): `nix develop -c make check` every slice;
  `nix develop -c make lint-workflows` whenever `.github/workflows` changes
  (both slices); `nix develop -c make test-package` once in slice 1 because
  `__all__` grows (installed distributions must export the new names).

## Outside-in proof

| Example (seed) | Observable signal | Owning slice |
| --- | --- | --- |
| 1. PRIMARY and CLIPBOARD differ → `paste_primary()` gives PRIMARY, `paste()` CLIPBOARD (X11) | Desktop-free: fake xclip with separate CLIPBOARD / PRIMARY owners; argv uses `-selection primary` only for PRIMARY calls. Native: independent `xclip -selection primary -i` / `-selection clipboard -i` owners with different text, child Python `paste_primary()` / `paste()` | 1 |
| 2. `copy_primary` → independent PRIMARY consumer sees it, CLIPBOARD unchanged, after writer exit | Desktop-free: PRIMARY owner started, CLIPBOARD offer untouched. Native: `copy_primary` in a child Python that exits, then independent `xclip -selection primary -o` and `-selection clipboard -o` | 1 |
| 3. `copy` leaves PRIMARY unchanged | Native: child `copy("new copy")`, then independent PRIMARY consumer still sees the earlier text; desktop-free: CLIPBOARD-only argv | 1 |
| 4. Unowned PRIMARY → `""` | Desktop-free with the observed no-owner wording; native: fresh Xvfb, child `paste_primary()` → `""` | 1 |
| 5. Examples 1–3 on Sway | Same steps with `wl-copy [--primary] --type text/plain;charset=utf-8` / `wl-paste [--primary] -n` independent helpers | 2 |
| 6. Compositor without PRIMARY → raises, CLIPBOARD neither read nor changed | Desktop-free: fake wl-clipboard reporting the observed unsupported wording, no non-`--primary` argv run. Native: Sway with `primary_selection disabled` if slice 2's early probe shows a distinct report; otherwise README evidence limit | 2 |
| 7. macOS / Windows / WSL / no session → "not available" / no-session error, nothing run | Desktop-free via `fake_platform` and env: error type plus named platform; no helper or pyperclip call recorded | 1 |
| 8. X11 with `xsel` but no `xclip` → `paste()` works, `paste_primary()` names `xclip` | Desktop-free: `shutil.which` faked; native: child with `PATH` lacking `xclip` → error naming `xclip`, within the bound | 1 |
| 9. `copy_primary("a\x00b")` rejected before replacing | Desktop-free: no helper started; native: earlier PRIMARY still read by the independent consumer | 1 |
| Seam isolation | Desktop-free: with `set_text_clipboard_writer` / `_reader` fakes injected, `copy_primary` / `paste_primary` still reach the PRIMARY helper argv and the fakes record nothing | 1 |
| Public surface | `import clipboard` without Pillow exposes `copy_primary` / `paste_primary` in `__all__` (`tests/test_no_pillow_extra.py`); `make test-package` installed wheel + sdist | 1 |
| Documentation | README section and Evidence name X11 / Sway sessions, helper versions, the no-fallback rule, and evidence limits (GNOME, KDE, other compositors, XWayland PRIMARY bridging, clipboard managers syncing PRIMARY); AGENTS.md summary names the PRIMARY operations | 1 (X11), 2 (Wayland, AGENTS.md) |
| Regression | `copy` / `paste` X11 and Wayland argv and native text probes unchanged; `nix develop -c make check` green | 1, 2 |

A same-process write-then-read is only a consistency check; native claims
need the independent helper processes above.

## Decisive premises

Observed in this workspace (Darwin 25.6.0, branch
`claude/use-the-linux-primary-selection-explicitly` at 4667b4c, whose
product code equals `master` 388dd5b):

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| The local gates run in this checkout | Every slice's `nix develop -c make check`, both slices' `make lint-workflows`, slice 1's `make test-package` | AGENTS.md now names `nix develop -c <command>` (the offline `./scripts/dev` wrapper was reverted in 0b08521). `nix develop -c make check` → `612 passed, 27 skipped`, exit 0; `nix develop -c make lint-workflows` → `actionlint`, exit 0; `nix develop -c make test-package` → wheel and sdist installed and checked, exit 0 (the installed X11 clear helper reports `failure libx11` on macOS, which the check accepts) | Settled |
| Default suite and native text jobs are green at the start, on the CI venues this plan uses | Slice regression baseline; slices 1–2 native venues | `gh run view 41778191888` (master 388dd5b): `success`, including `Native Linux X11 text copy/paste (Xvfb)` and `Native Linux Wayland text copy/paste (Sway)`; logs: `xclip version 0.13`, `sway version 1.11`, `wl-clipboard 2.2.1` | Settled for CI |
| `_text_session_owner` picks `x11` / `wayland` / `pyperclip` as documented, so PRIMARY can reuse it | Slice 1–2 dispatch | `tests/test_text_session.py` runs in the default suite, green locally (`make check` above) and in run 41778191888 | Settled |
| Existing fakes model only CLIPBOARD | Slice 1–2 desktop-free proof needs per-selection fakes | `tests/fake_xclip_text.py` (`FakeX11.offers`, one owner) and `tests/fake_wl_clipboard_text.py` hold one selection | Settled: the fakes gain a selection dimension, CLIPBOARD behavior unchanged |
| `xclip -selection primary` reports an unowned PRIMARY with the same no-owner wording `_desktop._xclip_reports_no_owner` recognizes, and a background `xclip -selection primary -i` owner survives writer exit without touching CLIPBOARD | Slice 1 absence classification and writer | Needs Xvfb | **Early probe** at the start of slice 1 (records-only CI step on a fresh Xvfb); different wording is added to the recognizer with that observation, unknown wording keeps raising |
| `wl-paste --primary` reports nothing selected with a `_wl_paste_reports_nothing_copied` wording; `wl-copy --primary` sets only PRIMARY and its fork serves after exit; Sway 1.11 `primary_selection disabled` makes wl-clipboard 2.2.1 report PRIMARY unsupported distinctly | Slice 2 classification, writer, and example 6's native proof | Needs Sway | **Early probe** at the start of slice 2 (records-only CI step on two fresh Sways, enabled and disabled). No distinct unsupported report → the unsupported case is classified from wl-clipboard's own wording observed in the probe output, or, if none can be observed, any non-zero `--primary` exit raises (still no fallback) and example 6's native proof becomes a README evidence limit |

## Ordered slices

### 1. Explicit PRIMARY text on X11, unavailable everywhere else
Type: Behavior
Status: done
Proof: desktop-free tests through public `clipboard.copy_primary` /
`clipboard.paste_primary` with per-selection fake `xclip` (examples 1–4, 7–9,
seam isolation); `tests/test_no_pillow_extra.py` names; new gated probe
`scripts/probe_linux_x11_native_primary.py` with wrapper
`tests/test_primary_native_linux_x11.py` (`CLIPBOARD_NATIVE_PROBE`, exit 2
with `evidence_limit` off X11, fails on an evidence limit in CI) run as an
added step of the existing native Linux X11 text job under Xvfb + `xclip`
(source 5a: "under the existing ... CI jobs"); local
`nix develop -c make check`, `make lint-workflows`, `make test-package`.

Behavior: Linux X11 session with `xclip`, PRIMARY and CLIPBOARD owned by
independent `xclip` processes with different text → `paste_primary()` /
`copy_primary(text)` → PRIMARY text is read / replaced (and still served
after the writing process exits), CLIPBOARD stays as it was, `copy` /
`paste` leave PRIMARY as it was, unowned PRIMARY reads `""`. On macOS,
Windows, WSL, other platforms, Linux without a session, X11 without `xclip`,
and (interim) Wayland, both raise `ClipboardContentError` naming the reason
without running any helper or pyperclip.

Early probe (first step, before the classification code): a records-only CI
step on a fresh Xvfb prints `xclip -selection primary -o -t TARGETS` stderr
and exit, then a background `xclip -selection primary -i` owner's
`-selection primary -o` / `-selection clipboard -o` results after its
launching shell exits. A surprise changes this slice before broad work.

Interim behavior: a Wayland session raises "not yet supported on Wayland"
(`ClipboardContentError`, no fallback); slice 2 replaces it. README states
X11 only until then.

README: new PRIMARY section (API, X11 helper, absence, no-fallback rule,
"not available" platforms) and an X11 Evidence entry with the probe steps,
`xclip` version, and evidence limits.

### 2. Explicit PRIMARY text on Wayland, with unsupported compositors reported
Type: Behavior
Status: planned
Proof: desktop-free tests with per-selection fake wl-clipboard (example 5
dispatch / argv, example 6 with the probe-observed unsupported wording, the
mixed `DISPLAY` + `WAYLAND_DISPLAY` session following the text rule); new
gated probe `scripts/probe_linux_wayland_native_primary.py` with wrapper
`tests/test_primary_native_linux_wayland.py` run as an added step of the
existing `.github/workflows/native-wayland-text.yml` Sway + wl-clipboard job
(source 5b); no disabled-PRIMARY Sway step (early probe: no distinct report);
local `nix develop -c make check`, `make lint-workflows`.

Behavior: Sway session with wl-clipboard, PRIMARY and CLIPBOARD set by
independent `wl-copy` processes with different text → `paste_primary()` /
`copy_primary(text)` → same results as slice 1 through
`wl-paste --primary` / `wl-copy --primary` (writer-exit lifetime,
CLIPBOARD unchanged, nothing selected reads `""`, `copy_primary("")`
leaves PRIMARY reading `""`); a compositor where wl-clipboard reports
PRIMARY unsupported → `ClipboardContentError` saying so, with no
non-`--primary` helper run. Wayland without wl-clipboard raises naming
`wl-clipboard`. Replaces slice 1's interim Wayland error.

Early probe (first step): records-only CI step on a fresh Sway (and a fresh
Sway with `primary_selection disabled`) prints `wl-paste --primary
--list-types` / `-n` stderr and exit with nothing selected, a
`wl-copy --primary` result read with and without `--primary` after the
launching shell exits, and the disabled compositor's `wl-copy --primary` /
`wl-paste --primary` stderr and exit. The outcome selects example 6's
classification and native proof per the premise table.

README: Wayland half of the PRIMARY section and Evidence (Sway 1.11,
wl-clipboard 2.2.1, compositor not generalized; GNOME / KDE / other
compositors, XWayland PRIMARY bridging and PRIMARY↔CLIPBOARD syncing managers
as evidence limits). AGENTS.md summary names `copy_primary` /
`paste_primary`, their X11 / Wayland paths and no-fallback rule.

## Plan concern evidence

Slice-plan refinement was not needed: the two slices are one cohesive
outcome per desktop, each with its own native proof loop and CI venue, and
the selection parameter is one common rule extended by both rather than a
per-desktop special case. This review identified no remaining slice-specific
concern. The two early probes are bounded by their slices' first steps.

## Learnings

- **Slice 1 early probe (settled, 2026-11-04).** Run by the coordinator in a
  local Docker `ubuntu:24.04` container with Xvfb + `xclip 0.13` (same `xclip`
  as CI; CI still owns native proof). Unowned `xclip -selection primary -o -t
  TARGETS` → stderr `Error: target TARGETS not available`, exit 1 (already in
  `_desktop._XCLIP_NO_OWNER_MARKERS`); a `xclip -selection primary -i` owner
  launched from a shell that exits keeps serving PRIMARY (`TARGETS`,
  `UTF8_STRING`) while a separate CLIPBOARD owner still serves its own text.
  No recognizer change.
- **Slice 2 early probe (settled, 2026-11-04).** Local Docker `ubuntu:24.04`,
  headless Sway 1.9 (CI: 1.11) + `wl-clipboard 2.2.1`. Enabled: nothing
  selected → `wl-paste --primary --list-types` / `-n` stderr `Nothing is
  copied`, exit 1 (the existing nothing-copied wording); `wl-copy --primary`
  from an exiting shell keeps serving PRIMARY while CLIPBOARD keeps its own
  text; `copy_primary("")`-equivalent leaves PRIMARY offering empty text.
  `primary_selection disabled`: wl-clipboard reports nothing distinct —
  `wl-paste --primary` says `Nothing is copied`, `wl-copy --primary` exits 0
  and the write is silently dropped. So that compositor is the story's
  evidence limit (source 5g), not example 6's native proof; slice 2 has no
  disabled-Sway step. wl-clipboard 2.2.1's own unsupported wording, taken
  from its binary strings, is `The compositor does not seem to support
  primary selection`: classify it as unsupported in desktop-free tests
  (example 6). Since a dropped write exits 0, `copy_primary` on Wayland should
  confirm by exact `wl-paste --primary` read-back (as X11 does) and raise on
  mismatch rather than report false success.

- **Slice 1 accepted proof (2026-11-04).** `nix develop -c make check`
  (643 passed, 28 skipped), `make lint-workflows`, `make test-package` exit 0;
  after refactor `nix develop -c uv run pytest tests/test_primary_x11.py
  tests/test_primary_unavailable.py tests/test_text_x11.py
  tests/test_text_session.py tests/test_text_dispatch.py tests/test_clipboard.py
  tests/test_text_native_linux_bound.py tests/test_text_wayland.py
  tests/test_no_pillow_extra.py -q` → 153 passed. Native
  `tests/test_primary_native_linux_x11.py` passed all 6 steps in a local
  Docker `ubuntu:24.04` Xvfb + `xclip 0.13` container; the CI step in
  `native-linux-x11-text` is pending (obligation G2). Slice 2 reuses the
  selection parameter (`_text_native_x11._CLIPBOARD` / `_PRIMARY`, error
  `subject`) and `_desktop_text._is_wsl`, and replaces `_primary.py`'s
  interim Wayland error (obligation G1).

## Story obligations

### G1. Wayland PRIMARY raises "not yet supported" after slice 1
Reported: slice 1 — "Wayland → \"is not yet supported on Wayland\"."
Story clause: "Linux Wayland on Sway → examples 1–3 hold through `wl-copy --primary` / `wl-paste --primary` and their non-primary counterparts."
Disposition: interim until slices 2

### G2. X11 PRIMARY native proof observed only in a local container until CI runs
Reported: slice 1 — "The official native proof is CI-owned and needs a branch push; the CI venue has not run this yet."
Story clause: "Gated native probes (`CLIPBOARD_NATIVE_PROBE`) under the existing Xvfb + `xclip` and Sway + wl-clipboard CI jobs"
Disposition: interim until slices 2
