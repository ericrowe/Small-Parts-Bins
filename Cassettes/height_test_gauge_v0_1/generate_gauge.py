#!/usr/bin/env python3
"""Stepped Height Test Gauge for Plan 002.

Generates a compact stepped gauge to evaluate candidate cassette heights
inside a 3x4 7U carrier tray when stacked with an upper carrier in a 14U stack.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

DEFAULT_OUT = Path(__file__).resolve().parent / "build"

# Gauge dimensions
GAUGE_W = 20.00
STEP_DEPTH = 12.00
STEP_HEIGHTS = [
    ("28.0", 28.00),   # Baseline (14.25 mm clearance to 42.25 mm datum)
    ("34.0", 34.00),   # +6 mm (8.25 mm clearance)
    ("38.0", 38.00),   # +10 mm (4.25 mm clearance)
    ("40.0", 40.00),   # +12 mm (2.25 mm clearance)
    ("42.25", 42.25), # Engagement Plane Datum (0.00 mm clearance)
]

def make_box_mesh(x0, x1, y0, y1, z0, z1):
    triangles = []
    # 8 vertices
    p000 = (x0, y0, z0)
    p100 = (x1, y0, z0)
    p110 = (x1, y1, z0)
    p010 = (x0, y1, z0)
    p001 = (x0, y0, z1)
    p101 = (x1, y0, z1)
    p111 = (x1, y1, z1)
    p011 = (x0, y1, z1)

    # -Z (bottom)
    triangles.append((p000, p110, p100))
    triangles.append((p000, p010, p110))
    # +Z (top)
    triangles.append((p001, p101, p111))
    triangles.append((p001, p111, p011))
    # -Y (front)
    triangles.append((p000, p100, p101))
    triangles.append((p000, p101, p001))
    # +Y (back)
    triangles.append((p010, p111, p110))
    triangles.append((p010, p011, p111))
    # -X (left)
    triangles.append((p000, p001, p011))
    triangles.append((p000, p011, p010))
    # +X (right)
    triangles.append((p100, p110, p111))
    triangles.append((p100, p111, p101))

    return triangles

def build_gauge_mesh():
    x0 = -GAUGE_W / 2.0
    x1 = GAUGE_W / 2.0
    total_steps = len(STEP_HEIGHTS)
    total_depth = total_steps * STEP_DEPTH
    start_y = -total_depth / 2.0

    all_triangles = []
    
    # Each step is an independent column from Z=0 to h with 0.05 mm overlap in Y
    for i, (name, h) in enumerate(STEP_HEIGHTS):
        y_min = start_y + i * STEP_DEPTH - (0.05 if i > 0 else 0.0)
        y_max = start_y + (i + 1) * STEP_DEPTH + (0.05 if i < total_steps - 1 else 0.0)
        all_triangles.extend(make_box_mesh(x0, x1, y_min, y_max, 0.0, h))

    return all_triangles

def export_binary_stl(triangles, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = b'Stepped Height Test Gauge v0.1'.ljust(80, b' ')
    with open(out_path, 'wb') as f:
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))
        for v0, v1, v2 in triangles:
            # Compute normal
            ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
            bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
            nx = ay * bz - az * by
            ny = az * bx - ax * bz
            nz = ax * by - ay * bx
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length > 0:
                nx /= length
                ny /= length
                nz /= length
            else:
                nx, ny, nz = 0.0, 0.0, 1.0
            
            f.write(struct.pack('<fff', nx, ny, nz))
            f.write(struct.pack('<fff', *v0))
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<H', 0))

def audit_mesh(triangles):
    edge_counts = {}
    degen = 0
    finite = True
    decimals = 5
    def key(p): return (round(p[0], decimals), round(p[1], decimals), round(p[2], decimals))

    for tri in triangles:
        pts = [key(v) for v in tri]
        for p in pts:
            if not all(math.isfinite(coord) for coord in p):
                finite = False
        if pts[0] == pts[1] or pts[1] == pts[2] or pts[0] == pts[2]:
            degen += 1
        for i in range(3):
            a, b = pts[i], pts[(i + 1) % 3]
            e = (a, b) if a <= b else (b, a)
            edge_counts[e] = edge_counts.get(e, 0) + 1

    boundary = sum(1 for c in edge_counts.values() if c == 1)
    nonmanifold = sum(1 for c in edge_counts.values() if c > 2)

    return {
        "triangles": len(triangles),
        "finite_coordinates": finite,
        "degenerate_triangles": degen,
        "boundary_edges": boundary,
        "nonmanifold_edges": nonmanifold
    }

def main():
    parser = argparse.ArgumentParser(description="Generate stepped height test gauge")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--preview", action="store_true", help="Generate preview SVG")
    args = parser.parse_args()

    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    triangles = build_gauge_mesh()
    stl_path = out_dir / "height_gauge_stepped_v0_1.stl"
    export_binary_stl(triangles, stl_path)
    audit = audit_mesh(triangles)

    manifest = {
        "design": "Stepped Height Test Gauge",
        "version": "0.1",
        "units": "mm",
        "steps": STEP_HEIGHTS,
        "envelope_mm": [GAUGE_W, len(STEP_HEIGHTS) * STEP_DEPTH, STEP_HEIGHTS[-1][1]],
        "stl_audit": audit,
        "file": stl_path.name
    }

    manifest_path = out_dir / "manifest_v0_1.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
