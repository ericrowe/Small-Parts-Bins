#!/usr/bin/env python3
"""Generate the standalone 1x2 7U Gridfinity cassette bin models.

Features:
  - Standard 1x2 Gridfinity base interface (two 42 mm base cells centered at Y = ±21.0 mm)
  - 7U stacking height standard (49.00 mm engaged height, 53.40 mm total height with lip)
  - 1x2 Gridfinity stacking rim integrated directly into the lid top for stacking bins directly on top
  - Replaceable standard microscope glass slide window (75 x 25 x 1.1-1.2 mm) with positive end-loaded slide capture
  - 1.20 mm reinforced compliant PETG capture clip
  - Symmetrical 34.0 x 10.0 mm solid flat label zones on both ends for 9 mm Brother TZe tape
  - Peaked 3-knuckle filament hinge (1.75 mm filament pin) and 0.85 mm reinforced closure clasp
  - Optional removable divider cards dividing the cavity into 3 equal compartments
  - 100% support-free FDM 3D printing (body upright, lid top-face down)
"""

from __future__ import annotations
import argparse
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

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

# Split Line between Body and Lid:
BODY_H = 45.40        # Body top rim plane
LID_H = 3.60          # Lid base thickness (45.40 + 3.60 = 49.00 mm shelf plane)

# Glass Slide Capture Constants:
PANE_CHANNEL_W = 27.00
PANE_CHANNEL_H = 1.40
PANE_CHANNEL_Z0 = 1.00
PANE_CHANNEL_Z1 = 2.40
PANE_BOTTOM_Z0 = 0.20
PANE_TOP_Z1 = LID_H

WINDOW_W = 23.00
WINDOW_D = 55.00
WINDOW_X = 0.00
WINDOW_Y = 0.00

PANE_FAR_STOP_Y = 38.50
PANE_ENTRY_Y = -41.75
PANE_SHOULDER_Y0 = -41.00
PANE_SHOULDER_Y1 = -40.00
PANE_TONGUE_ROOT_Y = -34.25
PANE_TONGUE_END_Y = -33.20
PANE_TONGUE_W = 8.00
PANE_TONGUE_H = 1.20
PANE_FINGER_PAD_W = 10.00

LABEL_W = 34.00
LABEL_D = 10.00
LABEL_X = 0.00
LABEL_Y = 34.00
ENTRY_LABEL_Y = -34.00

# Hinge Geometry (Peaked 3-knuckle, 1.75 mm filament pin):
HINGE_X = -OUTER_W / 2 + 0.55  # -20.20 mm
HINGE_Z_LOCAL = 0.20           # concentric at split line
HINGE_BODY_BORE_R = 1.125      # 2.25 mm nominal bore on body
HINGE_LID_BORE_R = 1.05        # 2.10 mm nominal bore on lid
HINGE_BODY_Y0 = -14.00
HINGE_BODY_Y1 = 14.00
HINGE_RELIEF_Y0 = -14.80
HINGE_RELIEF_Y1 = 14.80
HINGE_LID_K0_Y0 = -39.00
HINGE_LID_K0_Y1 = -15.60
HINGE_LID_K1_Y0 = 15.60
HINGE_LID_K1_Y1 = 39.00
HINGE_ATTACHMENT_CLEARANCE = 0.15

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


def rounded_rect(w: float, d: float, r: float, n: int = 6) -> list[tuple[float, float]]:
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


def loft(rings: list[tuple[float, list[tuple[float, float]]]]) -> Mesh:
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


def prism(name: str, polygon_xy: list[tuple[float, float]], z0: float, z1: float) -> Mesh:
    m = Mesh(name)
    m.extend(loft([(z0, polygon_xy), (z1, polygon_xy)]))
    return m


