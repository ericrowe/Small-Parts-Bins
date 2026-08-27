# Plan 009 — Re-evaluate glass slide capture and material options

- Status: Executing — v0.3 passed; direct 75%-shorter v0.4 latch ready for test
- Depends on: No prerequisite for concept and coupon work; final carrier-envelope validation uses Plan 001 measurements
- Created: 2026-08-27
- Started: 2026-08-27
- Completed: Not completed
- Git start: `c61ff9f`
- Git completion: Not completed

## Triggering physical feedback

The Firmest 0.45 PETG retainer provided the best hold within the v0.6 snap-fit
ladder, but subsequent handling shows that the glass can still be knocked out
easily. The existing retainer is therefore an experimental best-of-ladder result,
not an adequate production capture method.

## Outcome

Develop and physically validate a more positive, replaceable pane-capture system
that resists accidental knockout and can accommodate at least two practically
useful pane thicknesses or materials without redesigning the lid's primary
capture geometry.

## Requirements

- Mechanically enclose and support every pane edge without a press fit.
- Prevent pane escape under a documented impact, rollover, and handling test.
- Keep the pane replaceable without levering tools against glass.
- Investigate end-loading geometry in which the pane slides into continuous lid
  rails and is blocked by a positive, removable end-retention mechanism.
- Compare at least one alternative positive-capture concept if it can be tested
  economically; do not select end-loading without evidence.
- Accommodate measured standard microscope slides and at least one transparent
  plastic pane candidate through the same main capture interface. Interchangeable
  non-destructive spacers or compliant backing elements are acceptable if the
  lid and edge-retention geometry remain common.
- Preserve top visibility, the 34 × 10 mm label zone where practical, hinge and
  latch access, safe edge coverage, and clearance below the carrier engagement
  plane.
- Keep the glass surface recessed or otherwise protected from stacking contact.

## Material questions to resolve

- Measure the actual glass batch rather than relying on nominal slide sizes.
- Select transparent plastic test panes based on availability, clarity, scratch
  behavior, impact resistance, thickness consistency, and safe edge finishing.
- Record whether plastic introduces unacceptable scratching, bowing, static,
  chemical compatibility, or visibility loss in routine small-parts use.
- Treat glass as the current baseline and plastic as an experimental alternative
  until comparative testing is complete.

## Non-goals

- Do not change cassette body height, footprint, divider geometry, or carrier
  geometry except where a lid envelope check is necessary.
- Do not assume a thicker or more flexible snap retainer solves positive capture.
- Do not claim universal compatibility with unspecified slide dimensions.
- Do not force, bend, drill, or impact glass during insertion or removal.

## Reusable parts and compatibility

- Preserve the v0.6 body, verified hinge geometry, 1.75 mm pin, latch relationship,
  label format, and carrier envelope if the new lid can remain compatible.
- Existing glass panes may be reused only if measured, undamaged, and compatible
  with the selected test geometry.
- Existing snap retainers remain calibration evidence but are expected to be
  superseded for production containment.
- Version every changed lid, retainer, end gate, spacer, or pane specification;
  do not overwrite v0.6.

## Implementation steps and test prints

1. [ ] Define and document a repeatable baseline knockout test using the current
   v0.6 lid, installed measured glass, and Firmest 0.45 PETG retainer. Use a safe
   enclosure and record impact direction, orientation, cycles, and outcome.
2. [ ] Measure representative glass panes and obtain/measure at least one clear
   plastic pane candidate with a meaningfully different thickness.
3. [ ] Convert the physical failure into requirements for edge engagement,
   positive end blocking, thickness accommodation, removal access, and protected
   top-surface height.
4. [x] Develop a concept matrix including end-loaded rails with a removable end
   gate and at least one credible alternative. Evaluate escape paths, print
   orientation, wear, debris traps, glass loading, part count, and compatibility.
   The v0.1 matrix retains a sliding locked bezel and keyed clip for comparison.
