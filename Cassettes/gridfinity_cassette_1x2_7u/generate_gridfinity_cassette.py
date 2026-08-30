#!/usr/bin/env python3
"""Generate the standalone 1x2 7U Gridfinity cassette bin models.

Architecture:
  - Designed directly from standard Gridfinity specifications:
    * 1x2 Gridfinity footprint (41.50 x 83.50 mm outside, r = 3.75 mm corner radius)
    * Two standard 42 mm base cells centered at Y = ±21.0 mm (35.6 -> 37.2 -> 41.5 mm stepped profile)
    * Monolithic standard 7U stacking lip on the top of the body (Z = 49.00 to 53.40 mm)
  - Inset lid rim below the Gridfinity stacking features:
    * Internal shelf at Z = 45.40 mm
    * Lid top rests at Z = 48.60 mm (0.40 mm below the Z = 49.00 mm stacking shelf plane)
    * Other Gridfinity bins stack directly into the top of the body with zero contact on the lid or glass
  - Embedded Hinge & Full-Length Through-Tunnel:
    * Thickened left wall (5.25 mm thick, inner face at X = -15.50 mm) embeds the entire hinge
    * Hinge axis moved back to X = -18.50 mm, providing +0.60 mm of clear vertical drop-in clearance past the knuckle peak
    * Full-length hinge bore tunnel extends completely through the front and back end walls (Y = -41.75 to +41.75 mm)
      with external pin entry ports on the outside of the box for effortless pin insertion
  - Squeeze-to-release closure catch:
    * Squeezing the front long wall flexes the wall inward ~0.7 mm, instantly disengaging the catch
  - Replaceable standard microscope glass slide window (75 x 25 x 1.1-1.2 mm) with end-loaded positive capture:
    * 1.20 mm solid PETG compliant retention clip with 0.50 mm tight flexure perimeter cutout
    * Centered 23.0 x 55.0 mm clear viewing window
    * Symmetrical 34.0 x 10.0 mm solid flat label zones on both ends for 9 mm Brother TZe tape
  - Smooth R = 4.0 mm curved finger scoop radius along inside bottom front (latch) floor
  - Removable divider cards at thirds stations dividing cavity into 3 equal compartments
  - 100% support-free FDM 3D printing (body upright, lid top-face down)
"""

from __future__ import annotations
import argparse
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

# --- Gridfinity Dimensional Constants ---
PITCH = 42.0
GRID_X = 1
GRID_Y = 2
OUTER_W = 41.50   # Short width along X
OUTER_L = 83.50   # Long length along Y
OUTER_R = 3.75    # Standard outer corner radius

# 7U Height Standards
HEIGHT_U = 7
ENGAGED_H = 49.00     # Stacking shelf engagement plane
LIP_H = 4.40          # Gridfinity stacking lip height
TOTAL_H = ENGAGED_H + LIP_H  # 53.40 mm
BASE_H = 4.75         # Height of Gridfinity base feet
FLOOR_Z = 6.00        # Inside cavity floor
WALL_T = 2.00         # Front/Back/Right perimeter wall thickness

# Thickened Left Wall (Embeds Hinge & Clears Dividers):
LEFT_WALL_INNER_X = -15.50  # 5.25 mm thick solid left wall
RIGHT_WALL_INNER_X = 18.75  # 2.00 mm thick right wall

# Internal Lid Shelf & Split Line:
LID_SHELF_Z = 45.40   # Internal inset rim plane inside the body
LID_THICKNESS = 3.20  # Lid thickness (45.40 + 3.20 = 48.60 mm; 0.40 mm below 49.00 mm stacking plane)

# Embedded Hinge Geometry (X = -18.50 mm, Z = 45.40 mm):
HINGE_X = -18.50               # Embedded inside thickened left wall
HINGE_Z = LID_SHELF_Z         # At internal lid rim plane (45.40 mm)
HINGE_OUTER_HALF_W = 2.00
HINGE_OUTER_POINT = 2.40
HINGE_OUTER_SIDE_TOP = 0.80
HINGE_BODY_BORE_R = 1.125      # 2.25 mm nominal bore on body
HINGE_LID_BORE_R = 1.05        # 2.10 mm nominal bore on lid

# Knuckle Stations along Y:
HINGE_BODY_FRONT_Y0 = -41.75   # External front entry port
HINGE_BODY_FRONT_Y1 = -37.80   # Front body knuckle/tunnel
HINGE_BODY_CENTER_Y0 = -14.00  # Center body knuckle
HINGE_BODY_CENTER_Y1 = 14.00
HINGE_BODY_BACK_Y0 = 37.80     # Back body knuckle/tunnel
HINGE_BODY_BACK_Y1 = 41.75     # External back exit port

HINGE_LID_K0_Y0 = -37.00       # Lower lid knuckle
HINGE_LID_K0_Y1 = -14.80
HINGE_LID_K1_Y0 = 14.80        # Upper lid knuckle
HINGE_LID_K1_Y1 = 37.00

# Glass Slide Capture Constants:
PANE_CHANNEL_W = 27.00
PANE_CHANNEL_H = 1.40
PANE_CHANNEL_Z0 = 0.80
PANE_CHANNEL_Z1 = 2.20
PANE_BOTTOM_Z0 = 0.20
PANE_TOP_Z1 = LID_THICKNESS

