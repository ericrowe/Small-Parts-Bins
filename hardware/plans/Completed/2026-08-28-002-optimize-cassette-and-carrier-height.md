# Plan 002 — Optimize cassette and carrier height

- Status: Complete
- Depends on: Plan 001 physical measurements and Plan 009 verified lid/capture envelope
- Created: 2026-08-27
- Started: 2026-08-27
- Completed: 2026-08-28
- Git start: `e13dfba`
- Git completion: `main` (Plan 002 completion commit)

## Outcome

Establish the physically supported vertical design standard and use it to
increase cassette capacity without violating the 7U carrier engagement plane,
the 14U drawer stack, or practical handling clearance.

## Requirements

- Treat 111.125 mm as the absolute measured drawer ceiling.
- Preserve 7 mm Gridfinity height increments and the selected base/lip profile.
- Include the support floor, print variation, labels, hinge, latch, glass, and
  removal motion in the usable-height calculation.
- Keep every cassette feature below the carrier stacking engagement plane and upper tray feet.
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
  components. The v0.8 height increase is confined to the body, making the v0.7 lid 100% reusable.
- Preserve the tested Plan 001 carriers.
- Version changed body as v0.8.

## Implementation steps and test prints

1. [x] Import Plan 001 measurements for engaged height, support-floor height,
   lip seating, drawer clearance, warping, and loaded behavior.
2. [x] Define the vertical tolerance budget, including a named practical drawer
   clearance, carrier foot depth, and cassette-to-engagement-plane clearance.
3. [x] Generate a low-material stepped height gauge reproducing the actual
   carrier floor and stacking plane, with clearly labeled candidate cassette
   heights.
4. [x] Measure carrier foot protrusion (4.75 mm downward from lip shelf) and calculate exact upper foot datum (Z = 44.25 mm).
5. [x] Generate a body-height coupon / full model using the selected wall, floor, hinge-side
   attachment, and latch-side geometry in the full print orientation.
6. [x] Print the v0.8 body and check wall quality, hinge/latch attachment support,
   dimensional accuracy, and fit in a loaded carrier.
7. [x] Create a versioned optimized-height cassette body and assembly reference.
8. [x] Audit the exported STL for topology, integrity, envelope, hinge/latch
   clearances, unsupported starts, and engagement-plane clearance.
9. [x] Assemble v0.8 body with verified v0.7/v0.8 lid and test closure, handling, and carrier stacking.
10. [x] Physically test two-tray 14U stack loaded with v0.8 cassette in target drawer; verify upper carrier seats fully with clearance under feet.
11. [x] Record measurements, settings, reusable components, and the selected vertical standard in release notes and manifest.

## Acceptance criteria

- [x] The selected cassette height has a documented tolerance budget rather
  than relying on nominal subtraction.
- [x] The complete cassette closes and operates without altered slicer scale.
- [x] The upper loaded carrier seats fully without cassette contact under Gridfinity feet.
- [x] The 14U loaded stack fits the drawer with the practical clearance defined
  from Plan 001 evidence.
- [x] The height increase produces useful internal capacity (+35.1% volume gain) and does not make
  cassette removal materially worse.
- [x] All printable STLs pass binary, finite-coordinate, degenerate-triangle,
  boundary-edge, and non-manifold-edge audits.
- [x] Physical results distinguish the tested material/settings from untested
  alternatives.

## Validation record

### Vertical Tolerance Budget & Upper Tray Foot Clearance — 2026-08-28

- **Measured Drawer Ceiling:** 111.125 mm (4 3/8 in).
- **14U Stack Engagement Height (Two 7U carriers):** 49.00 + 53.40 = 102.40 mm.
- **Stack-to-Drawer Ceiling Margin:** 111.125 - 102.40 = 8.725 mm.
- **Carrier Internal Vertical Cavity:** Carrier support floor at Z = 6.75 mm, stacking plane at Z = 49.00 mm.
- **Upper Tray Gridfinity Feet Protrusion:** The 3 × 4 array of feet extends 4.75 mm downward below the 49.00 mm lip shelf into the lower tray's throat cavity -> lowest surface of upper tray sits at Z = 44.25 mm.
- **Total Usable Internal Space:** 44.25 mm - 6.75 mm = 37.50 mm.
- **Selected Closed Cassette Height:** 36.00 mm (`BODY_H = 32.80 mm`, `LID_H = 3.20 mm`).
- **Internal Usable Cavity Depth:** 30.80 mm (2.0 mm floor) vs. baseline 22.80 mm (+35.1% capacity increase).
- **Stacking Non-Interference Buffer:** 37.50 - 36.00 = 1.50 mm safe clearance below the upper carrier feet (accounting for 0.15 mm label tape and print layer variations).

### Physical Test Outcome — 2026-08-28

- Printed `cassette_body_v0_8.stl` in PETG.
- Assembled with existing v0.7/v0.8 lid and glass slide.
- Installed in lower 3 × 4 carrier tray and stacked upper carrier tray on top.
- Confirmed: Upper tray seats completely with clean clearance under its Gridfinity feet. Height standard is physically verified and frozen at 36.00 mm closed height (32.80 mm body).

### Exported v0.8 STL Audit — 2026-08-28

- `cassette_body_v0_8.stl`: 39.55 × 80.0 × 35.45 mm (nominal 38.6 × 80.0 × 32.8 mm), 376 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles, finite coordinates.
- `cassette_lid_v0_8_print.stl`: 39.55 × 80.0 × 6.5 mm, 780 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles, fully connected shell overlap graph.
- `REFERENCE_closed_assembly_DO_NOT_PRINT.stl`: 39.55 × 80.0 × 36.0 mm, 1168 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
