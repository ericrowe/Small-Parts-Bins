# Queued-plan priorities

Plan numbers are permanent historical identifiers, not execution priority. This
file is the authoritative order for selecting the next queued plan after the
active plan is completed and archived.

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
priority does not renumber plan files or authorize parallel execution. Record
the reason and date below, update each queued plan's `Priority` field, run the
pipeline checker, and commit the change before activating a different plan.

## Current order — 2026-08-27

| Priority | Plan | Reason |
|---:|---|---|
| 1 | 009 — Re-evaluate glass slide capture and material options | The Firmest 0.45 retainer is the best tested snap fit but the glass can still be knocked out easily. This is a containment and glass-safety failure that affects every cassette size and should be resolved before height or family optimization. |
| 2 | 002 — Optimize cassette and carrier height | Establishes the shared vertical envelope after the lid/capture interface is known. |
| 3 | 003 — Develop optional cassette dividers | Adds the requested small-part partitions after the final internal height and lid interface are available. |
| 4 | 004 — Finalize the smallest cassette and carrier | Integrates the verified carrier, glass capture, height, and divider work into the smallest production candidate. |
| 5 | 005 — Develop the larger cassette family | Extends the verified smallest interfaces without propagating unresolved geometry. |
| 6 | 006 — Develop mixed-layout carriers | Requires physical envelopes from the completed cassette family. |
| 7 | 007 — Validate system durability and materials | Exercises production-candidate cassettes and carriers after their interfaces stabilize. |
| 8 | 008 — Prepare and archive the production baseline | Final integration and release work; depends on all prior physical evidence. |

Plan 001 remains the sole active plan. Unless new evidence changes this table,
Plan 009 is activated immediately after Plan 001 is completed and archived.

