# Plan 003 — Develop optional cassette dividers

- Status: Executing
- Depends on: Early concept/coupon work may use the v0.6 cavity; final divider geometry requires Plan 002 verified height and internal cavity
- Created: 2026-08-27
- Started: 2026-08-28
- Completed: Not completed
- Git start: Not committed
- Git completion: Not completed

## Outcome

Provide removable divider configurations for one, two, or three equal cassette
compartments while minimizing transfer of very small parts when a closed
cassette rolls over.

## Requirements

- Support zero dividers, one centered divider, or two equally spaced dividers.
- Positively locate dividers at the floor and side walls so they cannot become
  loose inside a closed cassette.
- Minimize transfer gaps at the floor, walls, and closed-lid interface; complete
  isolation is explicitly not required.
- Permit removal without damaging the body, lid, glass, or divider.
- Avoid interference with the hinge, latch, glass pocket, retainer, label area,
  fingernail relief, and cassette removal features.
- Establish a divider interface that can be repeated or scaled consistently in
  larger cassette sizes.

## Non-goals

- Do not create sealed or liquid-tight compartments.
- Do not change the outer cassette or carrier envelope solely to fit dividers.
- Do not require supports trapped inside divider slots.

## Reusable parts and compatibility

- Prefer a body-only revision so the verified lid, glass, retainer, hinge pin,
  and carrier remain reusable.
- Retain an undivided configuration with the largest practical continuous
  cavity.
- Existing v0.6 bodies remain valid undivided cassettes even if they cannot
  accept the new removable dividers.

## Implementation steps and test prints

1. [ ] Measure the Plan 002 printed cavity and closed lid-to-floor relationship
   at the proposed divider stations.
2. [ ] Select representative small test parts and record their dimensions so
   rollover results are reproducible.
3. [ ] Compare locating concepts such as shallow floor sockets, wall grooves,
   or flexible end features against printability, cleanability, and lost volume.
4. [ ] Generate a compact divider-fit coupon containing the real floor, both
   side-wall interfaces, lid-side clearance, and a ladder of named tolerances.
5. [ ] Print the coupon and test insertion, retention, removal, floor gaps,
   wall gaps, deformation, and rattling.
6. [ ] Generate full-width one-divider and two-divider test bodies using equal
   cavity spacing measured between the functional divider faces.
7. [ ] Audit the exported body and divider STLs, including slot support,
   minimum wall thickness, floating islands, manifold edges, and closed-envelope
   compatibility.
8. [ ] Print one complete cassette body and at least three divider samples so
   zero-, one-, and two-divider configurations can all be exercised.
9. [ ] With the proper lid and glass installed, test closure and shake the
   cassette in every configuration; confirm dividers do not load the glass.
10. [ ] Conduct a documented rollover protocol through multiple orientations
    using a counted quantity of the representative small parts. Record part
    transfers between every adjacent compartment.
11. [ ] Repeat divider removal and installation cycles, checking slot wear,
    divider damage, and retention.
12. [ ] Select the lightest reliable fit, update source dimensions and notes,
    and preserve unsuccessful tolerance variants for future recalibration.

## Acceptance criteria

- [ ] One divider creates two equal usable compartments within documented print
  tolerance; two dividers create three equal usable compartments.
- [ ] Dividers remain located during normal handling and the rollover protocol.
- [ ] Observed transfer is limited and documented; no claim of complete
  isolation is made.
- [ ] No divider contacts or applies force to the installed glass or retainer.
- [ ] The hinge, latch, label, fingernail opening, and carrier fit remain usable.
- [ ] Divider installation/removal does not require destructive flexing or tools
  likely to contact the glass.
- [ ] All printable files pass the complete exported-STL audit.

## Validation record

Record material, nozzle, layers, measured divider/slot dimensions, insertion
force observations, rollover cycle count, test-part dimensions and counts,
transfer counts, and wear after repeated removal.

## Stop and rollback conditions

- Reject any interface that depends on the lid or glass to force a warped
  divider into position.
- Fall back to a larger controlled clearance if a tight fit creates body stress,
  poor cleaning access, or inconsistent installation.

## Archive handoff

The walkthrough must document the divider interface, equal-spacing method,
selected fit, tested transfer behavior, installation instructions, compatible
cassette revisions, and how the interface should extend to larger sizes.