5. [x] Generate low-material coupons reproducing the complete pane cross-section,
   end-entry geometry, rail support, thickness accommodation, and named retention
   variants. The first set includes three channel heights, three pin bores, a
   full-length pinned-gate mechanics frame, gate, and three optional spacers.
6. [ ] Print coupons and first test them with dimensionally representative
   non-glass blanks. Reject fits that require forcing, sharp bending, prying, or
   dependence on friction alone.
   Physical selection on 2026-08-27: the 2.05 mm pin bore and 1.4 mm pane
   channel both work and meet requirements. Test material, pane identity,
   measurements, and print settings were not reported, so the broader material
   validation in Steps 2, 6, and 7 remains open.
7. [ ] Test surviving coupons with measured glass and plastic panes. Evaluate
   insertion, positive end retention, rattle, bowing, removal, rail wear, edge
   protection, and repeatability across pane thicknesses.
8. [ ] Apply the documented knockout/rollover protocol inside a protective
   enclosure. Compare escape, damage, and movement directly with the v0.6
   Firmest 0.45 baseline.
9. [ ] Select the simplest positive-capture design that passes, then generate a
   complete versioned lid and all required gates, spacers, or retainers.
10. [ ] Audit every exported STL for integrity, topology, degenerates, floating
    parts, support requirements, glass clearances, hinge/latch sections, closed
    envelope, and carrier engagement-plane clearance.
11. [ ] Print and assemble at least one complete lid with glass and one with the
    selected plastic pane. Reuse a verified body where compatible.
12. [ ] Test normal opening, latch closure, hinge sweep, pane replacement,
    repeated end-retainer cycles, loaded rollover, carrier removal, and stacked-
    carrier clearance for both pane materials.
13. [ ] Record the selected pane/capture combination, alternative material result,
    compatibility, required reprints, rejected concepts, and residual risks.

## Test safety

- Wear eye protection and contain the specimen during knockout or rollover tests.
- Inspect glass before and after every test; immediately retire chipped, cracked,
  deeply scratched, or edge-damaged panes.
- Use non-glass blanks while tuning fit and reserve glass for already-safe coupon
  variants.
- Never force a pane or use its exposed face as a reaction surface for tools.

## Acceptance criteria

- [ ] The new system prevents pane escape in the documented test that exposes
  the v0.6 Firmest 0.45 weakness.
- [ ] Retention comes from positive geometry, not friction or uncontrolled
  flexible preload alone.
- [ ] One common lid capture interface successfully retains the measured glass
  and at least one tested plastic/thickness alternative.
- [ ] Each pane can be inserted and replaced without forcing, glass prying, or
  damage to reusable lid components.
- [ ] The end gate or other closure remains positively retained after repeated
  access cycles and cannot enter the cassette cavity as a loose part.
- [ ] Visibility, labeling, hinge, latch, closed envelope, and stacked-carrier
  clearance remain acceptable.
- [ ] All printable STLs pass the complete exported-artifact audit.
- [ ] Documentation clearly identifies which material/capture combinations are
  physically verified and which remain experimental.

## Validation record

Record pane material, supplier/description, measured width/length/thickness,
coupon identifier, print material/settings, insertion/removal observations,
retention cycles, knockout protocol and results, scratches or damage, final
envelope, carrier clearance, and specimen disposition.

### Exported v0.1 coupon audit — 2026-08-27

- Nine binary printable STLs generated from the checked-in Python source.
- Every STL reports zero boundary edges and zero non-manifold edges.
- All signed mesh volumes are positive after print-orientation transforms.
- Channel ladder: 1.4, 1.8, and 2.2 mm clear heights with 27.0 mm width.
- Pin ladder: 2.05, 2.15, and 2.25 mm support-free octagonal bores.
- Full frame: 31.0 × 83.35 × 3.6 mm mechanics coupon; 0.325 mm modeled
  length clearance for a 76.3 mm pane after the 1.0 mm gate.
