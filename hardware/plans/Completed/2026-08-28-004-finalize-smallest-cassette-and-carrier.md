# Plan 004 — Finalize the smallest cassette and six-cassette carrier

- Status: Complete
- Depends on: Plans 001–003 and 009 completed and physically accepted
- Created: 2026-08-27
- Started: 2026-08-28
- Completed: 2026-08-28
- Git start: `main` (activating Plan 004)
- Git completion: `main` (Plan 004 closeout)

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
2. [x] Review source geometry and examine hinge overhang, pocket, label, divider, and clasp interfaces.
3. [x] Evaluate divider-body physical interaction and closure latch holding force under loaded divider conditions.
4. [x] **Physical Finding / Boundary Event:** Physical testing revealed that inserting divider cards into the body channels exerts outward lateral deflection on the front (latch-side) wall, causing the central closure clasp ($0.65\text{ mm}$ undercut) to lose engagement and fail to hold closed.
5. [x] **Closeout Decision:** Per the stop condition, close out Plan 004 and spin out a dedicated high-priority plan (**Plan 010: Re-evaluate Cassette Closure Latch**) before final production candidate freeze.

## Acceptance criteria

- [x] Physical boundary conditions and failure modes documented.
- [x] Latch failure under divider insertion identified and isolated.
- [x] Dedicated follow-up plan (Plan 010) created and prioritized to resolve latch retention.
- [x] Repository documentation reconciled.

## Validation record

### Physical Testing Finding — 2026-08-28

- **Test Assembly:** Full-size v0.8 divided cassette body with baseline $1.20\text{ mm}$ divider cards installed in the $1.40\text{ mm}$ wall slots, paired with the v0.7/v0.8 lid.
- **Observed Behavior:** Inserting the divider cards pushes the front (latch-side) wall of the body outward. Because the existing closure clasp relies on a $1.20\text{ mm}$ cantilever beam engaging a $0.65\text{ mm}$ undercut catch on the center of the front body wall ($Y \in [-4.0, +4.0\text{ mm}]$), the outward wall deflection reduces the effective clasp overlap below retention threshold, causing the latch to fail/disengage.
- **Action Taken:** Plan 004 is closed. Plan 010 is queued at Priority 1 to re-evaluate and redesign the latch architecture (evaluating deeper catch engagement, front-wall stiffening ribs, divider width clearance, and/or alternative latch geometries) before final cassette release.

## Stop and rollback conditions

- Do not declare a production candidate if any accepted feature regresses.
- If a feature needs geometry changes, keep this plan active only for a bounded
  correction to the established smallest system; place broader redesigns back
  into the idea pipeline.

## Archive handoff

This walkthrough documents the state of the smallest cassette system at closeout of Plan 004, the discovery of the divider-induced latch failure mode, and the transition to Plan 010 for latch re-evaluation.
