# Plan 005 — Develop the larger cassette family

- Status: Queued
- Depends on: Plan 004 verified smallest-module baseline
- Created: 2026-08-27
- Started: Not started
- Completed: Not completed
- Git start: Not committed
- Git completion: Not completed

## Outcome

Develop a deliberately limited family of larger, individually closed cassettes
using integer multiples of the verified cassette sub-grid and the same carrier,
window, label, closure, and divider principles.

## Requirements

- Select sizes from demonstrated hardware-volume needs and useful carrier mixes.
- Use integer multiples of the verified cassette sub-grid; do not enlarge parts
  merely to align them to a 42 mm Gridfinity cell.
- Maintain a consistent external clearance convention across the family.
- Support removable dividers that create equal partitions and minimize small-
  part transfer during rollover.
- Use one or more standard microscope-slide window modules without press fits.
- Keep hinge access, latch access, labels, and all features below the carrier
  engagement plane.

## Non-goals

- Do not attempt every mathematically possible sub-grid multiple.
- Do not change the verified smallest cassette to simplify larger sizes.
- Do not assume one long hinge or one large glass pane will print or behave like
  the smallest verified components.

## Reusable parts and compatibility

- Reuse the verified hinge profile, pin material, Plan 009 pane-capture strategy,
  label tape, divider interface, and carrier datums when their tested spans
  permit.
- Prefer repeated standard window or hinge modules over untested long spans.
- Mark every new size provisional until its own complete print passes.

## Implementation steps and test prints

1. [ ] Inventory representative stored hardware and select the smallest useful
   set of larger module footprints and target volumes.
2. [ ] Produce a packing matrix showing each proposed cassette in verified and
   prospective carrier throats with real inter-cassette clearance.
3. [ ] Define per-size window count, hinge-knuckle arrangement, latch count,
   divider stations, label zones, and removal access.
4. [ ] Generate size-specific fit coupons for hinge spans, latch regions,
   divider interfaces, glass pockets/retainers, and carrier throat clearance.
5. [ ] Print and validate coupons for the first proposed size; revise named
   tolerances instead of scaling parts.
6. [ ] Generate and audit one complete cassette of that size, including opening
   sweep, pin containment, glass capture, divider clearance, islands, topology,
   and closed envelope.
7. [ ] Print, assemble, load, and test the complete cassette for hinge/latch
   operation, divider transfer, glass security, removal, rollover, and stacking.
8. [ ] Repeat steps 4–7 independently for each additional selected size; do not
   infer physical success from another footprint.
9. [ ] Print a representative mixed group and verify that the family shares a
   consistent sub-grid and clearance convention.
10. [ ] Publish a compatibility matrix covering bodies, lids, retainers,
    dividers, pins, windows, and carrier layouts.

## Acceptance criteria

- [ ] Every released size occupies an integer sub-grid multiple and participates
  in at least one useful carrier layout.
- [ ] Each size has its own successful coupon and complete physical print.
- [ ] Windows are mechanically captured without forcing glass.
- [ ] Hinges and latches operate throughout their required range without support
  trapped in functional voids.
- [ ] Divider configurations remain installed and have documented rollover
  transfer results.
- [ ] All features remain below the appropriate carrier engagement plane.
- [ ] Every printable STL passes the full exported-artifact audit.

## Validation record

Maintain a per-size table of dimensions, material/settings, coupon results,
complete-print measurements, cycle tests, rollover transfers, compatible layouts,
and verified versus provisional components.

## Stop and rollback conditions

- Remove a proposed size from this plan if it lacks a useful carrier layout or
  requires an incompatible interface solely for extra volume.
- Split an unexpectedly complex size into a later idea rather than holding the
  entire family plan open indefinitely.

## Archive handoff

The walkthrough must explain the selected family, rejected sizes, sub-grid
math, per-size test evidence, shared parts, unique parts, and mixing rules.
