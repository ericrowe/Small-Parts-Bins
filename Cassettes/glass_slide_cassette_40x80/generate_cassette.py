#!/usr/bin/env python3
"""Generate the production-candidate small-parts cassette release (Plan 004).

Produces:
1. cassette_body_v0_8_divided.stl (Divided body with 2 thirds divider stations)
2. cassette_body_v0_8.stl (Undivided body)
3. cassette_lid_v0_8_print.stl (Transverse end-loaded lid with compliant PETG latch)
4. divider_card_1_2mm.stl (Baseline 1.20 mm divider card)
5. divider_card_1_0mm.stl (Auxiliary 1.00 mm calibration card)
6. divider_card_1_4mm.stl (Auxiliary 1.40 mm calibration card)
"""

from __future__ import annotations

import argparse, json, math, struct, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

HERE = Path(__file__).resolve().parent
BUILD_DIR = HERE / "build"

# Geometry parameters
VERSION = "0.8-prod"
VERSION_TAG = "v0_8"

BODY_W = 38.60
BODY_D = 80.00
BODY_H = 32.80
BODY_BOTTOM = 2.00
BODY_CORNER = 2.00

# Usable internal cavity with thickened left wall (Plan 003 / Plan 004 verified)
# Left wall thickness = 4.30 mm (inner face at X = -15.00 mm)
# Right wall thickness = 2.00 mm (inner face at X = +17.30 mm)
INNER_X_LEFT = -15.00
INNER_X_RIGHT = 17.30
CAVITY_W = INNER_X_RIGHT - INNER_X_LEFT  # 32.30 mm
CAVITY_D = 76.00                         # Y in [-38.00, 38.00]
CAVITY_FLOOR_Z = BODY_BOTTOM             # 2.00 mm
CAVITY_RIM_Z = BODY_H                    # 32.80 mm

# Plan 003 / Plan 004 Divider Slot Stations
SLOT_W = 1.40
SLOT_RECESS = 0.60
FLOOR_GROOVE_D = 0.60
OV = 0.05
SLOT_STATIONS = [-12.87, 12.87]  # Two stations at thirds (creates 3 equal 24.53 mm compartments)

# Hinge parameters
HINGE_X = -18.20
HINGE_Z_LOCAL = 0.20
HINGE_BODY_BORE_R = 1.125
HINGE_LID_BORE_R = 1.05
HINGE_BODY_Y0 = -18.75
HINGE_BODY_Y1 = 18.75
HINGE_RELIEF_Y0 = -19.55
HINGE_RELIEF_Y1 = 19.55
HINGE_BODY_SUPPORT_TOP = BODY_H - 0.70
HINGE_BODY_RELIEF_TOP = BODY_H - 1.20

# Lid and glass parameters
LID_H = 3.20
POCKET_W = 27.00
POCKET_D = 76.80
POCKET_X = 0.50
WINDOW_W = 23.00
WINDOW_D = 58.50
WINDOW_X = 0.50
WINDOW_Y = -1.75

PANE_CHANNEL_W = 27.00
PANE_TOP_OPENING_W = 23.00
PANE_BOTTOM_OPENING_W = 24.00
PANE_CHANNEL_Z0 = 1.00
PANE_CHANNEL_Z1 = 2.40
PANE_BOTTOM_Z0 = 0.20
PANE_TOP_Z1 = LID_H
PANE_FAR_STOP_Y = 38.20
PANE_ENTRY_Y = -40.00
PANE_SHOULDER_Y0 = -39.80
PANE_SHOULDER_Y1 = -38.80
PANE_TONGUE_ROOT_Y = -33.05
PANE_TONGUE_END_Y = -32.00
PANE_TONGUE_W = 8.00
PANE_TONGUE_H = 0.80
PANE_FINGER_PAD_W = 10.00

LABEL_W = 34.00
LABEL_D = 10.00
LABEL_X = 0.50
LABEL_Y = 33.50

FINGER_RELIEF_W = 14.00
FINGER_RELIEF_DEPTH = 1.30
FINGER_RELIEF_H = 1.40

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

