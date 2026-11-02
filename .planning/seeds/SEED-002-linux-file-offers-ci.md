---
id: SEED-002
status: active
planted: 2026-11-02
planted_during: Request to verify copy-files interoperability with GitHub Actions
trigger_when: now
scope: One bounded Linux file-manager interoperability experiment
---

# Verify Linux clipboard file offers in GitHub Actions

<a id="linux-file-offers-ci"></a>
### Verify Linux file offers in CI

**Identity:** SEED-002#linux-file-offers-ci
```json dough-story-state
{"schemaVersion":1,"refinement":"refined","approach":"planned","plan":"../slice-plans/009-linux-file-offers-ci/PLAN.md","assessment":"ready","reasons":[],"basis":{"document":"26c6979602696a95ba32a6b16ad7ad56060ed5e59282c5cf8d94d99de31ef0c2","plan":"f096be9fee34b03fc032418cdf09a87627db8c65722fe5188833ec9f3a604747"}}
```

**Goal:** Replace the owner-held Linux desktop prerequisite with observed
GitHub Actions evidence about which single-format clipboard offer a named
Linux file manager can paste as copies after the writer exits.

**Scope:** A gated, repeatable experiment with Thunar on X11 under Xvfb,
using helper-made `text/uri-list` and `x-special/gnome-copied-files` offers.
Record actual destination files and unchanged sources, Unicode and spaces,
writer-exit lifetime, environment versions, and the precise evidence limit.
Include a control proving the Paste action and check assertions discriminate.
Publish the workflow on a reviewable branch and run it in GitHub Actions.
Record the result where the existing copy-files plan can consume it.

**Excluded:** Implementing `copy_files`, completing SEED-001#copy-files,
generalizing X11/Thunar evidence to Wayland or other file managers, and changing
the public API or runtime dependencies.

**Key examples:** Two Unicode/space-named source files offered by a process
that exits are pasted by Thunar into an empty destination with matching bytes
and unchanged originals. Each candidate MIME type has its observed outcome
recorded; an unavailable desktop or broken automation fails the experiment
instead of being reported as clipboard incompatibility or silently skipped.
