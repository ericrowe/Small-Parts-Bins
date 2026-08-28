# Plan 010 — Re-evaluate cassette closure latch

- Status: Queued
- Depends on: Plans 001–003 and 009 completed; Plan 004 findings
- Created: 2026-08-28
- Started: Not started
- Completed: Not completed
- Git start: Not committed
- Git completion: Not completed

## Outcome

Re-evaluate and redesign the cassette closure latch mechanism to guarantee positive,
reliable lid retention under all operating conditions—specifically resolving latch
disengagement caused by front-wall outward deflection when dividers are installed,
while maintaining comfortable, tool-free fingernail opening and preserving the
stacking clearance envelope.

## Requirements

- Provide secure, positive lid retention with zero, one, or two divider cards installed.
- Accommodate or eliminate front-wall outward deflection induced by divider card insertion.
- Evaluate candidate mechanical improvements:
  1. **Catch Engagement Depth:** Test an engagement depth ladder (e.g. $0.65\text{ mm}$, $0.85\text{ mm}$, $1.05\text{ mm}$, $1.25\text{ mm}$) to ensure positive overlap even when the wall deflects.
  2. **Front-Wall Stiffening:** Add localized wall thickening or vertical stiffener ribs around the central catch zone ($Y \in [-6.0, +6.0\text{ mm}]$) to resist lateral flex without consuming internal part volume.
  3. **Cantilever Tab Geometry:** Optimize the lid clasp's cantilever beam thickness, angle of attack, lead-in chamfer, and deflection travel for crisp snap engagement and tactile feedback.
  4. **Divider Card Tolerance & Clearance:** Refine divider card width ($33.30\text{ mm}$ baseline) and slot depth to ensure cards seat firmly in the floor groove without exerting lateral outward preload against the long walls.
  5. **Dual-Point vs. Single Catch:** Evaluate whether dual distributed catches (e.g. aligned near the divider stations) or a single reinforced center catch provides superior stability.
- Preserve comfortable fingernail opening ergonomics via the lid edge relief without requiring tools or loading/prying against the glass.
- Maintain full external envelope compatibility with the 3 × 4 carrier throat ($39.55 \times 80.0 \times 36.0\text{ mm}$ maximum closed envelope).
- Ensure no latch feature protrudes above the carrier stacking engagement plane ($Z = 36.0\text{ mm}$, well below the $Z = 44.25\text{ mm}$ upper carrier foot clearance limit).
- Maintain support-free FDM 3D printing in PETG (lid and body) and ASA (body).
- Use rapid, low-cost test coupons before committing to full-size body/lid prints.

## Non-goals

- Do not alter the physically verified 14U carrier tray footprints, walls, or stacking interface.
- Do not alter the microscope-slide glass dimensions or the verified Plan 009 end-loaded slide capture mechanism.
- Do not modify the 3-knuckle 1.75 mm filament hinge geometry.

## Reusable parts and compatibility

- The 3 × 4 7U carrier trays (`Carriers/carrier_3x4_14u_test/`), glass slide window, 1.75 mm filament pin, and baseline divider cards remain reusable.
- The v0.8 body cavity depth ($30.80\text{ mm}$) and thickened left hinge wall ($4.30\text{ mm}$) are preserved.

## Implementation steps

1. [ ] **Deflection & Geometry Analysis:** Measure physical deflection of the front body wall with $1.20\text{ mm}$ cards inserted in the $1.40\text{ mm}$ slots, and calculate the exact engagement loss on the current $0.65\text{ mm}$ undercut.
2. [ ] **Coupon Design:** Design a compact latch test coupon (`Cassettes/latch_fit_coupon_v0_1/`) containing the front wall, a divider slot, the central catch interface, and mating lid clasp tabs with a parameter ladder of undercut depths and wall thicknesses.
3. [ ] **Mesh Audit:** Audit all exported coupon STLs for binary integrity, manifoldness, and support-free printability.
4. [ ] **Physical Coupon Testing:** Print the coupon matrix in PETG and evaluate snap engagement force, retention under divider spreading force, and fingernail release effort.
5. [ ] **Full-Size Model Integration:** Update the parametric generator (`Cassettes/glass_slide_cassette_40x80/generate_cassette.py`) with the physically validated latch parameters.
6. [ ] **Full-Size Cassette Validation:** Print a full-size cassette (body and lid) with the revised latch geometry; physically verify positive closure retention with 2 dividers installed, drop/rollover containment, and easy opening.
7. [ ] **Documentation & Archive:** Update READMEs, CAD sheets, AGENTS.md, and archive Plan 010 with its walkthrough narrative.

## Acceptance criteria

- [ ] Latch positively retains the lid when 2 divider cards are installed (no spontaneous opening during handling, shaking, or rollover).
- [ ] Latch positively retains the lid when 0 dividers are installed.
- [ ] Fingernail opening remains comfortable and non-destructive.
- [ ] Closed envelope remains strictly within $39.55 \times 80.0 \times 36.0\text{ mm}$.
- [ ] Exported STLs pass 100% geometric and mesh audits (0 boundary edges, 0 non-manifold edges).
- [ ] Physical validation records document print settings, measured dimensions, and functional outcomes.

## Validation record

Record measurements, coupon test results, physical findings, and final latch parameters here during execution.

## Stop and rollback conditions

- If an evaluated latch concept requires force that risks cracking the glass or deforming the hinge pin, halt and test alternative geometry.
- If a latch concept increases the outside body width beyond $39.55\text{ mm}$, it cannot be accepted.

## Archive handoff

The walkthrough must document the evaluated latch variants, measured wall deflections, final catch geometry, and physical validation results under both divided and undivided configurations.
