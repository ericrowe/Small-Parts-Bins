# Plan 002 Walkthrough — Optimize Cassette and Carrier Height

- Plan: `Plans/Completed/2026-08-28-002-optimize-cassette-and-carrier-height.md`
- Completed: 2026-08-28
- Outcome: **Physically Verified and Accepted**

## 1. Executive Summary

Plan 002 optimized the vertical height of the modular small-parts cassette to maximize internal hardware storage volume while maintaining strict non-interference clearance below the upper carrier tray's downward-protruding Gridfinity feet.

The physical test confirmed:
1. The **v0.8 body** ($32.80\text{ mm}$ body height, $36.00\text{ mm}$ closed cassette height) fits cleanly inside the 3 × 4 × 7U carrier tray with positive non-interference clearance below the upper carrier's Gridfinity feet.
2. Usable cavity depth increased from $22.80\text{ mm}$ (v0.7 baseline) to **$30.80\text{ mm}$ (+35.1% capacity gain)**.
3. The lid remains 100% backwards-compatible: existing printed v0.7 lids, glass slides, 6.75 mm compliant PETG latches, and 1.75 mm filament hinge pins mate directly with the v0.8 body.
4. The $36.00\text{ mm}$ closed height ($32.80\text{ mm}$ body height) is frozen as the system vertical standard for all 1U cassette models.

## 2. Complete Vertical Tolerance Budget

| Datum / Feature | Z Height | Delta / Role |
|---|---:|---|
| Drawer Ceiling Datum | $111.125\text{ mm}$ | Measured absolute ceiling ($4\text{ }^3/_8\text{ in}$) |
| Top of Upper Carrier Lip | $102.40\text{ mm}$ | $+8.725\text{ mm}$ drawer headroom |
| Upper Carrier Stacking Lip Shelf | $49.00\text{ mm}$ | Standard 7U engaged height plane |
| Lowest Surface of Upper Carrier Feet | $44.25\text{ mm}$ | Feet protrude $4.75\text{ mm}$ below shelf |
| Top of Closed v0.8 Cassette Lid | $42.75\text{ mm}$ | $+1.50\text{ mm}$ safe foot non-interference buffer |
| Cassette Split-Line Rim | $39.55\text{ mm}$ | $3.20\text{ mm}$ lid thickness |
| Cassette Inside Floor | $8.75\text{ mm}$ | $30.80\text{ mm}$ usable cavity depth (+35.1% volume) |
| Lower Carrier Support Floor Datum | $6.75\text{ mm}$ | $2.00\text{ mm}$ cassette bottom floor |
| Baseplate Datum | $0.00\text{ mm}$ | $6.75\text{ mm}$ carrier base & floor |

## 3. Physical Validation Results

- **Component:** `Cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8.stl` printed in PETG.
- **Assembly:** Paired with physically verified v0.7/v0.8 PETG lid, 1.15 mm microscope slide glass, and 1.75 mm filament hinge pin.
- **Fit & Stacking:** Installed into the lower 3 × 4 carrier tray; upper carrier tray placed on top. The upper tray seated completely on the lower tray's lip shelf without any contact or binding against the cassette.

## 4. Released Component Inventory

- Printable Body STL: `Cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8.stl` (376 triangles, 0 boundary edges, 0 non-manifold edges)
- Printable Lid STL: `Cassettes/glass_slide_cassette_40x80/build/cassette_lid_v0_8_print.stl` (780 triangles, 0 boundary edges, 0 non-manifold edges)
- Component README: `Cassettes/glass_slide_cassette_40x80/README.md`
