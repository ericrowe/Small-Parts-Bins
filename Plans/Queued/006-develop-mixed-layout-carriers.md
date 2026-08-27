# Plan 006 — Develop mixed-layout carriers

- Status: Queued
- Depends on: Plan 005 verified cassette-family envelopes
- Created: 2026-08-27
- Started: Not started
- Completed: Not completed
- Git start: Not committed
- Git completion: Not completed

## Outcome

Create a small, useful carrier family that organizes verified cassette-size
combinations while remaining stackable, Gridfinity compatible, removable from
the drawer, and safe for the glass windows.

## Requirements

- Base footprints on the 42 mm Gridfinity pitch and verified base/lip profile.
- Calculate layouts against each carrier's narrowest measured or authoritative
  stacking-lip throat.
- Maintain at least 2.0 mm printed walls and real insertion clearance.
- Keep every cassette feature below the stacking engagement plane.
- Provide fingertip or equivalent removal access without prying on glass.
- Prefer fewer than ten cassettes per carrier when practical while allowing
  dense layouts where part size or packing clearly benefits.

## Non-goals

- Do not create a unique carrier for every possible cassette permutation.
- Do not reduce walls or use zero-clearance packing to rescue a layout.
- Do not alter cassette envelopes in this plan.

## Reusable parts and compatibility

- Preserve the verified 3 × 4 six-smallest-cassette carrier as the baseline.
- Reuse the verified 7U vertical architecture unless a specific cassette family
  member has an already documented height requirement.
- Keep carriers mutually stackable regardless of their internal layout.

## Implementation steps and test prints

1. [ ] Rank mixed layouts by real storage use, cassette count, wasted throat
   area, removal access, and compatibility with drawer footprints.
2. [ ] Select the minimum carrier set that covers the valuable combinations.
3. [ ] Calculate exact packed envelopes, inter-cassette gaps, throat clearances,
   wall thicknesses, and engagement-plane clearance for each layout.
4. [ ] Generate shallow throat/packing coupons with the actual corner and access
   geometry for every selected layout.
5. [ ] Print coupons and insert the complete physical cassette mix; record
   binding, rattle, orientation errors, and removal behavior.
6. [ ] Revise named clearances and generate one full carrier for the first layout.
7. [ ] Audit its STL for profile, topology, coordinates, degenerates, islands,
   throat dimensions, floor support, walls, and stacking envelope.
8. [ ] Print the full carrier, load it, stack it above and below the baseline
   carrier, and test handling and drawer clearance.
9. [ ] Repeat full generation and testing for each remaining selected layout.
10. [ ] Test deliberately incorrect cassette placements and add simple visual or
    geometric orientation cues only where they prevent plausible misuse.
11. [ ] Publish layout diagrams and a compatibility table.

## Acceptance criteria

- [ ] Every released layout has a successful packing coupon and full loaded print.
- [ ] All intended cassettes insert and remove without glass loading.
- [ ] No unintended orientation appears to fit while preventing stacking or
  damaging a functional feature.
- [ ] Mixed carriers stack with the baseline in both orders and remain engaged
  during normal handling.
- [ ] Loaded stacks fit the drawer with the verified practical clearance.
- [ ] All printed walls meet the 2.0 mm minimum and all STLs pass their audits.

## Validation record

Record each layout, physical cassette identities, measured gaps, material and
settings, stack order, drawer measurements, access observations, failures, and
final compatibility classification.

## Stop and rollback conditions

- Reject layouts that require fragile wall sections, glass contact, awkward
  removal, or ambiguous cassette orientation.
- Keep low-value mathematical permutations documented but unreleased.

## Archive handoff

The walkthrough must show each released layout, supported combinations, stacking
tests, removal method, packing clearances, and which layouts were rejected.
