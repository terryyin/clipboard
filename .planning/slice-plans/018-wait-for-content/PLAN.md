# Plan: Wait for clipboard content with bounded cancellation and timeouts

**Identity:** SEED-001#wait-for-content
**Source:** [Wait for clipboard content with bounded cancellation and timeouts](../../seeds/SEED-001-clipboard-true-to-its-name.md#wait-for-content)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Add `wait_for_kind(kind, *, timeout, interval=0.5, cancel=None)` and
`wait_for_text_change(*, timeout, interval=0.5, cancel=None)`: bounded,
cancellable waits that observe through the already delivered `inspect` and
`paste`, return the observed snapshot / text, return `None` on deadline or
cancellation, and raise any observation failure at once without retrying.
Scope, required restrictions and their reasons, and key examples 1–9 are in
the seed section; this plan adds none.

**Excluded** (seed scope limits): native change notification
(`changeCount`, clipboard sequence number / format listener, XFixes,
`wl-paste --watch`), changed-value waits for image / HTML / files, PRIMARY,
async waits, callbacks or iterators, background watchers, lossless or
per-event delivery.

## Assumptions and direction

- Follows the North Star topic: explicit new API beside `copy` / `paste`,
  the same absence / value / failure model (absence keeps waiting, failures
  raise `ClipboardContentError`), fakes in default CI, native claims only
  with independent producers and stated evidence limits. No revision needed.
  No ADR store exists; no Accepted ADR constrains this plan.
- **PFE.** Reuse: `inspect()` (`clipboard/_offer.py`) already gives a
  non-mutating, payload-free kind snapshot with empty-offer-as-absence on all
  four desktops, and `paste()` (`clipboard/_text.py`) gives `""` absence and
  bounded helpers; both honour their injection seams. pyperclip 1.11 has no
  `waitForPaste` / `waitForNewPaste` (domain research), so nothing upstream is
  reused for the loop. **Gap:** no wait exists. One new module
  `clipboard/_wait.py` owns one concept: a bounded observation loop
  (observe → predicate → deadline / cancel check → sleep on
  `cancel.wait(remaining-capped interval)` or `time.sleep`) on
  `time.monotonic`, plus argument validation. Both public waits are that one
  loop with a different observation and predicate (kind membership; changed
  non-empty text against the baseline); slice 2 extends the loop, it does
  not add a second one.
- The waits call the public `inspect` / `paste` functions of their owning
  modules on each observation, so `set_clipboard_inspector` /
  `set_text_clipboard_reader` fakes drive desktop-free tests; the clock and
  sleep are module attributes of `clipboard/_wait.py` that tests monkeypatch
  (no `sys.platform` faking, AGENTS.md). Tests assert error type and the
  named argument / platform, not copied wording.
- Validation reuses the `ClipboardKind` vocabulary from `clipboard/_offer.py`
  (no second kind list).
- Preparation checkout: Darwin 25.6.0 macOS Aqua, the developer machine for
  the gated macOS probe (run it yourself after checking the screen is
  unlocked; memory "Run desktop rounds yourself"). Linux X11, Linux Wayland
  and Windows native proof runs in GitHub Actions after a branch push.
- Local gates (AGENTS.md): `nix develop -c make check` every slice;
  `nix develop -c make test-package` in slice 1 because `__all__` grows
  (installed distributions must export the new names);
  `nix develop -c make lint-workflows` in slice 3 (workflows change).

## Outside-in proof

| Example / promise (seed) | Observable signal | Owning slice |
| --- | --- | --- |
| 1. Kind appears after several observations → snapshot returned | Desktop-free: injected inspector yields empty, empty, `{"image"}` snapshots; result is the third snapshot; fake clock shows two interval sleeps. Native: wait from an empty clipboard, independent producer copies text → snapshot with `"text"` before the deadline | 1 (desktop-free, macOS), 3 (X11, Wayland, Windows) |
| 2. Kind already offered → immediate return | Desktop-free: one inspector call, no sleep | 1 |
| 3. Text changes → new text returned | Desktop-free: injected reader yields `"old"`, `"old"`, `"new"` → `"new"`. Native: baseline from an independent producer, second independent copy → returned text | 2 (desktop-free, macOS), 3 |
| 4. Clearing and identical recopy are not changes | Desktop-free: reader yields `"old"`, `""`, `"old"` until the fake deadline → `None` | 2 |
| 5. Deadline → `None`, no observation after it | Desktop-free: fake clock; observation count and the last observation time ≤ deadline. Native: nothing copied, `timeout=1` → `None`, elapsed within `timeout` + one observation | 1, 2 (desktop-free), 1 / 3 (native) |
| 6. Cancellation from another thread ends the wait promptly | Desktop-free: real `threading.Event` set from a thread during a long interval; the wait returns `None` well before the interval elapses (generous bound), one observation made | 1 (reused by 2) |
| 7. No session / any observation failure → raised at once, never retried | Desktop-free: injected inspector / reader raising `ClipboardContentError` on the first call → raised, exactly one call, no sleep; a failure after absent observations is also raised at once | 1, 2 |
| 8. Invalid `kind` / `timeout` / `interval` / `cancel` → error before observing | Desktop-free: each invalid value raises `ClipboardContentError` and the inspector / reader records no call | 1, 2 |
| 9. `timeout=0` → one observation then `None` | Desktop-free: one call, no sleep | 1, 2 |
| No busy spinning, no watcher thread, no payload history | Desktop-free: every sleep equals `min(interval, remaining)` > 0; `threading.active_count()` unchanged after the wait; the change wait keeps only the baseline (code review, no log calls) | 1, 2 |
| Public surface | `tests/test_no_pillow_extra.py` names both waits in `__all__` without Pillow; `make test-package` installed wheel + sdist | 1 (`wait_for_kind`), 2 (`wait_for_text_change`) |
| Documentation | README section on waiting (API, state-wait vs change-wait, `None` on deadline / cancel, failures raise, observation limits: missed identical recopy and between-observation changes, return no later than timeout plus one observation) and Evidence entries per desktop; AGENTS.md summary names the waits | 1, 2 (README API), 3 (Evidence, AGENTS.md) |
| Regression | `inspect` / `paste` contract and native probes unchanged; `nix develop -c make check` green | every slice |

A same-process copy-then-wait is only a consistency check; native claims need
an independent producer process copying while the library's wait is running.

## Decisive premises

Observed in this workspace (Darwin 25.6.0, branch
`claude/wait-for-clipboard-content-with-bounded-cancella` at 20a459c, plus
the uncommitted seed refinement):

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| The local gate runs in this checkout | Every slice's `make check`; slice 1–2 `make test-package` | `nix develop -c make check` → exit 0, `606 passed, 27 skipped in 10.85s` | Settled |
| Default suite and native jobs are green at the start | Regression baseline; slice 3 CI venues | `gh run view 41768147173` (head 20a459c): every job `success`, including Native Linux X11 / Wayland / Windows text and clear jobs | Settled for CI |
| `inspect()` and `paste()` are cheap enough on macOS for a 0.5 s default interval | Default `interval` | `nix develop -c uv run python -c '…'` timing one call each on this Mac: `inspect` 0.191 s (osascript), `paste` 0.011 s | Settled: 0.5 s leaves headroom; no faster default |
| Native `inspect()` reads an empty clipboard as an empty snapshot (absence, not failure) on X11, Wayland and Windows | Examples 1 and 5 native: the wait keeps observing an empty clipboard | `scripts/native_clear_support.py:173` calls `clipboard.inspect()` after `clear()` and requires `{"kinds": [], "formats": []}`; the X11 / Wayland / Windows clear jobs are `success` in run 41768147173; desktop-free `tests/test_inspect_wayland.py::test_nothing_copied_inspects_as_empty_snapshot` and the X11 no-owner path in `clipboard/_desktop.py:173` | Settled |
| Native `inspect()` lists the `"text"` kind for an independent text producer on X11, Wayland and Windows within one observation | Example 1 native on those desktops | Gated inspect probes exist (`scripts/probe_{linux_x11,linux_wayland,windows}_native_inspect.py`) but no CI job runs them (not in run 41768147173) | **Early probe** at the start of slice 3: the new wait probes report the snapshot each observation returns; a missing text kind stops slice 3 and changes the plan (README evidence limit or an inspect fix as a separate decision) |
| Desktop-free tests can drive the loop deterministically without real sleeps | Slices 1–2 proof | Design premise: clock and sleep are `clipboard/_wait.py` attributes; the cancel path uses a real `threading.Event` with a short real bound | Settled by construction; slice 1's first test observes it |

## Ordered slices

### 1. Wait for a clipboard kind with deadline and cancellation
Type: Behavior
Status: planned
Proof: desktop-free tests through public `clipboard.wait_for_kind` in a new
`tests/test_wait_for_kind.py` with an injected inspector, a monkeypatched
clock / sleep and a real `threading.Event` (examples 1, 2, 5–9 and the
no-busy-spin / no-thread rows); `tests/test_no_pillow_extra.py` names; new
gated probe `scripts/probe_macos_native_wait.py` with wrapper
`tests/test_wait_native_macos.py` (`CLIPBOARD_NATIVE_PROBE`, exit 2 with
`evidence_limit` off macOS Aqua) run locally: `clear()` as setup, a child
Python starts `wait_for_kind("text", timeout=20)`, `pbcopy` copies after
about 1 s, the child reports the snapshot and elapsed time; then
`wait_for_kind("html", timeout=1)` with nothing copied returns `None`;
local `nix develop -c make check`, `nix develop -c make test-package`.

Behavior: clipboard without the requested kind → `wait_for_kind(kind,
timeout=…)` → returns the first snapshot containing the kind once another
application offers it (at once when already offered), `None` at the
deadline or when `cancel` is set, `ClipboardContentError` at once on an
observation failure or invalid argument, with no observation after the
deadline, no zero-length sleep and no thread left behind.

README: new "Waiting for content" section with `wait_for_kind`, its state
semantics, deadline / cancellation / failure outcomes and observation
limits; macOS Aqua Evidence entry naming the probe and macOS version.

### 2. Wait for changed text on the same bounded loop
Type: Behavior
Status: planned
Proof: desktop-free tests through public `clipboard.wait_for_text_change`
in `tests/test_wait_for_text_change.py` with an injected text reader and the
same clock / cancel fakes (examples 3, 4, 5–9 for the change wait); the
macOS probe gains a change step: `pbcopy "old"`, child starts
`wait_for_text_change(timeout=20)`, `pbcopy "new"` after about 1 s → child
reports `"new"`; and a clear-then-recopy-`"old"` step with `timeout=3` →
`None`; `tests/test_no_pillow_extra.py` names; local `make check`,
`make test-package`.

Behavior: clipboard holding text → `wait_for_text_change(timeout=…)` →
returns the first later non-empty text that differs from the baseline read
at the start; clearing, non-text offers and identical recopy keep it
waiting; deadline, cancellation, failures and invalid arguments behave as
in slice 1 through the same loop.

README: the section gains `wait_for_text_change`, the baseline rule and the
missed-change limits.

### 3. Native wait evidence on Linux X11, Linux Wayland and Windows
Type: Behavior
Status: planned
Proof: new gated probes `scripts/probe_linux_x11_native_wait.py`,
`scripts/probe_linux_wayland_native_wait.py`,
`scripts/probe_windows_native_wait.py` with wrappers
`tests/test_wait_native_{linux_x11,linux_wayland,windows}.py` (fail on an
evidence limit in CI), run by new jobs in `ci.yml` (Xvfb + `xclip`,
`windows-latest`) and a reusable `.github/workflows/native-wayland-wait.yml`
(Sway + wl-clipboard, as `native-wayland-text.yml`), each added to the
`CI passed` needs; local `nix develop -c make lint-workflows` and
`make check`; the branch-push CI run is the acceptance observation.

Behavior: on each desktop's fresh empty clipboard, a child Python waiting
with `wait_for_kind("text", timeout=20)` returns a snapshot with `"text"`
after an independent producer (`xclip -selection clipboard -i`, `wl-copy`,
PowerShell `Set-Clipboard`) copies; `wait_for_text_change(timeout=20)` after
an independent baseline copy returns the second independently copied text;
a wait with nothing copied and `timeout=1` returns `None` within
`timeout` plus one observation.

Early probe (first step, before the README claims): the probes record every
snapshot / text each observation returned; push them and read the run. A
desktop where `inspect` never reports `"text"` for the independent producer
stops this slice and changes the plan.

README: Evidence entries for Xvfb + `xclip`, Sway + wl-clipboard and
`windows-latest` with helper versions; other compositors, GNOME / KDE and
non-text kinds rely on `inspect`'s existing evidence and are stated as
limits for the wait. AGENTS.md summary names `wait_for_kind` /
`wait_for_text_change`, their observation through `inspect` / `paste`, and
the native wait probes.

## Plan concern evidence

Slice-plan refinement was not needed: slices 1–2 share one observation loop
introduced in slice 1 and extended by a second predicate in slice 2 (one
common rule, not per-wait special cases), each with its own desktop-free and
macOS proof loop; slice 3 is one native evidence loop on CI venues that slice
1–2 cannot reach from this Mac, with its one unobserved premise bounded by
its early probe. This review identified no remaining slice-specific concern.
