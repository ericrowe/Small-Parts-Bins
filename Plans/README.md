# Plan pipeline

The project executes one defined plan at a time while allowing future plans to
be developed in a non-executing queue:

`Idea → Queued plan → Active execution → Archive`

## 1. Idea

Record new work in `../IDEAS.md`. Keep each idea under three sentences. Ideas
may be clarified or combined in the inbox, but implementation does not begin
until one idea is promoted into a numbered plan.

## 2. Plan

Create a Markdown file in `Queued/` using the next unused number and a short
kebab-case name, such as `Queued/009-design-carrier-removal-feature.md`. Copy
`_templates/plan.md`, replace every placeholder, and develop the idea into a
bounded implementation plan with requirements, non-goals, ordered steps, test
prints, validation, and rollback/reuse notes.

Plan numbers are permanent and never reused. `README.md` and `_templates/` do
not count as plans. Queued plans may be developed in advance, but they authorize
no implementation work and must use `Status: Queued`. There must never be more
than one numbered Markdown file directly inside `Plans/`.

## Prioritization

[`PRIORITIES.md`](PRIORITIES.md) is the authoritative execution order for queued
plans. Permanent plan numbers describe creation history and do not determine
priority. Each queued plan must declare one unique positive `Priority` value,
and the current priorities must form a contiguous sequence beginning at 1.

Prioritize known safety/containment failures first, followed by dependency
blocking, rework avoidance, information gain, user value, and finally readiness
and print cost. Reassess and commit the priority table whenever physical feedback
reveals a failure, dependencies change, or project goals change. Record the
reason; never renumber existing plan files merely to reorder execution.

## 3. Execution

After the current active plan is archived, move the priority-1 eligible plan
from `Queued/` directly into `Plans/`, remove its queue-only priority field, and
set its status to `Executing` before changing implementation files. Renumber the
remaining priority ranks and update `PRIORITIES.md` in the same transition.
Work through the active plan's numbered steps in order, update the checklist as
evidence is produced, and record important decisions and physical results.

Use Git to preserve continuity:

1. Commit the accepted plan before implementation with a message beginning
   `plan-NNN:`.
2. Make focused implementation checkpoints that reference the same plan
   number.
3. Do not rewrite or delete tested revisions; record replacements explicitly.
4. Before archiving, require a clean validation result or clearly document
   every remaining limitation.

## 4. Archive

When every acceptance criterion is satisfied:

1. Set the plan status to `Complete` and add its completion date and final
   commit references.
2. Complete the required documentation reconciliation checklist in `AGENTS.md`,
   including the top-level project README and all applicable release records.
3. Move it into `Completed/`, prefixing the original filename with the ISO
   completion date: `YYYY-MM-DD-NNN-name.md`.
4. Create a detailed walkthrough beside it named
   `YYYY-MM-DD-NNN-name-walkthrough.md`, using the walkthrough template.
5. Commit the move and walkthrough with a message beginning `plan-NNN:`.
6. Only after that archive commit may a queued plan be activated or the next
   inbox idea become a plan.

Archived plans and walkthroughs are immutable historical records. Corrections
must be appended and committed, not silently rewritten.

Run `python3 Plans/check_pipeline.py` from the repository root before committing
a plan transition. It verifies active and queued filenames, the single-active-
plan rule, unique numbers, contiguous queue priorities, and completed
plan/walkthrough pairs.
