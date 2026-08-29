# Plan 010 — Re-evaluate cassette closure latch

- Status: Executing
- Depends on: Plans 001–003 and 009 completed; Plan 004 findings
- Created: 2026-08-28
- Started: 2026-08-28
- Completed: Not completed
- Git start: `0643d9d`
- Git completion: Not completed

## Outcome

Re-evaluate and redesign the cassette closure latch mechanism and divider interface to guarantee
positive, reliable lid retention under all operating conditions—specifically resolving latch
disengagement caused by front-wall outward deflection when dividers are installed,
while maintaining comfortable, tool-free fingernail opening and preserving the
stacking clearance envelope.

## Requirements

- Provide secure, positive lid retention with zero, one, or two divider cards installed.
- Eliminate front-wall outward deflection induced by divider card insertion:
  - Add internal vertical flanking ridges ($+0.80\text{ mm}$ projection) flanking each divider station on the front wall to create deep $1.40\text{–}1.60\text{ mm}$ guide channels and brace the front wall span.
  - Sizing divider cards for true loose-fit gravity drop-in ($33.00\text{ mm}$ width across $34.10\text{ mm}$ channel bottom span; $+1.10\text{ mm}$ lateral clearance) with zero transverse wedging.
  - Increase closure catch undercut to $0.85\text{–}0.90\text{ mm}$ for rock-solid retention.
- Preserve comfortable fingernail opening ergonomics via the lid edge relief without requiring tools or loading/prying against the glass.
- Maintain full external envelope compatibility with the 3 × 4 carrier throat ($39.55 \times 80.0 \times 36.0\text{ mm}$ maximum closed envelope).
- Ensure no latch feature protrudes above the carrier stacking engagement plane ($Z = 36.0\text{ mm}$, well below the $Z = 44.25\text{ mm}$ upper carrier foot clearance limit).
- Maintain support-free FDM 3D printing in PETG (lid and body) and ASA (body).

## Non-goals

- Do not alter the physically verified 14U carrier tray footprints, walls, or stacking interface.
- Do not alter the microscope-slide glass dimensions or the verified Plan 009 end-loaded slide capture mechanism.
- Do not modify the 3-knuckle 1.75 mm filament hinge geometry.

## Reusable parts and compatibility

- The 3 × 4 7U carrier trays (`Carriers/carrier_3x4_14u_test/`), glass slide window, and 1.75 mm filament pin remain 100% reusable.
- The v0.8 body cavity depth ($30.80\text{ mm}$) and thickened left hinge wall ($4.30\text{ mm}$) are preserved.

## Implementation steps

1. [x] **Architecture Selection:** Select internal flanking ridge architecture with deep channel engagement ($1.40\text{–}1.60\text{ mm}$/side), loose-fit divider cards ($33.00\text{ mm}$), and reinforced closure clasp ($0.85\text{ mm}$ undercut).
2. [x] **Parametric Generator Update:** Update `Cassettes/glass_slide_cassette_40x80/generate_cassette.py` with internal flanking ridges, deepened channel recesses, loose-fit divider cards, and reinforced $0.85\text{ mm}$ closure clasp.
3. [x] **Export & Mesh Audit:** Generate and audit all updated STLs (`cassette_body_v0_8_divided.stl`, `cassette_body_v0_8.stl`, `cassette_lid_v0_8_print.stl`, `divider_card_1_2mm.stl`) for 0 boundary edges and 0 non-manifold edges.
4. [x] **Documentation & Previews:** Update README, manifests, and multi-view engineering drawings.
5. [ ] **Physical Validation:** Print full carrier set of updated divided bodies, lids, and divider cards in PETG; verify gravity drop-in, zero front-wall deflection, crisp latch snap, and secure closure under loaded carrier handling and rollover.
6. [ ] **Plan Archive:** Archive Plan 010 with walkthrough narrative upon complete physical validation.

## Acceptance criteria

- [ ] Latch positively retains the lid when 2 divider cards are installed (no spontaneous opening during handling, shaking, or rollover).
- [ ] Latch positively retains the lid when 0 dividers are installed.
- [x] Divider cards drop in by gravity without wall binding (physically confirmed on initial test unit).
- [x] Fingernail opening remains comfortable and non-destructive.
- [x] Closed envelope remains strictly within $39.55 \times 80.0 \times 36.0\text{ mm}$.
- [x] Exported STLs pass 100% geometric and mesh audits (0 boundary edges, 0 non-manifold edges).
- [ ] Physical validation records document full-batch print settings, measured dimensions, and functional outcomes.

## Validation record

### Initial Sample Validation — 2026-08-28

- **Test Article:** `cassette_body_v0_8_divided.stl`, `cassette_lid_v0_8_print.stl`, and `divider_card_1_2mm.stl` printed in PETG.
- **Physical Finding:** The $33.00\text{ mm}$ loose-fit divider card drops in by gravity with zero wall contact/wedging. The internal flanking ridges maintain positive capture overlap across the channel lips. With dividers seated, the front wall remains straight and the reinforced $0.85\text{ mm}$ closure clasp snaps crisply and holds firmly closed.
- **Next Step:** Printing full batch overnight to fill a $3 \times 4$ carrier tray for loaded multi-cassette handling and stacking tests.

## Stop and rollback conditions

- If an evaluated latch concept requires force that risks cracking the glass or deforming the hinge pin, halt and test alternative geometry.
- If a latch concept increases the outside body width beyond $39.55\text{ mm}$, it cannot be accepted.

## Archive handoff

The walkthrough must document the evaluated latch variants, measured wall deflections, final catch geometry, and physical validation results under both divided and undivided configurations.
