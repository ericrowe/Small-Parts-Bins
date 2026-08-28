# 3 × 4 Gridfinity carrier — 14U physical release v0.1

This validated carrier uses **two identical 7U carriers**. Printing two copies of
`build/carrier_3x4_7u_v0_1.stl` forms a 14U stack with a nominal overall height
of 102.4 mm including the exposed top stacking lip. Inside the measured 111.125 mm
drawer, that leaves 8.725 mm nominal clearance.

## Validation status — 2026-08-28

- **Physically Verified:** Two printed 3 × 4 × 7U carriers seat perfectly on existing
  Gridfinity baseplates in the target drawer and form a stable 14U stack with ample
  drawer clearance.
- **Plan 001:** Complete and physically accepted.
- Holds six modular cassettes per tray (3-across × 2-deep) with solid continuous
  outer walls.

Each carrier accepts six modular cassettes in a 3-across × 2-deep arrangement.
The cassette support floor is at Z = 6.75 mm and the stacking engagement plane
is at Z = 49.0 mm (lowest upper-tray foot surface is at Z = 44.25 mm).

## Print set

| File | Quantity | Purpose |
|---|---:|---|
| `build/carrier_3x4_7u_v0_1.stl` | 2 | Printable lower and upper carriers |
| `build/REFERENCE_two_carrier_14u_stack_DO_NOT_PRINT.stl` | 0 | CAD/slicer height reference only |

Print upright as supplied. Reasonable starting settings are a 0.4 mm nozzle,
0.20 mm layers, four perimeters, and no internal support. The carrier walls are
2.6 mm at the working throat, exceeding the project's 2.0 mm minimum.

All four outer carrier walls are continuous solids (2.6 mm at the working
throat). Cassette extraction is handled via top-edge pinch-grip features on the
cassettes themselves, avoiding holes in the carrier perimeter.

## Physical checks to record

1. Load six closed v0.6 cassettes into each tray and check insertion, removal,
   binding, and rattle. Do not pry against the glass.
2. Stack the loaded carriers and confirm that the upper carrier seats on the
   lip without touching any cassette feature.
3. Measure one carrier's engaged height, the complete two-carrier height, and
   the remaining drawer clearance at several drawer locations.
4. Tip and handle the loaded stack normally, checking that the carrier remains
   engaged and every cassette stays latched.

Record the outcome in `PHYSICAL_TEST_NOTES.md` before changing the carrier
geometry or releasing a new revision.

This release is a physical-fit prototype. Its Gridfinity profile, nominal
120.3 × 162.3 mm throat, 14U drawer result, and access openings remain
provisional until the printed test is reported.

![14U test layout and height section](build/carrier_14u_test_preview_v0_1.svg)

Regenerate with `python3 generate_carrier.py`.
