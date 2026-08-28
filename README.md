# Gridfinity Glass-Window Cassette System

This project is developing a durable, modular storage system for screws, nuts,
bolts, and other small hardware. Individually closed and labeled cassettes sit
inside stackable Gridfinity-compatible carrier trays, preventing the broad spill
failure of conventional open bins while keeping contents and approximate stock
levels visible through replaceable microscope-slide glass.

> [!WARNING]
> **AI-assisted development:** This project includes dimensions, code, geometry,
> documentation, and recommendations produced with assistance from generative
> AI. AI output can be incomplete, internally inconsistent, or geometrically
> wrong even when source calculations, previews, or mesh audits appear valid.
> Nothing in this repository is a certified engineering design or a substitute
> for independent review, slicer inspection, test prints, measurements, and
> real-world validation.
>
> Printed parts and glass can fail. Inspect every exported STL and sliced toolpath,
> reject chipped or forced glass, wear appropriate eye protection when handling
> or testing glass, and keep hands clear of sharp fragments. Do not rely on an
> unverified cassette or carrier to contain hazardous, valuable, food-contact,
> medical, electrical-safety-critical, or otherwise safety-critical contents.
> The person fabricating and using these parts is responsible for determining
> whether a particular revision, material, printer, and application are safe.

> [!CAUTION]
> **Active development:** This project is a work in progress. Dimensions,
> tolerances, interfaces, filenames, instructions, and compatibility may change
> at any time without notice as physical-test results become available. A part
> that fits one revision, material, printer, or slicer configuration may not fit
> another, and compatibility with future releases is not guaranteed unless it is
> explicitly documented.
>
> Before printing, record the exact Git commit and part version being used,
> review the matching README, manifest, and physical-test notes, and inspect the
> sliced toolpath. Print the supplied functional coupons and one complete sample
> before committing to a large batch. Do not mix revisions based only on similar
> appearance or filenames; use the documented compatibility rules. Keep known-
> good printed parts until their replacements have passed the same real-world
> tests, and expect failed or superseded prototypes during development.

## Project goals

- Keep every cassette individually closed when removed, handled, or tipped.
- Make contents and 9 mm Brother TZe labels visible from above in an open drawer.
- Use replaceable, mechanically retained microscope-slide glass rather than
  press-fit acrylic.
- Build a compatible family of cassette sizes on a consistent cassette sub-grid.
- Support optional removable dividers that form two or three equal compartments
  and minimize very-small-part transfer during rollover.
- Hold cassettes in loaded, stackable carriers using the standard 42 mm
  Gridfinity pitch, base, stacking interface, and 7 mm height increments.
- Fit practical loaded stacks below the measured drawer ceiling of
  **111.125 mm (4 3/8 in)**.
- Treat exported-STL audits and physical prints—not visual plausibility—as the
  authority for functional geometry.

## Current status — 2026-08-27

The canonical smallest cassette baseline is v0.7 with the unchanged maximum
closed envelope of 39.55 × 80.0 × 28.0 mm. It retains the physically verified
v0.6 hinge geometry and works with the successful v0.5/v0.6/v0.7 body and straight
1.75 mm filament pin. The end-loaded pane capture channel, integral 6.75 mm
compliant PETG latch, tight 0.50 mm perimeter cutout, reinforced closure clasp,
and concentric Z = 24.80 mm split line are physically verified and complete
([Plan 009](Plans/Completed/2026-08-27-009-re-evaluate-glass-slide-capture.md)).

The active in-work plan is [Plan 001](Plans/001-validate-14u-carrier-stack.md),
physical validation of two identical 3 × 4 × 7U carriers. The modeled carrier
stack height is 102.4 mm, leaving 8.725 mm nominal clearance below the drawer
ceiling. Carrier 1 of 2 is currently recorded as printing; carrier 2 and all
loaded stack, throat, stability, and drawer-clearance results remain pending.

