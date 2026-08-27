# Glass-slide small-parts cassette — prototype v0.7

Version 0.7 integrates the physically validated Plan 009 end-loaded pane channel
and shortened compliant PETG latch. Following physical test feedback confirming
that the retention of the glass slide and hinge is functional, this revision
incorporates four key refinements:
1. **Aesthetic Gap Refinement:** The large entry opening has been tightened to a
   uniform 0.50 mm perimeter outline matching the finger pad, compliant tongue,
   and root gussets.
2. **Reinforced Clasp:** The closure snap has been significantly strengthened with
   a 1.20 mm thick cantilever tongue (up from 0.85 mm), 8.0 mm wide engagement span,
   and 0.65 mm positive undercut interference (up from 0.40 mm).
3. **Flush Split-Line Body Walls:** Upper body side and end walls are raised to
   27.20 mm to meet the lid's top plate flush with no exterior gap, increasing
   usable internal cavity depth to 25.20 mm while keeping the 28.0 mm closed ceiling.
4. **Carrier Removal Ergonomics:** Outer carrier walls are solid; finger pinch
   extraction is facilitated via the top edge.

![Full-lid overview](build/cassette_preview_v0_7.svg)

![Pane loading and end stop](build/cassette_capture_section_v0_7.svg)

![Actual exported lid mesh](build/cassette_lid_mesh_preview_v0_7.svg)

## Print these files

- `build/cassette_lid_v0_7_print.stl` (print top/label-face down in PETG)
- `build/cassette_body_v0_7.stl` (print upright in PETG or ASA to benefit from the raised 27.20 mm walls and reinforced catch)

Print both parts exactly as supplied without internal support. A 0.4 mm nozzle,
0.20 mm layers, and four perimeters remain reasonable starting settings. Keep the
seam away from the hinge bores and record the actual material, printer, slicer, and
settings in `PHYSICAL_TEST_NOTES.md`.

Do not print `REFERENCE_closed_assembly_DO_NOT_PRINT.stl`.

## Pane-capture geometry

| Feature | Dimension |
|---|---:|
| Loading channel | 27.0 mm wide × 1.4 mm clear height |
| Top/visible opening | 23.0 mm |
| Opposite opening | 24.0 mm |
| Tested glass width | 24.9 mm |
| Overlap per side on tested glass | 0.95 mm top / 0.45 mm opposite |
| Maximum intended pane | 26.3 × 76.3 × 1.2 mm |
| Axial clearance at 76.3 mm length | 0.70 mm |
| PETG tongue | 8.0 mm wide × 0.8 mm thick × 6.75 mm free length with 45° root gussets |
| Latch finger pad | 10.0 mm wide |
| Frame entry slot cutout | Tight 0.50 mm perimeter outline (11.0 mm pad cut / 9.0 mm tongue cut) |
| Relaxed tongue-to-glass gap | Flush at channel ceiling (0.2–0.3 mm clearance over 1.1–1.2 mm glass) |

The pane enters at the end opposite the label, slides under the solid label band,
and stops at the far end. Manually depress the compliant tongue outward, slide
the pane completely past the shoulder, then release it. The shoulder returns
behind the trailing pane edge and blocks withdrawal. It must not remain pressed
against the glass face, and the glass must not be used to cam the latch aside.

The 23.0 × 58.5 mm visible window and 34.0 × 10.0 mm label zone are unchanged.
The full closed envelope remains 39.55 × 80.0 × 28.0 mm.

## Hinge and Clasp Features

- Original three-knuckle removable-pin hinge.
- 2.25 mm nominal body bore and 2.10 mm nominal lid bores with support-free peaked profiles.
- Continuous bed-supported roots beneath both lid knuckles.
- 0.20 mm root overlap past the hinge axis.
- 0.8 mm axial knuckle gaps and checked 0–120 degree sweep.
- Reinforced closure snap: 1.20 mm cantilever beam on lid with 0.65 mm undercut catch on body wall.
- 34 × 10 mm label zone and cassette/carrier envelope.

## Assembly and test order

1. Inspect the printed pane channel, opposite ledges, tongue root, hinge roots,
   and bores. Stop for cracks, incomplete tongue return, or obstructive sag.
2. With the lid held clear of the work surface, depress the pane tongue manually.
   Insert only an undamaged, measured pane; never force or pry the glass.
3. Slide the pane to the far stop, release the tongue, and confirm the shoulder
   returns fully behind the pane without touching its face.
4. Gently pull the pane toward the entry. Positive shoulder engagement—not
   friction—must prevent withdrawal.
5. Assemble the lid to the body with approximately 75 mm of straight 1.75 mm
   filament. Verify hinge motion through at least 120 degrees and positive body-latch closure.
6. Evaluate perimeter-supported lid stiffness, glass rattle/bowing, latch access,
   label clearance, and glass replacement for 25 cycles.
7. Only after those checks pass, test loaded rollover and the documented knockout
   comparison inside a protective enclosure.

Wear eye protection and contain the specimen during rollover or impact work.
Reject chipped, cracked, scratched, or oversize glass immediately.

## Export validation

The binary v0.7 lid contains 684 triangles and the v0.7 body contains 376 triangles,
each reporting zero boundary edges, zero non-manifold edges, zero degenerate triangles,
and finite coordinates. Their binary sizes and encoded triangle counts were re-read after
export. The body, lid, and reference assembly retain the 39.55 × 80.0 × 28.0 maximum closed envelope.

Regenerate all current artifacts with:

```bash
python3 generate_cassette.py --out build --preview
```
