# Glass-slide small-parts cassette — prototype v0.8 (Optimized Height, Internal Ridges & Top Pinch Grips)

Version 0.8 implements the vertical height optimization (Plan 002), removable divider system (Plan 003), internal flanking wall ridges with reinforced closure clasp (Plan 010), and top-surface pinch grips (Plan 011).
It increases the closed cassette envelope to **$39.55 \times 80.0 \times 36.0\text{ mm}$**
(body height $32.80\text{ mm}$, lid height $3.20\text{ mm}$), providing **$30.80\text{ mm}$ of
usable internal cavity depth** (+35.1% internal volume increase over the v0.7 baseline)
while maintaining a safe **$1.50\text{ mm}$ clearance margin** below the upper carrier
tray's bottom Gridfinity feet (lowest foot surface at $Z = 44.25\text{ mm}$, cassette floor at $Z = 6.75\text{ mm}$).

Key features:
1. **Optimized Usable Depth:** $30.80\text{ mm}$ internal cavity depth with $2.0\text{ mm}$ solid floor.
2. **Top-Surface Pinch Grips (Plan 011):** Transverse textured grip flutes integrated into the solid entry and label roof zones of the lid enable effortless one-handed vertical extraction from packed carrier trays from directly above, without requiring finger gaps between cassettes or contacting the glass.
3. **Flat Body Ends (Plan 011):** Body ends are flat at $80.00\text{ mm}$ length, restoring the full $\approx 2.30\text{ mm}$ $Y$-clearance across the carrier throat and preventing inter-row carrier binding.
4. **Internal Flanking Ridges (Plan 010):** Vertical ridges projecting $+0.80\text{ mm}$ into the cavity ($1.50\text{ mm}$ wide along Y) flank the divider slots on the front wall. They create deep $1.40\text{–}1.60\text{ mm}$ guide channels ($3.00\text{ mm}$ total engagement across the cavity) and brace the front wall span down from $80\text{ mm}$ to $22.6\text{ mm}$ around the center latch.
5. **Loose-Fit Gravity Drop-In Dividers:** $33.00\text{ mm}$ wide divider cards provide **$+1.10\text{ mm}$ of lateral float clearance** across the $34.10\text{ mm}$ channel bottom span, completely eliminating outward wall wedging while maintaining $\ge 0.75\text{ mm}$ of positive capture overlap past the channel lips.
6. **Reinforced $0.85\text{ mm}$ Closure Clasp:** $1.25\text{ mm}$ thick cantilever beam on the lid with $0.85\text{ mm}$ undercut catch on the front body wall guarantees firm, positive snap retention in both divided and undivided configurations.
7. **Backwards Compatibility:** Retains the physically verified positive end-loaded glass retention channel ($27.0 \times 1.4\text{ mm}$), 6.75 mm compliant PETG latch, and 3-knuckle peaked filament hinge.

![v0.8 Body Divided 3D Multi-View](../../docs/images/cassette_body_v0_8_divided_multiview.png)

![v0.8 Lid 3D Multi-View](../../docs/images/cassette_lid_v0_8_multiview.png)

## Print these files

- `build/cassette_lid_v0_8_print.stl` (lid with top pinch grip flutes; print top/label-face down in PETG)
- `build/cassette_body_v0_8_divided.stl` (divided body with internal flanking ridges and flat $80.0\text{ mm}$ ends; print upright in PETG or ASA)
- `build/cassette_body_v0_8.stl` (undivided body with flat $80.0\text{ mm}$ ends; print upright in PETG or ASA)
- `build/divider_card_1_2mm.stl` (baseline $33.00 \times 31.20 \times 1.20\text{ mm}$ divider card with top extraction notch and lead-in chamfers)

Print all parts exactly as supplied without internal support. A 0.4 mm nozzle,
0.20 mm layers, and four perimeters remain reasonable starting settings. Keep the
seam away from the hinge bores.

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
the pane completely past the shoulder, then release it.

The 23.0 × 58.5 mm visible window and 34.0 × 10.0 mm label zone are unchanged.
The full closed envelope is **39.55 × 80.0 × 36.0 mm**.

## Hinge, Catch & Divider Features

- Original three-knuckle removable-pin hinge (2.25 mm body bore, 2.10 mm lid bore).
- Continuous bed-supported roots beneath both lid knuckles with 0.20 mm overlap.
- Reinforced closure snap: 1.25 mm cantilever beam on lid with **0.85 mm undercut catch** on body wall.
- Top pinch grip flutes: Transverse textured grooves on entry pads and rear roof for zero-gap extraction.
- Internal flanking ridges: $+0.80\text{ mm}$ inward projection $\times 1.50\text{ mm}$ width at $Y = \pm 12.87\text{ mm}$ with $45^\circ$ top lead-in funnel chamfers.
- Divider card standard: $33.00\text{ mm}$ width $\times 31.20\text{ mm}$ height $\times 1.20\text{ mm}$ thickness with $10 \times 1.5\text{ mm}$ top extraction notch and $0.8\text{ mm}$ bottom corner lead-in chamfers.

## Assembly and test order

1. Inspect the printed body, divider channels, flanking ridges, pane channel, and hinge bores.
2. Insert pane into lid by depressing compliant tongue manually. Slide pane to far stop and release.
3. Assemble the lid to the body with approximately 75 mm of straight 1.75 mm filament.
4. Drop in divider cards: verify smooth gravity drop-in without wall friction.
5. Verify smooth hinge rotation through at least 120 degrees and positive clasp closure.
6. Place cassette inside a 3 × 4 carrier tray and extract from above using the top pinch grips.
7. Stack a second carrier tray on top to confirm full seating without contact.

## Export validation

All binary STLs pass topological inspection reporting zero boundary edges, zero non-manifold edges, zero degenerate triangles, and finite coordinates.

Regenerate all current artifacts with:

```bash
python3 generate_cassette.py --out build --preview
```
