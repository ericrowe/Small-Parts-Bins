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

## 3. Execution

After the current active plan is archived, move the next selected file from
`Queued/` directly into `Plans/` and set its status to `Executing` before
changing implementation files. Work through its numbered steps in order,
update the checklist as evidence is produced, and record important decisions
and physical results in the plan.

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
plan rule, unique numbers, and completed plan/walkthrough pairs.
