# Plan 004 — Finalize the smallest cassette and six-cassette carrier

- Status: Queued
- Depends on: Plans 001–003 completed and physically accepted
- Created: 2026-08-27
- Started: Not started
- Completed: Not completed
- Git start: Not committed
- Git completion: Not completed

## Outcome

Combine the verified carrier, optimized height, divider system, hinge, latch,
glass retention, label, and removal features into the production candidate for
the smallest cassette module and its six-cassette 3 × 4 carrier.

## Requirements

- Preserve all binding dimensions selected by Plans 001–003.
- Provide zero-, one-, and two-divider cassette configurations without changing
  the closed external envelope.
- Keep all cassette features below the carrier stacking engagement plane.
- Preserve the standard Gridfinity base/lip interface and 2.0 mm minimum carrier
  walls.
- Maintain visible glass and labels when the drawer is open.
- Retain individual cassette closure during removal and carrier tip-over.

## Non-goals

- Do not add larger cassette footprints or mixed-size layouts.
- Do not introduce cosmetic geometry that jeopardizes verified interfaces.
- Do not replace microscope-slide glass or the 1.75 mm filament hinge pin.

## Reusable parts and compatibility

- Identify and reuse every verified lid, body, retainer, glass pane, hinge pin,
  and carrier that remains geometrically compatible.
- A version-label change alone must not force a reprint.
- Preserve all earlier tested release directories and document superseded parts.

## Implementation steps and test prints

1. [ ] Reconcile the authoritative dimensions and physical results from Plans
   001–003 into one release parameter table.
2. [ ] Review source geometry for accidental deviations in Gridfinity profile,
   cassette envelope, hinge, latch, pocket, label, divider, and removal access.
3. [ ] Generate exact final hinge, divider, glass-pocket, throat, and stacking
   coupons from the production source revision.
4. [ ] Print the coupons in the intended production settings and confirm they
   reproduce the accepted fits before committing to the full set.
5. [ ] Generate the versioned cassette and carrier release with source,
   printable STLs, assembly references, manifests, previews, and instructions.
6. [ ] Audit every exported STL for binary integrity, topology, coordinates,
   degenerate faces, islands, sectional hinge/divider clearance, envelope,
   carrier packing, and stack sweep/contact.
7. [ ] Print enough parts for six complete cassettes with a deliberate mix of
   zero-, one-, and two-divider configurations.
8. [ ] Print or reuse two physically compatible carriers and load six cassettes
   in each for the complete 14U test.
9. [ ] Test every cassette's glass retention, hinge, latch, divider retention,
   opening access, and carrier insertion/removal.
10. [ ] Stack the two loaded carriers, measure drawer clearance at multiple
    positions, and perform normal handling and controlled tip-over tests.
11. [ ] Repeat representative cassette removal, hinge, latch, and divider cycles
    to expose assembly or tolerance outliers.
12. [ ] Record the verified configuration, rejected parts, reusable older parts,
    print settings, measurements, and remaining limitations.

## Acceptance criteria

- [ ] Six cassettes fit each carrier without binding or glass loading.
- [ ] All tested divider configurations remain functional and preserve equal
  compartment spacing.
- [ ] Every cassette remains closed during the controlled carrier test.
- [ ] Two loaded carriers stack fully and fit the drawer with practical clearance.
- [ ] Labels and windows remain visible and no feature crosses the engagement
  plane.
- [ ] Exported production STLs pass all geometric and mesh audits.
- [ ] Release documentation unambiguously identifies what to print, reuse, and
  avoid.

## Validation record

Record the identity and result of every printed cassette and carrier, including
material, slicer settings, measured envelopes, functional cycles, drawer
clearance, tip-over outcome, failures, and corrective actions.

## Stop and rollback conditions

- Do not declare a production candidate if any accepted feature regresses.
- If a feature needs geometry changes, keep this plan active only for a bounded
  correction to the established smallest system; place broader redesigns back
  into the idea pipeline.

## Archive handoff

The walkthrough must be a complete build-and-use reference for the verified
smallest system and must list every reusable earlier part and required reprint.

