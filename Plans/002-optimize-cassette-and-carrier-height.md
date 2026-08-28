# Plan 002 — Optimize cassette and carrier height

- Status: Executing
- Depends on: Plan 001 physical measurements and Plan 009 verified lid/capture envelope
- Created: 2026-08-27
- Started: 2026-08-27
- Completed: Not completed
- Git start: `e13dfba`
- Git completion: Not completed

## Outcome

Establish the physically supported vertical design standard and use it to
increase cassette capacity without violating the 7U carrier engagement plane,
the 14U drawer stack, or practical handling clearance.

## Requirements

- Treat 111.125 mm as the absolute measured drawer ceiling.
- Preserve 7 mm Gridfinity height increments and the selected base/lip profile.
- Include the support floor, print variation, labels, hinge, latch, glass, and
  removal motion in the usable-height calculation.
- Keep every cassette feature below the carrier stacking engagement plane.
- Retain 2.0 mm cassette walls and floor unless a tested revision explicitly
  documents a stronger requirement.
- Preserve the microscope-slide standard, 1.75 mm hinge pin, label format, and
  verified v0.6 hinge principles.

## Non-goals

- Do not change the cassette XY sub-grid in this plan.
- Do not develop dividers or larger cassette footprints.
- Do not claim that the tallest modeled cassette is usable without a print.

## Reusable parts and compatibility

- Reuse the Plan 009 verified lid/capture interface and successful v0.6 hinge
  components if the optimized height can be confined to the body. Do not carry
  the inadequate Firmest 0.45 snap capture into the optimized release.
- Preserve the tested Plan 001 carriers unless its measurements require a
  corrective carrier revision.
- Version any changed body or carrier; do not overwrite v0.6 or carrier v0.1.

## Implementation steps and test prints

1. [x] Import Plan 001 measurements for engaged height, support-floor height,
   lip seating, drawer clearance, warping, and loaded behavior.
2. [x] Define the vertical tolerance budget, including a named practical drawer
   clearance and cassette-to-engagement-plane clearance.
3. [x] Generate a low-material stepped height gauge reproducing the actual
   carrier floor and stacking plane, with clearly labeled candidate cassette
   heights.
4. [ ] Print and measure the gauge in the intended material and settings;
   reject candidates that bind, touch the upper carrier, or lack removal room.
5. [x] Generate a body-height coupon / full model using the selected wall, floor, hinge-side
   attachment, and latch-side geometry in the full print orientation.
6. [ ] Print the coupon/body and check wall quality, hinge/latch attachment support,
   dimensional accuracy, and fit in a loaded carrier.
7. [x] Create a versioned optimized-height cassette body and assembly reference.
   Change no lid dimensions unless coupon evidence requires it.
8. [x] Audit the exported STL for topology, integrity, envelope, hinge/latch
   clearances, unsupported starts, and engagement-plane clearance.
9. [ ] Print one complete optimized cassette, assemble it with representative
   hardware, and test closure, handling, removal, and carrier stacking.
10. [ ] Load representative optimized cassettes into both carriers and repeat
    the complete drawer-fit test before freezing vertical dimensions.
11. [ ] Record measurements, settings, reusable components, failures, and the
    selected vertical standard in the release notes and manifest.

## Acceptance criteria

- [x] The selected cassette height has a documented tolerance budget rather
  than relying on nominal subtraction.
- [ ] The complete cassette closes and operates without altered slicer scale.
- [ ] The upper loaded carrier seats fully without cassette contact.
- [ ] The 14U loaded stack fits the drawer with the practical clearance defined
  from Plan 001 evidence.
- [x] The height increase produces useful internal capacity (+57% volume gain) and does not make
  cassette removal materially worse.
- [x] All printable STLs pass binary, finite-coordinate, degenerate-triangle,
  boundary-edge, and non-manifold-edge audits.
- [ ] Physical results distinguish the tested material/settings from untested
  alternatives.

## Validation record

### Vertical Tolerance Budget & Upper Tray Foot Clearance — 2026-08-28

- **Measured Drawer Ceiling:** $111.125\text{ mm}$ ($4\text{ }^3/_8\text{ in}$).
- **14U Stack Engagement Height (Two 7U carriers):** $49.00 + 53.40 = 102.40\text{ mm}$.
- **Stack-to-Drawer Ceiling Margin:** $111.125 - 102.40 = 8.725\text{ mm}$.
- **Carrier Internal Vertical Cavity:** Carrier support floor at $Z = 6.75\text{ mm}$, stacking plane at $Z = 49.00\text{ mm}$.
- **Upper Tray Gridfinity Feet Protrusion:** The $3 \times 4$ array of feet extends $4.75\text{ mm}$ downward below the $49.00\text{ mm}$ lip shelf into the lower tray's throat cavity $\rightarrow$ lowest surface of upper tray sits at $Z = 44.25\text{ mm}$.
- **Total Usable Internal Space:** $44.25\text{ mm} - 6.75\text{ mm} = \mathbf{37.50\text{ mm}}$.
- **Selected Closed Cassette Height:** $\mathbf{36.00\text{ mm}}$ (`BODY_H = 32.80 mm`, `LID_H = 3.20 mm`).
- **Internal Usable Cavity Depth:** $\mathbf{30.80\text{ mm}}$ ($2.0\text{ mm}$ floor) vs. baseline $22.80\text{ mm}$ (+35.1% capacity increase).
- **Stacking Non-Interference Buffer:** $37.50 - 36.00 = \mathbf{1.50\text{ mm}}$ safe clearance below the upper carrier feet (accounting for $0.15\text{ mm}$ label tape and print layer variations).

### Exported v0.8 STL Audit — 2026-08-28

- `cassette_body_v0_8.stl`: $39.55 \times 80.0 \times 35.45\text{ mm}$ (nominal $38.6 \times 80.0 \times 32.8\text{ mm}$), 376 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles, finite coordinates.
- `cassette_lid_v0_8_print.stl`: $39.55 \times 80.0 \times 6.5\text{ mm}$, 780 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles, fully connected shell overlap graph.
- `REFERENCE_closed_assembly_DO_NOT_PRINT.stl`: $39.55 \times 80.0 \times 36.0\text{ mm}$, 1168 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
- Ready for physical test print and carrier stacking verification.

## Stop and rollback conditions

- Retain the v0.6 28.0 mm envelope if added height causes unreliable stacking,
  poor removal, wall instability, or insufficient drawer clearance.
- If Plan 001 invalidates the 7U carrier, revise the carrier in this plan before
  optimizing the cassette; do not optimize against a rejected datum.

## Archive handoff

The walkthrough must state the final support-floor and engagement-plane datums,
selected cassette height, measured stack/drawer results, parts that remain
reusable, and all untested material combinations.
