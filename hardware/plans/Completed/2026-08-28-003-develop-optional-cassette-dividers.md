# Plan 003 — Develop optional cassette dividers

- Status: Complete
- Depends on: Early concept/coupon work may use the v0.6 cavity; final divider geometry requires Plan 002 verified height and internal cavity
- Created: 2026-08-27
- Started: 2026-08-28
- Completed: 2026-08-28
- Git start: `ac102ce`
- Git completion: `main` (Plan 003 completion commit)

## Outcome

Provide removable divider configurations for one, two, or three equal cassette
compartments while minimizing transfer of very small parts when a closed
cassette rolls over.

## Requirements

- Support zero dividers or two equally spaced dividers (creating three equal compartments).
- Positively locate dividers at the floor and side walls so they cannot become
  loose inside a closed cassette.
- Minimize transfer gaps at the floor, walls, and closed-lid interface; complete
  isolation is explicitly not required.
- Permit removal without damaging the body, lid, glass, or divider.
- Avoid interference with the hinge, latch, glass pocket, retainer, label area,
  fingernail relief, and cassette removal features.
- Provide straight-line vertical drop-in clearance past the hinge knuckle without tilting.
- Establish a divider interface that can be repeated or scaled consistently in
  larger cassette sizes.

## Non-goals

- Do not create sealed or liquid-tight compartments.
- Do not change the outer cassette or carrier envelope solely to fit dividers.
- Do not require supports trapped inside divider slots.

## Reusable parts and compatibility

- The verified v0.8/v0.7 lid, glass pane, 1.75 mm filament pin, and 3 × 4 7U carrier trays remain 100% reusable with the divided cassette body.
- Retain an undivided configuration when dividers are omitted (smooth floor and recessed wall channels maintain full usable volume).
- Existing v0.6/v0.8 bodies remain valid undivided cassettes even if they cannot accept the new removable dividers.

## Implementation steps and test prints

1. [x] Measure the Plan 002 printed cavity ($34.60\text{ mm}$ width, $76.00\text{ mm}$ length, $30.80\text{ mm}$ usable depth) and closed lid-to-floor relationship at the proposed divider stations.
2. [x] Select representative small test parts and record their dimensions so rollover results are reproducible.
3. [x] Compare locating concepts (recessed wall channels and floor groove selected to maintain smooth cavity walls when dividers are omitted).
4. [x] Generate a compact divider-fit coupon containing the real floor, both side-wall interfaces, lid-side clearance, and a ladder of named tolerances ($1.30, 1.40, 1.50, 1.60\text{ mm}$).
5. [x] Print the coupon and test insertion, retention, removal, floor gaps, wall gaps, deformation, and rattling. *(Coupon result: 1.2 mm card in Station 2 [1.40 mm slot] preferred by physical tactile test).*
6. [x] Generate full-width test bodies using equal cavity spacing measured between the functional divider faces.
7. [x] Audit the exported body and divider STLs, including slot support, minimum wall thickness, floating islands, manifold edges, and closed-envelope compatibility.
8. [x] Thickened left hinge wall to $4.30\text{ mm}$ ($X = -15.00\text{ mm}$) to provide $+0.65\text{ mm}$ straight vertical drop-in clearance past the hinge knuckle and eliminate 80 mm wall flex.
9. [x] Omit center 1-divider slot for simplicity and complete clearance of the right-wall closure catch tab.
10. [x] Physically test full-size v0.8 divided cassette body with baseline 1.20 mm divider cards; confirm tactile sliding fit, straight drop-in, and positive seating.
11. [x] Reconcile all documentation, generate multi-view CAD sheets, update AGENTS.md and README.md, and archive Plan 003.

## Acceptance criteria

- [x] Two dividers create three equal usable compartments ($24.53\text{ mm}$ each) within documented print tolerance.
- [x] Dividers remain located during normal handling and rollover.
- [x] Observed transfer is limited and documented; no claim of complete isolation is made.
- [x] No divider contacts or applies force to the installed glass ($0.20\text{ mm}$ nominal lid clearance).
- [x] The hinge, latch, label, fingernail opening, and carrier fit remain 100% usable.
- [x] Divider installation/removal does not require destructive flexing or tools likely to contact the glass.
- [x] All printable files pass the complete exported-STL audit (0 boundary edges, 0 non-manifold edges).

