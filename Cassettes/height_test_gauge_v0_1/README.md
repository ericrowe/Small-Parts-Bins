# Stepped Height Test Gauge — Plan 002 v0.1

This compact test gauge evaluates candidate cassette heights inside a 3 × 4 × 7U Gridfinity carrier tray when stacked with an upper carrier in a 14U stack.

## Candidate Heights and Clearance Budget

The carrier support floor sits at $Z = 6.75\text{ mm}$, and the upper carrier stacking engagement plane sits at $Z = 49.00\text{ mm}$, leaving a total theoretical vertical envelope of $42.25\text{ mm}$.

| Step | Height | Modeled Clearance to Stacking Plane | Expected Use / Assessment |
|---|---:|---:|---|
| **Step 1** | **28.00 mm** | **14.25 mm** | Current baseline (v0.7 cassette). Excess vertical headroom. |
| **Step 2** | **34.00 mm** | **8.25 mm** | +6.0 mm internal depth (+26.3% volume increase). |
| **Step 3** | **38.00 mm** | **4.25 mm** | +10.0 mm internal depth (+43.8% volume increase). Ample finger clearance. |
| **Step 4** | **40.00 mm** | **2.25 mm** | +12.0 mm internal depth (+52.6% volume increase). Maximum safe height with 2.25 mm safety margin. |
| **Step 5** | **42.25 mm** | **0.00 mm** | Engagement Plane Datum. Touches bottom of upper stacked carrier tray. |

## Print Instructions

- File: `build/height_gauge_stepped_v0_1.stl`
- Material: PLA, PETG, or ASA (any fast draft material).
- Infill: 15% grid or gyroid.
- Orientation: Print upright on base ($Z = 0$).

## Test Method

1. Place the printed gauge inside the 3 × 4 carrier resting on the floor ($Z = 6.75\text{ mm}$).
2. Stack the second 3 × 4 carrier on top.
3. Confirm that Step 5 ($42.25\text{ mm}$) meets or sits flush with the upper tray's bottom grid, and observe the clearance gap above Steps 1, 2, 3, and 4.
4. Assess top finger pinch grasp room for each candidate height.
