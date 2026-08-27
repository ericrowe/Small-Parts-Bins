# Plan pipeline

The project may execute multiple defined plans concurrently while retaining a
prioritized queue for work that has not started:

`Idea → Queued plan → In-work execution → Archive`

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
no implementation work and must use `Status: Queued`.

## Prioritization

[`PRIORITIES.md`](PRIORITIES.md) is the authoritative execution order for queued
plans and the only location where priority ranks are stored. Permanent plan
numbers describe creation history and do not determine priority. Do not add
priority fields to individual plan files. The priority table must list every
queued plan exactly once in a contiguous sequence beginning at 1.

Prioritize known safety/containment failures first, followed by dependency
blocking, rework avoidance, information gain, user value, and finally readiness
and print cost. Reassess and commit the priority table whenever physical
feedback reveals a failure, dependencies change, or project goals change.
Record the reason in that single file; never renumber existing plan files merely
to reorder execution.

## 3. Execution

Move a selected plan from `Queued/` directly into `Plans/` and set its status to
`Executing` before changing implementation files. Remove it from the priority
table and renumber the remaining queued ranks in `PRIORITIES.md` in the same
transition.

Multiple numbered plans may be in work directly inside `Plans/`. Concurrency is
appropriate when work is independent or when one plan is waiting for a print,
measurement, material, or other external result. For example, Plan 009 glass-
capture concepts and Plan 003 divider concepts may progress while Plan 001 waits
for carrier prints.

Concurrency does not waive dependencies. Each plan must state which steps may
proceed provisionally and which steps are gated by another plan's verified
result. Do not freeze dependent dimensions, release geometry, or claim physical
validation before the prerequisite evidence exists.

Keep concurrent work traceable:

- Update each plan's status and checklist independently.
- Use plan-numbered, focused Git commits; avoid combining unrelated plan changes
  in one commit.
- Record shared-interface decisions in every affected plan and update queue
  priorities if the dependency graph changes.
- A plan waiting on a physical result remains `Executing — waiting on ...`; it
  does not prevent eligible work in another active plan.

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
6. After that archive commit, continue other in-work plans and activate further
   eligible queued work only when the dependency and workload rules above permit.

Archived plans and walkthroughs are immutable historical records. Corrections
must be appended and committed, not silently rewritten.

Run `python3 Plans/check_pipeline.py` from the repository root before committing
a plan transition. It verifies active and queued filenames, unique plan numbers,
the single-source priority table, contiguous queued ranks, and completed
plan/walkthrough pairs.
