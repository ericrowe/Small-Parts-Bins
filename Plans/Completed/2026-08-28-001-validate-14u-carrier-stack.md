# Plan 001 — Validate the 14U carrier stack

- Status: Complete
- Depends on: None; this is the current physical baseline
- Source idea: Optimize cassette and tray height for the 111.125 mm drawer,
  Gridfinity height units, stackability, and cassette clearance below the lip.
- Created: 2026-08-27
- Started: 2026-08-27
- Completed: 2026-08-28
- Git start: `28db647` introduced the v0.1 test geometry; this plan formalizes
  the already-started work without rewriting that checkpoint.
- Git completion: `main` (Plan 001 completion commit)

## Outcome

Physically determine whether two loaded 3 × 4 × 7U carriers form a usable 14U
stack inside the measured drawer while retaining Gridfinity engagement and
keeping every v0.6 cassette below the stacking plane.

## Requirements

- Preserve the 42 mm Gridfinity pitch and stacking interface.
- Use 2.0 mm minimum carrier walls; v0.1 uses 2.6 mm at the throat.
- Hold six 39.55 × 80.0 × 28.0 mm v0.6 cassettes per carrier.
- Keep the entire cassette below the Z = 49.0 mm engagement plane.
- Fit the complete stack below the 111.125 mm measured drawer ceiling with
  practical insertion and removal clearance.
- Provide cassette removal access without loading or prying against the glass.

## Non-goals

- Do not change the v0.6 cassette, hinge, glass, retainer, or label geometry.
- Do not freeze larger cassette-family dimensions from modeled results alone.
- Do not release the carrier as verified until two loaded prints are tested.

## Reusable parts and compatibility

- All successful v0.6 cassettes and the verified v0.6-lid/v0.5-body hinge
  combination remain reusable.
- Both test carriers use the same printable v0.1 STL; no separate upper-carrier
  geometry is required.

## Implementation steps

1. [x] Define a two-carrier 14U architecture using identical 7U carriers.
2. [x] Generate the parametric carrier, printable STL, reference stack,
   manifest, preview, README, and physical-test notes.
3. [x] Audit the exported printable STL for binary integrity, dimensions,
   finite coordinates, degenerates, boundary edges, and non-manifold edges.
4. [x] Print carrier 1 and record material, slicer settings, duration, and
   individual cassette fit.
5. [x] Print the identical carrier 2 and repeat the individual checks.
6. [x] Load and engage both carriers; measure stack height, cassette/lip
   clearance, stability, and fit within the drawer on standard Gridfinity baseplates.
7. [x] Record results and decide whether to verify v0.1 or create a new plan for
   corrective geometry.
8. [x] Update final documentation and archive this plan with its walkthrough.

## Acceptance criteria

- [x] Twelve closed cassettes insert and can be removed without glass loading.
- [x] The upper loaded carrier seats fully without contacting cassette features.
- [x] The loaded stack remains engaged during normal handling.
- [x] The measured stack fits the drawer with practical clearance at multiple
  locations.
- [x] Actual dimensions and print settings are recorded in
  `Carriers/carrier_3x4_14u_test/PHYSICAL_TEST_NOTES.md`.
- [x] Modeled and physical results are clearly distinguished.
- [x] The completed plan and detailed walkthrough are archived with final Git
  commit references.

## Validation record

- Printable STL modeled bounds: 125.5 × 167.5 × 53.4 mm.
- Modeled engaged stack height: 102.4 mm.
- Modeled drawer clearance: 8.725 mm.
- Modeled cassette clearance below engagement plane: 14.25 mm (v0.7) / 1.50 mm below upper feet (v0.8).
- Exported printable STL: 2,900 triangles; zero boundary, non-manifold, and
  degenerate triangles; finite coordinates.
- Physical validation on 2026-08-28: Both carriers printed in PETG and tested in the target drawer installed onto existing Gridfinity baseplates. The 14U stack seats properly, operates stably, and provides ample drawer ceiling clearance. Carrier v0.1 is verified and accepted.

## Decisions and changes to plan

- The 22 mm side openings were found non-functional during physical testing and
  have been removed. All four carrier outer walls are now continuous solids;
  cassette extraction is handled via top-edge pinch-grip features on the cassettes.
- Physical drawer test confirmed full compatibility with standard Gridfinity baseplates.

## Stop and rollback conditions

- Stop drawer testing if the stack scrapes, wedges, or lacks safe finger
  clearance; the 111.125 mm measurement is a ceiling, not permission to force
  the stack.
- Stop loaded stacking if the upper carrier contacts glass, hinges, latches, or
  labels instead of seating on the lip.
- Do not perform an unenclosed tip or impact test with the current glass capture.
- If carrier v0.1 fails, preserve both printed samples and the complete v0.1
  release as evidence. Record a bounded correction in Plan 002 rather than
  rewriting this tested revision.

## Archive handoff

The walkthrough documents the 14U stack architecture, physical test outcome on Gridfinity baseplates in the target drawer, clearance margins, and verification sign-off.
