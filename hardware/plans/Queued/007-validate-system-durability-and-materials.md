# Plan 007 — Validate system durability and materials

- Status: Queued
- Depends on: Plans 004–006 production-candidate geometry
- Created: 2026-08-27
- Started: Not started
- Completed: Not completed
- Git start: Not committed
- Git completion: Not completed

## Outcome

Demonstrate that representative production candidates remain safe and usable
through repeated operation, loaded handling, and supported material/process
variation.

## Requirements

- Cover the smallest cassette, at least one larger cassette, a divided cassette,
  the baseline carrier, and at least one mixed-layout carrier.
- Test ASA and PETG body/lid prototypes where practical; retain PETG as the
  preferred flexible-retainer material.
- Use measured delivered glass and reject chipped or oversize panes.
- Define cycle counts and pass/fail observations before testing begins.
- Preserve complete traceability from each specimen to material and slicer
  settings.

## Non-goals

- Do not claim formal safety certification or universal material performance.
- Do not destructively test every retained successful prototype.
- Do not tune dimensions by slicer scaling.

## Reusable parts and compatibility

- Use production-source coupons and parts so durability results apply to the
  intended releases.
- Preserve at least one uncycled reference specimen of each critical fit.
- Recalibrate any compliant pane-capture spacers or removable retention parts
  when material or process changes; do not reinstate friction-only snap capture.

## Implementation steps and test prints

1. [ ] Define the test matrix, specimen count, representative loads, cycle
   counts, measurement intervals, and objective failure criteria.
2. [ ] Print compact hinge, latch, divider, retainer, and lip coupons in each
   supported material/process combination before full specimens.
3. [ ] Measure coupons, eliminate failed combinations, and print the minimum
   representative complete cassettes and carriers.
4. [ ] Cycle hinges and latches while recording force changes, pin migration,
   knuckle wear, cracking, and closure retention.
5. [ ] Cycle glass retainers and inspect rail recovery, lug wear, glass movement,
   and safe removal behavior with the correct glass installed.
6. [ ] Cycle divider installation/removal and repeat the documented rollover
   transfer protocol before and after wear.
7. [ ] Cycle cassette insertion/removal and carrier stacking while checking
   throat wear, lip damage, rattle, binding, and glass contact.
8. [ ] Perform controlled loaded tip-over and normal handling tests on individual
   cassettes and stacked carriers.
9. [ ] Re-measure critical dimensions and compare materials and settings against
   their uncycled references.
10. [ ] Document accepted material/process windows and create new ideas for any
    geometry changes rather than silently modifying released designs.

## Acceptance criteria

- [ ] No tested cassette opens unintentionally during the defined handling tests.
- [ ] Hinge pins remain contained and functional through the defined cycles.
- [ ] Glass and retainers remain securely captured without chips or forced fits.
- [ ] Divider retention and transfer behavior remain within the documented
  acceptance threshold after cycling.
- [ ] Carriers remain stackable and removable without functional damage.
- [ ] Supported material/settings combinations and rejected combinations are
  explicitly recorded without extrapolation.

## Validation record

Maintain specimen IDs, source revision, print settings, initial/final dimensions,
cycle logs, transfer counts, failures, images, and disposition for every sample.

## Stop and rollback conditions

- Stop a test immediately if glass chips, cracks, becomes loaded by tooling, or
  requires levering for removal.
- Quarantine any configuration with progressive hinge, latch, lip, or divider
  failure and keep it out of the production baseline.

## Archive handoff

The walkthrough must include the test matrix, specimen traceability, results by
material, accepted process assumptions, failure modes, and excluded variants.
