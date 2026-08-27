# Plan 008 — Prepare and archive the production baseline

- Status: Queued
- Depends on: Plans 001–007 completed with accepted physical evidence
- Created: 2026-08-27
- Started: Not started
- Completed: Not completed
- Git start: Not committed
- Git completion: Not completed

## Outcome

Publish a reproducible, audited production baseline containing only clearly
identified verified configurations, with complete build, assembly, compatibility,
and physical-validation documentation.

## Requirements

- Preserve editable generators, binary printable STLs, manifests, assembly
  references, preview images, release notes, and physical-test records.
- Version every geometry and keep all earlier tested releases intact.
- Identify verified, compatible, provisional, superseded, and do-not-print files.
- Lead documentation with what changed, what remains reusable, what must be
  reprinted, and what lacks physical validation.
- Maintain millimetres as source units and retain the measured drawer ceiling.

## Non-goals

- Do not add new geometry features during release preparation.
- Do not rewrite prior test history to make the final release appear cleaner.
- Do not include untested variants as production recommendations.

## Reusable parts and compatibility

- Consolidate the compatibility conclusions of all prior plans without changing
  them unless contradictory evidence is explicitly resolved.
- Preserve successful older bodies, lids, glass, retainers, dividers, pins, and
  carriers wherever the verified geometry permits reuse.

## Implementation steps and confirmation prints

1. [ ] Inventory all source revisions, generated artifacts, physical notes,
   manifests, previews, and Git checkpoints from Plans 001–007.
2. [ ] Define the exact production-baseline matrix of cassette sizes, divider
   configurations, carrier layouts, materials, and compatible components.
3. [ ] Regenerate every baseline artifact from a clean invocation of its checked-
   in source without hand-editing generated files.
4. [ ] Audit every printable binary STL for file integrity, triangle count,
   finite coordinates, degenerates, boundary/non-manifold edges, functional
   sections, unsupported starts, envelope, and packing.
5. [ ] Compare regenerated hashes and dimensions with the intended release and
   investigate every unexplained difference.
6. [ ] Print the smallest sufficient confirmation set spanning each unique
   hinge, latch, divider, glass-retainer, carrier-profile, and layout feature.
7. [ ] Assemble and test the confirmation set using the documented instructions;
   verify that the documentation alone is sufficient to avoid incorrect parts,
   orientations, supports, and unsafe glass handling.
8. [ ] Complete release READMEs, manifests, compatibility tables, print settings,
   assembly steps, labels, diagrams, and troubleshooting guidance.
9. [ ] Mark provisional future sizes/features and move follow-up work into
   `IDEAS.md` without extending this release plan.
10. [ ] Record final Git references, archive Plan 008 with its walkthrough, and
    confirm the repository is clean and the plan pipeline has no active work.

## Acceptance criteria

- [ ] Every recommended printable file is reproducible from checked-in source.
- [ ] Every printable STL passes its complete exported-artifact audit.
- [ ] The confirmation prints cover every unique functional interface and match
  the documented assembly process.
- [ ] Compatibility and reuse guidance is complete and internally consistent.
- [ ] No provisional or failed file can reasonably be mistaken for a verified
  production recommendation.
- [ ] All plan archives have matching dated walkthroughs and final Git references.
- [ ] `python3 Plans/check_pipeline.py` passes after archival.

## Validation record

Record regeneration commands, tool versions, file hashes, audit output,
confirmation-print identities and settings, assembly observations, documentation
corrections, and final repository status.

## Stop and rollback conditions

- Stop release preparation if regeneration changes functional geometry or a
  confirmation print contradicts earlier physical evidence.
- Return the defect to a new bounded plan; do not repair geometry silently inside
  the production-baseline plan.

## Archive handoff

The walkthrough must provide a guided tour of the complete system, explain how
to select and print parts, summarize validation evidence, list known limitations,
and identify the Git commit that constitutes the production baseline.