WINDOW_W = 23.00
WINDOW_D = 55.00
WINDOW_X = 0.00
WINDOW_Y = 0.00

PANE_FAR_STOP_Y = 37.50
PANE_ENTRY_Y = -39.00
PANE_SHOULDER_Y0 = -38.50
PANE_SHOULDER_Y1 = -37.50
PANE_TONGUE_ROOT_Y = -33.25
PANE_TONGUE_END_Y = -32.20
PANE_TONGUE_W = 8.00
PANE_TONGUE_H = 1.20
PANE_FINGER_PAD_W = 10.00

LABEL_W = 34.00
LABEL_D = 10.00
LABEL_X = 0.00
LABEL_Y = 33.00
ENTRY_LABEL_Y = -33.00

Vec2 = tuple[float, float]
V3 = tuple[float, float, float]
Tri = tuple[V3, V3, V3]


@dataclass
class Mesh:
    name: str
    triangles: list[Tri]

    def __init__(self, name: str = ""):
        self.name = name
        self.triangles = []

    def tri(self, a: V3, b: V3, c: V3) -> None:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        cross_sq = (uy * vz - uz * vy) ** 2 + (uz * vx - ux * vz) ** 2 + (ux * vy - uy * vx) ** 2
        if cross_sq > 1e-18:
            self.triangles.append((a, b, c))

    def quad(self, a: V3, b: V3, c: V3, d: V3) -> None:
        self.tri(a, b, c)
        self.tri(a, c, d)

    def extend(self, other: Mesh) -> None:
        self.triangles.extend(other.triangles)

    def translated(self, dx: float, dy: float, dz: float, name: str = "") -> Mesh:
        out = Mesh(name or self.name)
        out.triangles = [
            (
                (p0[0] + dx, p0[1] + dy, p0[2] + dz),
                (p1[0] + dx, p1[1] + dy, p1[2] + dz),
                (p2[0] + dx, p2[1] + dy, p2[2] + dz),
            )
            for p0, p1, p2 in self.triangles
        ]
        return out

    def bounds(self) -> tuple[V3, V3]:
        if not self.triangles:
            return ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        xs = [p[0] for t in self.triangles for p in t]
        ys = [p[1] for t in self.triangles for p in t]
        zs = [p[2] for t in self.triangles for p in t]
        return ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))

    def positive(self) -> Mesh:
        return self


def rounded_rect(w: float, d: float, r: float, n: int = 6) -> list[Vec2]:
    pts = []
    for cx, cy, start in (
        (w / 2 - r, d / 2 - r, 0),
        (-w / 2 + r, d / 2 - r, 90),
        (-w / 2 + r, -d / 2 + r, 180),
        (w / 2 - r, -d / 2 + r, 270),
    ):
        for i in range(n + 1):
            a = math.radians(start + i * 90 / n)
            pts.append((round(cx + r * math.cos(a), 4), round(cy + r * math.sin(a), 4)))
    return pts


def loft(rings: list[tuple[float, list[Vec2]]]) -> Mesh:
    m = Mesh()
    count = len(rings[0][1])
    for _, p in rings:
        assert len(p) == count
    z0, p0 = rings[0]
    for i in range(1, count - 1):
        m.tri((p0[0][0], p0[0][1], z0), (p0[i + 1][0], p0[i + 1][1], z0), (p0[i][0], p0[i][1], z0))
    zf, pf = rings[-1]
    for i in range(1, count - 1):
        m.tri((pf[0][0], pf[0][1], zf), (pf[i][0], pf[i][1], zf), (pf[i + 1][0], pf[i + 1][1], zf))
    for (za, pa), (zb, pb) in zip(rings, rings[1:]):
        for i in range(count):
            j = (i + 1) % count
            m.quad((pa[i][0], pa[i][1], za), (pa[j][0], pa[j][1], za), (pb[j][0], pb[j][1], zb), (pb[i][0], pb[i][1], zb))
    return m


