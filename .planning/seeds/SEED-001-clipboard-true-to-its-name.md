---
id: SEED-001
status: active
planted: 2026-11-02
planted_during: Terry Yin's request to make clipboard true to its name
trigger_when: Selecting the next clipboard library improvement
scope: 11 candidate stories; 4 L, 6 M, 1 S effort hypotheses
---

# SEED-001: Make clipboard true to its name

## Why This Matters

For Python application and automation developers, assembling separate tools
and platform-specific recipes for ordinary clipboard content should change to
dependable exchange with desktop applications through `clipboard`, while
preserving existing text callers and respecting native access restrictions.

The present public surface is text-only. Historical requests for
[image reading](https://github.com/terryyin/clipboard/issues/2) and
[Linux image writing](https://github.com/terryyin/clipboard/issues/5) provide
specific demand. The maintainer explicitly asked for domain research,
decomposition, and queueing, with the near-future direction of making the
project true to its name. When offered text-first ordering, Terry chose
**images and rich content first**. Terry also approved the
[initial planning conventions](../README.md).

The named beneficiary and the initial desktop scope are the proposed framing
retained from that exchange. The value hypothesis is less consumer glue and
more predictable cross-application behavior. The highest-learning hypothesis
is that an image copied by an independent desktop application can be consumed
through one understandable Python contract across the supported desktop set.
User prioritization does not establish the technical feasibility of that
hypothesis.

## Alternatives and Decision

- **Do nothing or defer:** preserves a tiny wrapper but leaves the image
  requests and the maintainer's stated direction unanswered.
- **Smaller change:** improve text documentation and expose more upstream
  helpers. Useful for text users, but it does not deliver images or HTML.
- **Strongest existing-tool alternative:** recommend pyperclip plus Pillow
  and native clipboard recipes. This may be enough for one expert's task,
  but consumers still own inconsistent results, native format mapping,
  installation, and lifetime behavior.
- **Recommended direction:** keep the simple text entry points and add
  explicit, dependable content operations. Reuse existing solutions when they
  satisfy the behavior; choose implementations during refinement/planning.

The alternatives and learning hypotheses above are research recommendations,
not a maintainer-approved backend design. See the
[domain research](../research/2026-11-02-clipboard-domain.md) for evidence,
platform distinctions, reuse candidates, and uncertainty.

## Shared Boundaries

- New desktop content support targets Windows, macOS, Linux X11, and Linux
  Wayland. Each story's refinement must name supported OS/desktop/compositor
  and helper versions, permission behavior, and the proof available for each.
  Do not generalize one compositor's result to all Wayland environments.
- Preserve `copy`, `paste`, and `VERSION` and the supported Python range.
  Keep existing text call sites working; add explicit content operations
  rather than changing `paste()` to return an image, bytes, or filenames.
- Each story owns the smallest end-to-end native integration, installation
  instructions, actionable errors, and tests needed for its own outcome.
  Missing access, denied permission, contention, timeout, absent format, and
  malformed data must not all collapse into an empty result. Respect native
  authorization; do not bypass it through a fallback backend.
- Read operations leave the clipboard unchanged. Invalid write input is
  rejected before replacing current content. Report native transfer failures
  truthfully; do not promise rollback or atomicity across platforms without
  proof. Ordinary clipboard contents are untrusted data, not commands.
- Successful writes must have a documented, tested lifetime, including
  pasting after the writing Python process exits in supported desktop
  sessions. Ownership transfer and serving resources belong to the writer's
  story. Do not require the consuming user to keep an incidental GUI window
  open. No persistence across logout/reboot, history, or cloud-sync guarantee.
- Support is established through independent native producers/consumers,
  appropriate automated checks, and explicit evidence limits. In-memory tests
  remain useful but cannot establish native interoperability. Native manual
  observations are performed only when explicitly requested or required by
  an authorized plan slice.
- No automatic history collection, clipboard payload logging, cloud service,
  keystroke injection, mobile API, or remote clipboard bridge is in scope.

## Story Decomposition

<a id="wait-for-content"></a>

### Wait for clipboard content with bounded cancellation and timeouts

**Identity:** SEED-001#wait-for-content
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Automation developers can wait for a user to copy supported
  content without writing their own unbounded polling loops.
- **Evaluation:** Starting without the requested supported kind, a wait returns
  when another application supplies it; a changed-value wait returns when the
  observed value changes. A deadline or cancellation ends the wait predictably;
  unavailable or denied access fails distinctly from timeout.
- **Value / learning:** Makes interactive automation practical and tests which
  monitoring semantics can be honest across native event and polling models.
- **Boundary:** One bounded wait, scoped to an explicitly supported content
  kind. Specify initial-value behavior, zero/invalid timeout, cancellation,
  clearing, and observation interval during refinement. Changed value does not
  mean every copy event: identical recopy and changes between observations may
  be missed. No global audit log, background watcher by default, or promise of
  lossless event delivery. Permission denial must not cause repeated prompts.
- **Effort hypothesis:** **M**, medium confidence; assumes a bounded observation
  contract is acceptable where native notification support is unavailable.
- **Depends on:** None. The story must include the supported read behavior it
  needs, reusing already delivered content operations when available. Do not
  wait for a hypothetical universal event backend.
- **Safe stopping point:** Callers gain predictable waiting without hidden
  history, payload logging, busy spinning, or stranded monitoring resources.

<a id="x11-clear-packaged-apps"></a>

### Fail fast when packaged apps cannot run the X11 clear helper

**Identity:** SEED-001#x11-clear-packaged-apps
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/016-x11-clear-packaged-apps/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"2137031e56869dc8d64ccd0cc96389ff2c9be5cd265571313a53385502436fef","plan":"997608e7d88c03f3493018b9a14fc5569d9197915172a14e2385061326cff3dc"}}
```

**Goal:** Developers shipping Python apps that call `clipboard.clear()` on
Linux X11 get an immediate, actionable `ClipboardContentError` when their
deployment cannot run the bounded libX11 clear helper, instead of a frozen
app silently launching a second copy of itself (its `sys.executable` is the
app, not a Python interpreter) and the caller waiting out the 10 s helper
bound. Maintainers also gain a packaging check proving that ordinary wheel
and sdist installs ship a helper that actually launches, so the native clear
is not lost in packaging. This keeps SEED-001#clear-clipboard's "a failed
clear is reported" promise honest for packaged deployments.

**Scope:**

- *Required behavior.* On the native Linux X11 clear path (`DISPLAY` only,
  as SEED-001#clear-clipboard selects it), `clear()` raises
  `ClipboardContentError` before starting any child process when either:
  - the runtime is a **recognized frozen runtime**: `sys.frozen` is set and
    truthy (PyInstaller, cx_Freeze, py2exe, py2app set it), even when the
    helper source file happens to be bundled; or
  - the helper script `clipboard/_x11_relinquish.py` is **not a file on the
    filesystem**, as in a zipapp, zipimport or other archive-only install
    (and bundlers that keep modules only in an archive).
  The message is X11-specific (it names Linux X11 clear like the existing
  X11 clear failures), says which of the two conditions applies, and points
  to `set_clipboard_clearer` for supplying a clearer the deployment can run.
- *Required behavior.* The README X11 clear paragraph documents the limit:
  the native X11 clear needs an ordinary installation whose Python
  interpreter can run the shipped helper file; frozen and archive-only apps
  get the error above.
- *Required behavior.* `make test-package` (local and the CI `ubuntu-latest`
  package job), for both the wheel and the sdist, installs the distribution
  in isolation, launches the **installed** helper through the library's own
  launch command (the helper path resolved inside the isolated install, not
  the source tree) with an unusable `DISPLAY`, and verifies its structured
  failure: exit status 3 and one JSON line whose `failure` is `display`
  (libX11 present) or `libx11` (libX11 absent, e.g. macOS). No desktop
  session or X server is needed.
- *Required restriction.* None beyond the guard itself; its reason is that
  launching `sys.executable` in a frozen app runs the app again (unsafe,
  slow) and launching a missing script cannot clear anything.
- *Scope limits.* Ordinary installations keep the bounded helper unchanged
  (same command, timeout, classification and messages). Making frozen or
  archive-only X11 clear work (for example extracting the helper or an
  in-process fallback), guarding other platforms or other helper-launching
  writers, recognizing frozen runtimes that set no `sys.frozen` (they still
  fail fast when the helper file is absent), and reorganizing the native
  clear probes are outside this story. The packaging check proves the
  installed helper launches and reports a failure; native clearing keeps its
  own gated proof.
- *Boundary assumptions.* A caller-supplied clearer
  (`set_clipboard_clearer`) is not guarded. Wayland, macOS, Windows and the
  "no desktop session" path are untouched, including on a frozen runtime.

**Key examples:**

1. A PyInstaller app on X11 (`sys.frozen = True`, `DISPLAY=:0`, no
   `WAYLAND_DISPLAY`) calls `clear()` → `ClipboardContentError` naming Linux
   X11 clear, the frozen runtime and `set_clipboard_clearer`, raised at once;
   no child process starts.
2. A zipapp install on X11 whose `clipboard/_x11_relinquish.py` exists only
   inside the archive calls `clear()` → `ClipboardContentError` naming Linux
   X11 clear, the missing helper file and `set_clipboard_clearer`; no child
   process starts.
3. An ordinary virtualenv install on X11 calls `clear()` → the bounded helper
   runs exactly as today (success, or the existing classified `libx11-6` /
   `DISPLAY` / timeout errors).
4. A frozen app on Wayland, or one that installed its own clearer with
   `set_clipboard_clearer`, calls `clear()` → unaffected by this guard.
5. `make test-package` on the CI Linux runner, wheel then sdist: the
   installed helper, run with an unusable `DISPLAY`, exits 3 printing
   `{"failure": "display", ...}`; on a macOS developer machine it prints
   `{"failure": "libx11", ...}`; a distribution missing the helper, or a
   helper that cannot start, fails the target.

<a id="primary-selection"></a>

### Use the Linux primary selection explicitly

**Identity:** SEED-001#primary-selection
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/017-primary-selection/PLAN.md","assessment":"not-ready","reasons":["Local gate unavailable: ./scripts/dev make check cannot start because the pinned Nix toolchain is not in the local store (1674 derivations to build offline); every slice's make check and slice 1's make test-package wait for the maintainer to authorize online setup, then a fresh green make check"],"basis":{"document":"ebba7de01ba4eea61a1390381a7f7eee3282670efa9789c83cbb7067199d3ab6","plan":"147f89ffc869105076b804b7d8f37367959133b358d0cccbc0062fdaa5c867b3"}}
```

