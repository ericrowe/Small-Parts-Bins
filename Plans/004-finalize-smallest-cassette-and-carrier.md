# Plan 004 — Finalize the smallest cassette and six-cassette carrier

- Status: Executing
- Depends on: Plans 001–003 and 009 completed and physically accepted
- Created: 2026-08-27
- Started: 2026-08-28
- Completed: Not completed
- Git start: `main` (activating Plan 004)
- Git completion: Not completed

## Outcome

Combine the verified carrier, optimized height, divider system, hinge, latch,
glass retention, label, and dedicated cassette grab/removal features into the
production candidate for the smallest cassette module and its six-cassette 3 × 4 carrier.

## Requirements

- Preserve all binding dimensions selected by Plans 001–003.
- Provide zero-, one-, and two-divider cassette configurations without changing
  the closed external envelope.
- Implement positive grab features (such as tactile pinch ribs, recessed end
  grips, or edge-grasping features on the cassette ends/rim) to facilitate
  grasping and lifting cassettes from tightly packed carrier trays without
  requiring tools or loading/prying against the glass.
- Keep all cassette features, including grab ribs and pulls, below the carrier
  stacking engagement plane.
- Address outside hinge overhang geometry to ensure clean printability, minimal droop, and proper inter-cassette packing clearance.
- Remove legacy corner overhangs / step blocks at the ends of the hinge side of the body and lid.
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

1. [x] Reconcile the authoritative dimensions and physical results from Plans
   001–003 into one release parameter table.
2. [x] Review source geometry and redesign the hinge outside overhang for clean support-free printability, remove legacy corner overhang ledges at the hinge ends, and verify pocket, label, divider, and removal access.
3. [x] Design and evaluate cassette grab/removal features (e.g. pinch ribs, end
   recesses, or graspable rims) ensuring positive finger purchase from tight
   carrier throats without contacting the glass.
4. [ ] Generate exact final hinge, divider, grab-feature, glass-pocket, throat,
   and stacking coupons from the production source revision.
5. [ ] Print the coupons in the intended production settings and confirm they
   reproduce the accepted fits and grip ergonomics before committing to the full set.
6. [x] Generate the versioned cassette and carrier release with source,
   printable STLs, assembly references, manifests, previews, and instructions.
7. [x] Audit every exported STL for binary integrity, topology, coordinates,
   degenerate faces, islands, sectional hinge/divider clearance, envelope,
   carrier packing, and stack sweep/contact.
8. [ ] Print enough parts for six complete cassettes with a deliberate mix of
   zero-, one-, and two-divider configurations.
9. [ ] Print or reuse two physically compatible carriers and load six cassettes
   in each for the complete 14U test.
10. [ ] Test every cassette's glass retention, hinge, latch, divider retention,
    opening access, grab-feature extraction ergonomics, and carrier insertion/removal.
11. [ ] Stack the two loaded carriers, measure drawer clearance at multiple
    positions, and perform normal handling and controlled tip-over tests.
12. [ ] Repeat representative cassette removal from middle and edge carrier
    positions, hinge, latch, and divider cycles to expose assembly or tolerance outliers.
13. [ ] Record the verified configuration, rejected parts, reusable older parts,
    print settings, measurements, and remaining limitations.

## Acceptance criteria

- [ ] Six cassettes fit each carrier without binding or glass loading.
- [ ] Grab features allow easy, reliable individual extraction from any carrier
  position (including tightly packed inner slots) without tool use or glass contact.
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
