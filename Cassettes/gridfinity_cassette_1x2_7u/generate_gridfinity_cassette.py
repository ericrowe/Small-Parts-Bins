#!/usr/bin/env python3
"""Generate the standalone 1x2 7U Gridfinity cassette bin with horizontal sliding lid.

Architecture:
  - Designed directly from standard Gridfinity specifications:
    * 1x2 Gridfinity footprint (41.50 x 83.50 mm outside, r = 3.75 mm corner radius)
    * Two standard 42 mm base cells centered at Y = ±21.0 mm (35.6 -> 37.2 -> 41.5 mm stepped profile)
    * Monolithic standard 7U stacking lip on the top of the body (Z = 49.00 to 53.40 mm)
  - Horizontal Sliding Lid Slot below Stacking Lip:
    * Continuous guide rails along left and right walls (Z in [45.20, 48.60 mm], 3.40 mm clear height)
    * Solid back end stop at Y = +39.75 mm
    * Open front entry mouth at Y = -41.75 mm
    * Stacking plane at Z = 49.00 mm sits completely above the lid, allowing bins to stack with zero lid contact
  - Loose-Fit Horizontal Sliding Lid:
    * Slides smoothly in and out along the long Y-axis with generous loose float clearances
    * Front protruding finger pull tab (extends past front face by 4.0 mm) with ergonomic fingernail catch
    * Replaceable standard microscope glass slide window (75 x 25 x 1.1-1.2 mm) with end-loaded positive capture:
      - 1.20 mm solid PETG compliant retention clip with 0.50 mm tight flexure perimeter cutout
      - Centered 23.0 x 55.0 mm clear viewing aperture
      - Symmetrical 34.0 x 10.0 mm solid flat label zones on both ends for 9 mm Brother TZe tape
  - Smooth R = 4.0 mm curved finger scoop radius along inside bottom front floor
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
WALL_T = 2.00         # Perimeter wall thickness

# Sliding Lid Slot in Body (Below Stacking Lip):
SLOT_Z0 = 45.20       # Bottom shelf of slide slot
SLOT_Z1 = 48.60       # Top roof of slide slot (0.40 mm below 49.00 mm stacking plane)
SLOT_W = 38.00        # Clear width between left and right slot channels
SLOT_STOP_Y = 39.75   # Solid back end stop

# Sliding Lid Dimensions:
LID_THICKNESS = 3.00  # 0.40 mm vertical float clearance
LID_W = 37.40         # 0.60 mm total horizontal loose float clearance
LID_L_INSERT = 79.20  # Main body span inserted into bin
PULL_TAB_L = 4.00     # Protrusion past front face (Y = -41.75 to -43.50 mm)
PULL_TAB_W = 24.00    # Ergonomic finger grip width

# Glass Slide Capture Constants:
PANE_CHANNEL_W = 27.00
PANE_CHANNEL_H = 1.40
PANE_CHANNEL_Z0 = 0.70
PANE_CHANNEL_Z1 = 2.10
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
    """Build a smooth curved finger scoop radius along the inside front bottom corner."""
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
    """Build the 1x2 7U divided Gridfinity cassette body with horizontal sliding lid guide rails and scoop."""
    out = Mesh("gridfinity_body_1x2_7u_divided")
    out.extend(build_gridfinity_base())

    hx, hy = OUTER_W / 2, OUTER_L / 2
    c = OUTER_R
    ix, iy = hx - WALL_T, hy - WALL_T  # 18.75 x 39.75 mm cavity
    join = 0.05
    z_floor = FLOOR_Z
    rx_slot = SLOT_W / 2  # 19.00 mm

    # 1. Continuous Outer Perimeter Walls (Z = 6.00 to 45.20 mm):
    out.extend(box("body_lower_left", -hx, -ix + join, -hy + c - join, hy - c + join, z_floor - join, SLOT_Z0 + join))
    out.extend(box("body_lower_right", ix - join, hx, -hy + c - join, hy - c + join, z_floor - join, SLOT_Z0 + join))
    out.extend(box("body_lower_front", -hx + c - join, hx - c + join, -hy, -iy + join, z_floor - join, SLOT_Z0 + join))
    out.extend(box("body_lower_back", -hx + c - join, hx - c + join, iy - join, hy, z_floor - join, SLOT_Z0 + join))

    # 2. Upper Wall Shells & Stacking Lip (Z = 45.20 to 49.00 mm):
    # Left & Right slot guide walls (recessed to rx_slot):
    out.extend(box("body_upper_left_wall", -hx, -rx_slot + join, -hy + c - join, hy - c + join, SLOT_Z0 - join, ENGAGED_H))
    out.extend(box("body_upper_right_wall", rx_slot - join, hx, -hy + c - join, hy - c + join, SLOT_Z0 - join, ENGAGED_H))
    # Solid back end-stop wall:
    out.extend(box("body_upper_back_wall", -hx + c - join, hx - c + join, iy - join, hy, SLOT_Z0 - join, ENGAGED_H))
    # Open front entry slot: front wall above SLOT_Z0 only exists above SLOT_Z1 under the lip:
    out.extend(box("body_upper_front_overhang", -hx + c - join, hx - c + join, -hy, -iy + join, SLOT_Z1 - join, ENGAGED_H))

    # 3. Outer 4 corner rounded columns:
    out.extend(build_corner_wedges(hx, hy, c, z_floor - join, ENGAGED_H, join))

    # 4. Monolithic Stacking Lip on Top of Body (Z = 49.00 to 53.40 mm):
    out.extend(build_stacking_lip())

    # 5. Sliding guide rails (under-roof retainers at Z = 48.60 mm):
    rail_w = 1.00
    out.extend(box("slide_rail_left", -rx_slot - join, -rx_slot + rail_w, -hy + c - join, hy - c + join, SLOT_Z1 - 0.80, SLOT_Z1 + join))
    out.extend(box("slide_rail_right", rx_slot - rail_w, rx_slot + join, -hy + c - join, hy - c + join, SLOT_Z1 - 0.80, SLOT_Z1 + join))

    # 6. Divider slots (Two stations at thirds Y = ±13.50 mm):
    slot_w = 1.40
    slot_stations = [-13.50, 13.50]
    ridge_proj = 0.80
    ridge_w = 1.50

    for cy in slot_stations:
        # Right wall ridges & slot:
        ry0_a, ry1_a = cy - slot_w / 2 - ridge_w, cy - slot_w / 2
        out.extend(box(f"ridge_lower_{cy:.2f}", ix - ridge_proj, ix + join, ry0_a - join, ry1_a + join, z_floor - join, SLOT_Z0 - 1.00 + join))
        chamfer_pts = [(ix - ridge_proj, SLOT_Z0 - 1.00), (ix, SLOT_Z0), (ix, SLOT_Z0 - 1.00)]
        out.extend(prism_y(f"ridge_lead_lower_{cy:.2f}", chamfer_pts, ry0_a - join, ry1_a + join))

        ry0_b, ry1_b = cy + slot_w / 2, cy + slot_w / 2 + ridge_w
        out.extend(box(f"ridge_upper_{cy:.2f}", ix - ridge_proj, ix + join, ry0_b - join, ry1_b + join, z_floor - join, SLOT_Z0 - 1.00 + join))
        out.extend(prism_y(f"ridge_lead_upper_{cy:.2f}", chamfer_pts, ry0_b - join, ry1_b + join))

        # Left wall ridges:
        out.extend(box(f"left_ridge_lower_{cy:.2f}", -ix - join, -ix + ridge_proj, ry0_a - join, ry1_a + join, z_floor - join, SLOT_Z0 - 1.00 + join))
        chamfer_left = [(-ix + ridge_proj, SLOT_Z0 - 1.00), (-ix, SLOT_Z0), (-ix, SLOT_Z0 - 1.00)]
        out.extend(prism_y(f"left_lead_lower_{cy:.2f}", chamfer_left, ry0_a - join, ry1_a + join))
        out.extend(box(f"left_ridge_upper_{cy:.2f}", -ix - join, -ix + ridge_proj, ry0_b - join, ry1_b + join, z_floor - join, SLOT_Z0 - 1.00 + join))
        out.extend(prism_y(f"left_lead_upper_{cy:.2f}", chamfer_left, ry0_b - join, ry1_b + join))

    # 7. Smooth finger scoop fillets (R = 4.0 mm) along inside bottom front (right) floor edge:
    r_scoop = 4.00
    out.extend(build_scoop_fillet(ix, z_floor, r_scoop, -hy + c, slot_stations[0] - slot_w / 2 + join))
    out.extend(build_scoop_fillet(ix, z_floor, r_scoop, slot_stations[0] + slot_w / 2 - join, slot_stations[1] - slot_w / 2 + join))
    out.extend(build_scoop_fillet(ix, z_floor, r_scoop, slot_stations[1] + slot_w / 2 - join, hy - c))

    return out


def build_1x2_body() -> Mesh:
    """Build the undivided 1x2 7U Gridfinity cassette body with horizontal sliding lid guide rails and scoop."""
    out = Mesh("gridfinity_body_1x2_7u")
    out.extend(build_gridfinity_base())

    hx, hy = OUTER_W / 2, OUTER_L / 2
    c = OUTER_R
    ix, iy = hx - WALL_T, hy - WALL_T
    join = 0.05
    z_floor = FLOOR_Z
    rx_slot = SLOT_W / 2

    # 1. Continuous Lower Walls:
    out.extend(box("body_lower_left", -hx, -ix + join, -hy + c - join, hy - c + join, z_floor - join, SLOT_Z0 + join))
    out.extend(box("body_lower_right", ix - join, hx, -hy + c - join, hy - c + join, z_floor - join, SLOT_Z0 + join))
    out.extend(box("body_lower_front", -hx + c - join, hx - c + join, -hy, -iy + join, z_floor - join, SLOT_Z0 + join))
    out.extend(box("body_lower_back", -hx + c - join, hx - c + join, iy - join, hy, z_floor - join, SLOT_Z0 + join))

    # 2. Upper Wall Shells & Stacking Lip:
    out.extend(box("body_upper_left_wall", -hx, -rx_slot + join, -hy + c - join, hy - c + join, SLOT_Z0 - join, ENGAGED_H))
    out.extend(box("body_upper_right_wall", rx_slot - join, hx, -hy + c - join, hy - c + join, SLOT_Z0 - join, ENGAGED_H))
    out.extend(box("body_upper_back_wall", -hx + c - join, hx - c + join, iy - join, hy, SLOT_Z0 - join, ENGAGED_H))
    out.extend(box("body_upper_front_overhang", -hx + c - join, hx - c + join, -hy, -iy + join, SLOT_Z1 - join, ENGAGED_H))

    # 3. Outer 4 corner rounded columns:
    out.extend(build_corner_wedges(hx, hy, c, z_floor - join, ENGAGED_H, join))

    # 4. Monolithic Stacking Lip:
    out.extend(build_stacking_lip())

    # 5. Sliding guide rails:
    rail_w = 1.00
    out.extend(box("slide_rail_left", -rx_slot - join, -rx_slot + rail_w, -hy + c - join, hy - c + join, SLOT_Z1 - 0.80, SLOT_Z1 + join))
    out.extend(box("slide_rail_right", rx_slot - rail_w, rx_slot + join, -hy + c - join, hy - c + join, SLOT_Z1 - 0.80, SLOT_Z1 + join))

    # 6. Continuous smooth finger scoop fillet:
    r_scoop = 4.00
    out.extend(build_scoop_fillet(ix, z_floor, r_scoop, -hy + c, hy - c))

    return out


def build_1x2_sliding_lid_local() -> Mesh:
    """Build the horizontal loose-fit sliding lid with glass window, compliant clip, and front pull tab."""
    out = Mesh("gridfinity_lid_1x2_7u_local")

    hx = LID_W / 2          # 18.70 mm
    hy_back = 39.50         # Rear end
    hy_front = -39.50       # Front body plane
    hy_pull = -43.50        # Front pull tab apex

    top_z0 = PANE_CHANNEL_Z1
    top_z1 = PANE_TOP_Z1
    window_y0 = WINDOW_Y - WINDOW_D / 2   # -27.50
    window_y1 = WINDOW_Y + WINDOW_D / 2   # +27.50
    window_x0 = WINDOW_X - WINDOW_W / 2   # -11.50
    window_x1 = WINDOW_X + WINDOW_W / 2   # +11.50

    # Compliant clip cutout dimensions:
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

    # 1. Main Lid Top Plate (local Z in [top_z0, top_z1] = [2.10, 3.00 mm]):
    # A. Entry side top frame with 0.50 mm clearance cutouts:
    out.extend(box("top_entry_pad_left", -hx, pad_cut_x0, PANE_ENTRY_Y, -36.20, top_z0, top_z1))
    out.extend(box("top_entry_pad_right", pad_cut_x1, hx, PANE_ENTRY_Y, -36.20, top_z0, top_z1))
    out.extend(box("top_entry_tongue_left", -hx, tongue_cut_x0, -36.25, -33.50, top_z0, top_z1))
    out.extend(box("top_entry_tongue_right", tongue_cut_x1, hx, -36.25, -33.50, top_z0, top_z1))
    out.extend(box("top_entry_gusset_left", -hx, pad_cut_x0, -33.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))
    out.extend(box("top_entry_gusset_right", pad_cut_x1, hx, -33.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))
    out.extend(box("top_tongue_root_band", -hx, hx, PANE_TONGUE_ROOT_Y, window_y0 + 0.05, top_z0, top_z1))

    # B. Side Rails flanking the 23.0 mm window:
    out.extend(box("top_left_rail", -hx, window_x0, window_y0 - 0.05, window_y1 + 0.05, top_z0, top_z1))
    out.extend(box("top_right_rail", window_x1, hx, window_y0 - 0.05, window_y1 + 0.05, top_z0, top_z1))

    # C. Far end solid label band:
    out.extend(box("top_far_border", -hx, hx, window_y1 - 0.05, hy_back, top_z0, top_z1))

    # 2. Glass Microscope Slide Channel (local Z in [PANE_CHANNEL_Z0, PANE_CHANNEL_Z1] = [0.70, 2.10 mm]):
    ch_x0 = WINDOW_X - PANE_CHANNEL_W / 2  # -13.50
    ch_x1 = WINDOW_X + PANE_CHANNEL_W / 2  # +13.50
    bot_x0 = WINDOW_X - 12.00              # -12.00
    bot_x1 = WINDOW_X + 12.00              # +12.00

    out.extend(box("pane_left_wall", -hx, ch_x0, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("pane_right_wall", ch_x1, hx, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("pane_left_bottom_ledge", -hx, bot_x0, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box("pane_right_bottom_ledge", bot_x1, hx, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box("pane_far_stop", ch_x0 - 0.05, ch_x1 + 0.05, PANE_FAR_STOP_Y, hy_back, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))

    # 3. Reinforced Compliant Glass Retention Clip (1.20 mm solid PETG, local Z in [LID_THICKNESS - 1.20, LID_THICKNESS]):
    out.extend(box("pane_compliant_tongue", tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_TONGUE_END_Y, LID_THICKNESS - PANE_TONGUE_H, LID_THICKNESS))
    out.extend(box("pane_latch_finger_pad", pad_x0, pad_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1 + 0.20, LID_THICKNESS - PANE_TONGUE_H, LID_THICKNESS))
    out.extend(box("pane_positive_end_shoulder", tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1, PANE_CHANNEL_Z0, LID_THICKNESS - PANE_TONGUE_H + 0.05))

    # 3D Root Gussets:
    out.extend(prism("tongue_gusset_left", [(tongue_x0 - 2.5, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x0 + 0.1, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x0 + 0.1, PANE_TONGUE_ROOT_Y - 2.0)], LID_THICKNESS - PANE_TONGUE_H, LID_THICKNESS))
    out.extend(prism("tongue_gusset_right", [(tongue_x1 - 0.1, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x1 + 2.5, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x1 - 0.1, PANE_TONGUE_ROOT_Y - 2.0)], LID_THICKNESS - PANE_TONGUE_H, LID_THICKNESS))

    # 4. Front Protruding Finger Pull Tab (Y in [-43.50, -39.50 mm]):
    tab_hx = PULL_TAB_W / 2  # 12.00 mm
    grip_profile = [
        (hy_front + 0.05, 0.00),
        (hy_pull + 1.00, 0.00),
        (hy_pull, 1.00),
        (hy_pull, LID_THICKNESS),
        (hy_front + 0.05, LID_THICKNESS),
    ]
    out.extend(prism_x("pull_tab_grip_lip", grip_profile, -tab_hx, tab_hx))

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
    """Build divider card for the 7U 1x2 Gridfinity cassette."""
    name = f"divider_card_1x2_7u_{thickness:.1f}mm"
    x_left = -18.75 + 0.80   # Symmetrical cavity
    x_right = 18.75 - 0.80
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
    parser = argparse.ArgumentParser(description="Generate 1x2 7U Gridfinity Cassette Bin models with Sliding Lid")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "build")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    body_divided = build_1x2_body_divided()
    body_undivided = build_1x2_body()
    lid_local = build_1x2_sliding_lid_local()
    lid_print = lid_print_orientation(lid_local)
    card_1_2 = build_divider_card_1x2_7u(1.20)

    # Reference assembly (lid inserted in guide slots at Z = 45.40 mm; top at Z = 48.40 mm):
    closed_lid = lid_local.translated(0.0, 0.0, SLOT_Z0 + 0.20, "closed_lid")
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
        "format": "Gridfinity 1x2 7U Cassette Bin (Direct Stacking Body with Horizontal Sliding Lid)",
        "pitch_mm": [PITCH, 2 * PITCH],
        "envelope_outside_mm": [OUTER_W, OUTER_L, TOTAL_H],
        "stacking_engaged_height_mm": ENGAGED_H,
        "total_height_with_lip_mm": TOTAL_H,
        "lid_top_height_mm": SLOT_Z0 + 0.20 + LID_THICKNESS,
        "lid_clearance_below_stacking_shelf_mm": ENGAGED_H - (SLOT_Z0 + 0.20 + LID_THICKNESS),
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
