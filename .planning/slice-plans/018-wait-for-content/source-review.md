# Source review: SEED-001#wait-for-content

**Launch:** fresh general-purpose sub-agent, no conversation inheritance, launched 2026-11-04 by the execution coordinator (Tsubomi-chan) before slice 1 acceptance.
**Input:** only the story's Goal, Scope (plan link line removed) and Key examples from `.planning/seeds/SEED-001-clipboard-true-to-its-name.md#wait-for-content`, extracted to a single file (sha256 `5404f34390d5cdd790438a1210f2f774a00802a5046f981611c3c5ef73b40428`); instructed to read no other file, change nothing, and return numbered commitments with qualifications, examples and exclusions.
**Return:** the table below (source commitment text as returned; Slice and Observation columns added by the coordinator). Commitments shared by both waits are allocated to slice 2, which completes them; whole-story goals, cross-desktop claims and exclusions to slice 3.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| G1 | Automation developers can wait for content that the user or another application copies, in one bounded call, instead of writing their own polling loops around `inspect` / `paste` with ad hoc sleeps, deadlines and error handling | slice 3 | |
| G2 | A wait returns as soon as the content is observed | slice 3 | |
| G3 | A wait ends predictably at its deadline or on cancellation | slice 3 | |
| G4 | A wait never hides an access failure as "nothing copied yet" | slice 3 | |
| G5 | Interactive automation ("copy the image you want to process") becomes practical using the content operations that already exist | slice 3 | |
| G6 | Records honestly what a polling observer can and cannot see | slice 3 | |
| 1.1 | New public function `wait_for_kind(kind, *, timeout, interval=0.5, cancel=None)`. `kind` is keyword-or-positional; `timeout`, `interval` and `cancel` are keyword-only, with defaults interval=0.5 and cancel=None | slice 1 | observed: clipboard/_wait.py wait_for_kind signature; tests/test_wait_for_kind_failures.py::test_wait_for_kind_is_public |
| 1.2 | `wait_for_kind` observes the current offer through `inspect` | slice 1 | observed: clipboard/_wait.py wait_for_kind observes _offer.inspect(); tests/test_wait_for_kind.py injected Inspector call records |
| 1.3 | `wait_for_kind` returns the first `ClipboardOfferSnapshot` whose `kinds` contain `kind` | slice 1 | observed: tests/test_wait_for_kind.py::test_kind_appearing_after_several_observations_returns_that_snapshot (result is IMAGE snapshot) |
| 1.4 | `kind` is one of `"text"`, `"image"`, `"html"`, `"files"` | slice 1 | observed: tests/test_wait_for_kind_failures.py::test_every_kind_in_the_vocabulary_is_accepted; kinds from get_args(ClipboardKind) |
| 1.5 | It is a state wait: if the kind is already offered at the first observation, it returns at once | slice 1 | observed: tests/test_wait_for_kind.py::test_kind_already_offered_returns_at_once_after_one_observation |
| 1.6 | A caller who needs *new* content uses the text-change wait or clears the clipboard first (alternatives) | slice 2 | |
| 1.7 | `wait_for_kind` reads no payload, so it needs no images extra | slice 1 | observed: tests/test_no_pillow_extra.py::test_public_function_without_pillow[wait_for_kind] |
| 1.8 | `wait_for_kind` leaves the clipboard unchanged | slice 1 | observed: clipboard/_wait.py wait_for_kind calls only inspect() (non-mutating); no write path |
| 2.1 | New public function `wait_for_text_change(*, timeout, interval=0.5, cancel=None)` with all arguments keyword-only | slice 2 | |
| 2.2 | It reads the text through `paste` once, as its baseline | slice 2 | |
| 2.3 | It returns the first later observed text that is non-empty and differs from the baseline | slice 2 | |
| 2.4 | Clearing the clipboard is not a change; the wait continues | slice 2 | |
| 2.5 | An offer with no text is not a change; the wait continues | slice 2 | |
| 2.6 | "Changed" compares observed values, not copy events | slice 2 | |
| 2.7 | An identical recopy is missed. This is documented, not a defect | slice 2 | |
| 2.8 | Values that come and go between two observations are missed. This is documented, not a defect | slice 2 | |
| 3.1 | `timeout` is required. There is no unbounded wait | slice 2 | |
| 3.2 | `timeout` is a non-negative finite number of seconds | slice 2 | |
| 3.3 | `timeout` is measured on a monotonic clock | slice 2 | |
| 3.4 | `timeout=0` makes exactly one observation; for the text-change wait, that is only the baseline | slice 2 | |
| 3.5 | When the deadline passes, the wait returns `None` without another observation | slice 2 | |
| 3.6 | When `cancel` is set, the wait returns `None` without another observation | slice 2 | |
| 3.7 | `cancel` accepts a `threading.Event`, or any object with `is_set()` and `wait(seconds)` (alternatives) | slice 2 | |
| 3.8 | Between observations the wait sleeps on `cancel.wait(...)` or an equivalent sleep (alternatives) | slice 2 | |
| 3.9 | Setting `cancel` from another thread ends the wait without waiting out the interval | slice 2 | |
| 3.10 | No time is spent busy spinning | slice 2 | |
| 3.11 | No new observation starts after the deadline | slice 2 | |
| 3.12 | An observation already in flight finishes within its own existing helper bound | slice 2 | |
| 3.13 | A wait returns no later than `timeout` plus one observation | slice 2 | |
| 3.14 | `KeyboardInterrupt` propagates | slice 2 | |
| 4.1 | Any `ClipboardContentError` from an observation is raised at once | slice 2 | |
| 4.1.1 | This covers no desktop session | slice 2 | |
| 4.1.2 | This covers a missing helper | slice 2 | |
| 4.1.3 | This covers denied access | slice 2 | |
| 4.1.4 | This covers enumeration failure | slice 2 | |
| 4.1.5 | This covers helper failure | slice 2 | |
| 4.1.6 | This covers helper timeout | slice 2 | |
| 4.1.7 | This covers "not available" on the platform | slice 2 | |
| 4.2 | Failures are never retried | slice 2 | |
| 4.3 | Reason for 4.2: the wait itself cannot ask again for a permission that was refused | slice 2 | |
| 4.4 | An empty clipboard is absence, not failure: `inspect` yields no kinds, `paste` yields `""`, and the wait keeps observing | slice 2 | |
| 4.5 | A timeout or cancellation returns `None`, so it can never be mistaken for a failure | slice 2 | |
| 5.0 | Invalid input raises `ClipboardContentError` before any observation, following the library's invalid-input rule | slice 2 | |
| 5.1 | Invalid input: an unknown `kind` | slice 1 | observed: tests/test_wait_for_kind_failures.py::test_invalid_argument_raises_before_any_observation (kind cases, zero inspector calls) |
| 5.2 | Invalid input: a negative `timeout` | slice 2 | |
| 5.3 | Invalid input: a NaN `timeout` | slice 2 | |
| 5.4 | Invalid input: an infinite `timeout` | slice 2 | |
| 5.5 | Invalid input: a boolean `timeout` | slice 2 | |
| 5.6 | Invalid input: a non-numeric `timeout` | slice 2 | |
| 5.7 | Invalid input: an `interval` that is not a positive finite number | slice 2 | |
| 5.8 | Invalid input: a `cancel` without `is_set` / `wait` | slice 2 | |
| 5.9 | `interval` must be positive because a zero interval busy-spins helper processes against the desktop | slice 2 | |
| 5.10 | `timeout` must be finite because the story's promise is a bounded wait | slice 2 | |
| 6.1 | The waits run wherever their observation operation runs, with that operation's session selection and errors | slice 3 | |
| 6.2 | `wait_for_kind` runs through `inspect` on macOS Aqua, Windows desktop, Linux X11 TARGETS and Linux Wayland MIME list | slice 3 | |
| 6.3 | Elsewhere, `inspect`'s "not available" error is raised at the first observation | slice 1 | observed: tests/test_wait_for_kind_failures.py::test_platform_without_inspect_raises_naming_it_at_once (sunos5) |
| 6.4 | `wait_for_text_change` runs through `paste` on all `paste` backends, including pyperclip delegation | slice 2 | |
| 6.5 | Injected seams (`set_clipboard_inspector`, `set_text_clipboard_reader`) are honoured | slice 2 | |
| 6.6 | Desktop-free tests need no new seam | slice 2 | |
| 7.1 | The wait runs in the calling thread | slice 2 | |
| 7.2 | It starts no background watcher, thread or long-lived helper | slice 2 | |
| 7.3 | It keeps no history beyond the one baseline text it compares against | slice 2 | |
| 7.4 | It logs no payload | slice 2 | |
| 7.5 | Every helper it starts is the bounded helper of the observation operation | slice 2 | |
| 7.6 | Each such helper is finished before the wait returns or raises | slice 2 | |
| 8.1 | Desktop-free default tests use an in-memory inspector and reader, a fake clock and a fake cancel | slice 2 | |
| 8.1.1 | Desktop-free test: immediate return | slice 1 | observed: tests/test_wait_for_kind.py::test_kind_already_offered_returns_at_once_after_one_observation |
| 8.1.2 | Desktop-free test: content appears after several observations | slice 1 | observed: tests/test_wait_for_kind.py::test_kind_appearing_after_several_observations_returns_that_snapshot |
| 8.1.3 | Desktop-free test: deadline | slice 2 | |
| 8.1.4 | Desktop-free test: `timeout=0` | slice 2 | |
| 8.1.5 | Desktop-free test: cancellation from another thread | slice 2 | |
| 8.1.6 | Desktop-free test: failure propagates without retry | slice 2 | |
| 8.1.7 | Desktop-free test: clearing during a change wait | slice 2 | |
| 8.1.8 | Desktop-free test: the invalid inputs | slice 2 | |
| 8.2 | Gated native probes (`CLIPBOARD_NATIVE_PROBE`) run on four sessions | slice 3 | |
| 8.2.1 | Gated native probe on macOS, producer `pbcopy` | slice 2 | |
| 8.2.2 | Gated native probe on Windows, producer PowerShell `Set-Clipboard` | slice 3 | |
| 8.2.3 | Gated native probe on Linux X11 (Xvfb + `xclip`), producer `xclip` | slice 3 | |
| 8.2.4 | Gated native probe on Linux Wayland (Sway + wl-clipboard), producer `wl-copy` | slice 3 | |
| 8.3 | Each probe starts a wait, then copies with an independent producer | slice 3 | |
| 8.3.1 | Probe check: `wait_for_kind("text")` from an empty clipboard returns within the deadline | slice 3 | |
| 8.3.2 | Probe check: `wait_for_text_change` returns within the deadline | slice 3 | |
| 8.3.3 | Probe check: a wait with nothing copied returns `None` after its timeout | slice 3 | |
| 8.4 | The README documents the two functions | slice 2 | |
| 8.5 | The README documents the observation limits | slice 2 | |
| 8.6 | The README documents the observed sessions | slice 3 | |
| 8.7 | Other kinds and other compositors rely on `inspect`'s existing native proof; they are evidence limits for the wait itself | slice 3 | |
| X1 | Deferred, not rejected: native change notification as an optimization (macOS `changeCount`, Windows clipboard sequence number or format listener, X11 XFixes, `wl-paste --watch`) | slice 3 | |
| X2 | Deferred: changed-value waits for images, HTML or files | slice 3 | |
| X3 | Deferred: waiting on PRIMARY (SEED-001#primary-selection) | slice 3 | |
| X4 | Deferred: async/awaitable waits | slice 3 | |
| X5 | Deferred: callbacks or iterators over successive changes | slice 3 | |
| X6 | Deferred: a background watcher | slice 3 | |
| X7 | Deferred: any promise of lossless or per-event delivery | slice 3 | |
| E1 | Empty clipboard → `wait_for_kind("image", timeout=30)` → the user copies a screenshot in another app 3 s later → returns a snapshot whose `kinds` contain `"image"` within about one interval of the copy | slice 1 | observed: tests/test_wait_for_kind.py::test_kind_appearing_after_several_observations_returns_that_snapshot (IMAGE after two 0.5 s sleeps) |
| E2 | Clipboard already offers text → `wait_for_kind("text", timeout=5)` → returns at once after one observation | slice 1 | observed: tests/test_wait_for_kind.py::test_kind_already_offered_returns_at_once_after_one_observation |
| E3 | Clipboard holds `"old"` → `wait_for_text_change(timeout=30)` → another app copies `"new"` → returns `"new"` | slice 2 | |
| E4 | Clipboard holds `"old"` → `wait_for_text_change(timeout=30)` → the clipboard is cleared, then `"old"` is copied again → the wait keeps observing and returns `None` at 30 s (clearing and identical recopy are not changes) | slice 2 | |
| E5 | Nothing copied → `wait_for_kind("html", timeout=2)` → returns `None` about 2 s later, with no observation started after the deadline | slice 1 | observed: tests/test_wait_for_kind.py::test_deadline_returns_none_with_no_observation_after_it (max call time <= deadline) |
| E6 | Wait with `cancel=event`, `timeout=60` → another thread sets `event` after 1 s → returns `None` without waiting out the interval or the timeout | slice 1 | observed: tests/test_wait_for_kind.py::test_cancel_set_from_another_thread_ends_the_wait_promptly (real Event, timeout 60, interval 30) |
| E7 | Linux with no desktop session → `wait_for_kind("text", timeout=10)` → raises `ClipboardContentError` ("no desktop session") at once, not after 10 s and not `None` | slice 1 | observed: tests/test_wait_for_kind_failures.py::test_linux_without_session_raises_at_once (fake_platform linux, no sleep, clock unchanged) |
| E8.1 | `wait_for_kind("rtf", timeout=1)` → `ClipboardContentError` before the clipboard is observed | slice 1 | observed: tests/test_wait_for_kind_failures.py::test_invalid_argument_raises_before_any_observation (kind rtf) |
| E8.2 | `wait_for_text_change(timeout=-1)` → `ClipboardContentError` before the clipboard is observed | slice 2 | |
| E8.3 | `wait_for_kind("text", timeout=float("inf"))` → `ClipboardContentError` before the clipboard is observed | slice 1 | observed: tests/test_wait_for_kind_failures.py::test_invalid_argument_raises_before_any_observation (timeout inf) |
| E8.4 | `wait_for_kind("text", timeout=1, interval=0)` → `ClipboardContentError` before the clipboard is observed | slice 1 | observed: tests/test_wait_for_kind_failures.py::test_invalid_argument_raises_before_any_observation (interval 0) |
| E9 | `wait_for_text_change(timeout=0)` → reads the baseline once and returns `None` | slice 2 | |
