# Queued-plan priorities

Plan numbers are permanent historical identifiers, not execution priority. This
file is the authoritative order for selecting the next queued plan after the
currently in-work plans. Priority ranks exist only in this file; never copy them
into individual plan documents.

## Prioritization method

Review every queued plan against these factors, in order:

1. **Safety and containment risk:** known failures involving glass, spills,
   sharp parts, or unstable loaded assemblies take precedence.
2. **Dependency blocking:** work needed by several later plans ranks ahead of
   work that affects only one optional variant.
3. **Rework avoidance:** resolve uncertain interfaces before optimizing or
   duplicating geometry that depends on them.
4. **Evidence and information gain:** prefer focused tests that can eliminate
   major design uncertainty at reasonable print cost.
5. **User value:** prioritize features that materially improve routine storage,
   handling, visibility, capacity, or configuration.
6. **Readiness and cost:** when higher factors are comparable, prefer work that
   can be tested with available parts and smaller prints.

Priority is reassessed whenever physical feedback reveals a new failure, a plan
changes a downstream dependency, or the user changes project goals. Changing
priority does not renumber plan files. Record the reason and date below, edit
only this table, run the pipeline checker, and commit the change.

Several plans may be in work simultaneously. The table orders work that remains
queued; it does not rank active plans against one another. A lower-ranked queued
plan may be activated alongside higher-ranked work when its current steps are
independent, capacity is available, and all dependency-gated decisions remain
explicitly provisional.

## Current order — 2026-08-28

| Priority | Plan | Reason |
|---:|---|---|
| 1 | 003 — Develop optional cassette dividers | Adds the requested small-part partitions after the final internal height and lid interface are available. |
| 2 | 004 — Finalize the smallest cassette and carrier | Integrates the verified carrier, glass capture, height, grab features, and divider work into the smallest production candidate. |
| 3 | 005 — Develop the larger cassette family | Extends the verified smallest interfaces without propagating unresolved geometry. |
| 4 | 006 — Develop mixed-layout carriers | Requires physical envelopes from the completed cassette family. |
| 5 | 007 — Validate system durability and materials | Exercises production-candidate cassettes and carriers after their interfaces stabilize. |
| 6 | 008 — Prepare and archive the production baseline | Final integration and release work; depends on all prior physical evidence. |

Plan 001 (14U carrier stack validation) is completed and archived. Plan 002 is
currently active, establishing the vertical tolerance budget and optimizing
cassette body height for maximum internal capacity. The next queued plan is Plan 003.
