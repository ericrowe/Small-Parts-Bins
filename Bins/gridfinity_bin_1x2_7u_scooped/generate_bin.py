#!/usr/bin/env python3
"""Generate a standalone 1x2 7U Gridfinity bin with scooped inside front edge.

Specifications:
  - 1x2 Gridfinity footprint (42.0 x 84.0 mm nominal pitch, 41.50 x 83.50 mm outer, R = 3.75 mm corners).
  - Two standard 42 mm Gridfinity base feet at Z = 0.00 to 4.75 mm.
  - Base support floor at Z = 6.00 mm.
  - Standard 7U engaged stacking shelf height at Z = 49.00 mm.
  - Continuous 3D lofted standard Gridfinity stacking lip (Z = 49.00 to 53.40 mm).
  - Internal usable cavity: 37.50 mm width x 79.50 mm length x 43.00 mm depth (2.00 mm walls).
  - Inside front floor finger scoop: smooth concave R = 6.00 mm fillet along the front bottom edge.
"""

from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

# ==============================================================================
# PARAMETRIC CONSTANTS
# ==============================================================================

PITCH = 42.00
OUTER_W = 41.50         # 1x2 outer width (X)
OUTER_L = 83.50         # 1x2 outer length (Y)
OUTER_R = 3.75          # Standard Gridfinity corner radius

BASE_H = 4.75           # Gridfinity foot profile height
FLOOR_Z = 6.00          # Internal floor support plane
ENGAGED_H = 49.00       # Standard 7U engaged stacking shelf height
LIP_H = 4.40            # Standard Gridfinity stacking lip height
TOTAL_H = ENGAGED_H + LIP_H  # 53.40 mm total height

WALL_T = 2.00           # Minimum wall thickness
CAVITY_W = OUTER_W - 2 * WALL_T  # 37.50 mm inside cavity width
CAVITY_L = OUTER_L - 2 * WALL_T  # 79.50 mm inside cavity length
SCOOP_R = 6.00          # Finger scoop radius along inside bottom front edge

DRAWER_CEILING = 111.125  # Measured inside drawer ceiling

# ==============================================================================
# 3D MESH DATA STRUCTURES & PRIMITIVES
# ==============================================================================

V = tuple[float, float, float]
Triangle = tuple[V, V, V]


@dataclass
class Mesh:
    name: str
    triangles: list[Triangle]

    def __init__(self, name: str = ""):
        self.name = name
        self.triangles = []

    def tri(self, a: V, b: V, c: V):
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        if nx * nx + ny * ny + nz * nz > 1e-18:
            self.triangles.append((a, b, c))

    def quad(self, a: V, b: V, c: V, d: V):
        self.tri(a, b, c)
        self.tri(a, c, d)

    def extend(self, other: Mesh):
        self.triangles.extend(other.triangles)

    def translated(self, dx: float, dy: float, dz: float, name: str = "") -> Mesh:
        out = Mesh(name or self.name)
        out.triangles = [
            (
                (a[0] + dx, a[1] + dy, a[2] + dz),
                (b[0] + dx, b[1] + dy, b[2] + dz),
                (c[0] + dx, c[1] + dy, c[2] + dz),
            )
            for a, b, c in self.triangles
        ]
        return out


def rounded_rect(w: float, d: float, r: float, n: int = 8) -> list[tuple[float, float]]:
    """Generate 2D counter-clockwise vertices of a rounded rectangle."""
    pts = []
    corners = [
        (w / 2 - r, d / 2 - r, 0),
        (-w / 2 + r, d / 2 - r, 90),
        (-w / 2 + r, -d / 2 + r, 180),
        (w / 2 - r, -d / 2 + r, 270),
    ]
    for cx, cy, start in corners:
        for i in range(n + 1):
            a = math.radians(start + i * 90 / n)
            pts.append((round(cx + r * math.cos(a), 4), round(cy + r * math.sin(a), 4)))
    return pts