- The full frame intentionally exceeds the 80.0 mm cassette depth. Envelope
  compaction is unvalidated and cannot begin until the mechanics pass.

### Physical v0.1 ladder result — 2026-08-27

- Selected transverse pin bore: 2.05 mm, the shortest ladder boss.
- Selected pane-channel clear height: 1.4 mm.
- Both were reported to work and meet the requirements.
- The v0.1 full frame uses a 2.15 mm bore and 2.0 mm channel and is therefore
  superseded before printing by an exact-dimension follow-up mechanics coupon.
- Printer, material, slicer settings, pane identity, and measured pane dimensions
  remain unreported; this result does not yet validate alternate pane materials,
  the end gate, knockout retention, durability, or the final cassette envelope.

### Exported v0.2 selected-fit mechanics audit — 2026-08-27

- The versioned follow-up frame uses the physically selected 2.05 mm bore and
  1.4 mm clear pane channel; the fitted gate has 0.1 mm nominal vertical
  clearance in that channel.
- Frame: 31.0 × 83.35 × 3.6 mm, 260 triangles, zero boundary edges, zero
  non-manifold edges, zero degenerate triangles, and finite coordinates.
- Gate in print orientation: 26.6 × 1.3 × 1.0 mm, 12 triangles, zero boundary
  edges, zero non-manifold edges, zero degenerate triangles, and finite
  coordinates.
- Both binary STL sizes and encoded triangle counts were verified by re-reading
  the exported files. Pin-boss bridges positively overlap the rails and remain
  0.125 mm clear of the selected bore vertices.
- The v0.2 frame and gate now require physical assembly and cycle testing. The
  83.35 mm depth remains deliberately outside the final cassette envelope.

### Physical v0.2 mechanics result — 2026-08-27

- The printed gate fits the gate end.
- The nominal gate clearance is acceptable, but print sag required minor cleanup
  before the gate would fit. Treat the dimension as provisionally selected while
  treating support-free printability as failed.
- Gate insertion fractured one side of the frame because the surrounding
  material was too thin. Gate clearance therefore passes, but v0.2 structural
  strength fails.
- The actual glass is narrower than the frame's assumed capture geometry. The
  existing roof-rail overlap is insufficient and the pane tends to fall out;
  lateral pane capture therefore fails independently of the selected 1.4 mm
  channel height.
- Stop testing the damaged specimen. Preserve the verified gate clearance and
  1.4 mm channel height, reinforce the gate-end frame, and increase lateral roof
  overlap in the next version after the remaining observations are recorded.
  Improve or better support the sag-prone printed span without adding slicer
  support. A thicker continuous lid frame may help, but requires coupon evidence.
- The tested glass is 24.9 mm wide. Keep the 27.0 mm loading channel so wider
  alternate panes remain possible, but reduce the capture opening to a
  provisional 23.0 mm. This yields 0.95 mm overlap per side on the tested pane
  and 1.65 mm per side on a 26.3 mm pane. The resulting 2.0 mm roof ledge per
  side requires explicit print-orientation, sag, and insertion testing.
- Print material/settings, pane length/thickness, and the exact fracture location
  remain unreported.
- User suggestion: replace the separate gate and filament pin with an integral
  compliant end latch. This becomes the leading v0.3 comparison because it can
  reduce loose parts and envelope length. It must be manually actuated without
  using the glass as a cam or pry surface, spring to a positive shoulder behind
  the pane, resist accidental release, and pass cycle, creep, and impact tests.

## Stop and rollback conditions

- Stop immediately for chipped or cracked glass, unsafe ejection, rail fracture,
  or any test requiring force against the pane.
- If no common-thickness interface passes, prefer a positively retained,
  replaceable material-specific spacer over weakening edge capture.
- Keep v0.6 as historical test evidence but do not restore its snap retainer as
  the production recommendation unless new physical evidence resolves the
  knockout failure.

## Archive handoff