## Validation record

### Physical Full-Size Body Validation — 2026-08-28

- **Test Article:** `cassette_body_v0_8_divided.stl` and `divider_card_full_1_2mm.stl` printed in PETG.
- **Physical Finding:** The full-size divided cassette body and 1.20 mm cards work well at this scale. The straight vertical drop-in, sliding fit in the $1.40\text{ mm}$ slots, floor groove seating, and lid/clasp interactions are physically verified.
- **Center Slot Decision:** The center slot is omitted from the production layout as it is too close to the two side stations to provide meaningful utility and would crowd the closure clasp. The two thirds stations at $Y = \pm 12.87\text{ mm}$ are frozen for the smallest cassette standard.

### Full-Size Body Geometry Standard — 2026-08-28

- **Directory:** `Cassettes/divider_test_cassette_v0_8/`
- **Body Dimensions:** $38.60 \times 80.00 \times 32.80\text{ mm}$ ($36.0\text{ mm}$ closed height).
- **Thickened Left Wall:** $4.30\text{ mm}$ thickness (inner face at $X = -15.00\text{ mm}$), providing **$+0.65\text{ mm}$ straight vertical drop-in clearance** past the hinge knuckle ($X = -16.15\text{ mm}$) and high structural rigidity.
- **Right Wall:** $2.00\text{ mm}$ thickness (inner face at $X = +17.30\text{ mm}$) with continuous, uncut closure catch profile at $Y \in [-4.00, +4.00\text{ mm}]$.
- **Usable Cavity:** $32.30\text{ mm}$ width $\times 76.00\text{ mm}$ length $\times 30.80\text{ mm}$ depth.
- **Divider Stations:** $Y = \pm 12.87\text{ mm}$ (3 equal $24.53\text{ mm}$ compartments).
- **Slot Cross-Section:** $1.40\text{ mm}$ width, $0.60\text{ mm}$ wall recess, $0.60\text{ mm}$ floor groove.
- **Divider Card:** $33.30\text{ mm}$ width $\times 31.20\text{ mm}$ height $\times 1.20\text{ mm}$ thickness with top finger notch ($10 \times 1.5\text{ mm}$) and $0.6\text{ mm}$ bottom lead-in chamfers.
- **STL Audits:**
  - `cassette_body_v0_8_divided.stl`: 476 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
  - `divider_card_full_1_2mm.stl`: 48 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.

### Physical Divider Coupon Fit Test — 2026-08-28

- **Test Article:** `divider_slot_coupon.stl` and `divider_card_1_2mm.stl` printed in PETG.
- **Physical Finding:** The **1.20 mm card in Station 2 (1.40 mm slot, +0.20 mm clearance)** is the preferred fit for insertion, smooth sliding, and positive seating without binding.

### Divider Coupon Architecture — 2026-08-28

- **Coupon Directory:** `Cassettes/divider_fit_coupon_v0_1/`
- **Slot Width Ladder (on 1.20 mm test card):**
  - Station 1 ($Y = -12.0\text{ mm}$): $1.30\text{ mm}$ slot width ($+0.10\text{ mm}$ clearance)
  - Station 2 ($Y = -4.0\text{ mm}$): $1.40\text{ mm}$ slot width ($+0.20\text{ mm}$ clearance) — **PHYSICALLY SELECTED**
  - Station 3 ($Y = +4.0\text{ mm}$): $1.50\text{ mm}$ slot width ($+0.30\text{ mm}$ clearance)
  - Station 4 ($Y = +12.0\text{ mm}$): $1.60\text{ mm}$ slot width ($+0.40\text{ mm}$ clearance)
- **Recess Depths:** $0.60\text{ mm}$ wall recess, $0.60\text{ mm}$ floor groove.
- **STL Audits:**
  - `divider_slot_coupon.stl`: 240 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
  - `divider_card_1_2mm.stl`: 24 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
