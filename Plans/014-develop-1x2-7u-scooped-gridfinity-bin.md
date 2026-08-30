# Plan 014 — Develop 1x2 7U Scooped Gridfinity Bin

- Status: In Work
- Depends on: Baseline Gridfinity base and stacking lip specifications
- Created: 2026-08-29
- Started: 2026-08-29
- Completed: Not completed
- Git start: `24f58fe`
- Git completion: Not completed

## Outcome

Develop a standard, robust $1 \times 2$ Gridfinity bin at standard 7U height ($49.00\text{ mm}$ engaged shelf height, $53.40\text{ mm}$ total height with stacking lip) featuring an ergonomic curved finger scoop along the inside bottom front floor edge.

## Requirements

### 1. Standard Gridfinity Architecture
- **Footprint:** Standard $1 \times 2$ Gridfinity footprint ($42.0 \times 84.0\text{ mm}$ nominal pitch, $41.50 \times 83.50\text{ mm}$ outer dimensions, $R = 3.75\text{ mm}$ outer corner radius).
- **Base Interface:** Two standard $42\text{ mm}$ Gridfinity base feet centered at $(0, \pm 21.00\text{ mm})$ ($35.6 \to 37.2 \to 41.5\text{ mm}$ stepped $45^\circ$ profile, $4.75\text{ mm}$ height, solid floor at $Z = 6.00\text{ mm}$).
- **Stacking Lip:** Continuous 3D lofted standard Gridfinity stacking lip ($+4.40\text{ mm}$ height, $41.50 \times 83.50\text{ mm}$ outer, $37.20 \times 79.20\text{ mm}$ throat, $r = 3.40\text{ mm}$) at $Z = 49.00\text{ to }53.40\text{ mm}$.
- **Stacking Capability:** Standard Gridfinity bins stack directly into the top stacking lip.

### 2. Cavity & Ergonomics
- **Usable Cavity:** $37.50\text{ mm}$ width $\times 79.50\text{ mm}$ length $\times 43.00\text{ mm}$ depth ($2.00\text{ mm}$ thick outer walls).
- **Inside Front Finger Scoop:** Smooth concave fillet ($R = 4.0\text{--}6.0\text{ mm}$) along the inside bottom front floor edge for effortless one-finger parts retrieval.

### 3. Mesh Quality & Documentation
- Clean topology (0 boundary edges, 0 non-manifold edges, 0 degenerate triangles).
- Multi-view engineering CAD render.
- Parametric generator script with binary STL export.

## Non-goals
- No complex lids, sliding grooves, or external protrusions.

## Implementation steps

1. [x] **Parametric CAD Generator:** Write `Bins/gridfinity_bin_1x2_7u_scooped/generate_bin.py`.
2. [x] **3D Mesh Auditing:** Verify 0 boundary edges, 0 non-manifold edges, 0 degenerate triangles.
3. [x] **CAD Multi-Views:** Render 3D orthographic multi-view engineering sheet.
4. [x] **Documentation & Pipeline Check:** Create README and verify pipeline integrity.

## Acceptance criteria

- [x] STL passes mesh audit (0 boundary / 0 non-manifold / 0 degenerate).
- [x] Dimensions measure exactly $41.50 \times 83.50 \times 53.40\text{ mm}$ ($49.00\text{ mm}$ engaged height).
- [x] Base feet fit standard Gridfinity baseplates.