The walkthrough must compare the old and new escape paths, show the entry and
positive-retention mechanism, list tested pane dimensions/materials, provide the
safe replacement procedure and knockout evidence, state body/carrier compatibility,
and identify all lids or retainers that must be reprinted or retired.

## Decisions and changes to plan

- Coupon geometry began before exact pane measurements were reported so short
  print articles could run between Plan 001 carrier prints. The width, channel,
  and bore ladders deliberately bracket the current v0.6 pane specification;
  no glass may be forced into them, and measurement remains required before use.
- The first full-length article isolates positive retention mechanics and is not
  a lid or envelope-compatible release. This avoids prematurely weakening the
  end stop or pin support merely to satisfy the 80.0 mm depth.
- After the v0.2 gate-end fracture and the user's compliant-feature suggestion,
  prioritize an integral positive end latch for v0.3. Preserve the pinned-gate
  result as comparison evidence rather than adding more parts to that concept
  before the lower-part-count alternative is tested.

### Exported v0.3 compliant-latch coupon audit — 2026-08-27

- Generated a short 31.0 × 32.0 × 3.0 mm pass-through coupon so the end of the
  full pane can cross and re-engage an integral latch without printing another
  full-length frame.
- The supplied top-face-down orientation puts the 2.0 mm top capture ledges on
  the bed. The opposite ledges project 1.5 mm and form a 24.0 mm opening; this
  provides 0.45 mm overlap per side on the measured 24.9 mm pane.
- The central 8.0 × 27.0 × 0.6 mm compliant tongue has a positive end shoulder,
  no loose parts, 1.4 mm nominal release travel, and approximately 0.69% simple
  beam outer-fiber strain before print/material effects.
- The exported binary STL contains 120 triangles with zero boundary edges, zero
  non-manifold edges, zero degenerate triangles, finite coordinates, and a valid
  binary size/count. All separate modeled solids use positive overlaps rather
  than coplanar-only attachment.
- Physical validation remains required for overhang sag, latch travel and return,
  the measured pane's two-sided overlap, positive pull retention, and 25 cycles.

### Physical v0.3 result — reported after print

- Overall user result: everything works. Treat the revised overlap, channel,
  support-free ledges, compliant actuation, latch return, and positive capture as
  physically passing for this specimen.
- The user recommends reducing the compliant lever-arm footprint by about 75%.
  A direct reduction from the current 27.0 mm free length to 6.75 mm is not
  suitable without redesign: at the same 0.6 mm thickness and 1.4 mm travel,
  the simple beam estimate increases from approximately 0.69% to 11.1% strain.
- Develop the compact follow-up using a folded/serpentine compliant path that
  preserves effective flex length, or a smaller straight-length reduction with
  a physically validated strain margin. Do not trade the successful positive
  shoulder engagement for reduced travel based only on visual clearance.
- Material/settings, completion of all 25 cycles, wear/creep detail, pane length,
  and pane thickness remain unreported and must not be inferred from the general
  pass statement.

### Exported v0.4 direct-shortening coupon audit — 2026-08-27

- At the user's direction, generated a direct 75% shortening test rather than a
  folded flexure. All successful v0.3 capture dimensions remain unchanged; only
  the straight compliant free length changes from 27.0 mm to 6.75 mm.
- The coupon is 31.0 × 20.0 × 3.0 mm and uses a nearby bed-supported root
  crossbar. It contains 120 triangles with zero boundary edges, zero non-manifold
  edges, zero degenerate triangles, finite coordinates, and a valid binary STL
  size/count.
- The same-travel simple-beam estimate is 11.06% outer-fiber strain. Retain that
  value as design metadata, but the user's material experience indicates the
  0.6 mm PETG feature will tolerate the motion and physical PETG behavior is
  authoritative. PLA is explicitly excluded from this shortened geometry.
- Test actuation before inserting glass, then five inspected cycles before
  continuing to 25. Stop for whitening, creasing, cracking, permanent set,
  incomplete return, or root/frame damage.
