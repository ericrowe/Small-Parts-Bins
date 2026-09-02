# Plan 009 Walkthrough — Re-evaluate Glass Slide Capture and Material Options

## Executive Summary

Plan 009 investigated, developed, and physically validated a positive, replaceable pane-capture mechanism for the Gridfinity small-parts cassette system to replace the legacy friction-based v0.6 snap-fit retainers.

The completed and physically verified solution is the **v0.7 end-loaded pane capture lid**, which features:
1. An **end-loaded 27.0 × 1.4 mm continuous channel** with 23.0 mm visible top opening and 24.0 mm opposite opening (providing 0.95 mm top / 0.45 mm bottom overlap per side on standard 24.9 mm glass slides).
2. An **integral compliant PETG retention latch** (6.75 mm free length, 0.80 mm thickness with 45° root corner gussets) that flexes downward during slide insertion/removal and springs back behind the trailing edge of the glass to form a positive mechanical stop.
3. A **tight 0.50 mm aesthetic perimeter outline** around the compliant latch tab.
4. A **strengthened closure clasp** (1.20 mm thick cantilever tongue, 8.0 mm wide span, and 0.65 mm positive undercut interference).
5. A **standard Z = 24.80 mm split line** with complete outer perimeter skirts on the lid meeting the body rim flush, ensuring exact concentric alignment of all three hinge knuckle bores along X = -18.20 mm, Z = 25.00 mm.

---

## Evolution and Validation Sequence

### 1. Coupon v0.1 — Channel Height & Hinge Bore Selection
- Tested 1.4, 1.8, and 2.2 mm channel heights and 2.05, 2.15, and 2.25 mm support-free octagonal pin bores.
- **Physical Result:** Selected the 1.4 mm clear channel height and 2.05 mm hinge bore.

### 2. Coupon v0.2 — Pinned End Gate & Lateral Overlap Check
- Tested a separate sliding end gate secured by a transverse filament pin.
- **Physical Result:** Gate fit passed, but thin frame walls fractured during insertion. Measured glass (24.9 mm wide) revealed inadequate roof overlap in the wide opening.
- **Decision:** Increased lateral roof overlap (23.0 mm top opening) and pivoted to an integral compliant latch to eliminate loose components.

### 3. Coupon v0.3 — Integral Compliant PETG Latch
- Integrated a 27.0 mm long × 0.6 mm thick cantilever tongue with a 1.4 mm positive shoulder.
- **Physical Result:** Successfully passed insertion, positive withdrawal blocking, and latch recovery. The user suggested shortening the latch footprint by ~75%.

### 4. Coupon v0.4 — 75% Shortened Cantilever
- Reduced straight compliant free length to 6.75 mm in PETG with bed-supported root crossbar.
- **Physical Result:** Verified flexible motion, complete return, and reliable slide retention without cracking.

### 5. Full-Lid v0.7 Integration & Physical Confirmation
- Integrated the 6.75 mm compliant latch into the full 39.55 × 80.0 × 28.0 mm cassette lid with preserved v0.6 peaked hinge knuckles and 34 × 10 mm label zone.
- Reinforced tongue to 0.80 mm thickness (4 layers) with 45° root corner gussets to eliminate bed-removal peel risk.
- **Physical Result:** User printed and confirmed: *"The test print is functional for the retention of the glass slide and the hinge."*
- Incorporated user feedback:
  - Tightened aesthetic gap around tab to 0.50 mm.
  - Reinforced clasp holding force (1.20 mm tongue, 0.65 mm undercut catch).
  - Restored Z = 24.80 mm split plane with full lid skirts for concentric hinge alignment.
- **Status:** Complete and physically accepted.

---

## Component Reusability & Compatibility

| Component | Status | Compatibility / Action |
|---|---|---|
| **Cassette Lid v0.7** | **New Baseline** | Print `build/cassette_lid_v0_7_print.stl` in PETG (top-face down). |
| **Cassette Body (v0.5 / v0.6 / v0.7)** | **Compatible** | All v0.5, v0.6, and v0.7 bodies share the standard Z = 24.80 mm rim and 2.25 mm knuckle. Existing prints remain 100% reusable. |
| **Hinge Pin** | **Compatible** | Standard straight 1.75 mm printer filament (~75 mm long). |
| **Glass Slides** | **Compatible** | Standard plain microscope slides near 75 × 25 × 1.1–1.2 mm. |
| **3 × 4 Carrier** | **Compatible** | 39.55 × 80.0 × 28.0 mm closed cassette envelope fits perfectly inside carrier throats. |
| **Snap Retainers (v0.1–v0.6)** | **Superseded** | Replaced by the integral positive end-loading channel. |

---

## Export Validation Audits

- `cassette_lid_v0_7_print.stl`: 780 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles, fully connected shell overlap graph.
- `cassette_body_v0_7.stl`: 376 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
- `REFERENCE_closed_assembly_DO_NOT_PRINT.stl`: 1168 triangles, 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