def build_body(divided: bool = True) -> Mesh:
    name = f"cassette_body_{VERSION_TAG}" + ("_divided" if divided else "")
    m = Mesh(name)
    hx, hy = BODY_W / 2, BODY_D / 2
    lx, rx = INNER_X_LEFT, INNER_X_RIGHT
    iy = CAVITY_D / 2
    c = BODY_CORNER
    h = BODY_H
    floor_z = CAVITY_FLOOR_Z
    groove_d = FLOOR_GROOVE_D if divided else 0.0
    slot_recess = SLOT_RECESS if divided else 0.0
    slot_w = SLOT_W
    relief_top = HINGE_BODY_RELIEF_TOP
    support_top = HINGE_BODY_SUPPORT_TOP
    
    # 1. Base floor slab
    outer = chamfer_rect(BODY_W, BODY_D, BODY_CORNER)
    m.add(prism_z(outer, 0.00, floor_z - groove_d + OV))
    
    # 2. Outer left wall: flush relief across entire end zones (eliminating legacy 1 mm corner posts)
    m.add(box(-hx, lx - slot_recess + OV, -hy + c - OV, hy - c + OV, floor_z - groove_d, relief_top + OV))
    # Center support for center knuckle:
    m.add(box(-hx, lx - slot_recess + OV, -19.55, 19.55, relief_top, support_top))
    
    # 3. Outer right wall
    m.add(box(rx + slot_recess - OV, hx, -hy + c - OV, hy - c + OV, floor_z - groove_d, h))
    
    # 4. Front wall (-Y)
    m.add(box(-hx + c - OV, hx - c + OV, -hy, -iy + OV, floor_z - groove_d, h))
    
    # 5. Back wall (+Y)
    m.add(box(-hx + c - OV, hx - c + OV, iy - OV, hy, floor_z - groove_d, h))
    
    # 6. Outer corner chamfers
    m.add(prism_z([(-hx + c, -hy), (-hx, -hy + c), (-hx + c - OV, -hy + c - OV)], floor_z - groove_d, h))
    m.add(prism_z([(hx - c, -hy), (hx, -hy + c), (hx - c + OV, -hy + c - OV)], floor_z - groove_d, h))
    m.add(prism_z([(-hx + c, hy), (-hx, hy - c), (-hx + c - OV, hy - c + OV)], floor_z - groove_d, h))
    m.add(prism_z([(hx - c, hy), (hx, hy - c), (hx - c + OV, hy - c + OV)], floor_z - groove_d, h))
    
    # 7. Cavity floor & walls
    if divided:
        y_points = [-iy]
        for cy in sorted(SLOT_STATIONS):
            y_points.extend([cy - slot_w / 2, cy + slot_w / 2])
        y_points.append(iy)
        
        for idx in range(0, len(y_points) - 1, 2):
            y0, y1 = y_points[idx], y_points[idx + 1]
            m.add(box(lx - OV, rx + OV, y0 - OV, y1 + OV, floor_z - groove_d, floor_z + OV))
            m.add(box(lx - slot_recess - OV, lx, y0 - OV, y1 + OV, floor_z - groove_d, relief_top + OV))
            if y0 >= -19.55 and y1 <= 19.55:
                m.add(box(lx - slot_recess - OV, lx, y0 - OV, y1 + OV, relief_top, support_top))
            m.add(box(rx, rx + slot_recess + OV, y0 - OV, y1 + OV, floor_z - groove_d, h))
    else:
        m.add(box(lx - OV, rx + OV, -iy - OV, iy + OV, floor_z, floor_z + OV))
        
    # 8. Centre hinge knuckle
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
    
    cx, cz = HINGE_X, h + HINGE_Z_LOCAL
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
    
    # 9. Outer Hinge Support Ramp (45 degree ramp from body wall to knuckle apex, eliminating droop)
    ramp_xz = [(-hx - OV, relief_top - OV), (cx - ow, cz), (-hx - OV, cz + OV)]
    m.add(prism_y(ramp_xz, HINGE_BODY_Y0 + OV, HINGE_BODY_Y1 - OV))
    
    # 10. Closure catch on inner right wall
    catch_profile = [
        (17.30, h - 2.50),
        (16.55, h - 2.08),
        (16.55, h - 1.72),
        (17.30, h - 1.22),
    ]
    m.add(prism_y(catch_profile, -4.00, 4.00))
    
    # 11. Ergonomic tactile end pinch ribs
    for z_rib in [27.5, 29.2, 30.9]:
        m.add(box(-7.0, 7.0, -hy - 0.40, -hy + OV, z_rib, z_rib + 0.90))
        m.add(box(-7.0, 7.0, hy - OV, hy + 0.40, z_rib, z_rib + 0.90))
        
    return m

