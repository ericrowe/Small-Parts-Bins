# Plan 009 — Re-evaluate glass slide capture and material options

- Status: Queued
- Priority: 1
- Depends on: Plan 001 completion for orderly activation; cassette investigation can reuse v0.6 parts
- Created: 2026-08-27
- Started: Not started
- Completed: Not completed
- Git start: Not committed
- Git completion: Not completed

## Triggering physical feedback

The Firmest 0.45 PETG retainer provided the best hold within the v0.6 snap-fit
ladder, but subsequent handling shows that the glass can still be knocked out
easily. The existing retainer is therefore an experimental best-of-ladder result,
not an adequate production capture method.

## Outcome

Develop and physically validate a more positive, replaceable pane-capture system
that resists accidental knockout and can accommodate at least two practically
useful pane thicknesses or materials without redesigning the lid's primary
capture geometry.

## Requirements

- Mechanically enclose and support every pane edge without a press fit.
- Prevent pane escape under a documented impact, rollover, and handling test.
- Keep the pane replaceable without levering tools against glass.
- Investigate end-loading geometry in which the pane slides into continuous lid
  rails and is blocked by a positive, removable end-retention mechanism.
- Compare at least one alternative positive-capture concept if it can be tested
  economically; do not select end-loading without evidence.
- Accommodate measured standard microscope slides and at least one transparent
  plastic pane candidate through the same main capture interface. Interchangeable
  non-destructive spacers or compliant backing elements are acceptable if the
  lid and edge-retention geometry remain common.
- Preserve top visibility, the 34 × 10 mm label zone where practical, hinge and
  latch access, safe edge coverage, and clearance below the carrier engagement
  plane.
- Keep the glass surface recessed or otherwise protected from stacking contact.

## Material questions to resolve

- Measure the actual glass batch rather than relying on nominal slide sizes.
- Select transparent plastic test panes based on availability, clarity, scratch
  behavior, impact resistance, thickness consistency, and safe edge finishing.
- Record whether plastic introduces unacceptable scratching, bowing, static,
  chemical compatibility, or visibility loss in routine small-parts use.
- Treat glass as the current baseline and plastic as an experimental alternative
  until comparative testing is complete.

## Non-goals

- Do not change cassette body height, footprint, divider geometry, or carrier
  geometry except where a lid envelope check is necessary.
- Do not assume a thicker or more flexible snap retainer solves positive capture.
- Do not claim universal compatibility with unspecified slide dimensions.
- Do not force, bend, drill, or impact glass during insertion or removal.

## Reusable parts and compatibility

- Preserve the v0.6 body, verified hinge geometry, 1.75 mm pin, latch relationship,
  label format, and carrier envelope if the new lid can remain compatible.
- Existing glass panes may be reused only if measured, undamaged, and compatible
  with the selected test geometry.
- Existing snap retainers remain calibration evidence but are expected to be
  superseded for production containment.
- Version every changed lid, retainer, end gate, spacer, or pane specification;
  do not overwrite v0.6.

## Implementation steps and test prints

1. [ ] Define and document a repeatable baseline knockout test using the current
   v0.6 lid, installed measured glass, and Firmest 0.45 PETG retainer. Use a safe
   enclosure and record impact direction, orientation, cycles, and outcome.
2. [ ] Measure representative glass panes and obtain/measure at least one clear
   plastic pane candidate with a meaningfully different thickness.
3. [ ] Convert the physical failure into requirements for edge engagement,
   positive end blocking, thickness accommodation, removal access, and protected
   top-surface height.
4. [ ] Develop a concept matrix including end-loaded rails with a removable end
   gate and at least one credible alternative. Evaluate escape paths, print
   orientation, wear, debris traps, glass loading, part count, and compatibility.
5. [ ] Generate low-material coupons reproducing the complete pane cross-section,
   end-entry geometry, rail support, thickness accommodation, and named retention
   variants. Clearly mark every coupon and removable component.
6. [ ] Print coupons and first test them with dimensionally representative
   non-glass blanks. Reject fits that require forcing, sharp bending, prying, or
   dependence on friction alone.
7. [ ] Test surviving coupons with measured glass and plastic panes. Evaluate
   insertion, positive end retention, rattle, bowing, removal, rail wear, edge
   protection, and repeatability across pane thicknesses.
8. [ ] Apply the documented knockout/rollover protocol inside a protective
   enclosure. Compare escape, damage, and movement directly with the v0.6
   Firmest 0.45 baseline.
9. [ ] Select the simplest positive-capture design that passes, then generate a
   complete versioned lid and all required gates, spacers, or retainers.
10. [ ] Audit every exported STL for integrity, topology, degenerates, floating
    parts, support requirements, glass clearances, hinge/latch sections, closed
    envelope, and carrier engagement-plane clearance.
11. [ ] Print and assemble at least one complete lid with glass and one with the
    selected plastic pane. Reuse a verified body where compatible.
12. [ ] Test normal opening, latch closure, hinge sweep, pane replacement,
    repeated end-retainer cycles, loaded rollover, carrier removal, and stacked-
    carrier clearance for both pane materials.
13. [ ] Record the selected pane/capture combination, alternative material result,
    compatibility, required reprints, rejected concepts, and residual risks.

## Test safety

- Wear eye protection and contain the specimen during knockout or rollover tests.
- Inspect glass before and after every test; immediately retire chipped, cracked,
  deeply scratched, or edge-damaged panes.
- Use non-glass blanks while tuning fit and reserve glass for already-safe coupon
  variants.
- Never force a pane or use its exposed face as a reaction surface for tools.

## Acceptance criteria

- [ ] The new system prevents pane escape in the documented test that exposes
  the v0.6 Firmest 0.45 weakness.
- [ ] Retention comes from positive geometry, not friction or uncontrolled
  flexible preload alone.
- [ ] One common lid capture interface successfully retains the measured glass
  and at least one tested plastic/thickness alternative.
- [ ] Each pane can be inserted and replaced without forcing, glass prying, or
  damage to reusable lid components.
- [ ] The end gate or other closure remains positively retained after repeated
  access cycles and cannot enter the cassette cavity as a loose part.
- [ ] Visibility, labeling, hinge, latch, closed envelope, and stacked-carrier
  clearance remain acceptable.
- [ ] All printable STLs pass the complete exported-artifact audit.
- [ ] Documentation clearly identifies which material/capture combinations are
  physically verified and which remain experimental.

## Validation record

Record pane material, supplier/description, measured width/length/thickness,
coupon identifier, print material/settings, insertion/removal observations,
retention cycles, knockout protocol and results, scratches or damage, final
envelope, carrier clearance, and specimen disposition.

## Stop and rollback conditions

- Stop immediately for chipped or cracked glass, unsafe ejection, rail fracture,
  or any test requiring force against the pane.
- If no common-thickness interface passes, prefer a positively retained,
  replaceable material-specific spacer over weakening edge capture.
- Keep v0.6 as historical test evidence but do not restore its snap retainer as
  the production recommendation unless new physical evidence resolves the
  knockout failure.

## Archive handoff

The walkthrough must compare the old and new escape paths, show the entry and
positive-retention mechanism, list tested pane dimensions/materials, provide the
safe replacement procedure and knockout evidence, state body/carrier compatibility,
and identify all lids or retainers that must be reprinted or retired.