**Goal:** Python users and automation developers on a Linux desktop can take
part in the select-and-middle-click text workflow: read the text the user has
just selected, or offer text for a middle-click paste, without changing what
the ordinary clipboard holds. Today `copy` / `paste` reach only CLIPBOARD, so
such a user has to call `xclip -selection primary` or `wl-paste --primary`
themselves. This adds Linux's second everyday text exchange beside the
ordinary clipboard, and never pretends macOS or Windows have one.

**Scope:**

- *Required behavior.* Two new public functions beside `copy` / `paste`:
  `copy_primary(text)` replaces the PRIMARY selection with `text`, and
  `paste_primary()` returns PRIMARY's text as `str`. Both act on PRIMARY
  only: `copy_primary` leaves CLIPBOARD as it was, and `copy` / `paste` keep
  acting on CLIPBOARD only and leave PRIMARY as it was. `copy_primary`
  applies the same input rules as `copy` (non-`str` values through `str()`;
  text containing `"\x00"` or not UTF-8 encodable is rejected with
  `ClipboardContentError` before PRIMARY is replaced). `paste_primary`
  returns `""` when nothing is selected or the owner offers no text, never
  `None`, with line endings untranslated, as `paste` does. Text written with
  `copy_primary` stays pasteable by middle-click after the Python process
  exits, as `copy` text does.