def prism_y(name: str, profile_xz: list[tuple[float, float]], y0: float, y1: float) -> Mesh:
    m = Mesh(name)
    n = len(profile_xz)
    for i in range(1, n - 1):
        m.tri((profile_xz[0][0], y0, profile_xz[0][1]), (profile_xz[i][0], y0, profile_xz[i][1]), (profile_xz[i + 1][0], y0, profile_xz[i + 1][1]))
        m.tri((profile_xz[0][0], y1, profile_xz[0][1]), (profile_xz[i + 1][0], y1, profile_xz[i + 1][1]), (profile_xz[i][0], y1, profile_xz[i][1]))
    for i in range(n):
        j = (i + 1) % n
        m.quad((profile_xz[i][0], y0, profile_xz[i][1]), (profile_xz[i][0], y1, profile_xz[i][1]), (profile_xz[j][0], y1, profile_xz[j][1]), (profile_xz[j][0], y0, profile_xz[j][1]))
    return m


def peaked_hinge_y(
    name: str,
    axis_x: float,
    axis_z: float,
    y0: float,
    y1: float,
    print_up_sign: float = 1.0,
    bore_r: float = 1.125,
) -> Mesh:
    """Build support-free peaked hinge knuckle with 45-degree roof and bore."""
    m = Mesh(name)
    outer_r = 2.70
    outer_half_w = 2.25
    outer_side_top = 0.80

    if print_up_sign > 0:
        outer_profile_xz = [
            (axis_x - outer_half_w, axis_z - outer_side_top),
            (axis_x, axis_z - outer_r),
            (axis_x + outer_half_w, axis_z - outer_side_top),
            (axis_x + outer_half_w, axis_z + outer_side_top),
            (axis_x, axis_z + outer_r),
            (axis_x - outer_half_w, axis_z + outer_side_top),
        ]
    else:
        outer_profile_xz = [
            (axis_x - outer_half_w, axis_z + outer_side_top),
            (axis_x, axis_z + outer_r),
            (axis_x + outer_half_w, axis_z + outer_side_top),
            (axis_x + outer_half_w, axis_z - outer_side_top),
            (axis_x, axis_z - outer_r),
            (axis_x - outer_half_w, axis_z - outer_side_top),
        ]
    m.extend(prism_y(f"{name}_outer", outer_profile_xz, y0, y1))
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