def box(name: str, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Mesh:
    m = Mesh(name)
    p = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    m.extend(loft([(z0, p), (z1, p)]))
    return m


def prism(name: str, polygon_xy: list[Vec2], z0: float, z1: float) -> Mesh:
    m = Mesh(name)
    m.extend(loft([(z0, polygon_xy), (z1, polygon_xy)]))
    return m


def prism_y(name: str, profile_xz: list[Vec2], y0: float, y1: float) -> Mesh:
    m = Mesh(name)
    n = len(profile_xz)
    for i in range(1, n - 1):
        m.tri((profile_xz[0][0], y0, profile_xz[0][1]), (profile_xz[i][0], y0, profile_xz[i][1]), (profile_xz[i + 1][0], y0, profile_xz[i + 1][1]))
        m.tri((profile_xz[0][0], y1, profile_xz[0][1]), (profile_xz[i + 1][0], y1, profile_xz[i + 1][1]), (profile_xz[i][0], y1, profile_xz[i][1]))
    for i in range(n):
        j = (i + 1) % n
        m.quad((profile_xz[i][0], y0, profile_xz[i][1]), (profile_xz[i][0], y1, profile_xz[i][1]), (profile_xz[j][0], y1, profile_xz[j][1]), (profile_xz[j][0], y0, profile_xz[j][1]))
    return m


def prism_x(name: str, profile_yz: list[Vec2], x0: float, x1: float) -> Mesh:
    m = prism_y(name, profile_yz, x0, x1)
    out = Mesh(name)
    out.triangles = [tuple((y, x, z) for x, y, z in t) for t in m.triangles]
    return out


def hinge_profile_xz(cx: float, cz: float, print_up_sign: float, bore_r: float) -> tuple[list[Vec2], list[Vec2]]:
    """Return matched outer peaked profile and inner bore loops for support-free hollow hinge knuckles."""
    ow = HINGE_OUTER_HALF_W
    op = HINGE_OUTER_POINT
    st = HINGE_OUTER_SIDE_TOP

    outer_print = [(-ow, st), (-ow, 0.0)]
    outer_print.extend((-ow * (1.0 - step / 9.0), -op * step / 9.0) for step in range(1, 10))
    outer_print.extend((ow * step / 9.0, -op * (1.0 - step / 9.0)) for step in range(1, 10))
    outer_print.extend([(ow, st), (0.0, op)])

    # 21 circular points + 45-degree peaked roof point:
    bore_print = [
        (bore_r * math.cos(math.radians(135.0 + 13.5 * index)), bore_r * math.sin(math.radians(135.0 + 13.5 * index)))
        for index in range(21)
    ]
    bore_print.append((0.0, math.sqrt(2.0) * bore_r))

    def place(loop: Sequence[Vec2]) -> list[Vec2]:
        return [(cx + x, cz + print_up_sign * z) for x, z in loop]

    return place(outer_print), place(bore_print)


def peaked_hinge_y(name: str, cx: float, cz: float, y0: float, y1: float, print_up_sign: float, bore_r: float) -> Mesh:
    """Build a support-free hollow peaked hinge knuckle with true open filament bore."""
    outer_xz, inner_xz = hinge_profile_xz(cx, cz, print_up_sign, bore_r)
    m = Mesh(name)
    outer0 = [(x, y0, z) for x, z in outer_xz]
    outer1 = [(x, y1, z) for x, z in outer_xz]
    inner0 = [(x, y0, z) for x, z in inner_xz]
    inner1 = [(x, y1, z) for x, z in inner_xz]

    for i in range(len(outer0)):
        j = (i + 1) % len(outer0)
        m.quad(outer0[i], outer1[i], outer1[j], outer0[j])
        m.quad(inner0[i], inner0[j], inner1[j], inner1[i])
        m.quad(outer0[i], outer0[j], inner0[j], inner0[i])
        m.quad(outer1[i], inner1[i], inner1[j], outer1[j])
    return m


def build_gridfinity_base() -> Mesh:
    """Build the standard 1x2 Gridfinity base feet."""
    m = Mesh("gridfinity_1x2_base")
    for iy, cy in enumerate([-21.0, 21.0]):
        rings = []
        for z, w, r in ((0.0, 35.6, 3.2), (0.8, 37.2, 3.4), (2.6, 37.2, 3.4), (4.75, 41.5, 3.75)):
            rings.append((z, [(x, y + cy) for x, y in rounded_rect(w, w, r)]))
        m.extend(loft(rings))
    # Solid transition slab from 4.70 to FLOOR_Z:
    m.extend(loft([(BASE_H - 0.05, rounded_rect(OUTER_W, OUTER_L, OUTER_R)), (FLOOR_Z, rounded_rect(OUTER_W, OUTER_L, OUTER_R))]))
    return m


def build_scoop_fillet(ix: float, z_floor: float, r: float, y0: float, y1: float, n: int = 8) -> Mesh:
    """Build a smooth curved finger scoop radius along the inside front (latch) bottom corner."""
    cx = ix - r
    cz = z_floor + r
    join = 0.05
    profile = [(cx, z_floor - join), (ix + join, z_floor - join), (ix + join, cz)]
    for i in range(n, -1, -1):
        a = math.radians(270 + i * 90 / n)
        profile.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return prism_y("scoop_fillet", profile, y0, y1)


def build_corner_wedges(hx: float, hy: float, c: float, z0: float, z1: float, join: float = 0.05) -> Mesh:
    """Build the 4 rounded corner columns of the outer shell without filling the internal cavity."""
    m = Mesh("corner_wedges")
    n = 6
    for cx, cy, start in ((hx - c, -hy + c, 270), (hx - c, hy - c, 0), (-hx + c, hy - c, 90), (-hx + c, -hy + c, 180)):
        poly = [(cx, cy)]
        for i in range(n + 1):
            a = math.radians(start + i * 90 / n)
            poly.append((round(cx + c * math.cos(a), 4), round(cy + c * math.sin(a), 4)))
        m.extend(prism(f"corner_{int(start)}", poly, z0, z1))
    return m


def build_stacking_lip() -> Mesh:
    """Build the standard 1x2 Gridfinity stacking lip rim at the top of the body (Z in [49.00, 53.40 mm])."""
    m = Mesh("stacking_lip")
    hx = OUTER_W / 2  # 20.75
    hy = OUTER_L / 2  # 41.75
    c_out = OUTER_R   # 3.75
    c_in = 3.40       # 3.40 inner throat radius
    ix = 18.60        # throat half-width (37.2 mm total)
    iy = 39.60        # throat half-length (79.2 mm total)
    z0 = ENGAGED_H    # 49.00 mm
    z_top = TOTAL_H   # 53.40 mm
    join = 0.05

    xp = [(ix, z0 - join), (hx, z0 - join), (hx, z0 + 2.00), (hx - 0.40, z_top), (ix + 0.70, z_top), (ix + 0.70, z0 + 1.80), (ix, z0 + 1.10)]
    xn = [(-x, z) for x, z in xp]
    yp = [(iy, z0 - join), (hy, z0 - join), (hy, z0 + 2.00), (hy - 0.40, z_top), (iy + 0.70, z_top), (iy + 0.70, z0 + 1.80), (iy, z0 + 1.10)]
    yn = [(-y, z) for y, z in yp]

    # 4 Straight lip segments:
    m.extend(prism_y("lip_right", xp, -hy + c_out - join, hy - c_out + join))
    m.extend(prism_y("lip_left", xn, -hy + c_out - join, hy - c_out + join))
    m.extend(prism_x("lip_back", yp, -hx + c_out - join, hx - c_out + join))
    m.extend(prism_x("lip_front", yn, -hx + c_out - join, hx - c_out + join))

    # 4 Hollow corner arcs (ring polygons between outer and inner throat radius):
    corners = [
        (hx - c_out, -hy + c_out, ix - c_in, -iy + c_in, 270),
        (hx - c_out, hy - c_out, ix - c_in, iy - c_in, 0),
        (-hx + c_out, hy - c_out, -ix + c_in, iy - c_in, 90),
        (-hx + c_out, -hy + c_out, -ix + c_in, -iy + c_in, 180),
    ]
    for cx_o, cy_o, cx_i, cy_i, start in corners:
        poly = []
        for i in range(7):
            a = math.radians(start + i * 90 / 6)
            poly.append((round(cx_o + c_out * math.cos(a), 4), round(cy_o + c_out * math.sin(a), 4)))
        for i in range(6, -1, -1):
            a = math.radians(start + i * 90 / 6)
            poly.append((round(cx_i + c_in * math.cos(a), 4), round(cy_i + c_in * math.sin(a), 4)))
        m.extend(prism(f"lip_corner_{int(start)}", poly, z0 - join, z_top))

    return m


def build_1x2_body_divided() -> Mesh:
    """Build the 1x2 7U divided Gridfinity cassette body with thickened left wall, embedded through-tunnel hinge, and squeeze catch."""
    out = Mesh("gridfinity_body_1x2_7u_divided")
    out.extend(build_gridfinity_base())

    hx, hy = OUTER_W / 2, OUTER_L / 2
    c = OUTER_R
    lx = LEFT_WALL_INNER_X   # -15.50 mm (5.25 mm thick solid left wall)
    rx = RIGHT_WALL_INNER_X  # +18.75 mm (2.00 mm thick right wall)
    iy = hy - WALL_T         # 39.75 mm
    join = 0.05
    z_floor = FLOOR_Z

    # 1. Thickened Solid Left Wall below the lid shelf (Z = 6.00 to 45.40 mm):
    out.extend(box("body_thickened_left_wall_lower", -hx, lx + join, -hy + c - join, hy - c + join, z_floor - join, LID_SHELF_Z + join))

    # 2. Outer Thin Left Wall Shell above the lid shelf (Z = 45.40 to 49.00 mm):
    out.extend(box("body_left_outer_wall_upper", -hx, -hx + 2.00 + join, -hy + c - join, hy - c + join, LID_SHELF_Z - join, ENGAGED_H))

    # 3. Right, Front, and Back Outer Walls (Z = 6.00 to 49.00 mm):
    out.extend(box("body_outer_right", rx - join, hx, -hy + c - join, hy - c + join, z_floor - join, ENGAGED_H))
    out.extend(box("body_outer_front", -hx + c - join, hx - c + join, -hy, -iy + join, z_floor - join, ENGAGED_H))
    out.extend(box("body_outer_back", -hx + c - join, hx - c + join, iy - join, hy, z_floor - join, ENGAGED_H))

    # 3. Outer 4 corner rounded wedges (Z = 6.00 to 49.00 mm):
    out.extend(build_corner_wedges(hx, hy, c, z_floor - join, ENGAGED_H, join))

    # 4. Monolithic Stacking Lip on Top of Body (Z = 49.00 to 53.40 mm):
    out.extend(build_stacking_lip())

    # 5. Inset Lid Shelf Ledges (Z = 45.40 mm) supporting the lid:
    shelf_w = 1.20
    out.extend(box("lid_shelf_right", rx - shelf_w, rx + join, -hy + c, hy - c, LID_SHELF_Z - 1.20, LID_SHELF_Z + join))
    out.extend(box("lid_shelf_front", lx + join, rx - join, -iy - join, -iy + shelf_w, LID_SHELF_Z - 1.20, LID_SHELF_Z + join))
    out.extend(box("lid_shelf_back", lx + join, rx - join, iy - shelf_w, iy + join, LID_SHELF_Z - 1.20, LID_SHELF_Z + join))

    # 6. Divider slots (Two stations at thirds Y = ±13.50 mm):
    slot_w = 1.40
    slot_stations = [-13.50, 13.50]
    ridge_proj = 0.80
    ridge_w = 1.50

    for cy in slot_stations:
        # Right wall ridges & slot:
        ry0_a, ry1_a = cy - slot_w / 2 - ridge_w, cy - slot_w / 2
        out.extend(box(f"ridge_lower_{cy:.2f}", rx - ridge_proj, rx + join, ry0_a - join, ry1_a + join, z_floor - join, LID_SHELF_Z - 1.00 + join))
        chamfer_pts = [(rx - ridge_proj, LID_SHELF_Z - 1.00), (rx, LID_SHELF_Z), (rx, LID_SHELF_Z - 1.00)]
        out.extend(prism_y(f"ridge_lead_lower_{cy:.2f}", chamfer_pts, ry0_a - join, ry1_a + join))

        ry0_b, ry1_b = cy + slot_w / 2, cy + slot_w / 2 + ridge_w
        out.extend(box(f"ridge_upper_{cy:.2f}", rx - ridge_proj, rx + join, ry0_b - join, ry1_b + join, z_floor - join, LID_SHELF_Z - 1.00 + join))
        out.extend(prism_y(f"ridge_lead_upper_{cy:.2f}", chamfer_pts, ry0_b - join, ry1_b + join))

        # Left wall slot channel (recessed into thickened wall):
        out.extend(box(f"left_slot_channel_{cy:.2f}", lx - 0.60, lx + join, cy - slot_w / 2, cy + slot_w / 2, z_floor - join, LID_SHELF_Z + join))

    # 7. Smooth finger scoop fillets (R = 4.0 mm) along inside front (latch) floor edge:
    r_scoop = 4.00
    out.extend(build_scoop_fillet(rx, z_floor, r_scoop, -hy + c, slot_stations[0] - slot_w / 2 + join))
    out.extend(build_scoop_fillet(rx, z_floor, r_scoop, slot_stations[0] + slot_w / 2 - join, slot_stations[1] - slot_w / 2 + join))
    out.extend(build_scoop_fillet(rx, z_floor, r_scoop, slot_stations[1] + slot_w / 2 - join, hy - c))

    # 8. Embedded Hinge Knuckles & Full-Length Pin Tunnels:
    # Front end tunnel (extends through front face Y = -41.75 mm):
    out.extend(peaked_hinge_y("body_front_tunnel", HINGE_X, HINGE_Z, HINGE_BODY_FRONT_Y0, HINGE_BODY_FRONT_Y1, print_up_sign=1.0, bore_r=HINGE_BODY_BORE_R))
    # Center knuckle:
    out.extend(peaked_hinge_y("body_centre_knuckle", HINGE_X, HINGE_Z, HINGE_BODY_CENTER_Y0, HINGE_BODY_CENTER_Y1, print_up_sign=1.0, bore_r=HINGE_BODY_BORE_R))
    # Back end tunnel (extends through back face Y = +41.75 mm):
    out.extend(peaked_hinge_y("body_back_tunnel", HINGE_X, HINGE_Z, HINGE_BODY_BACK_Y0, HINGE_BODY_BACK_Y1, print_up_sign=1.0, bore_r=HINGE_BODY_BORE_R))

    # 9. Squeeze-to-Release Inward Catch on Inside of Right Wall (0.60 mm undercut):
    catch_profile = [
        (rx, LID_SHELF_Z + 1.20),
        (rx - 0.60, LID_SHELF_Z + 2.00),
        (rx - 0.60, LID_SHELF_Z + 2.60),
        (rx, LID_SHELF_Z + 3.10),
    ]
    out.extend(prism_y("body_squeeze_catch", catch_profile, -6.00, 6.00))

    return out


def build_1x2_body() -> Mesh:
    """Build the undivided 1x2 7U Gridfinity cassette body with thickened left wall, embedded through-tunnel hinge, and squeeze catch."""
    out = Mesh("gridfinity_body_1x2_7u")
    out.extend(build_gridfinity_base())

    hx, hy = OUTER_W / 2, OUTER_L / 2
    c = OUTER_R
    lx = LEFT_WALL_INNER_X
    rx = RIGHT_WALL_INNER_X
    iy = hy - WALL_T
    join = 0.05
    z_floor = FLOOR_Z

    # 1. Thickened Solid Left Wall below the lid shelf (Z = 6.00 to 45.40 mm):
    out.extend(box("body_thickened_left_wall_lower", -hx, lx + join, -hy + c - join, hy - c + join, z_floor - join, LID_SHELF_Z + join))

    # 2. Outer Thin Left Wall Shell above the lid shelf (Z = 45.40 to 49.00 mm):
    out.extend(box("body_left_outer_wall_upper", -hx, -hx + 2.00 + join, -hy + c - join, hy - c + join, LID_SHELF_Z - join, ENGAGED_H))

    # 3. Right, Front, and Back Outer Walls:
    out.extend(box("body_outer_right", rx - join, hx, -hy + c - join, hy - c + join, z_floor - join, ENGAGED_H))
    out.extend(box("body_outer_front", -hx + c - join, hx - c + join, -hy, -iy + join, z_floor - join, ENGAGED_H))
    out.extend(box("body_outer_back", -hx + c - join, hx - c + join, iy - join, hy, z_floor - join, ENGAGED_H))

    # 3. Outer 4 corner rounded wedges:
    out.extend(build_corner_wedges(hx, hy, c, z_floor - join, ENGAGED_H, join))

    # 4. Monolithic Stacking Lip on Top of Body:
    out.extend(build_stacking_lip())

    # 5. Inset Lid Shelf Ledges (Z = 45.40 mm):
    shelf_w = 1.20
    out.extend(box("lid_shelf_right", rx - shelf_w, rx + join, -hy + c, hy - c, LID_SHELF_Z - 1.20, LID_SHELF_Z + join))
    out.extend(box("lid_shelf_front", lx + join, rx - join, -iy - join, -iy + shelf_w, LID_SHELF_Z - 1.20, LID_SHELF_Z + join))
    out.extend(box("lid_shelf_back", lx + join, rx - join, iy - shelf_w, iy + join, LID_SHELF_Z - 1.20, LID_SHELF_Z + join))

    # 6. Continuous smooth finger scoop fillet (R = 4.0 mm) along inside front (latch) floor edge:
    r_scoop = 4.00
    out.extend(build_scoop_fillet(rx, z_floor, r_scoop, -hy + c, hy - c))

    # 7. Embedded Hinge Knuckles & Full-Length Pin Tunnels:
    out.extend(peaked_hinge_y("body_front_tunnel", HINGE_X, HINGE_Z, HINGE_BODY_FRONT_Y0, HINGE_BODY_FRONT_Y1, print_up_sign=1.0, bore_r=HINGE_BODY_BORE_R))
    out.extend(peaked_hinge_y("body_centre_knuckle", HINGE_X, HINGE_Z, HINGE_BODY_CENTER_Y0, HINGE_BODY_CENTER_Y1, print_up_sign=1.0, bore_r=HINGE_BODY_BORE_R))
    out.extend(peaked_hinge_y("body_back_tunnel", HINGE_X, HINGE_Z, HINGE_BODY_BACK_Y0, HINGE_BODY_BACK_Y1, print_up_sign=1.0, bore_r=HINGE_BODY_BORE_R))

    # 8. Squeeze-to-Release Inward Catch:
    catch_profile = [
        (rx, LID_SHELF_Z + 1.20),
        (rx - 0.60, LID_SHELF_Z + 2.00),
        (rx - 0.60, LID_SHELF_Z + 2.60),
        (rx, LID_SHELF_Z + 3.10),
    ]
    out.extend(prism_y("body_squeeze_catch", catch_profile, -6.00, 6.00))

    return out


def build_1x2_lid_local() -> Mesh:
    """Build the internal inset lid that seats below the Gridfinity stacking features with embedded hinge knuckles."""
    out = Mesh("gridfinity_lid_1x2_7u_local")

    lid_x0 = HINGE_X          # -18.50 mm (hinge axis)
    lid_x1 = 17.50            # Latch hook edge
    lid_w = lid_x1 - lid_x0   # 36.00 mm
    lid_l = 77.80             # Fits within 79.2 mm throat
    hy = lid_l / 2            # 38.90

    top_z0 = PANE_CHANNEL_Z1
    top_z1 = PANE_TOP_Z1
    window_y0 = WINDOW_Y - WINDOW_D / 2   # -27.50
    window_y1 = WINDOW_Y + WINDOW_D / 2   # +27.50
    window_x0 = WINDOW_X - WINDOW_W / 2   # -11.50
    window_x1 = WINDOW_X + WINDOW_W / 2   # +11.50

    # Compliant clip cutout dimensions (0.50 mm clearance gap around cantilever tongue and pad):
    tongue_x0 = WINDOW_X - PANE_TONGUE_W / 2      # -4.00
    tongue_x1 = WINDOW_X + PANE_TONGUE_W / 2      #  4.00
    pad_x0 = WINDOW_X - PANE_FINGER_PAD_W / 2     # -5.00
    pad_x1 = WINDOW_X + PANE_FINGER_PAD_W / 2     #  5.00

    pad_gap = 0.50
    tongue_gap = 0.50
    pad_cut_x0 = pad_x0 - pad_gap                 # -5.50
    pad_cut_x1 = pad_x1 + pad_gap                 #  5.50
    tongue_cut_x0 = tongue_x0 - tongue_gap         # -4.50
    tongue_cut_x1 = tongue_x1 + tongue_gap         #  4.50

    # 1. Main Lid Top Plate (local Z in [top_z0, top_z1] = [2.20, 3.20 mm]):
    # A. Entry side top frame with 0.50 mm clearance cutouts around the compliant clip:
    out.extend(box("top_entry_pad_left", lid_x0, pad_cut_x0, PANE_ENTRY_Y, -36.20, top_z0, top_z1))
    out.extend(box("top_entry_pad_right", pad_cut_x1, lid_x1, PANE_ENTRY_Y, -36.20, top_z0, top_z1))
    out.extend(box("top_entry_tongue_left", lid_x0, tongue_cut_x0, -36.25, -33.50, top_z0, top_z1))
    out.extend(box("top_entry_tongue_right", tongue_cut_x1, lid_x1, -36.25, -33.50, top_z0, top_z1))
    out.extend(box("top_entry_gusset_left", lid_x0, pad_cut_x0, -33.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))
    out.extend(box("top_entry_gusset_right", pad_cut_x1, lid_x1, -33.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))
    out.extend(box("top_tongue_root_band", lid_x0, lid_x1, PANE_TONGUE_ROOT_Y, window_y0 + 0.05, top_z0, top_z1))

    # B. Side Rails flanking the 23.0 mm window:
    out.extend(box("top_left_rail", lid_x0, window_x0, window_y0 - 0.05, window_y1 + 0.05, top_z0, top_z1))
    out.extend(box("top_right_rail", window_x1, lid_x1, window_y0 - 0.05, window_y1 + 0.05, top_z0, top_z1))

    # C. Far end solid label band:
    out.extend(box("top_far_border", lid_x0, lid_x1, window_y1 - 0.05, hy, top_z0, top_z1))

    # 2. Glass Microscope Slide Channel (local Z in [PANE_CHANNEL_Z0, PANE_CHANNEL_Z1] = [0.80, 2.20 mm]):
    ch_x0 = WINDOW_X - PANE_CHANNEL_W / 2  # -13.50
    ch_x1 = WINDOW_X + PANE_CHANNEL_W / 2  # +13.50
    bot_x0 = WINDOW_X - 12.00              # -12.00
    bot_x1 = WINDOW_X + 12.00              # +12.00

    out.extend(box("pane_left_wall", lid_x0, ch_x0, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("pane_right_wall", ch_x1, lid_x1, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("pane_left_bottom_ledge", lid_x0, bot_x0, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box("pane_right_bottom_ledge", bot_x1, lid_x1, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box("pane_far_stop", ch_x0 - 0.05, ch_x1 + 0.05, PANE_FAR_STOP_Y, hy, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))

    # 3. Reinforced Compliant Glass Retention Clip (1.20 mm solid PETG, local Z in [LID_THICKNESS - 1.20, LID_THICKNESS]):
    out.extend(box("pane_compliant_tongue", tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_TONGUE_END_Y, LID_THICKNESS - PANE_TONGUE_H, LID_THICKNESS))
    out.extend(box("pane_latch_finger_pad", pad_x0, pad_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1 + 0.20, LID_THICKNESS - PANE_TONGUE_H, LID_THICKNESS))
    out.extend(box("pane_positive_end_shoulder", tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1, PANE_CHANNEL_Z0, LID_THICKNESS - PANE_TONGUE_H + 0.05))

    # 3D Root Gussets:
    out.extend(prism("tongue_gusset_left", [(tongue_x0 - 2.5, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x0 + 0.1, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x0 + 0.1, PANE_TONGUE_ROOT_Y - 2.0)], LID_THICKNESS - PANE_TONGUE_H, LID_THICKNESS))
    out.extend(prism("tongue_gusset_right", [(tongue_x1 - 0.1, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x1 + 2.5, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x1 - 0.1, PANE_TONGUE_ROOT_Y - 2.0)], LID_THICKNESS - PANE_TONGUE_H, LID_THICKNESS))

    # 4. Inset Twin Hinge Knuckles along Left Edge (aligned at HINGE_X = -18.50 mm):
    for name_k, y0_k, y1_k in (("lid_knuckle_0", HINGE_LID_K0_Y0, HINGE_LID_K0_Y1), ("lid_knuckle_1", HINGE_LID_K1_Y0, HINGE_LID_K1_Y1)):
        out.extend(peaked_hinge_y(name_k, HINGE_X, 0.00, y0_k, y1_k, print_up_sign=-1.0, bore_r=HINGE_LID_BORE_R))

    # 5. Matching Catch Hook on Right Wall Edge (snaps under body squeeze catch):
    hook_xz = [
        (lid_x1 - 1.20, 0.00),
        (lid_x1, 0.00),
        (lid_x1 + 0.55, 2.00),
        (lid_x1 + 0.55, 2.60),
        (lid_x1, 3.20),
        (lid_x1 - 1.20, 3.20),
    ]
    out.extend(prism_y("lid_closure_hook", hook_xz, -5.50, 5.50))

    return out


def lid_print_orientation(lid: Mesh) -> Mesh:
    """Orient the lid for support-free printing (top face down on build plate)."""
    rot = Mesh("gridfinity_lid_1x2_7u_print")
    rot.triangles = [
        (
            (p0[0], p0[1], LID_THICKNESS - p0[2]),
            (p2[0], p2[1], LID_THICKNESS - p2[2]),
            (p1[0], p1[1], LID_THICKNESS - p1[2]),
        )
        for p0, p1, p2 in lid.triangles
    ]
    zmin = rot.bounds()[0][2]
    return rot.translated(0.0, 0.0, -zmin, "gridfinity_lid_1x2_7u_print").positive()


def build_divider_card_1x2_7u(thickness: float = 1.20) -> Mesh:
    """Build divider card for the 7U 1x2 Gridfinity cassette clearing the embedded hinge."""
    name = f"divider_card_1x2_7u_{thickness:.1f}mm"
    x_left = LEFT_WALL_INNER_X - 0.50  # -16.00 mm (seats in left slot channel)
    x_right = RIGHT_WALL_INNER_X       # 18.75 mm
    z_top = 38.80
    ht = thickness / 2.0
    notch_w = 12.0
    notch_d = 2.0
    r_scoop = 4.00

    pts_xz = [
        (x_left + 1.0, 0.0),
        (x_right - r_scoop, 0.0),
        (x_right, r_scoop),
        (x_right, z_top - 1.0),
        (x_right - 1.0, z_top),
        (notch_w / 2.0, z_top),
        (notch_w / 4.0, z_top - notch_d),
        (-notch_w / 4.0, z_top - notch_d),
        (-notch_w / 2.0, z_top),
        (x_left + 1.0, z_top),
        (x_left, z_top - 1.0),
        (x_left, 1.0),
    ]
    return prism_y(name, pts_xz, -ht, ht)


def normal(t: Tri) -> V3:
    a, b, c = t
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    q = math.sqrt(sum(x * x for x in n))
    return tuple(x / q for x in n) if q else (0.0, 0.0, 0.0)


def write_binary_stl(path: Path, mesh: Mesh) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        header = f"Gridfinity Cassette Bin 1x2 7U: {mesh.name}".encode("ascii", "replace")[:80].ljust(80, b" ")
        f.write(header)
        f.write(struct.pack("<I", len(mesh.triangles)))
        for t in mesh.triangles:
            norm = normal(t)
            f.write(
                struct.pack(
                    "<12fH",
                    norm[0], norm[1], norm[2],
                    t[0][0], t[0][1], t[0][2],
                    t[1][0], t[1][1], t[1][2],
                    t[2][0], t[2][1], t[2][2],
                    0,
                )
            )


def main():
    parser = argparse.ArgumentParser(description="Generate 1x2 7U Gridfinity Cassette Bin models")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "build")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    body_divided = build_1x2_body_divided()
    body_undivided = build_1x2_body()
    lid_local = build_1x2_lid_local()
    lid_print = lid_print_orientation(lid_local)
    card_1_2 = build_divider_card_1x2_7u(1.20)

    # Reference assembly (lid seated on internal shelf at Z = 45.40 mm; top at Z = 48.60 mm):
    closed_lid = lid_local.translated(0.0, 0.0, LID_SHELF_Z + 0.02, "closed_lid")
    ref_closed = Mesh("REFERENCE_closed_assembly_1x2_7u_DO_NOT_PRINT")
    ref_closed.extend(body_divided)
    ref_closed.extend(closed_lid)

    # Reference 2-high stack (demonstrating exact 14U engaged height = 102.40 mm):
    ref_2high = Mesh("REFERENCE_two_high_stack_1x2_14u_DO_NOT_PRINT")
    ref_2high.extend(ref_closed)
    ref_2high.extend(ref_closed.translated(0.0, 0.0, ENGAGED_H + 0.02))

    files = [
        ("gridfinity_cassette_body_1x2_7u_divided.stl", body_divided),
        ("gridfinity_cassette_body_1x2_7u.stl", body_undivided),
        ("gridfinity_cassette_lid_1x2_7u_print.stl", lid_print),
        ("divider_card_1x2_7u_1_2mm.stl", card_1_2),
        ("REFERENCE_closed_assembly_1x2_7u_DO_NOT_PRINT.stl", ref_closed),
        ("REFERENCE_two_high_stack_1x2_14u_DO_NOT_PRINT.stl", ref_2high),
    ]

    manifest = {
        "format": "Gridfinity 1x2 7U Cassette Bin (Direct Stacking Body with Inset Lid & Through-Tunnel Hinge)",
        "pitch_mm": [PITCH, 2 * PITCH],
        "envelope_outside_mm": [OUTER_W, OUTER_L, TOTAL_H],
        "stacking_engaged_height_mm": ENGAGED_H,
        "total_height_with_lip_mm": TOTAL_H,
        "lid_top_height_mm": LID_SHELF_Z + LID_THICKNESS,
        "lid_clearance_below_stacking_shelf_mm": ENGAGED_H - (LID_SHELF_Z + LID_THICKNESS),
        "two_high_stack_height_mm": ENGAGED_H + TOTAL_H,
        "drawer_ceiling_mm": 111.125,
        "drawer_stack_clearance_mm": 111.125 - (ENGAGED_H + TOTAL_H),
        "files": [],
    }

    for fn, m in files:
        write_binary_stl(args.out / fn, m)
        bmin, bmax = m.bounds()
        dims = [round(bmax[i] - bmin[i], 2) for i in range(3)]
        manifest["files"].append({
            "file": fn,
            "triangles": len(m.triangles),
            "bounds_min_mm": [round(x, 2) for x in bmin],
            "bounds_max_mm": [round(x, 2) for x in bmax],
            "size_mm": dims,
        })
        print(f"Generated {fn}: {len(m.triangles)} tris, size: {dims}")

    (args.out / "manifest_1x2_7u.json").write_text(json.dumps(manifest, indent=2))
    print(f"Manifest written to {args.out / 'manifest_1x2_7u.json'}")


if __name__ == "__main__":
    main()
