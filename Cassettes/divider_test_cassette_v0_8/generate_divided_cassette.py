#!/usr/bin/env python3
"""Generate the full-size v0.8 cassette body with Plan 003 removable divider stations."""

from __future__ import annotations

import argparse, json, math, struct, sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD_DIR = HERE / "build"

# Geometry parameters
VERSION = "0.8-divided"
VERSION_TAG = "v0_8_divided"

BODY_W = 38.60
BODY_D = 80.00
BODY_H = 32.80
BODY_CORNER = 2.00
BODY_BOTTOM = 2.00

# Usable internal cavity with thickened left wall to clear hinge knuckle
# Left wall thickness = 4.30 mm (inner face at X = -15.00 mm)
# Right wall thickness = 2.00 mm (inner face at X = +17.30 mm)
INNER_X_LEFT = -15.00
INNER_X_RIGHT = 17.30
CAVITY_W = INNER_X_RIGHT - INNER_X_LEFT  # 32.30 mm
CAVITY_D = 76.00                         # Y in [-38.00, 38.00]
CAVITY_FLOOR_Z = BODY_BOTTOM             # 2.00 mm
CAVITY_RIM_Z = BODY_H                    # 32.80 mm

# Plan 003 Divider Slot Stations (Station 2 verified fit)
SLOT_W = 1.40
SLOT_RECESS = 0.60
FLOOR_GROOVE_D = 0.60
OV = 0.05

# Slot Stations along Y:
# 1. Offset 1-divider station at Y = +8.50 mm (clears central clasp and fingernail zone [-7.0, +7.0])
# 2. 2-divider stations at Y = -12.87 mm and Y = +12.87 mm (3 equal compartments)
SLOT_STATIONS = [8.50, -12.87, 12.87]

# Hinge parameters (identical to verified v0.8 / v0.6)
HINGE_X = -18.20
HINGE_Z_LOCAL = 0.20
HINGE_BODY_BORE_R = 1.125
HINGE_BODY_Y0 = -18.75
HINGE_BODY_Y1 = 18.75
HINGE_RELIEF_Y0 = -19.55
HINGE_RELIEF_Y1 = 19.55
HINGE_BODY_SUPPORT_TOP = BODY_H - 0.70
HINGE_BODY_RELIEF_TOP = BODY_H - 1.20
HINGE_BODY_END_RELIEF_Y0 = -39.00
HINGE_BODY_END_RELIEF_Y1 = 39.00

V = tuple[float, float, float]
T = tuple[V, V, V]
Vec2 = tuple[float, float]

@dataclass
class Mesh:
    name: str
    triangles: list[T]
    def __init__(self, name: str = ""):
        self.name = name
        self.triangles = []
    def tri(self, a: V, b: V, c: V):
        ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
        vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
        if (uy*vz-uz*vy)**2 + (uz*vx-ux*vz)**2 + (ux*vy-uy*vx)**2 > 1e-18:
            self.triangles.append((a, b, c))
    def quad(self, a: V, b: V, c: V, d: V):
        self.tri(a, b, c)
        self.tri(a, c, d)
    def add(self, other: Mesh):
        self.triangles.extend(other.triangles)

def normal(t: T) -> V:
    a, b, c = t
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1]*v[2] - u[2]*v[1], u[2]*v[0] - u[0]*v[2], u[0]*v[1] - u[1]*v[0])
    q = math.sqrt(sum(x*x for x in n))
    return tuple(x/q for x in n) if q else (0, 0, 0)

def chamfer_rect(w: float, d: float, c: float) -> list[Vec2]:
    hw, hd = w / 2.0, d / 2.0
    return [
        (-hw + c, -hd), (hw - c, -hd),
        (hw, -hd + c), (hw, hd - c),
        (hw - c, hd), (-hw + c, hd),
        (-hw, hd - c), (-hw, -hd + c),
    ]

def box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Mesh:
    m = Mesh()
    m.quad((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)) # -Z
    m.quad((x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)) # +Z
    m.quad((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)) # -X
    m.quad((x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)) # +X
    m.quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)) # -Y
    m.quad((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)) # +Y
    return m

def prism_z(loop: list[Vec2], z0: float, z1: float) -> Mesh:
    m = Mesh()
    n = len(loop)
    cx = sum(p[0] for p in loop) / n
    cy = sum(p[1] for p in loop) / n
    for i in range(n):
        j = (i + 1) % n
        m.tri((cx, cy, z0), (loop[j][0], loop[j][1], z0), (loop[i][0], loop[i][1], z0))
        m.tri((cx, cy, z1), (loop[i][0], loop[i][1], z1), (loop[j][0], loop[j][1], z1))
        m.quad((loop[i][0], loop[i][1], z0), (loop[j][0], loop[j][1], z0),
               (loop[j][0], loop[j][1], z1), (loop[i][0], loop[i][1], z1))
    return m

