# Planning records

Terry approved these conventions on 2026-11-02 while commissioning the initial
clipboard domain research and product backlog.

- The ordered product queue is [PRODUCT-BACKLOG.md](PRODUCT-BACKLOG.md).
- Story homes are `seeds/SEED-NNN-<slug>.md`. Allocate identities using the
  installed product-backlog tool's `identity-evidence` report, including history;
  never reuse a deleted identity. Numbering starts at `001` when no identity has
  ever been used.
- Each story has an explicit lowercase kebab-case HTML anchor and an
  `**Identity:** SEED-NNN#<anchor>` line. Titles and paths may change without
  changing that recorded identity.
- Seed metadata records `id`, `status`, `planted`, `planted_during`,
  `trigger_when`, and `scope`. `dormant` means no current selection; `active`
  means the seed contains selected queued or taken work. These describe the
  seed, not implementation progress. `scope` describes the whole set and its
  rough effort distribution.
- Effort bands are comparative hypotheses: **S** is one bounded behavior;
  **M** includes several cases or integrations; **L** has substantial
  cross-platform uncertainty. Include confidence and assumptions. These are
  neither elapsed-time promises nor execution plans.
- Keep research in `research/`, with dates, source links, observations,
  recommendations, and unverified assumptions distinguished.
- Future executable plans live in `slice-plans/<NNN>-<slug>/PLAN.md`, numbered
  above the highest historical plan number. Writing or queueing a story does
  not authorize implementation. Decomposed stories start `not-refined` with
  an `unselected` execution approach, recorded by the installed tooling.

Use the installed `dough-product-backlog` operations for queue membership,
ordering, direction, identity evidence, and structured preparation facts.
Keep the queue to exact linked titles and identities; keep scope and examples
in each story's canonical section.