def loft(rings: list[tuple[float, list[tuple[float, float]]]]) -> Mesh:
    """Loft a solid 3D mesh through closed planar rings at increasing Z."""
    m = Mesh("loft")
    count = len(rings[0][1])
    for _, p in rings:
        assert len(p) == count, f"Mismatched ring points: {len(p)} vs {count}"

    # Bottom cap:
    z_bot, p_bot = rings[0]
    for i in range(1, count - 1):
        m.tri((p_bot[0][0], p_bot[0][1], z_bot), (p_bot[i + 1][0], p_bot[i + 1][1], z_bot), (p_bot[i][0], p_bot[i][1], z_bot))

    # Top cap:
    z_top, p_top = rings[-1]
    for i in range(1, count - 1):
        m.tri((p_top[0][0], p_top[0][1], z_top), (p_top[i][0], p_top[i][1], z_top), (p_top[i + 1][0], p_top[i + 1][1], z_top))

    # Side walls:
    for (z0, p0), (z1, p1) in zip(rings, rings[1:]):
        for i in range(count):
            j = (i + 1) % count
            m.quad((p0[i][0], p0[i][1], z0), (p0[j][0], p0[j][1], z0), (p1[j][0], p1[j][1], z1), (p1[i][0], p1[i][1], z1))
    return m


def prism(name: str, poly: list[tuple[float, float]], z0: float, z1: float) -> Mesh:
    """Extrude a 2D CCW polygon vertically along Z."""
    m = loft([(z0, poly), (z1, poly)])
    m.name = name
    return m


def prism_x(name: str, profile_yz: list[tuple[float, float]], x0: float, x1: float) -> Mesh:
    """Extrude a 2D CCW profile in the YZ plane along the X axis."""
    m = Mesh(name)
    n = len(profile_yz)
    for i in range(1, n - 1):
        m.tri(
            (x0, profile_yz[0][0], profile_yz[0][1]),
            (x0, profile_yz[i + 1][0], profile_yz[i + 1][1]),
            (x0, profile_yz[i][0], profile_yz[i][1]),
        )
        m.tri(
            (x1, profile_yz[0][0], profile_yz[0][1]),
            (x1, profile_yz[i][0], profile_yz[i][1]),
            (x1, profile_yz[i + 1][0], profile_yz[i + 1][1]),
        )
    for i in range(n):
        j = (i + 1) % n
        m.quad(
            (x0, profile_yz[i][0], profile_yz[i][1]),
            (x1, profile_yz[i][0], profile_yz[i][1]),
            (x1, profile_yz[j][0], profile_yz[j][1]),
            (x0, profile_yz[j][0], profile_yz[j][1]),
        )
    return m


# ==============================================================================
# GRIDFINITY 1x2 7U SCOOPED BIN MODEL
# ==============================================================================

def build_gridfinity_base() -> Mesh:
    """Build the standard 1x2 Gridfinity base feet and bottom support floor."""
    m = Mesh("gridfinity_base")
    centers = [-PITCH / 2, PITCH / 2]  # -21.0, +21.0 mm

    # Stepped 4.75 mm Gridfinity foot profiles:
    for cy in centers:
        rings = [
            (0.00, [(x, y + cy) for x, y in rounded_rect(35.6, 35.6, 3.2)]),
            (0.80, [(x, y + cy) for x, y in rounded_rect(37.2, 37.2, 3.4)]),
            (2.60, [(x, y + cy) for x, y in rounded_rect(37.2, 37.2, 3.4)]),
            (BASE_H, [(x, y + cy) for x, y in rounded_rect(41.5, 41.5, 3.75)]),
        ]
        m.extend(loft(rings))

    # Base solid joining the feet up to the floor plane (Z = 6.00 mm):
    m.extend(
        loft([
            (BASE_H - 0.05, rounded_rect(OUTER_W, OUTER_L, OUTER_R)),
            (FLOOR_Z + 0.05, rounded_rect(OUTER_W, OUTER_L, OUTER_R)),
        ])
    )
    return m