def build_lid() -> Mesh:
    m = Mesh(f"cassette_lid_{VERSION_TAG}_print")
    top_z0 = PANE_CHANNEL_Z1
    top_z1 = PANE_TOP_Z1
    window_y0 = WINDOW_Y - WINDOW_D / 2
    window_y1 = WINDOW_Y + WINDOW_D / 2
    window_x0 = WINDOW_X - WINDOW_W / 2
    window_x1 = WINDOW_X + WINDOW_W / 2

    tongue_x0 = POCKET_X - PANE_TONGUE_W / 2
    tongue_x1 = POCKET_X + PANE_TONGUE_W / 2
    pad_x0 = POCKET_X - PANE_FINGER_PAD_W / 2
    pad_x1 = POCKET_X + PANE_FINGER_PAD_W / 2

    pad_gap = 0.50
    tongue_gap = 0.50
    pad_cut_x0 = pad_x0 - pad_gap
    pad_cut_x1 = pad_x1 + pad_gap
    tongue_cut_x0 = tongue_x0 - tongue_gap
    tongue_cut_x1 = tongue_x1 + tongue_gap

    # 1. Top frame around latch with 0.50 mm perimeter cutout
    m.add(box(-17.00, pad_cut_x0, -40.00, -37.20, top_z0, top_z1))
    m.add(box(pad_cut_x1, 19.30, -40.00, -37.20, top_z0, top_z1))
    m.add(box(-17.00, tongue_cut_x0, -37.25, -34.50, top_z0, top_z1))
    m.add(box(tongue_cut_x1, 19.30, -37.25, -34.50, top_z0, top_z1))
    m.add(box(-17.00, pad_cut_x0, -34.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))
    m.add(box(pad_cut_x1, 19.30, -34.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))
    m.add(box(-17.00, 19.30, PANE_TONGUE_ROOT_Y, window_y0 + 0.05, top_z0, top_z1))

    # Main window side rails
    m.add(box(-17.00, window_x0, window_y0 - 0.05, HINGE_RELIEF_Y0, top_z0, top_z1))
    m.add(box(-15.50, window_x0, HINGE_RELIEF_Y0 - 0.05, HINGE_RELIEF_Y1 + 0.05, top_z0, top_z1))
    m.add(box(-17.00, window_x0, HINGE_RELIEF_Y1, window_y1 + 0.05, top_z0, top_z1))
    m.add(box(window_x1, 19.30, window_y0 - 0.05, window_y1 + 0.05, top_z0, top_z1))

    # Solid label band
    m.add(box(-17.00, 19.30, window_y1, 38.05, top_z0, top_z1))
    m.add(box(LABEL_X - LABEL_W / 2, LABEL_X + LABEL_W / 2, 37.95, 38.55, top_z0, top_z1))
    m.add(box(-16.20, 17.30, 38.45, 40.00, top_z0, top_z1))

    channel_x0 = POCKET_X - PANE_CHANNEL_W / 2
    channel_x1 = POCKET_X + PANE_CHANNEL_W / 2
    bottom_x0 = POCKET_X - PANE_BOTTOM_OPENING_W / 2
    bottom_x1 = POCKET_X + PANE_BOTTOM_OPENING_W / 2

    # Continuous side walls and bottom ledges
    m.add(box(-15.50, channel_x0, PANE_ENTRY_Y, 38.45, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    m.add(box(channel_x1, 17.30, PANE_ENTRY_Y, 38.45, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    m.add(box(-15.50, bottom_x0, PANE_ENTRY_Y, 38.45, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    m.add(box(bottom_x1, 17.30, PANE_ENTRY_Y, 38.45, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    m.add(box(channel_x0 - 0.05, channel_x1 + 0.05, PANE_FAR_STOP_Y, 39.50, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))

    # Outer side walls of lid meeting body rim
    m.add(box(17.25, 19.30, -38.05, -6.95, 0.0, PANE_CHANNEL_Z1 + 0.05))
    m.add(box(17.25, 19.30, 6.95, 38.05, 0.0, PANE_CHANNEL_Z1 + 0.05))
    m.add(box(17.25, 18.00, -5.85, 5.85, 0.0, FINGER_RELIEF_H + 0.05))
    m.add(box(17.25, 19.30, -7.05, 7.05, FINGER_RELIEF_H, PANE_CHANNEL_Z1 + 0.05))

    # Outer wall corners
    m.add(box(-17.00, -13.00, 38.00, 40.00, 0.0, PANE_CHANNEL_Z1 + 0.05))
    m.add(box(14.00, 19.30, 38.00, 40.00, 0.0, PANE_CHANNEL_Z1 + 0.05))
    m.add(box(-17.00, -13.00, -40.00, -38.00, 0.0, PANE_CHANNEL_Z1 + 0.05))
    m.add(box(14.00, 19.30, -40.00, -38.00, 0.0, PANE_CHANNEL_Z1 + 0.05))

    # Compliant tongue, pad, shoulder, and gussets
    m.add(box(tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_TONGUE_END_Y, LID_H - PANE_TONGUE_H, LID_H))
    m.add(box(pad_x0, pad_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1 + 0.20, LID_H - PANE_TONGUE_H, LID_H))
    m.add(box(tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1, PANE_CHANNEL_Z0, LID_H - PANE_TONGUE_H + 0.05))
    m.add(prism_z([(tongue_x0 - 1.50, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x0 + 0.10, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x0 + 0.10, PANE_TONGUE_ROOT_Y - 1.50)], LID_H - PANE_TONGUE_H, LID_H))
    m.add(prism_z([(tongue_x1 - 0.10, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x1 + 1.50, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x1 - 0.10, PANE_TONGUE_ROOT_Y - 1.50)], LID_H - PANE_TONGUE_H, LID_H))

    # Lid hinge knuckles (printed top-down, local Z inverted)
    # Roots
    m.add(box(-18.40, -17.00 + 0.05, -37.40, -19.45, FINGER_RELIEF_H, LID_H))
    m.add(box(-18.40, -17.00 + 0.05, 19.45, 37.40, FINGER_RELIEF_H, LID_H))

    ow, op, st = 2.05, 2.45, 0.45
    outer_print = [(-ow, st), (-ow, 0.0)]
    outer_print.extend((-ow * (1.0 - step / 9.0), -op * step / 9.0) for step in range(1, 10))
    outer_print.extend((ow * step / 9.0, -op * (1.0 - step / 9.0)) for step in range(1, 10))
    outer_print.extend([(ow, st), (0.0, op)])

    bore_r = HINGE_LID_BORE_R
    bore_print = [
        (bore_r * math.cos(math.radians(135.0 + 13.5 * i)),
         bore_r * math.sin(math.radians(135.0 + 13.5 * i)))
        for i in range(21)
    ]
    bore_print.append((0.0, math.sqrt(2.0) * bore_r))

    cx, cz = HINGE_X, 0.20
    outer_xz = [(cx + x, cz - z) for x, z in outer_print] # inverted for top-down print
    inner_xz = [(cx + x, cz - z) for x, z in bore_print]

    for y0, y1 in [(-37.30, -19.55), (19.55, 37.30)]:
        kn = Mesh()
        outer0 = [(x, y0, z) for x, z in outer_xz]
        outer1 = [(x, y1, z) for x, z in outer_xz]
        inner0 = [(x, y0, z) for x, z in inner_xz]
        inner1 = [(x, y1, z) for x, z in inner_xz]
        for i in range(len(outer0)):
            j = (i + 1) % len(outer0)
            kn.quad(outer0[i], outer1[i], outer1[j], outer0[j])
            kn.quad(inner0[i], inner0[j], inner1[j], inner1[i])
            kn.quad(outer0[i], outer0[j], inner0[j], inner0[i])
            kn.quad(outer1[i], inner1[i], inner1[j], outer1[j])
        m.add(kn)

    # Reinforced cantilever closure clasp on lid
    clasp_profile = [
        (17.30, 0.00),
        (18.50, 0.00),
        (18.50, -1.80),
        (17.95, -2.40),
        (17.30, -2.40),
        (17.30, -2.15),
        (17.95, -2.15),
        (17.95, -0.60),
        (17.30, -0.60),
    ]
    m.add(prism_y(clasp_profile, -3.50, 3.50))
    
    # Tactile end pinch ribs on lid
    for z_rib in [0.8, 1.8, 2.6]:
        m.add(box(-7.0, 7.0, -40.40, -40.00 + OV, z_rib, z_rib + 0.70))
        m.add(box(-7.0, 7.0, 40.00 - OV, 40.40, z_rib, z_rib + 0.70))

    return m

def build_divider_card(thickness: float = 1.20,
                       notch_w: float = 10.0, notch_d: float = 1.5,
                       bottom_chamfer: float = 0.6) -> Mesh:
    m = Mesh(f"divider_card_{thickness:.1f}mm")
    x_left = INNER_X_LEFT - 0.50   # -15.50 mm
    x_right = INNER_X_RIGHT + 0.50 # +17.80 mm
    z_top = 31.20
    ht = thickness / 2.0
    
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
        header = f"Plan 004 {m.name}".encode('ascii')[:80].ljust(80, b'\0')
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
    body_div = build_body(divided=True)
    write_stl(BUILD_DIR / "cassette_body_v0_8_divided.stl", body_div)
    audit_body_div = audit(body_div)
    print("Divided Body Audit:", audit_body_div)
    
    # 2. Build undivided body
    body_undiv = build_body(divided=False)
    write_stl(BUILD_DIR / "cassette_body_v0_8.stl", body_undiv)
    audit_body_undiv = audit(body_undiv)
    print("Undivided Body Audit:", audit_body_undiv)
    
    # 3. Build lid
    lid_mesh = build_lid()
    write_stl(BUILD_DIR / "cassette_lid_v0_8_print.stl", lid_mesh)
    audit_lid = audit(lid_mesh)
    print("Lid Audit:", audit_lid)
    
    # 4. Build divider cards
    card_1_2 = build_divider_card(1.20)
    write_stl(BUILD_DIR / "divider_card_1_2mm.stl", card_1_2)
    audit_1_2 = audit(card_1_2)
    print("Divider Card 1.2mm Audit:", audit_1_2)
    
    card_1_0 = build_divider_card(1.00)
    write_stl(BUILD_DIR / "divider_card_1_0mm.stl", card_1_0)
    
    card_1_4 = build_divider_card(1.40)
    write_stl(BUILD_DIR / "divider_card_1_4mm.stl", card_1_4)
    
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
            "cassette_body_v0_8_divided.stl": audit_body_div,
            "cassette_body_v0_8.stl": audit_body_undiv,
            "cassette_lid_v0_8_print.stl": audit_lid,
            "divider_card_1_2mm.stl": audit_1_2
        }
    }
    
    with (BUILD_DIR / "manifest.json").open("w") as f:
        json.dump(manifest, f, indent=2)
    print("Production candidate cassette files and manifest generated.")

if __name__ == "__main__":
    main()
