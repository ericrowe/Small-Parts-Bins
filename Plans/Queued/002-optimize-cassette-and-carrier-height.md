# Plan 002 — Optimize cassette and carrier height

- Status: Queued
- Priority: 2
- Depends on: Plan 001 physical measurements and Plan 009 verified lid/capture envelope
- Created: 2026-08-27
- Started: Not started
- Completed: Not completed
- Git start: Not committed
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

1. [ ] Import Plan 001 measurements for engaged height, support-floor height,
   lip seating, drawer clearance, warping, and loaded behavior.
2. [ ] Define the vertical tolerance budget, including a named practical drawer
   clearance and cassette-to-engagement-plane clearance.
3. [ ] Generate a low-material stepped height gauge reproducing the actual
   carrier floor and stacking plane, with clearly labeled candidate cassette
   heights.
4. [ ] Print and measure the gauge in the intended material and settings;
   reject candidates that bind, touch the upper carrier, or lack removal room.
5. [ ] Generate a body-height coupon using the selected wall, floor, hinge-side
   attachment, and latch-side geometry in the full print orientation.
6. [ ] Print the coupon and check wall quality, hinge/latch attachment support,
   dimensional accuracy, and fit in a loaded carrier.
7. [ ] Create a versioned optimized-height cassette body and assembly reference.
   Change no lid dimensions unless coupon evidence requires it.
8. [ ] Audit the exported STL for topology, integrity, envelope, hinge/latch
   clearances, unsupported starts, and engagement-plane clearance.
9. [ ] Print one complete optimized cassette, assemble it with representative
   hardware, and test closure, handling, removal, and carrier stacking.
10. [ ] Load representative optimized cassettes into both carriers and repeat
    the complete drawer-fit test before freezing vertical dimensions.
11. [ ] Record measurements, settings, reusable components, failures, and the
    selected vertical standard in the release notes and manifest.

## Acceptance criteria

- [ ] The selected cassette height has a documented tolerance budget rather
  than relying on nominal subtraction.
- [ ] The complete cassette closes and operates without altered slicer scale.
- [ ] The upper loaded carrier seats fully without cassette contact.
- [ ] The 14U loaded stack fits the drawer with the practical clearance defined
  from Plan 001 evidence.
- [ ] The height increase produces useful internal capacity and does not make
  cassette removal materially worse.
- [ ] All printable STLs pass binary, finite-coordinate, degenerate-triangle,
  boundary-edge, and non-manifold-edge audits.
- [ ] Physical results distinguish the tested material/settings from untested
  alternatives.

## Validation record

Populate during execution with candidate heights, printed dimensions, drawer
measurements, failure observations, STL audit output, and photographs or
sectional previews where available.

## Stop and rollback conditions

- Retain the v0.6 28.0 mm envelope if added height causes unreliable stacking,
  poor removal, wall instability, or insufficient drawer clearance.
- If Plan 001 invalidates the 7U carrier, revise the carrier in this plan before
  optimizing the cassette; do not optimize against a rejected datum.

## Archive handoff

The walkthrough must state the final support-floor and engagement-plane datums,
selected cassette height, measured stack/drawer results, parts that remain
reusable, and all untested material combinations.