Nothing about carrier v0.1 should yet be treated as physically verified. Its
dimensions, Gridfinity engagement, six-cassette fit, and loaded stack behavior
remain provisional until both prints are tested.

## Current reference configuration

| Component | Current reference | Validation state |
|---|---|---|
| Smallest cassette | v0.7 lid with v0.5/v0.6/v0.7 body, 39.55 × 80.0 × 28.0 mm closed | Physically verified; hinge, capture, clasp, and split line pass |
| Window | Plain slide glass, maximum intended 26.3 × 76.3 × 1.2 mm | Measure each delivered batch |
| Pane capture | End-loaded 27.0 × 1.4 mm channel; integral 6.75 mm PETG latch | Physically verified (Plan 009 complete) |
| Hinge pin | Straight 1.75 mm printer filament | Works well in the verified hinge pair |
| Reference carrier | 3 × 4 × 7U, six cassettes | v0.1 physical test in progress |
| Two-carrier stack | 14U, modeled 102.4 mm overall | Not yet physically verified |
| Drawer ceiling | 111.125 mm | Measured absolute ceiling |

## Development sequence

Multiple plans may be in work when their current steps are independent or one is
waiting for a physical print. Plans 002–008 are fully developed in
[`Plans/Queued/`](Plans/Queued/) and cover height optimization, cassette
dividers, finalization of the smallest system, larger cassettes, mixed-layout
carriers, durability/material testing, and the production baseline.

The authoritative queue order and its rationale exist only in
[`Plans/PRIORITIES.md`](Plans/PRIORITIES.md). Plan 009 was completed and moved
to [`Plans/Completed/`](Plans/Completed/). Next queued plan is Plan 002.

The complete lid is available in the current
[`glass-slide cassette release`](Cassettes/glass_slide_cassette_40x80/) as
`cassette_lid_v0_7_print.stl`. At the user's direction, that directory contains
only the current generated release artifacts; Git preserves v0.6 history.

New ideas belong in [IDEAS.md](IDEAS.md) and must remain under three sentences.
See the [plan pipeline](Plans/README.md) for promotion, execution, Git checkpoint,
validation, and dated archive rules.

## Repository map

- [`AGENTS.md`](AGENTS.md) — binding dimensions, physical findings, validation
  rules, compatibility history, and repository working agreements.
- [`Cassettes/`](Cassettes/) — cassette generators, printable releases,
  manifests, previews, and assembly references.
- [`Carriers/`](Carriers/) — carrier generators, printable tests, manifests,
  previews, and physical-test records.
- [`Plans/`](Plans/) — in-work plans, the prioritized queue, templates, checker,
  and completed-plan archive.
- [`IDEAS.md`](IDEAS.md) — concise unprocessed project ideas.
- `Trays/` — reserved for future tray-related work not represented by the
  current carrier release.

## Working rules

- Read this README, `AGENTS.md`, the active plan, relevant release README and
  manifest, and the latest physical-test notes before changing geometry.
- Print exact functional coupons before committing material to complete parts.
- Never scale parts in the slicer to correct tolerances; change named source
  dimensions and release a new version.
- Preserve tested history through Git. A working release directory may replace
  old generated artifacts after a checkpoint when the user explicitly chooses
  Git rather than parallel copies as the revision store.
- Keep modeled, printed, and physically verified claims clearly separated.
- Treat all AI-assisted output as unverified until independently reviewed and
  validated against the actual exported artifact and physical print.
- Record the exact revision before printing, validate one sample before a batch,
  and do not assume compatibility between versions unless it is documented.
- Before completing a plan, reconcile every required project and release
  document listed in `AGENTS.md`, then archive the plan with its walkthrough.

## License

This project is available under the [MIT License](LICENSE). The license's
software warranty disclaimer supplements, and does not replace, the AI-use,
glass-handling, print-validation, and physical-safety warning above.