def prism_y(xz_loop: list[Vec2], y0: float, y1: float) -> Mesh:
    m = Mesh()
    n = len(xz_loop)
    cx = sum(p[0] for p in xz_loop) / n
    cz = sum(p[1] for p in xz_loop) / n
    for i in range(n):
        j = (i + 1) % n
        m.tri((cx, y0, cz), (xz_loop[i][0], y0, xz_loop[i][1]), (xz_loop[j][0], y0, xz_loop[j][1]))
        m.tri((cx, y1, cz), (xz_loop[j][0], y1, xz_loop[j][1]), (xz_loop[i][0], y1, xz_loop[i][1]))
        m.quad((xz_loop[i][0], y0, xz_loop[i][1]), (xz_loop[j][0], y0, xz_loop[j][1]),
               (xz_loop[j][0], y1, xz_loop[j][1]), (xz_loop[i][0], y1, xz_loop[i][1]))
    return m

def build_divided_body() -> Mesh:
    m = Mesh("cassette_body_v0_8_divided")
    hx, hy = BODY_W / 2, BODY_D / 2
    lx, rx = INNER_X_LEFT, INNER_X_RIGHT
    iy = CAVITY_D / 2
    c = BODY_CORNER
    
    # 1. Base floor slab: Z in [0, CAVITY_FLOOR_Z - FLOOR_GROOVE_D + OV] = [0, 1.45]
    outer = chamfer_rect(BODY_W, BODY_D, BODY_CORNER)
    m.add(prism_z(outer, 0.00, CAVITY_FLOOR_Z - FLOOR_GROOVE_D + OV))
    
    # 2. Outer left wall: X in [-hx, lx - SLOT_RECESS + OV], Z in [CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H]
    m.add(box(-hx, lx - SLOT_RECESS + OV, -hy + c - OV, hy - c + OV, CAVITY_FLOOR_Z - FLOOR_GROOVE_D, HINGE_BODY_RELIEF_TOP + OV))
    # Upper left sections:
    m.add(box(-hx, lx - SLOT_RECESS + OV, HINGE_RELIEF_Y0, HINGE_RELIEF_Y1, HINGE_BODY_RELIEF_TOP, HINGE_BODY_SUPPORT_TOP))
    m.add(box(-hx, lx - SLOT_RECESS + OV, -hy + c - OV, HINGE_BODY_END_RELIEF_Y0, HINGE_BODY_RELIEF_TOP, BODY_H))
    m.add(box(-hx, lx - SLOT_RECESS + OV, HINGE_BODY_END_RELIEF_Y1, hy - c + OV, HINGE_BODY_RELIEF_TOP, BODY_H))
    
    # 3. Outer right wall: X in [rx + SLOT_RECESS - OV, hx], Z in [CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H]
    m.add(box(rx + SLOT_RECESS - OV, hx, -hy + c - OV, hy - c + OV, CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H))
    
    # 4. Front wall (-Y): Y in [-hy, -iy + OV]
    m.add(box(-hx + c - OV, hx - c + OV, -hy, -iy + OV, CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H))
    
    # 5. Back wall (+Y): Y in [iy - OV, hy]
    m.add(box(-hx + c - OV, hx - c + OV, iy - OV, hy, CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H))
    
    # 6. Outer corner chamfers
    m.add(prism_z([(-hx + c, -hy), (-hx, -hy + c), (-hx + c - OV, -hy + c - OV)], CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H))
    m.add(prism_z([(hx - c, -hy), (hx, -hy + c), (hx - c + OV, -hy + c - OV)], CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H))
    m.add(prism_z([(-hx + c, hy), (-hx, hy - c), (-hx + c - OV, hy - c + OV)], CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H))
    m.add(prism_z([(hx - c, hy), (hx, hy - c), (hx - c + OV, hy - c + OV)], CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H))
    
    # 7. Segments between divider slots along Y
    y_points = [-iy]
    for cy in sorted(SLOT_STATIONS):
        y_points.extend([cy - SLOT_W / 2, cy + SLOT_W / 2])
    y_points.append(iy)
    
    for idx in range(0, len(y_points) - 1, 2):
        y0, y1 = y_points[idx], y_points[idx + 1]
        # Floor slab between slots (Z in [1.40, 2.05]):
        m.add(box(lx - OV, rx + OV, y0 - OV, y1 + OV, CAVITY_FLOOR_Z - FLOOR_GROOVE_D, CAVITY_FLOOR_Z + OV))
        
        # Inner left wall segment between slots (X in [lx - SLOT_RECESS - OV, lx]):
        m.add(box(lx - SLOT_RECESS - OV, lx, y0 - OV, y1 + OV, CAVITY_FLOOR_Z - FLOOR_GROOVE_D, HINGE_BODY_RELIEF_TOP + OV))
        if y1 <= HINGE_BODY_END_RELIEF_Y0 or y0 >= HINGE_BODY_END_RELIEF_Y1:
            m.add(box(lx - SLOT_RECESS - OV, lx, y0 - OV, y1 + OV, HINGE_BODY_RELIEF_TOP, BODY_H))
        elif y0 >= HINGE_RELIEF_Y0 and y1 <= HINGE_RELIEF_Y1:
            m.add(box(lx - SLOT_RECESS - OV, lx, y0 - OV, y1 + OV, HINGE_BODY_RELIEF_TOP, HINGE_BODY_SUPPORT_TOP))
            
        # Inner right wall segment between slots (X in [rx, rx + SLOT_RECESS + OV], Z up to BODY_H):
        m.add(box(rx, rx + SLOT_RECESS + OV, y0 - OV, y1 + OV, CAVITY_FLOOR_Z - FLOOR_GROOVE_D, BODY_H))
        
    # 8. Centre hinge knuckle (identical to standard v0.8)
    ow, op, st = 2.05, 2.45, 1.10
    outer_print = [(-ow, st), (-ow, 0.0)]
    outer_print.extend((-ow * (1.0 - step / 9.0), -op * step / 9.0) for step in range(1, 10))
    outer_print.extend((ow * step / 9.0, -op * (1.0 - step / 9.0)) for step in range(1, 10))
    outer_print.extend([(ow, st), (0.0, op)])
    
    bore_r = HINGE_BODY_BORE_R
    bore_print = [
        (bore_r * math.cos(math.radians(135.0 + 13.5 * i)),
         bore_r * math.sin(math.radians(135.0 + 13.5 * i)))
        for i in range(21)
    ]
    bore_print.append((0.0, math.sqrt(2.0) * bore_r))
    
    cx, cz = HINGE_X, BODY_H + HINGE_Z_LOCAL
    outer_xz = [(cx + x, cz + z) for x, z in outer_print]
    inner_xz = [(cx + x, cz + z) for x, z in bore_print]
    
    knuckle = Mesh()
    outer0 = [(x, HINGE_BODY_Y0, z) for x, z in outer_xz]
    outer1 = [(x, HINGE_BODY_Y1, z) for x, z in outer_xz]
    inner0 = [(x, HINGE_BODY_Y0, z) for x, z in inner_xz]
    inner1 = [(x, HINGE_BODY_Y1, z) for x, z in inner_xz]
    for i in range(len(outer0)):
        j = (i + 1) % len(outer0)
        knuckle.quad(outer0[i], outer1[i], outer1[j], outer0[j])
        knuckle.quad(inner0[i], inner0[j], inner1[j], inner1[i])
        knuckle.quad(outer0[i], outer0[j], inner0[j], inner0[i])
        knuckle.quad(outer1[i], inner1[i], inner1[j], outer1[j])
    m.add(knuckle)
    
    # 9. Closure catch on inner right wall (100% continuous and solid)
    catch_profile = [
        (17.30, BODY_H - 2.50),
        (16.55, BODY_H - 2.08),
        (16.55, BODY_H - 1.72),
        (17.30, BODY_H - 1.22),
    ]
    m.add(prism_y(catch_profile, -4.00, 4.00))
    
    return m

