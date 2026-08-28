# Plan 003 — Full-Size Cassette Body with Divider Stations (v0.8)

This directory contains the full-size prototype cassette body and divider cards physically validated for **Plan 003** (Removable Dividers) within the height-optimized **v0.8** cassette architecture.

![Small-Parts Cassette v0.8 Body with Divider Slots](build/divided_cassette_multiview.png)

## Design Summary

1. **Thickened Left Hinge Wall ($4.30\text{ mm}$):**
   - Inner left wall face is positioned at $X = -15.00\text{ mm}$ ($1.40\text{ mm}$ slot recess goes to $X = -15.60\text{ mm}$).
   - The entire vertical drop-in path clears the inward peak of the hinge knuckle ($X = -16.15\text{ mm}$) with **$+0.65\text{ mm}$ of unobstructed vertical clearance**.
   - Eliminates long-wall flex along the 80 mm span and makes the hinge mounting rock solid.
2. **Two Divider Stations at Thirds ($Y = \pm 12.87\text{ mm}$):**
   - Divides the cavity into three equal **$24.53\text{ mm}$** compartments.
   - Sits well clear of the central closure clasp ($Y \in [-4.0, +4.0\text{ mm}]$) and fingernail opening zone.
   - The body closure catch tab on the right wall remains 100% solid and uncut.
3. **Divider Card Dimensions:**
   - Width: **$33.30\text{ mm}$** ($0.10\text{ mm}$ clearance per side in the slot).
   - Height: **$31.20\text{ mm}$** (seats in $0.60\text{ mm}$ floor groove, $0.20\text{ mm}$ below closed lid ceiling).
   - Thickness: **$1.20\text{ mm}$** (Station 2 verified fit).
   - Features: Top center finger notch ($10 \times 1.5\text{ mm}$) and $0.6\text{ mm}$ bottom corner lead-ins.

## File Inventory

| File | Description | Triangles | Audit Status |
|---|---|---:|---|
| `build/cassette_body_v0_8_divided.stl` | Full-size body with 2 divider stations & thickened left wall | 476 | **0 boundary / 0 non-manifold edges** |
| `build/divider_card_full_1_2mm.stl` | Baseline 1.20 mm divider card ($33.3 \times 31.2\text{ mm}$) | 48 | **0 boundary / 0 non-manifold edges** |
| `build/divider_card_full_1_0mm.stl` | Auxiliary 1.00 mm calibration card | 48 | **0 boundary / 0 non-manifold edges** |
| `build/divider_card_full_1_4mm.stl` | Auxiliary 1.40 mm calibration card | 48 | **0 boundary / 0 non-manifold edges** |
| `generate_divided_cassette.py` | Parametric Python generator script | — | Editable source |
| `build/manifest.json` | Geometry parameters and audit records | — | Machine-readable metadata |

## Print Recommendations

- **Material:** PETG or ASA.
- **Slicer Settings:** $0.20\text{ mm}$ layer height, $0.4\text{ mm}$ nozzle, 4 perimeters, 20% infill.
- **Supports:** **No supports required.**
- **Divider Cards:** Print flat on the print bed.