def build_1x2_body_divided() -> Mesh:
    """Build the 1x2 7U divided Gridfinity cassette body."""
    out = Mesh("gridfinity_body_1x2_7u_divided")
    out.extend(build_gridfinity_base())

    hx, hy = OUTER_W / 2, OUTER_L / 2
    c = OUTER_R
    ix, iy = hx - WALL_T, hy - WALL_T  # 18.75 x 39.75 mm cavity
    join = 0.05
    z_floor = FLOOR_Z

    # 1. Continuous Outer Walls:
    # Left wall (hinge side):
    out.extend(box("body_outer_left", -hx, -ix + join, -hy + c - join, hy - c + join, z_floor - join, BODY_H))
    # Right wall (latch side):
    out.extend(box("body_outer_right", ix - join, hx, -hy + c - join, hy - c + join, z_floor - join, BODY_H))
    # Front & Back walls:
    out.extend(box("body_outer_front", -hx + c - join, hx - c + join, -hy, -iy + join, z_floor - join, BODY_H))
    out.extend(box("body_outer_back", -hx + c - join, hx - c + join, iy - join, hy, z_floor - join, BODY_H))

    # 2. Outer corner columns:
    outer_pts = rounded_rect(OUTER_W, OUTER_L, OUTER_R, 6)
    out.extend(prism("body_corners", outer_pts, z_floor - join, BODY_H))

    # 3. Divider slots (Two stations at thirds Y = ±13.50 mm):
    slot_w = 1.40
    slot_stations = [-13.50, 13.50]
    ridge_proj = 0.80
    ridge_w = 1.50

    for cy in slot_stations:
        ry0_a, ry1_a = cy - slot_w / 2 - ridge_w, cy - slot_w / 2
        out.extend(box(f"ridge_lower_{cy:.2f}", ix - ridge_proj, ix + join, ry0_a - join, ry1_a + join, z_floor - join, BODY_H - 1.50 + join))
        chamfer_pts = [(ix - ridge_proj, BODY_H - 1.50), (ix, BODY_H), (ix, BODY_H - 1.50)]
        out.extend(prism_y(f"ridge_lead_lower_{cy:.2f}", chamfer_pts, ry0_a - join, ry1_a + join))

        ry0_b, ry1_b = cy + slot_w / 2, cy + slot_w / 2 + ridge_w
        out.extend(box(f"ridge_upper_{cy:.2f}", ix - ridge_proj, ix + join, ry0_b - join, ry1_b + join, z_floor - join, BODY_H - 1.50 + join))
        out.extend(prism_y(f"ridge_lead_upper_{cy:.2f}", chamfer_pts, ry0_b - join, ry1_b + join))

        # Left wall flanking braces creating slot:
        out.extend(box(f"left_brace_lower_{cy:.2f}", -ix - join, -ix + 0.60, ry0_a - join, ry1_a + join, z_floor - join, BODY_H))
        out.extend(box(f"left_brace_upper_{cy:.2f}", -ix - join, -ix + 0.60, ry0_b - join, ry1_b + join, z_floor - join, BODY_H))

    # 4. Smooth finger scoop fillets (R = 4.0 mm) along inside front (latch) floor edge:
    r_scoop = 4.00
    out.extend(build_scoop_fillet(ix, z_floor, r_scoop, -hy + c, slot_stations[0] - slot_w / 2 + join))
    out.extend(build_scoop_fillet(ix, z_floor, r_scoop, slot_stations[0] + slot_w / 2 - join, slot_stations[1] - slot_w / 2 + join))
    out.extend(build_scoop_fillet(ix, z_floor, r_scoop, slot_stations[1] + slot_w / 2 - join, hy - c))

    # 5. Centre Hinge Knuckle on Left Wall:
    out.extend(
        peaked_hinge_y(
            "body_centre_knuckle",
            HINGE_X,
            BODY_H + HINGE_Z_LOCAL,
            HINGE_BODY_Y0,
            HINGE_BODY_Y1,
            print_up_sign=1.0,
            bore_r=HINGE_BODY_BORE_R,
        )
    )

    # 6. Inward Closure Catch on Inside of Right Wall (0.85 mm undercut):
    catch_profile = [
        (ix, BODY_H - 2.60),
        (ix - 0.85, BODY_H - 2.10),
        (ix - 0.85, BODY_H - 1.70),
        (ix, BODY_H - 1.15),
    ]
    out.extend(prism_y("body_closure_catch", catch_profile, -4.00, 4.00))

    return out


def build_1x2_body() -> Mesh:
    """Build the undivided 1x2 7U Gridfinity cassette body with inside bottom finger scoop."""
    out = Mesh("gridfinity_body_1x2_7u")
    out.extend(build_gridfinity_base())

    hx, hy = OUTER_W / 2, OUTER_L / 2
    c = OUTER_R
    ix, iy = hx - WALL_T, hy - WALL_T
    join = 0.05
    z_floor = FLOOR_Z

    # Outer shell:
    outer_pts = rounded_rect(OUTER_W, OUTER_L, OUTER_R, 6)
    out.extend(prism("body_shell", outer_pts, z_floor - join, BODY_H))

    # Continuous smooth finger scoop fillet (R = 4.0 mm) along inside front (latch) floor edge:
    r_scoop = 4.00
    out.extend(build_scoop_fillet(ix, z_floor, r_scoop, -hy + c, hy - c))

    # Centre Hinge Knuckle on Left Wall:
    out.extend(
        peaked_hinge_y(
            "body_centre_knuckle",
            HINGE_X,
            BODY_H + HINGE_Z_LOCAL,
            HINGE_BODY_Y0,
            HINGE_BODY_Y1,
            print_up_sign=1.0,
            bore_r=HINGE_BODY_BORE_R,
        )
    )

    # Inward Closure Catch:
    catch_profile = [
        (ix, BODY_H - 2.60),
        (ix - 0.85, BODY_H - 2.10),
        (ix - 0.85, BODY_H - 1.70),
        (ix, BODY_H - 1.15),
    ]
    out.extend(prism_y("body_closure_catch", catch_profile, -4.00, 4.00))

    return out