def build_divider_card(thickness: float = 1.20,
                       notch_w: float = 10.0, notch_d: float = 1.5,
                       bottom_chamfer: float = 0.6) -> Mesh:
    m = Mesh(f"divider_card_{thickness:.1f}mm")
    
    # Card boundaries:
    # Left edge: INNER_X_LEFT - (SLOT_RECESS - 0.10) = -15.00 - 0.50 = -15.50 mm
    # Right edge: INNER_X_RIGHT + (SLOT_RECESS - 0.10) = +17.30 + 0.50 = +17.80 mm
    # Total card width = 17.80 - (-15.50) = 33.30 mm (leaves 0.10 mm side clearance in slot)
    # Bottom: Z = 0 (seats in 1.40 mm floor groove, 0.60 mm deep)
    # Top: Z = 31.20 mm (leaves 0.20 mm lid clearance below Z = 32.80 mm)
    x_left = INNER_X_LEFT - 0.50   # -15.50 mm
    x_right = INNER_X_RIGHT + 0.50 # +17.80 mm
    z_top = 31.20
    ht = thickness / 2.0
    
    # 2D contour in XZ plane (standing upright):
    pts_xz = [
        (x_left + bottom_chamfer, 0.0),
        (x_right - bottom_chamfer, 0.0),
        (x_right, bottom_chamfer),
        (x_right, z_top - 1.0),
        (x_right - 1.0, z_top),
        (notch_w / 2.0, z_top),
        (notch_w / 4.0, z_top - notch_d),
        (-notch_w / 4.0, z_top - notch_d),
        (-notch_w / 2.0, z_top),
        (x_left + 1.0, z_top),
        (x_left, z_top - 1.0),
        (x_left, bottom_chamfer),
    ]
    
    n = len(pts_xz)
    for i in range(n):
        j = (i + 1) % n
        p0 = (pts_xz[i][0], -ht, pts_xz[i][1])
        p1 = (pts_xz[j][0], -ht, pts_xz[j][1])
        m.tri((0.0, -ht, z_top / 2.0), p0, p1)
        
        q0 = (pts_xz[i][0], ht, pts_xz[i][1])
        q1 = (pts_xz[j][0], ht, pts_xz[j][1])
        m.tri((0.0, ht, z_top / 2.0), q1, q0)
        
        m.quad(p0, p1, q1, q0)
    return m

