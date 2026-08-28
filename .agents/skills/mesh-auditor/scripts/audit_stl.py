#!/usr/bin/env python3
"""Standalone binary STL mesh auditor with zero external dependencies."""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

V = tuple[float, float, float]
T = tuple[V, V, V]

def normal(t: T) -> V:
    a, b, c = t
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1]*v[2] - u[2]*v[1], u[2]*v[0] - u[0]*v[2], u[0]*v[1] - u[1]*v[0])
    q = math.sqrt(sum(x*x for x in n))
    return tuple(x/q for x in n) if q else (0.0, 0.0, 0.0)

def audit_stl_file(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"STL file not found: {path}")

    with path.open("rb") as f:
        header = f.read(80)
        tri_count_data = f.read(4)
        if len(tri_count_data) < 4:
            raise ValueError(f"File too short to be a valid binary STL: {path}")
        tri_count = struct.unpack("<I", tri_count_data)[0]

        edges: dict[tuple[V, V], int] = {}
        degenerate = 0
        finite = True
        min_pt = [float("inf"), float("inf"), float("inf")]
        max_pt = [float("-inf"), float("-inf"), float("-inf")]

        for _ in range(tri_count):
            data = f.read(50)
            if len(data) < 50:
                raise ValueError("Unexpected end of STL data")
            floats = struct.unpack("<12f", data[:48])
            v0: V = (round(floats[3], 4), round(floats[4], 4), round(floats[5], 4))
            v1: V = (round(floats[6], 4), round(floats[7], 4), round(floats[8], 4))
            v2: V = (round(floats[9], 4), round(floats[10], 4), round(floats[11], 4))
            tri = (v0, v1, v2)

            for v in tri:
                for i in range(3):
                    if not math.isfinite(v[i]):
                        finite = False
                    if v[i] < min_pt[i]: min_pt[i] = v[i]
                    if v[i] > max_pt[i]: max_pt[i] = v[i]

            norm = normal(tri)
            if norm == (0.0, 0.0, 0.0):
                degenerate += 1

            for p, q in ((v0, v1), (v1, v2), (v2, v0)):
                k = tuple(sorted((p, q)))
                edges[k] = edges.get(k, 0) + 1

    boundary_edges = sum(1 for count in edges.values() if count == 1)
    nonmanifold_edges = sum(1 for count in edges.values() if count > 2)
    dims = [round(max_pt[i] - min_pt[i], 3) for i in range(3)] if finite else [0, 0, 0]

    return {
        "file": path.name,
        "triangles": tri_count,
        "boundary_edges": boundary_edges,
        "nonmanifold_edges": nonmanifold_edges,
        "degenerate_triangles": degenerate,
        "finite_coordinates": finite,
        "bounds_min": [round(x, 3) for x in min_pt] if finite else [],
        "bounds_max": [round(x, 3) for x in max_pt] if finite else [],
        "dimensions": dims,
        "passed": (boundary_edges == 0 and nonmanifold_edges == 0 and degenerate == 0 and finite)
    }

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_stl_file>", file=sys.stderr)
        sys.exit(1)
    stl_path = Path(sys.argv[1])
    res = audit_stl_file(stl_path)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["passed"] else 1)

if __name__ == "__main__":
    main()