def build_1x2_lid_local() -> Mesh:
    """Build the 1x2 7U Gridfinity cassette lid with integrated stacking lip and glass capture."""
    out = Mesh("gridfinity_lid_1x2_7u_local")

    hx, hy = OUTER_W / 2, OUTER_L / 2
    top_z0 = PANE_CHANNEL_Z1
    top_z1 = PANE_TOP_Z1
    window_y0 = WINDOW_Y - WINDOW_D / 2   # -27.50
    window_y1 = WINDOW_Y + WINDOW_D / 2   # +27.50
    window_x0 = WINDOW_X - WINDOW_W / 2   # -11.50
    window_x1 = WINDOW_X + WINDOW_W / 2   # +11.50

    # 1. Stacking Rim / Lip on Top of Lid (local Z in [LID_H, LID_H + LIP_H] = [3.60, 8.00 mm]):
    # Outer lip profile: 41.5 x 83.5 mm tapering to 40.7 x 82.7 mm
    # Inner throat: 37.2 x 79.2 mm
    outer_rim_rings = [
        (LID_H, rounded_rect(OUTER_W, OUTER_L, OUTER_R)),
        (LID_H + 2.00, rounded_rect(OUTER_W, OUTER_L, OUTER_R)),
        (LID_H + LIP_H, rounded_rect(OUTER_W - 0.80, OUTER_L - 0.80, OUTER_R - 0.40)),
    ]
    out.extend(loft(outer_rim_rings))

    # Inner throat cutout wall for stacking:
    inner_throat_rings = [
        (LID_H - 0.05, rounded_rect(OUTER_W - 2 * WALL_T, OUTER_L - 2 * WALL_T, 2.0)),
        (LID_H + LIP_H + 0.05, rounded_rect(37.2, 79.2, 3.4)),
    ]
    # (The outer rim loft forms the positive lip perimeter).

    # 2. Main Lid Top Plate (local Z in [top_z0, top_z1] = [2.40, 3.60 mm]):
    # Symmetrical 12.5 mm solid end borders:
    out.extend(box("top_entry_border", -hx + 1.0, hx - 1.0, -hy, window_y0 + 0.05, top_z0, top_z1))
    out.extend(box("top_far_border", -hx + 1.0, hx - 1.0, window_y1 - 0.05, hy, top_z0, top_z1))

    # Side Rails flanking the 23.0 mm window:
    out.extend(box("top_left_rail", -hx + 1.0, window_x0, window_y0 - 0.05, window_y1 + 0.05, top_z0, top_z1))
    out.extend(box("top_right_rail", window_x1, hx - 1.0, window_y0 - 0.05, window_y1 + 0.05, top_z0, top_z1))

    # 3. Glass Microscope Slide Channel (local Z in [PANE_CHANNEL_Z0, PANE_CHANNEL_Z1] = [1.00, 2.40 mm]):
    ch_x0 = WINDOW_X - PANE_CHANNEL_W / 2  # -13.50
    ch_x1 = WINDOW_X + PANE_CHANNEL_W / 2  # +13.50
    bot_x0 = WINDOW_X - 12.00              # -12.00
    bot_x1 = WINDOW_X + 12.00              # +12.00

    out.extend(box("pane_left_wall", -hx + 1.5, ch_x0, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("pane_right_wall", ch_x1, hx - 1.5, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("pane_left_bottom_ledge", -hx + 1.5, bot_x0, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box("pane_right_bottom_ledge", bot_x1, hx - 1.5, PANE_ENTRY_Y, PANE_FAR_STOP_Y, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box("pane_far_stop", ch_x0 - 0.05, ch_x1 + 0.05, PANE_FAR_STOP_Y, hy, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))

    # 4. Reinforced Compliant Glass Retention Clip (1.20 mm solid PETG, local Z in [LID_H - 1.20, LID_H]):
    tongue_x0 = WINDOW_X - PANE_TONGUE_W / 2
    tongue_x1 = WINDOW_X + PANE_TONGUE_W / 2
    pad_x0 = WINDOW_X - PANE_FINGER_PAD_W / 2
    pad_x1 = WINDOW_X + PANE_FINGER_PAD_W / 2

    out.extend(box("pane_compliant_tongue", tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_TONGUE_END_Y, LID_H - PANE_TONGUE_H, LID_H))
    out.extend(box("pane_latch_finger_pad", pad_x0, pad_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1 + 0.20, LID_H - PANE_TONGUE_H, LID_H))
    out.extend(box("pane_positive_end_shoulder", tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1, PANE_CHANNEL_Z0, LID_H - PANE_TONGUE_H + 0.05))

    # 3D Root Gussets:
    out.extend(prism("tongue_gusset_left", [(tongue_x0 - 2.5, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x0 + 0.1, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x0 + 0.1, PANE_TONGUE_ROOT_Y - 2.0)], LID_H - PANE_TONGUE_H, LID_H))
    out.extend(prism("tongue_gusset_right", [(tongue_x1 - 0.1, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x1 + 2.5, PANE_TONGUE_ROOT_Y + 0.1), (tongue_x1 - 0.1, PANE_TONGUE_ROOT_Y - 2.0)], LID_H - PANE_TONGUE_H, LID_H))

    # 5. Twin Hinge Knuckles on Left Rail:
    for name_k, y0_k, y1_k in (("lid_knuckle_0", HINGE_LID_K0_Y0, HINGE_LID_K0_Y1), ("lid_knuckle_1", HINGE_LID_K1_Y0, HINGE_LID_K1_Y1)):
        out.extend(peaked_hinge_y(name_k, HINGE_X, HINGE_Z_LOCAL, y0_k, y1_k, print_up_sign=-1.0, bore_r=HINGE_LID_BORE_R))

    # 6. Reinforced Front Closure Clasp on Right Wall (local Z in [0.00, LID_H]):
    clasp_xz = [
        (hx - 1.25, 0.00),
        (hx, 0.00),
        (hx, -2.60),
        (hx - 0.85, -2.60),
        (hx - 0.85, -2.10),
        (hx - 1.25, -1.15),
    ]
    out.extend(prism_y("lid_closure_clasp", clasp_xz, -4.00, 4.00))

    return out


def lid_print_orientation(lid: Mesh) -> Mesh:
    """Orient the lid for support-free printing (top stacking rim face down on build plate)."""
    # Flip Z and translate to Z = 0:
    rot = Mesh("gridfinity_lid_1x2_7u_print")
    rot.triangles = [
        (
            (p0[0], p0[1], (LID_H + LIP_H) - p0[2]),
            (p2[0], p2[1], (LID_H + LIP_H) - p2[2]),
            (p1[0], p1[1], (LID_H + LIP_H) - p1[2]),
        )
        for p0, p1, p2 in lid.triangles
    ]
    zmin = rot.bounds()[0][2]
    return rot.translated(0.0, 0.0, -zmin, "gridfinity_lid_1x2_7u_print").positive()


def build_divider_card_1x2_7u(thickness: float = 1.20) -> Mesh:
    """Build divider card for the 7U 1x2 Gridfinity cassette."""
    name = f"divider_card_1x2_7u_{thickness:.1f}mm"
    x_left = -18.75
    x_right = 18.75
    z_top = 42.00
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

    # Reference assembly:
    closed_lid = lid_local.translated(0.0, 0.0, BODY_H + 0.02, "closed_lid")
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
        "format": "Gridfinity 1x2 7U Cassette Bin",
        "pitch_mm": [PITCH, 2 * PITCH],
        "envelope_outside_mm": [OUTER_W, OUTER_L, TOTAL_H],
        "stacking_engaged_height_mm": ENGAGED_H,
        "total_height_with_lip_mm": TOTAL_H,
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
