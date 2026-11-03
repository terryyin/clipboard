# Plan: Keep owned text backends unless callers explicitly delegate

**Identity:** SEED-001#explicit-text-delegation
**Source:** [Keep owned text backends unless callers explicitly delegate](../../seeds/SEED-001-clipboard-true-to-its-name.md#explicit-text-delegation)
**North Star:** [Rich clipboard content beside text re-exports](../../NORTH-STAR.md#rich-clipboard-content-beside-text-re-exports)

## Goal and scope

Default `copy` / `paste` pick the backend from the current session on every
call and never let resolved pyperclip state (`pyperclip.is_available()`,
including `pyperclip.set_clipboard()` alone) displace the owned macOS, X11
(`xclip`) or Wayland (wl-clipboard) backend. Deliberate delegation is the
existing `set_text_clipboard_writer` / `set_text_clipboard_reader` pair
(`None` restores default dispatch). Windows, WSL, X11 without `xclip` but
with a pyperclip fallback, and other platforms keep delegating
automatically.

- Included: `clipboard/_text.py` selection rule and docstrings (module,
  `_select_text_backend`, both setters: no longer "tests / fakes" only);
  dispatch tests; README text section (the "already resolved" bullet, the
  "no working user changes mechanism" sentence, the delegated-paths list, a
  compatibility note, a deliberate-delegation recipe with call-time
  `pyperclip.copy` / `pyperclip.paste` lookup, Evidence "Unverified" list);
  AGENTS.md text-backend summary.
- Excluded (seed boundary): new backend, public selector, pyperclip
  monkeypatching, native content features, the X11 write deadline
  ([SEED-001#bounded-x11-text-write](../../seeds/SEED-001-clipboard-true-to-its-name.md#bounded-x11-text-write)).
- Assumption: no ordering dependency on the X11 write correction; both touch
  the text subsystem but different functions (`_text.py` here,
  `_text_native_x11.py` there).

## Decisive premises (observed 2026-11-03, this workspace, macOS)

| Premise | Consuming operation | Observation | Result |
| --- | --- | --- | --- |
| Real `pyperclip.set_clipboard()` alone flips the current rule to pyperclip | `_text._select_text_backend()` | fresh `python -I` script: `is_available()` / selection before and after `pyperclip.set_clipboard("pbcopy")` | baseline `False macos` → `True pyperclip`; with the `is_available()` branch removed (scratch) `True macos` |
| Removing the branch is the whole rule change; only the resolved-wins test consumes it | `tests/test_text_dispatch.py`, `test_clipboard.py`, `test_text_session.py`, `test_text_{macos,x11,wayland}.py` under the scratch edit | `nix develop -c uv run pytest -q <those files>` | 2 failed (`test_already_resolved_pyperclip_mechanism_wins[darwin,linux]`), 120 passed; scratch reverted (`git checkout clipboard/_text.py`) |
| Hooks delegating to pyperclip keep the error contract; `None` restores default | `clipboard.copy` via `_call_content_backend` | same script: hook `lambda t: pyperclip.copy(t)` with `pyperclip.copy` raising `PyperclipException`; then `set_text_clipboard_writer(None)` | `ClipboardContentError`, `__cause__` the `PyperclipException`; writer is `_default_text_clipboard_writer` again (unchanged code, both before and after the scratch edit) |

## Outside-in proof

| Key example | Observable signal |
| --- | --- |
| Direct pyperclip use / `set_clipboard()` alone keeps the owner | Replace the resolved-wins test: with `FakePyperclip(available=True)` on macOS, X11-with-`xclip` and Wayland session shapes, `copy` / `paste` reach the owned fake and `fake.writes == []`, `fake.reads == 0`; fails before the change |
| Same, with real pyperclip state | Fresh-interpreter test (`_run` in `tests/test_clipboard.py`): real `pyperclip.set_clipboard(...)` then `_text._select_text_backend()` on a forced macOS session names the owned backend; fails before the change |
| Explicit hooks delegate and keep the contract; `None` restores | Dispatch test: both hooks call `pyperclip.copy` / `pyperclip.paste` at call time on an owned session shape; text round-trips through the fake pyperclip, a `PyperclipException` becomes `ClipboardContentError` with it as `__cause__`; after resetting both to `None` the owned fake is reached again |
| Boundary: no-session Linux with resolved pyperclip | Former `[linux]` case becomes: `available=True`, no `DISPLAY` / `WAYLAND_DISPLAY` → no-desktop-session `ClipboardContentError`, pyperclip untouched |
| Selection not frozen | Existing `test_selection_follows_session_at_call_time` stays green |
| Unowned sessions still delegate automatically | Existing `test_delegated_sessions_round_trip_through_pyperclip` and subprocess delegation tests stay green |
| Regression | `nix develop -c make check` (AGENTS.md "Check Python") |

No native probe change: owned backends' native behavior is unchanged and
already gated by the `tests/test_text_native_*.py` wrappers; CI runs them
after publication.

## Ordered slices

### 1. Owned text backends ignore resolved pyperclip state
Type: Behavior
Status: planned
Proof: all rows above; `nix develop -c make check`.

Behavior: an owned desktop session whose process already resolved a pyperclip
mechanism (direct use or `set_clipboard()`) → `clipboard.copy` / `paste` →
the owned backend serves it, pyperclip is not called; with both hooks set to
pyperclip-forwarding callables text goes through pyperclip under clipboard's
error contract, and `None` restores the owner. README, AGENTS.md and
docstrings describe the new rule, the compatibility change, and the
delegation recipe.

## Current decisions

- Accepted (Terry Yin, 2026-11-03, in the seed): explicit opt-in through the
  existing hooks; no inference from pyperclip state, no new public API.
- One slice: the rule change is a three-line removal whose only consumer is
  one test; tests and docs describe the same behavior and do not separate
  into an independently valuable outcome.

## Plan review

Slice-plan refinement not needed: one cohesive Behavior slice with every key
example mapped to a discriminating or preserved proof and its premises
observed. No remaining slice-specific concerns were identified.

## Learnings

_(none yet)_
