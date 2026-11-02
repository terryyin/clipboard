# Plan: Verify Linux clipboard file offers in CI

**Identity:** SEED-002#linux-file-offers-ci
**Source:** [Verify Linux file offers in CI](../../seeds/SEED-002-linux-file-offers-ci.md#linux-file-offers-ci)
**Source review:** [Independent source commitments](source-review.md)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Observe actual Thunar Paste behavior on GitHub Actions X11/Xvfb for each
single-format helper-owned clipboard offer, after its writer process exits.
This answers the MIME-choice premise in SEED-001#copy-files without implementing
the API. Wayland and other file managers retain their evidence limits.

## Assumptions and existing solutions

- Reuse the existing `ci.yml` Xvfb job pattern, locked uv environment, and
  `CLIPBOARD_NATIVE_PROBE=1` gating; isolate the desktop in a D-Bus session.
- No file-manager paste harness exists. Add one bounded experiment, with no
  package dependency or product architecture change. No ADR store exists.
- GitHub remote is `origin`, repository `terryyin/clipboard`, trunk `master`.
  Local Darwin cannot perform the Linux round; the early probe is the slice.
- Existing push CI covers every branch; authenticated GitHub access and Nix
  commands are available. Actual GUI automation is unproved until the CI probe.
- AGENTS.md requires `nix develop -c make check` and, for workflow changes,
  `nix develop -c make lint-workflows`.

## Outside-in proof

| Example | Observable signal | Slice |
| --- | --- | --- |
| Named file manager accepts a candidate | Paste creates both files with exact bytes; sources survive unchanged | 1 |
| Offer outlives writer | Writer subprocess finishes before triggering the file-manager paste | 1 |
| Candidate rejection is an observation, not a harness success | Positive copy-format control pastes; unavailable session/window/action fails | 1 |
| Missing action cannot produce a passing paste proof | Negative control leaves the destination empty; corruption/missing files fail assertions | 1 |
| Reproducible evidence | Actions job logs/results include distro, Thunar/helper versions, MIME and result | 1 |

## Ordered slices

### 1. Observe Thunar clipboard interoperability in Actions
Type: Behavior
Status: planned
Proof: gated native experiment offers two Unicode/space file URIs using each
candidate MIME and invokes Thunar's Paste action in an isolated Xvfb/D-Bus
desktop. A positive control confirms file-manager operation and automation;
negative control proves absent paste cannot pass the copying assertions.
Actual copies must match both source bytes, with unchanged originals. Record
bounded non-paste outcomes accurately and fail on harness/setup failure.
Add the job to the required CI aggregate, upload bounded diagnostics, run
`nix develop -c make check lint-workflows`, publish the branch, and obtain the
exact-revision Actions result. Record findings and revise the existing
copy-files plan's affected proof route without changing its product scope.

Behavior: Pre-condition: Linux file-manager compatibility is unobserved.
Trigger: run the dedicated Actions probe. Postcondition: the named
X11/Thunar combination has real paste evidence for the tested MIME formats,
or an actionable CI/harness failure is reported; no unobserved platform claim.

## Current decisions

- Keep the experiment independent of the unimplemented `copy_files` API.
- Keep the experiment reviewable on its branch until the actual Actions result
  is known; delivery and closure cover this verification only, not `copy_files`.
- Desktop-free default tests remain isolated and skip the native experiment.

## Execution identity

Story Branch Mode; owned worktree created for SEED-002#linux-file-offers-ci at
`/Users/terryyin/git/clipboard/.worktrees/verify-linux-file-offers-ci`, branch
`codex/verify-linux-file-offers-ci`. Integration checkout
`/Users/terryyin/git/clipboard`; remote `origin`, trunk `master`.
Starting revision `2cf3ce57848067b64c1d35bbb3e10b48d55b65f2`;
published admission `7a908cc154369ed7552826f30181513eb76119e8`.
Checkout-bound setup and baseline: `nix develop -c make deps check
lint-workflows` passed (309 tests, 15 expected native skips). Hosted desktop
proof is owned by the coordinator after progress publication.

## Accepted local proof

- `nix develop -c uv run --locked pytest
  tests/test_file_manager_offer_assertions.py
  tests/test_file_manager_offers_native_linux_x11.py -v`: 4 passed, 1 gated
  skip. The copy oracle rejects missing copies, corrupt destination bytes,
  and changed originals. The real GUI test has not run locally.
- Inspected `probe_linux_x11_file_manager_offers.py`: `_offer` waits for
  the helper command's exit, checks the sole advertised payload MIME and
  independently reads its exact bytes; `_round` focuses a named Thunar
  destination and sends Paste only after the no-paste control fails the
  same copying assertions. `main` brackets the URI experiment with two
  successful GNOME-copy-format controls and records bounded outcomes.
- Consumer trace at `7a908cc154369ed7552826f30181513eb76119e8` with terms
  `native-linux-x11-file-manager-offers`,
  `probe_linux_x11_file_manager_offers`, `_assert_copies`: new probe/oracle
  observations own the script boundary; workflow lint and hosted CI own the
  required aggregate and reusable-release consumer. Unchanged gates and
  generic dictionary matches do not change product behavior.

## Learnings

None yet; the real GUI round is an early probe, not a settled premise.

## Plan review

Refinement not needed: one cohesive experiment and proof loop.
Remaining concerns: none outside the explicitly bounded early probe.


## Story obligations

### G1. Hosted GUI evidence awaits first progress publication
Reported: slice 1 — "Actual Thunar GUI evidence requires the new workflow to be published and run in GitHub Actions."
Story clause: "Publish the workflow on a reviewable branch and run it in GitHub Actions."
Disposition: return


### G2. Record measured MIME findings in the copy-files plan
Reported: slice 1 — "The existing copy-files plan still awaits the actual Actions MIME outcomes."
Story clause: "Record the result where the existing copy-files plan can consume it."
Disposition: return
