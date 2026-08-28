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
- Existing v0.6/v0.8 bodies remain valid undivided cassettes even if they cannot
  accept the new removable dividers.

## Implementation steps and test prints

1. [x] Measure the Plan 002 printed cavity ($34.60\text{ mm}$ width, $76.00\text{ mm}$ length, $30.80\text{ mm}$ usable depth) and closed lid-to-floor relationship at the proposed divider stations.
2. [ ] Select representative small test parts and record their dimensions so
   rollover results are reproducible.
3. [x] Compare locating concepts (recessed wall channels and floor groove selected to maintain smooth cavity walls when dividers are omitted).
4. [x] Generate a compact divider-fit coupon containing the real floor, both
   side-wall interfaces, lid-side clearance, and a ladder of named tolerances ($1.30, 1.40, 1.50, 1.60\text{ mm}$).
5. [x] Print the coupon and test insertion, retention, removal, floor gaps,
   wall gaps, deformation, and rattling. *(Coupon result: 1.2 mm card in Station 2 [1.40 mm slot] preferred by physical tactile test; full-size body test required to verify long-wall flexibility).*
6. [x] Generate full-width one-divider and two-divider test bodies using equal
   cavity spacing measured between the functional divider faces.
7. [x] Audit the exported body and divider STLs, including slot support,
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

### Physical Divider Coupon Fit Test — 2026-08-28

- **Test Article:** `divider_slot_coupon.stl` and `divider_card_1_2mm.stl` printed in PETG.
- **Physical Finding:** The **1.20 mm card in Station 2 (1.40 mm slot, +0.20 mm clearance)** is the preferred fit for insertion, smooth sliding, and positive seating without binding.
- **Next Step:** To account for differing wall flexibility over the full 80.0 mm body span compared to the short coupon, generate full-size cassette bodies with 1.40 mm slots and 1.20 mm full-size divider cards for physical validation.

### Full-Size Body Test Articles — 2026-08-28

- **Test Directory:** `Cassettes/divider_test_cassette_v0_8/`
- **Body STL:** `cassette_body_v0_8_divided.stl` ($38.60 \times 80.00 \times 32.80\text{ mm}$, 524 triangles, **0 boundary / 0 non-manifold edges**).
- **Divider Stations:**
  - Center ($Y = 0.00\text{ mm}$): Two $37.40\text{ mm}$ equal compartments.
  - Thirds ($Y = \pm 12.87\text{ mm}$): Three $24.53\text{ mm}$ equal compartments.
- **Slot Geometry:** $1.40\text{ mm}$ slot width (Station 2 verified), $0.60\text{ mm}$ wall recess, $0.60\text{ mm}$ floor groove.
- **Card STLs:**
  - `divider_card_full_1_2mm.stl`: Baseline $35.60 \times 31.20 \times 1.20\text{ mm}$ (32 triangles, **0 boundary / 0 non-manifold edges**).
  - `divider_card_full_1_0mm.stl`: Auxiliary $1.00\text{ mm}$ calibration card.
  - `divider_card_full_1_4mm.stl`: Auxiliary $1.40\text{ mm}$ calibration card.
- **Compatibility:** 100% compatible with existing verified v0.8/v0.7 lid, glass slide, 1.75 mm filament pin, and 3x4 7U carrier trays.

### Divider Coupon Architecture — 2026-08-28

- **Coupon Directory:** `Cassettes/divider_fit_coupon_v0_1/`
- **Slot Width Ladder (on 1.20 mm test card):**
  - Station 1 ($Y = -12.0\text{ mm}$): $1.30\text{ mm}$ slot width ($+0.10\text{ mm}$ clearance)
  - Station 2 ($Y = -4.0\text{ mm}$): $1.40\text{ mm}$ slot width ($+0.20\text{ mm}$ clearance) — **PHYSICALLY SELECTED**
  - Station 3 ($Y = +4.0\text{ mm}$): $1.50\text{ mm}$ slot width ($+0.30\text{ mm}$ clearance)
  - Station 4 ($Y = +12.0\text{ mm}$): $1.60\text{ mm}$ slot width ($+0.40\text{ mm}$ clearance)
- **Recess Depths:** $0.60\text{ mm}$ into left and right walls ($1.40\text{ mm}$ remaining outer wall); $0.60\text{ mm}$ floor groove ($1.40\text{ mm}$ solid bottom floor).
- **STL Audits:**
  - `divider_slot_coupon.stl`: 240 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
  - `divider_card_1_2mm.stl`: 24 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
  - `divider_card_1_0mm.stl`: 24 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
  - `divider_card_1_4mm.stl`: 24 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