def write_stl(path: Path, m: Mesh):
    with path.open('wb') as f:
        header = f"Plan 003 {m.name}".encode('ascii')[:80].ljust(80, b'\0')
        f.write(header)
        f.write(struct.pack('<I', len(m.triangles)))
        for t in m.triangles:
            norm = normal(t)
            f.write(struct.pack('<3f', *norm))
            for v in t:
                f.write(struct.pack('<3f', *v))
            f.write(struct.pack('<H', 0))

def audit(m: Mesh):
    edges = {}
    deg = 0
    finite = True
    for t in m.triangles:
        finite &= all(math.isfinite(q) for v in t for q in v)
        norm = normal(t)
        if norm == (0, 0, 0): deg += 1
        for p, q in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = tuple(sorted((tuple(round(x, 4) for x in p), tuple(round(x, 4) for x in q))))
            edges[k] = edges.get(k, 0) + 1
    return {
        'triangles': len(m.triangles),
        'boundary_edges': sum(v == 1 for v in edges.values()),
        'nonmanifold_edges': sum(v > 2 for v in edges.values()),
        'degenerate_triangles': deg,
        'finite_coordinates': finite
    }

def main():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Build divided body
    body_mesh = build_divided_body()
    body_stl = BUILD_DIR / "cassette_body_v0_8_divided.stl"
    write_stl(body_stl, body_mesh)
    audit_body = audit(body_mesh)
    print("Full Divided Body Audit:", audit_body)
    
    # 2. Build divider cards
    card_1_2 = build_divider_card(1.20)
    write_stl(BUILD_DIR / "divider_card_full_1_2mm.stl", card_1_2)
    audit_1_2 = audit(card_1_2)
    print("Divider Card 1.2mm Audit:", audit_1_2)
    
    card_1_0 = build_divider_card(1.00)
    write_stl(BUILD_DIR / "divider_card_full_1_0mm.stl", card_1_0)
    
    card_1_4 = build_divider_card(1.40)
    write_stl(BUILD_DIR / "divider_card_full_1_4mm.stl", card_1_4)
    
    manifest = {
        "version": VERSION,
        "parameters": {
            "body_outer": [BODY_W, BODY_D, BODY_H],
            "cavity_usable": [CAVITY_W, CAVITY_D, BODY_H - BODY_BOTTOM],
            "left_wall_thickness": BODY_W / 2 + INNER_X_LEFT,
            "right_wall_thickness": BODY_W / 2 - INNER_X_RIGHT,
            "slot_width": SLOT_W,
            "slot_recess": SLOT_RECESS,
            "floor_groove_depth": FLOOR_GROOVE_D,
            "slot_stations_y": SLOT_STATIONS,
            "card_baseline": [33.30, 31.20, 1.20],
            "hinge_vertical_drop_clearance": abs(INNER_X_LEFT - 0.50) - abs(HINGE_X + 2.05)
        },
        "audits": {
            "cassette_body_v0_8_divided.stl": audit_body,
            "divider_card_full_1_2mm.stl": audit_1_2
        }
    }
    
    with (BUILD_DIR / "manifest.json").open("w") as f:
        json.dump(manifest, f, indent=2)
    print("Divided cassette STLs and manifest generated.")

if __name__ == "__main__":
    main()