def build_stacking_lip() -> Mesh:
    """Build the authoritative continuous 3D lofted Gridfinity stacking lip (Z in [49.00, 53.40 mm])."""
    m = Mesh("stacking_lip")
    z_shelf = ENGAGED_H - 0.05  # 48.95 mm
    z_slope1 = 49.70
    z_slope2 = 51.50
    z_top = TOTAL_H             # 53.40 mm

    n = 8
    outer_rings = [
        (z_shelf, rounded_rect(41.50, 83.50, 3.75, n)),
        (z_slope1, rounded_rect(41.50, 83.50, 3.75, n)),
        (z_slope2, rounded_rect(41.50, 83.50, 3.75, n)),
        (z_top, rounded_rect(41.30, 83.30, 3.65, n)),
    ]

    inner_rings = [
        (z_shelf, rounded_rect(37.20, 79.20, 3.40, n)),
        (z_slope1, rounded_rect(38.60, 80.60, 3.40, n)),
        (z_slope2, rounded_rect(38.60, 80.60, 3.40, n)),
        (z_top, rounded_rect(41.00, 83.00, 3.50, n)),
    ]

    count = len(outer_rings[0][1])
    for i in range(len(outer_rings) - 1):
        z0, p0 = outer_rings[i]
        z1, p1 = outer_rings[i + 1]
        for j in range(count):
            k = (j + 1) % count
            m.quad((p0[j][0], p0[j][1], z0), (p0[k][0], p0[k][1], z0), (p1[k][0], p1[k][1], z1), (p1[j][0], p1[j][1], z1))

    for i in range(len(inner_rings) - 1):
        z0, p0 = inner_rings[i]
        z1, p1 = inner_rings[i + 1]
        for j in range(count):
            k = (j + 1) % count
            m.quad((p0[k][0], p0[k][1], z0), (p0[j][0], p0[j][1], z0), (p1[j][0], p1[j][1], z1), (p1[k][0], p1[k][1], z1))

    _, p_out_top = outer_rings[-1]
    _, p_in_top = inner_rings[-1]
    for j in range(count):
        k = (j + 1) % count
        m.quad((p_out_top[j][0], p_out_top[j][1], z_top), (p_in_top[j][0], p_in_top[j][1], z_top), (p_in_top[k][0], p_in_top[k][1], z_top), (p_out_top[k][0], p_out_top[k][1], z_top))

    _, p_out_bot = outer_rings[0]
    _, p_in_bot = inner_rings[0]
    for j in range(count):
        k = (j + 1) % count
        m.quad((p_out_bot[k][0], p_out_bot[k][1], z_shelf), (p_in_bot[k][0], p_in_bot[k][1], z_shelf), (p_in_bot[j][0], p_in_bot[j][1], z_shelf), (p_out_bot[j][0], p_out_bot[j][1], z_shelf))

    return m


def build_front_scoop_fillet(ix: float, iy: float, z_floor: float, r: float, join: float = 0.05) -> Mesh:
    """Build a smooth concave finger scoop fillet (R = 6.0 mm) along the inside bottom front edge."""
    n = 8
    # Front edge is at Y = -iy. Fillet rises along Z from z_floor up to z_floor + r, and spans Y from -iy to -iy + r.
    profile_yz = [
        (-iy - join, z_floor - join),
        (-iy + r, z_floor - join),
    ]
    cy = -iy + r
    cz = z_floor + r
    for i in range(n + 1):
        a = math.radians(180 + i * 90 / n)
        profile_yz.append((cy + r * math.cos(a), cz + r * math.sin(a)))
    profile_yz.append((-iy - join, cz + join))
    return prism_x("front_scoop_fillet", profile_yz, -ix - join, ix + join)


def build_1x2_7u_scooped_bin() -> Mesh:
    """Build the complete 1x2 7U Gridfinity scooped bin."""
    out = Mesh("gridfinity_bin_1x2_7u_scooped")

    # 1. Base feet & support floor:
    out.extend(build_gridfinity_base())

    hx, hy = OUTER_W / 2, OUTER_L / 2
    r_corner = OUTER_R
    ix, iy = hx - WALL_T, hy - WALL_T  # 18.75 x 39.75 mm cavity
    join = 0.05
    z_floor = FLOOR_Z

    outer_pts = rounded_rect(OUTER_W, OUTER_L, r_corner, n=12)

    # 2. Monolithic Cavity Walls (Z = 6.00 to 49.00 mm):
    # Back Wall:
    pts_b = [(-ix - join, iy - join), (ix + join, iy - join)]
    pts_b.extend(sorted([p for p in outer_pts if p[1] >= iy - join and -ix - join <= p[0] <= ix + join], key=lambda p: -p[0]))
    out.extend(prism("back_wall", pts_b, z_floor - join, ENGAGED_H + join))

    # Front Wall:
    pts_f = [(ix + join, -iy + join), (-ix - join, -iy + join)]
    pts_f.extend(sorted([p for p in outer_pts if p[1] <= -iy + join and -ix - join <= p[0] <= ix + join], key=lambda p: p[0]))
    out.extend(prism("front_wall", pts_f, z_floor - join, ENGAGED_H + join))

    # Left Wall:
    pts_l = [(-ix + join, -iy - join), (-ix + join, iy + join)]
    pts_l.extend(sorted([p for p in outer_pts if p[0] <= -ix + join and -iy - join <= p[1] <= iy + join], key=lambda p: p[1]))
    out.extend(prism("left_wall", pts_l, z_floor - join, ENGAGED_H + join))

    # Right Wall:
    pts_r = [(ix - join, iy + join), (ix - join, -iy - join)]
    pts_r.extend(sorted([p for p in outer_pts if p[0] >= ix - join and -iy - join <= p[1] <= iy + join], key=lambda p: -p[1]))
    out.extend(prism("right_wall", pts_r, z_floor - join, ENGAGED_H + join))

    # 3. Inside Front Floor Finger Scoop Fillet:
    out.extend(build_front_scoop_fillet(ix, iy, z_floor, SCOOP_R))

    # 4. Continuous 3D Lofted Stacking Lip (Z = 49.00 to 53.40 mm):
    out.extend(build_stacking_lip())

    return out


