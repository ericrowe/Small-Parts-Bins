---
name: mesh-auditor
description: >-
  Inspect and audit binary STL 3D models for topological integrity. Use this skill
  whenever generating 3D models, exporting STLs, or debugging slicer/mesh warnings.
  Detects boundary edges (holes), non-manifold edges, degenerate triangles, and non-finite coordinates.
---

# Mesh Auditor Skill

This skill provides automated, zero-external-dependency validation for 3D triangular mesh files (STL format).

## Quality Gates for Printable 3D Meshes

Every production STL file must satisfy:
1. **0 Boundary Edges:** The mesh must be a closed, watertight manifold solid with no open seams or missing faces.
2. **0 Non-Manifold Edges:** No edge may be shared by more than 2 triangles (no internal walls, self-intersections, or t-junctions).
3. **0 Degenerate Triangles:** No zero-area triangles or collinear vertices.
4. **100% Finite Coordinates:** All vertices must be real, finite numbers (no `NaN` or `Inf`).

## How to Audit an STL

Run the audit script from the command line:

```bash
python3 .agents/skills/mesh-auditor/scripts/audit_stl.py path/to/model.stl
```

Output format (JSON):
```json
{
  "file": "model.stl",
  "triangles": 536,
  "boundary_edges": 0,
  "nonmanifold_edges": 0,
  "degenerate_triangles": 0,
  "finite_coordinates": true,
  "bounds_min": [-19.3, -40.0, 0.0],
  "bounds_max": [19.3, 40.0, 32.8],
  "dimensions": [38.6, 80.0, 32.8],
  "passed": true
}
```