- *Native paths.* Linux X11 through `xclip -selection primary`; Linux
  Wayland through wl-clipboard's `--primary` (`wl-copy --primary`,
  `wl-paste --primary`), which works only where the compositor offers a
  primary-selection protocol to wl-clipboard. Session choice follows the
  text rule `copy` / `paste` already use (`_text_session_owner`: Wayland
  when `WAYLAND_DISPLAY` is set and both wl-clipboard helpers are on PATH,
  otherwise X11 with `DISPLAY`), so on one session PRIMARY and CLIPBOARD
  text are reached through the same desktop. Reads and writes use the
  10 s bound the Linux text helpers already share.
- *Unsupported never falls back to CLIPBOARD (required restriction).* Every
  case where PRIMARY cannot be reached raises `ClipboardContentError` naming
  the reason, and never reads or writes CLIPBOARD instead: macOS, Windows,
  WSL and other non-Linux platforms ("not available" on that platform); Linux
  with no desktop session; a Wayland compositor whose wl-clipboard reports
  that primary selection is not supported (distinct from "nothing
  selected", which reads `""`); and a session without the owned helper
  (X11 without `xclip`, even where pyperclip could still reach CLIPBOARD
  through `xsel` or Qt; Wayland without wl-clipboard), with an install hint.
  Other helper failures and timeouts raise as `paste` / `copy` do. Reason:
  the story's promise is that the ordinary clipboard is never changed or read
  by mistake; a silent fallback would overwrite what the user copied.
- *Injected text seams do not apply.* `set_text_clipboard_writer` /
  `set_text_clipboard_reader` keep governing `copy` / `paste` only; an
  injected CLIPBOARD writer or reader never receives PRIMARY traffic.
- *Proof.* Gated native probes (`CLIPBOARD_NATIVE_PROBE`) under the existing
  Xvfb + `xclip` and Sway + wl-clipboard CI jobs, with independent
  producers and consumers (`xclip -selection primary|clipboard`,
  `wl-copy` / `wl-paste` with and without `--primary`) and the writer-exit
  lifetime check. Desktop-free default tests cover dispatch, validation,
  absence, the unsupported cases and the no-fallback rule with fake helpers.
  The README names the observed sessions and helper versions. GNOME, KDE,
  other compositors, XWayland bridging of PRIMARY between X11 and Wayland
  clients, and a native compositor without primary-selection support are
  evidence limits unless observed.
- *Scope limits (deferred, not rejected).* Rich data (HTML, images, files)
  on PRIMARY; `inspect` and `clear` of PRIMARY; SECONDARY; the macOS Find
  pasteboard; automatic or optional synchronization between PRIMARY and
  CLIPBOARD; multi-seat routing; waiting for a selection change
  (SEED-001#wait-for-content); a public injection seam for PRIMARY
  (desktop-free tests fake the helpers). A clipboard manager or desktop
  setting that copies PRIMARY into CLIPBOARD (or back) on its own is a
  newer offer by that program, outside this promise; the README names it.
- *Plan:* [017-primary-selection](../slice-plans/017-primary-selection/PLAN.md).

**Key examples:**

1. Linux X11, CLIPBOARD holds `"copied"` and the user has selected
   `"selected"` in a terminal → `paste_primary()` returns `"selected"`;
   `paste()` still returns `"copied"`.
2. Same session → `copy_primary("for middle click")` → an independent
   `xclip -selection primary -o` (or a middle-click) gives
   `"for middle click"`, and `xclip -selection clipboard -o` still gives
   `"copied"`. The same holds after the Python process that wrote it exits.
3. Same session → `copy("new copy")` → `paste()` gives `"new copy"` and
   `paste_primary()` still gives `"selected"`.
4. Linux X11 with nothing owning PRIMARY → `paste_primary()` returns `""`.
5. Linux Wayland on Sway → examples 1–3 hold through `wl-copy --primary` /
   `wl-paste --primary` and their non-primary counterparts.
6. Linux Wayland compositor where wl-clipboard reports primary selection is
   unsupported → `paste_primary()` and `copy_primary("x")` raise
   `ClipboardContentError` saying so; CLIPBOARD is neither read nor
   changed.
7. macOS or Windows → `copy_primary("x")` raises `ClipboardContentError`
   saying PRIMARY is not available on that platform; the clipboard is
   unchanged.
8. Linux X11 session with `xsel` but no `xclip` → `paste()` still works
   through pyperclip, but `paste_primary()` raises naming the missing
   `xclip` with an install hint.
9. `copy_primary("a\x00b")` → `ClipboardContentError` before PRIMARY is
   replaced; the earlier selection is still readable.

<a id="bounded-helper-owner-write"></a>

### Bound every helper-owner clipboard write behind one launcher

**Identity:** SEED-001#bounded-helper-owner-write
```json dough-story-state
{"schemaVersion":1,"refinement":"not-refined","approach":"unselected"}
```

- **For / why:** Python users calling `copy_image` on a Linux desktop whose
  display or compositor stalls get the documented bounded
  `ClipboardImageError` instead of a hang; maintainers keep one rule for
  feeding a background clipboard owner its payload.
- **Evaluation:** With a helper owner that never reads its input,
  `copy_image` of a PNG larger than a pipe buffer (about 64 KiB) fails within
  its documented bound; the text, file-list and image owner writes start
  their helpers through one shared launcher (unlinked temp-file `stdin`,
  detached session) with each caller keeping its own error mapping.
- **Value / learning:** `clipboard/_image_write.py` still writes PNG bytes
  into `stdin=subprocess.PIPE` without a deadline, the pattern that hung
  large text on X11; the text and file-list X11 writers already duplicate the
  temp-file launcher. Whether the image hang reproduces on X11 and Wayland is
  unverified.
- **Boundary:** Helper input feeding and its bound only; no change to session
  selection, offered formats, or public API.
- **Effort hypothesis:** **S**, medium confidence.
- **Depends on:** None.
- **Safe stopping point:** The shared launcher with the image write bounded is
  useful by itself.

## Ordering and Scope Reduction

The global queue follows the maintainer's images/rich-content priority: image
reading, image writing, HTML writing, then HTML reading. Image reading has
direct user demand and a strong reuse candidate, so it tests useful scope
early. HTML writing precedes reading because its paired rich/plain offer
tests the more consequential multi-format assumption. Inspection follows
those concrete workflows; it is not a prerequisite framework project.

File input/output expands to another everyday content type. Text reliability,
clear, waits, and explicit PRIMARY finish the selected ordinary desktop
behaviors. All first seven stories retain their own text compatibility,
failure semantics, native lifetime, and installation obligations; their order
does not postpone those requirements. Priority is not a dependency chain.
No genuine blocking dependency has been identified, so none is recorded.

Effort distribution: **4 L, 6 M, 1 S**, with confidence stated per story. Each
read or write is independently useful; combining both would hide distinct
consumers and proof. These are decomposition hypotheses, not ready execution
plans. Refine one selected story before execution planning, splitting further
if native evidence makes its outcome too large.

If scope must shrink, drop PRIMARY first, then waits, then outbound files,
then inbound files. Stop after any delivered content workflow with its
compatibility and safety obligations complete. Preserve the image/HTML core
unless the maintainer revises the direction; native evidence that invalidates
it requires a scope decision rather than silently reducing platform coverage.

## Open Decisions

No remaining parent-level selection or order decision blocks this decomposition.
The research recommendations and effort hypotheses remain reviewable. Story
refinement must settle concrete supported platform combinations, image value
shapes, HTML context exposure, absence/error results, dependency installation,
and native proof. Those are not implementation decisions made by this seed.

RTF, arbitrary typed binary transfer, snapshot/restore, sensitive-data hints,
a CLI, async streams, history, cloud synchronization, and mobile are unqueued
extension possibilities in the research, not additional selected promises.

## When to Surface

Now, when selecting the first improvement that makes `clipboard` more than a
text wrapper; revisit the ordering after the first independent native image
interoperability evidence.

## Breadcrumbs

- Terry Yin's 2026-11-02 request to research the domain, decompose stories,
  queue them, and set the initial near-future direction.
- Terry's explicit replies: prioritize images/rich content; use the proposed
  planning conventions and comparative S/M/L bands.
- [Domain research and linked primary sources](../research/2026-11-02-clipboard-domain.md).
- [Product backlog](../PRODUCT-BACKLOG.md).
- [Repository contribution constraints](../../AGENTS.md).
