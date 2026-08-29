# Plan 011 — Develop cassette top-surface pinch grips

- Status: Executing
- Depends on: Plans 001–003, 009, 010 completed
- Created: 2026-08-28
- Started: 2026-08-29
- Completed: Not completed
- Git start: `845f42c`
- Git completion: Not completed

## Outcome

Design and integrate low-profile, ergonomic top-surface pinch grips directly onto the
solid roof zones of the cassette lid. This enables effortless, reliable one-handed
vertical extraction of cassettes from tightly packed carrier trays from directly above,
without requiring lateral finger clearance between adjacent cassettes, without loading
or touching the glass, and while remaining strictly within the carrier stacking clearance envelope.

## Requirements

- Implement positive top-surface pinch features on the two solid roof zones of the lid:
  1. **Entry End Roof:** $Y \in [-39.5, -34.5\text{ mm}]$ (flanking the slide entry slot).
  2. **Label End Roof:** $Y \in [33.0, 38.0\text{ mm}]$ (adjacent to the 34 × 10 mm label zone).
- Keep pull feature height low-profile: $\le 1.00\text{ mm}$ above the $Z = 3.20\text{ mm}$ lid top surface.
  - Inside the carrier, cassette bottom sits at $Z = 6.75\text{ mm}$, giving a maximum top feature height of $Z = 6.75 + 3.20 + 32.80 + 1.00 = 43.75\text{ mm}$.
  - This preserves $\ge \mathbf{+0.50\text{ mm}}$ of clear vertical air below the lowest Gridfinity feet of an upper stacked carrier tray ($Z = 44.25\text{ mm}$).
- Ensure support-free FDM 3D printing in PETG:
  - Since the lid prints top-face-down on the build plate (print $Z = 0$), design the top pinch grips with $45^\circ$ draft chamfers or as bed-level textured grip flutes that print cleanly without support.
- Eliminate external body end protrusions:
  - Remove the legacy $+0.40\text{ mm}$ horizontal body end ribs to keep the body ends flat at $80.00\text{ mm}$ overall length, restoring the full $\approx 2.30\text{ mm}$ lateral clearance in $Y$ across the carrier throat and preventing inter-row binding.
- Preserve all existing verified functional interfaces:
  - 34 × 10 mm Brother TZe label zone.
  - 23.0 × 58.5 mm visible glass aperture.
  - $27.0 \times 1.4\text{ mm}$ end-loaded slide channel and 6.75 mm compliant PETG pane latch.
  - 3-knuckle 1.75 mm filament hinge.
  - $0.85\text{ mm}$ undercut closure clasp.

## Non-goals

- Do not modify the Gridfinity 3 × 4 carrier tray walls or stacking lip.
- Do not alter the microscope-slide glass dimensions.
- Do not require tools, picks, or prying against the glass for extraction.

## Reusable parts and compatibility

- The v0.8 divided cassette bodies (`cassette_body_v0_8_divided.stl`), 3 × 4 7U carrier trays, glass slide panes, hinge pins, and divider cards remain 100% compatible.
- Upgrading to top pinch grips requires reprinting only the lid (`cassette_lid_v0_8_print.stl`), minimizing reprint time and material.

## Implementation steps

1. [ ] **Top-Pinch Geometry Design:** Model candidate top-surface pinch grip profiles in `generate_cassette.py` on the solid entry and label roof areas (evaluating transverse serrated grip ribs and recessed fingernail ledges with $45^\circ$ bed draft).
2. [ ] **Body End Clearance Cleanup:** Remove the $+0.40\text{ mm}$ protruding end ribs from `build_body()` and `build_divided_body()` to ensure flat $80.0\text{ mm}$ end walls.
3. [ ] **STL Export & Mesh Audit:** Generate and audit updated STLs for 0 boundary edges and 0 non-manifold edges.
4. [ ] **Print Test Lids:** Print test lids in PETG (top-face-down) and verify first-layer bed adhesion, grip sharpness, and smooth hinge/clasp action.
5. [ ] **Packed Carrier Extraction Test:** Load a 3 × 4 carrier with 6 cassettes; test thumb-and-forefinger extraction from center and edge positions. Verify zero binding and effortless lifting.
6. [ ] **Stacking Clearance Verification:** Stack a loaded upper 7U carrier tray on top; measure and confirm non-interference below the upper tray feet.
7. [ ] **Documentation & Archive:** Update READMEs, manifests, CAD drawings, and archive Plan 011 with its walkthrough narrative.

## Acceptance criteria

- [ ] Cassettes can be extracted easily with one hand from any position in a packed carrier using only the top-surface pinch grips.
- [ ] No feature contacts or applies force to the glass during extraction.
- [ ] Body ends are flat with zero inter-row binding in the carrier tray.
- [ ] Upper carrier tray stacks fully with $\ge +0.50\text{ mm}$ clearance below its Gridfinity feet.
- [ ] All exported STLs pass topological mesh audit (0 boundary edges, 0 non-manifold edges).
- [ ] Release documentation unambiguously identifies print settings and compatibility.

## Validation record

Record measurements, print settings, tactile extraction findings, and stacking clearances here during execution.

## Stop and rollback conditions

- If top grip features exceed the $Z = 44.25\text{ mm}$ upper carrier foot clearance limit or interfere with tray stacking, reduce feature height immediately.
- If top grip features impair top-face-down print bed adhesion, adjust draft angles.

## Archive handoff

The walkthrough must document the top grip geometry, extraction ergonomic evaluation, and verified stacking clearance budget.
