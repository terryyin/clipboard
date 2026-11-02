# Source-only review

Reviewer launch: collaboration agent `/root/source_review`, `fork_turns=none`.
The reviewer received only the user's CI verification request and the original
Goal, Scope, Excluded, and Key examples from
`SEED-002-linux-file-offers-ci.md`. It was instructed to read no project files,
change nothing, and derive numbered individual source commitments, preserving
qualifications, journeys, alternatives, and exclusions without judging slices
or acceptance. The original source text remains in the linked seed; the
reviewer's returned clauses are recorded verbatim below, with category
prefixes preserving their individual numbering.

## Commitments

| Id | Source commitment | Slice | Observation or obligation |
| --- | --- | --- | --- |
| C1 | Replace the owner-held Linux desktop prerequisite with observed GitHub Actions evidence. | slice 1 | G1 |
| C2 | Make the experiment gated. | slice 1 | observed: tests/test_file_manager_offers_native_linux_x11.py pytestmark and probe main enforce CLIPBOARD_NATIVE_PROBE; CI opts in explicitly |
| C3 | Make the experiment repeatable. | slice 1 | G1 |
| C4 | Use Thunar as the named file manager. | slice 1 | G1 |
| C5 | Run the experiment on X11. | slice 1 | G1 |
| C6 | Run the desktop under Xvfb. | slice 1 | G1 |
| C7 | Test a helper-made, single-format `text/uri-list` offer. | slice 1 | G1 |
| C8 | Test a helper-made, single-format `x-special/gnome-copied-files` offer. | slice 1 | G1 |
| C9 | Observe whether each candidate offer can be pasted as copies after its writer exits. | slice 1 | G1 |
| C10 | Record each candidate MIME type’s observed outcome. | slice 1 | G1 |
| C11 | Record the actual destination files. | slice 1 | G1 |
| C12 | Check destination contents against the source bytes. | slice 1 | G1 |
| C13 | Record that the original source files remain unchanged. | slice 1 | G1 |
| C14 | Exercise Unicode filenames. | slice 1 | G1 |
| C15 | Exercise filenames containing spaces. | slice 1 | G1 |
| C16 | Record evidence about clipboard lifetime after writer exit. | slice 1 | G1 |
| C17 | Record environment versions. | slice 1 | G1 |
| C18 | State the precise limits of the evidence. | slice 1 | G1 |
| C19 | Include a control proving that the Paste action works. | slice 1 | G1 |
| C20 | Include a control proving that the check assertions discriminate. | slice 1 | G1 |
| C21 | Publish the workflow on a reviewable branch. | slice 1 | G1 |
| C22 | Run the workflow in GitHub Actions. | slice 1 | G1 |
| C23 | Record the result where the existing copy-files plan can consume it. | slice 1 | G2 |
| Q1 | The outcome is observational; neither candidate format is promised to succeed. | slice 1 | G1 |
| Q2 | An unavailable desktop must fail the experiment. | slice 1 | G1 |
| Q3 | Broken automation must fail the experiment. | slice 1 | G1 |
| Q4 | Those experiment failures must not be reported as clipboard incompatibility. | slice 1 | G1 |
| Q5 | Those experiment failures must not be silently skipped. | slice 1 | G1 |
| Q6 | The original uncertainty preserves both possibilities: a lone `text/uri-list` offer may suffice, or `x-special/gnome-copied-files` may be required. | slice 1 | G1 |
| J1 | The triggering request is whether GitHub Actions CI can replace the report’s two manual pastes on an owner-held Linux desktop. | slice 1 | G1 |
| J2 | A writer offers two source files whose names exercise Unicode and spaces, then exits. | slice 1 | G1 |
| J3 | Thunar pastes into an empty destination. | slice 1 | G1 |
| J4 | The observation records destination files with matching bytes and unchanged originals. | slice 1 | G1 |
| J5 | The experiment records an outcome for each candidate MIME type. | slice 1 | G1 |
| X1 | Implementing `copy_files`. | slice 1 | observed: git diff: no clipboard/ or dependency changes; copy_files stays planned; probe evidence_limit names Thunar/X11 only |
| X2 | Completing `SEED-001#copy-files`. | slice 1 | observed: git diff: no clipboard/ or dependency changes; copy_files stays planned; probe evidence_limit names Thunar/X11 only |
| X3 | Generalizing the X11/Thunar evidence to Wayland. | slice 1 | observed: git diff: no clipboard/ or dependency changes; copy_files stays planned; probe evidence_limit names Thunar/X11 only |
| X4 | Generalizing the evidence to other file managers. | slice 1 | observed: git diff: no clipboard/ or dependency changes; copy_files stays planned; probe evidence_limit names Thunar/X11 only |
| X5 | Changing the public API. | slice 1 | observed: git diff: no clipboard/ or dependency changes; copy_files stays planned; probe evidence_limit names Thunar/X11 only |
| X6 | Changing runtime dependencies. | slice 1 | observed: git diff: no clipboard/ or dependency changes; copy_files stays planned; probe evidence_limit names Thunar/X11 only |