# ==============================================================================
# STL EXPORT & MAIN SCRIPT
# ==============================================================================

def compute_normal(t: Triangle) -> V:
    a, b, c = t
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if norm < 1e-12:
        return (0.0, 0.0, 0.0)
    return (nx / norm, ny / norm, nz / norm)


def write_binary_stl(path: Path, mesh: Mesh):
    """Write triangles to binary STL format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"STL binary export: {mesh.name}".encode("ascii")[:80].ljust(80, b"\0")
    with path.open("wb") as f:
        f.write(header)
        f.write(struct.pack("<I", len(mesh.triangles)))
        for tri in mesh.triangles:
            norm = compute_normal(tri)
            f.write(struct.pack("<3f", *norm))
            for pt in tri:
                f.write(struct.pack("<3f", *pt))
            f.write(struct.pack("<H", 0))


def main():
    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build the 1x2 7U Scooped Bin:
    bin_mesh = build_1x2_7u_scooped_bin()

    # 2. Build Reference 2-high stack (14U engaged height = 102.40 mm):
    ref_stack = Mesh("REFERENCE_two_high_stack_1x2_14u_DO_NOT_PRINT")
    ref_stack.extend(bin_mesh)
    ref_stack.extend(bin_mesh.translated(0.0, 0.0, ENGAGED_H + 0.02))

    files = [
        ("gridfinity_bin_1x2_7u_scooped.stl", bin_mesh),
        ("REFERENCE_two_high_stack_1x2_14u_DO_NOT_PRINT.stl", ref_stack),
    ]

    manifest = {
        "format": "Gridfinity 1x2 7U Bin with Inside Front Scoop",
        "pitch_mm": [PITCH, 2 * PITCH],
        "envelope_outside_mm": [OUTER_W, OUTER_L, TOTAL_H],
        "stacking_engaged_height_mm": ENGAGED_H,
        "total_height_with_lip_mm": TOTAL_H,
        "two_high_stack_height_mm": ENGAGED_H + TOTAL_H,
        "drawer_ceiling_mm": DRAWER_CEILING,
        "drawer_stack_clearance_mm": DRAWER_CEILING - (ENGAGED_H + TOTAL_H),
        "usable_cavity_mm": [CAVITY_W, CAVITY_L, ENGAGED_H - FLOOR_Z],
        "front_finger_scoop_radius_mm": SCOOP_R,
        "files": {},
    }

    for fname, mesh in files:
        fpath = out_dir / fname
        write_binary_stl(fpath, mesh)
        xs = [pt[0] for tri in mesh.triangles for pt in tri]
        ys = [pt[1] for tri in mesh.triangles for pt in tri]
        zs = [pt[2] for tri in mesh.triangles for pt in tri]
        size = [round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2), round(max(zs) - min(zs), 2)]
        manifest["files"][fname] = {
            "triangles": len(mesh.triangles),
            "dimensions_mm": size,
        }
        print(f"Generated {fname}: {len(mesh.triangles)} tris, size: {size}")

    manifest_path = out_dir / "manifest_1x2_7u_scooped.json"
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
