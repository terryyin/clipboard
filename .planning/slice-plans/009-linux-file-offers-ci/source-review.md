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
| C1 | Replace the owner-held Linux desktop prerequisite with observed GitHub Actions evidence. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C2 | Make the experiment gated. | slice 1 | observed: native pytestmark and probe main require both gates; job explicitly opts in |
| C3 | Make the experiment repeatable. | slice 1 | observed: workflow creates isolated D-Bus/Xvfb/Openbox session; three fresh destinations in the successful job |
| C4 | Use Thunar as the named file manager. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C5 | Run the experiment on X11. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C6 | Run the desktop under Xvfb. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C7 | Test a helper-made, single-format `text/uri-list` offer. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d URI round: only TARGETS and text/uri-list; exact independent payload read |
| C8 | Test a helper-made, single-format `x-special/gnome-copied-files` offer. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d both GNOME rounds: only TARGETS and x-special/gnome-copied-files; copy envelope |
| C9 | Observe whether each candidate offer can be pasted as copies after its writer exits. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C10 | Record each candidate MIME type’s observed outcome. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C11 | Record the actual destination files. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C12 | Check destination contents against the source bytes. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C13 | Record that the original source files remain unchanged. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C14 | Exercise Unicode filenames. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C15 | Exercise filenames containing spaces. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C16 | Record evidence about clipboard lifetime after writer exit. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C17 | Record environment versions. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d environment JSON; docs/file-manager-offers.md measured floors |
| C18 | State the precise limits of the evidence. | slice 1 | observed: docs/file-manager-offers.md evidence scope and probe evidence_limit: helper offers, Thunar/X11 only |
| C19 | Include a control proving that the Paste action works. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d positive-before and positive-after each copied both files |
| C20 | Include a control proving that the check assertions discriminate. | slice 1 | observed: 5 desktop-free oracle/startup tests passed; native no-paste control rejected every empty destination |
| C21 | Publish the workflow on a reviewable branch. | slice 1 | observed: published branch codex/verify-linux-file-offers-ci contains 14e9f6d; job checkout names exact SHA |
| C22 | Run the workflow in GitHub Actions. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| C23 | Record the result where the existing copy-files plan can consume it. | slice 1 | observed: .planning/slice-plans/008-copy-files/PLAN.md slice2 done with Actions evidence; slice5 retains actual API child-to-Thunar proof |
| Q1 | The outcome is observational; neither candidate format is promised to succeed. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| Q2 | An unavailable desktop must fail the experiment. | slice 1 | observed: initial run41459762923 failed on unavailable window before offers; main records error and native test requires exit0 |
| Q3 | Broken automation must fail the experiment. | slice 1 | observed: real child exit2 regression and initial failed Actions launch; errors propagate without MIME conclusion |
| Q4 | Those experiment failures must not be reported as clipboard incompatibility. | slice 1 | observed: initial report ok:false rounds:[]; only valid completed URI round can report bounded no copies observed |
| Q5 | Those experiment failures must not be silently skipped. | slice 1 | observed: both opted-in gates run assertions; actual failed launch failed CI and aggregate rather than skipping |
| Q6 | The original uncertainty preserves both possibilities: a lone `text/uri-list` offer may suffice, or `x-special/gnome-copied-files` may be required. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| J1 | The triggering request is whether GitHub Actions CI can replace the report’s two manual pastes on an owner-held Linux desktop. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| J2 | A writer offers two source files whose names exercise Unicode and spaces, then exits. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| J3 | Thunar pastes into an empty destination. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| J4 | The observation records destination files with matching bytes and unchanged originals. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| J5 | The experiment records an outcome for each candidate MIME type. | slice 1 | observed: Actions 41460755116/job/125328858098 at 14e9f6d rounds JSON: both files copied with exact bytes, sources unchanged, writer exited before Paste; docs records scope |
| X1 | Implementing `copy_files`. | slice 1 | observed: aggregate git diff has no library/dependency changes; docs and plan008 distinguish helper proof from API and other platforms |
| X2 | Completing `SEED-001#copy-files`. | slice 1 | observed: aggregate git diff has no library/dependency changes; docs and plan008 distinguish helper proof from API and other platforms |
| X3 | Generalizing the X11/Thunar evidence to Wayland. | slice 1 | observed: aggregate git diff has no library/dependency changes; docs and plan008 distinguish helper proof from API and other platforms |
| X4 | Generalizing the evidence to other file managers. | slice 1 | observed: aggregate git diff has no library/dependency changes; docs and plan008 distinguish helper proof from API and other platforms |
| X5 | Changing the public API. | slice 1 | observed: aggregate git diff has no library/dependency changes; docs and plan008 distinguish helper proof from API and other platforms |
| X6 | Changing runtime dependencies. | slice 1 | observed: aggregate git diff has no library/dependency changes; docs and plan008 distinguish helper proof from API and other platforms |
