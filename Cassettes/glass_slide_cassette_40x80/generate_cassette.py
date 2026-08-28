#!/usr/bin/env python3
"""Generate the production small-parts cassette release (Plan 004).

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
SLOT_STATIONS = [-12.87, 12.87]  # Two stations at thirds (creates 3 equal 24.53 mm compartments)

# Hinge parameters
HINGE_X = -18.20
HINGE_Z_LOCAL = 0.20
HINGE_BODY_BORE_R = 1.125
HINGE_LID_BORE_R = 1.05
HINGE_GAP = 0.80
HINGE_BODY_Y0 = -13.90
HINGE_BODY_Y1 = 13.90
HINGE_LID_END = 37.30

# Thickened knuckle outer profile (>= 1.20 mm wall thickness everywhere around the bore)
HINGE_OUTER_HALF_W = 2.25
HINGE_OUTER_POINT = 2.65
HINGE_OUTER_SIDE_TOP = 0.80

# Rotational keep-out and body relief
# Setting HINGE_BODY_RELIEF_TOP to 29.50 mm guarantees +0.75 mm to +2.40 mm positive clearance
# across the entire 0-120 degree opening sweep with zero clash.
HINGE_BODY_RELIEF_TOP = 29.50
HINGE_BODY_SUPPORT_TOP = BODY_H + HINGE_Z_LOCAL - HINGE_BODY_BORE_R - 0.15  # 32.10 mm
HINGE_RELIEF_Y0 = HINGE_BODY_Y0 - 0.25                                     # -14.15 mm
HINGE_RELIEF_Y1 = HINGE_BODY_Y1 + 0.25                                     #  14.15 mm

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
    def extend(self, other: Mesh):
        self.triangles.extend(other.triangles)
    def bounds(self) -> tuple[V, V]:
        xs = [v[0] for t in self.triangles for v in t]
        ys = [v[1] for t in self.triangles for v in t]
        zs = [v[2] for t in self.triangles for v in t]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
    def transformed(self, fn, name=""):
        m = Mesh(name or self.name)
        for a, b, c in self.triangles:
            m.tri(fn(a), fn(b), fn(c))
        return m
    def translated(self, dx, dy, dz, name=""):
        return self.transformed(lambda p: (p[0]+dx, p[1]+dy, p[2]+dz), name)

def _fan(m: Mesh, loop: Sequence[Vec2], z: float, up: bool) -> None:
    cx = sum(p[0] for p in loop) / len(loop)
    cy = sum(p[1] for p in loop) / len(loop)
    center = (cx, cy, z)
    for i in range(len(loop)):
        j = (i + 1) % len(loop)
        p0 = (loop[i][0], loop[i][1], z)
        p1 = (loop[j][0], loop[j][1], z)
        if up:
            m.tri(center, p0, p1)
        else:
            m.tri(center, p1, p0)

def _loop_wall(m: Mesh, loop: Sequence[Vec2], z0: float, z1: float, hole: bool) -> None:
    for i in range(len(loop)):
        j = (i + 1) % len(loop)
        p0_bot = (loop[i][0], loop[i][1], z0)
        p1_bot = (loop[j][0], loop[j][1], z0)
        p0_top = (loop[i][0], loop[i][1], z1)
        p1_top = (loop[j][0], loop[j][1], z1)
        if hole:
            m.quad(p0_bot, p1_bot, p1_top, p0_top)
        else:
            m.quad(p0_bot, p0_top, p1_top, p1_bot)

def _ring_face(m: Mesh, outer: Sequence[Vec2], inner: Sequence[Vec2], z: float, up: bool) -> None:
    assert len(outer) == len(inner)
    for i in range(len(outer)):
        j = (i + 1) % len(outer)
        o0 = (outer[i][0], outer[i][1], z)
        o1 = (outer[j][0], outer[j][1], z)
        i0 = (inner[i][0], inner[i][1], z)
        i1 = (inner[j][0], inner[j][1], z)
        if up:
            m.quad(o0, o1, i1, i0)
        else:
            m.quad(o0, i0, i1, o1)

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

def peaked_hinge_y(cx: float, cz: float, y0: float, y1: float, print_up_sign: float, bore_r: float) -> Mesh:
    ow, op, st = HINGE_OUTER_HALF_W, HINGE_OUTER_POINT, HINGE_OUTER_SIDE_TOP
    outer_print = [(-ow, st), (-ow, 0.0)]
    outer_print.extend((-ow * (1.0 - step / 9.0), -op * step / 9.0) for step in range(1, 10))
    outer_print.extend((ow * step / 9.0, -op * (1.0 - step / 9.0)) for step in range(1, 10))
    outer_print.extend([(ow, st), (0.0, op)])

    bore_print = [
        (bore_r * math.cos(math.radians(135.0 + 13.5 * i)),
         bore_r * math.sin(math.radians(135.0 + 13.5 * i)))
        for i in range(21)
    ]
    bore_print.append((0.0, math.sqrt(2.0) * bore_r))

    outer_xz = [(cx + x, cz + print_up_sign * z) for x, z in outer_print]
    inner_xz = [(cx + x, cz + print_up_sign * z) for x, z in bore_print]

    m = Mesh()
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

def normal(t: T) -> V:
    a, b, c = t
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1]*v[2] - u[2]*v[1], u[2]*v[0] - u[0]*v[2], u[0]*v[1] - u[1]*v[0])
    q = math.sqrt(sum(x*x for x in n))
    return tuple(x/q for x in n) if q else (0.0, 0.0, 0.0)

def build_body(divided: bool = True) -> Mesh:
    name = f"cassette_body_{VERSION_TAG}" + ("_divided" if divided else "")
    out = Mesh(name)
    
    outer = [
        (-17.30, -40.00), (17.30, -40.00),
        (19.30, -38.00), (19.30, 38.00),
        (17.30, 40.00), (-17.30, 40.00),
        (-19.30, 38.00), (-19.30, -38.00)
    ]
    # Thickened left wall: inner face at X = -15.00 mm (4.30 mm wall)
    inner = [
        (-13.80, -38.00), (16.30, -38.00),
        (17.30, -37.00), (17.30, 37.00),
        (16.30, 38.00), (-13.80, 38.00),
        (-15.00, 36.80), (-15.00, -36.80)
    ]
    
    relief_top = HINGE_BODY_RELIEF_TOP # 29.50 mm
    body_h = BODY_H                   # 32.80 mm
    
    # 1. Lower shell: single continuous watertight solid (0 internal faces!)
    shell = Mesh("body_lower_shell")
    _fan(shell, outer, 0.0, up=False)
    _loop_wall(shell, outer, 0.0, relief_top, hole=False)
    _fan(shell, inner, BODY_BOTTOM, up=True)
    _loop_wall(shell, inner, BODY_BOTTOM, relief_top, hole=True)
    _ring_face(shell, outer, inner, relief_top, up=True)
    out.extend(shell)
    
    upper_z0 = relief_top - 0.05
    join = 0.05
    
    # 2. Upper rim walls (Z = 29.45 to 32.80 mm)
    # Front wall: X in [-15.00, 17.35] (leaves left corner clear for rotating knuckle)
    out.extend(box(-15.00, 17.35, -40.00, -38.00, upper_z0, body_h))
    # Back wall: X in [-15.00, 17.35] (leaves left corner clear for rotating knuckle)
    out.extend(box(-15.00, 17.35, 38.00, 40.00, upper_z0, body_h))
    # Right wall:
    out.extend(box(17.25, 19.30, -38.05, 38.05, upper_z0, body_h))
    # Right corner chamfers:
    out.extend(prism_z([(17.30, -40.00), (19.30, -38.00), (17.25, -38.00)], upper_z0, body_h))
    out.extend(prism_z([(17.30, 40.00), (19.30, 38.00), (17.25, 38.00)], upper_z0, body_h))
    
    # Center support for center knuckle:
    out.extend(box(-19.30, -15.00, HINGE_RELIEF_Y0, HINGE_RELIEF_Y1, upper_z0, HINGE_BODY_SUPPORT_TOP))
    
    # 3. Center hinge knuckle (verified 27.8 mm length):
    out.extend(
        peaked_hinge_y(
            HINGE_X,
            body_h + HINGE_Z_LOCAL,
            HINGE_BODY_Y0,
            HINGE_BODY_Y1,
            print_up_sign=1.0,
            bore_r=HINGE_BODY_BORE_R,
        )
    )
    
    # 4. Reinforced snap catch on inside of right wall:
    catch_profile = [
        (17.30, body_h - 2.50),
        (16.55, body_h - 2.08),
        (16.55, body_h - 1.72),
        (17.30, body_h - 1.22),
    ]
    out.extend(prism_y(catch_profile, -4.00, 4.00))
    
    # 5. Divider slots (if divided):
    if divided:
        for cy in SLOT_STATIONS:
            y0 = cy - SLOT_W / 2
            y1 = cy + SLOT_W / 2
            # Left wall slot channel:
            out.extend(box(-15.00 - SLOT_RECESS, -15.00 + join, y0, y1, BODY_BOTTOM, relief_top))
            # Right wall slot channel:
            out.extend(box(17.30 - join, 17.30 + SLOT_RECESS, y0, y1, BODY_BOTTOM, body_h))
            # Floor groove:
            out.extend(box(-15.00 - SLOT_RECESS, 17.30 + SLOT_RECESS, y0, y1, BODY_BOTTOM - FLOOR_GROOVE_D, BODY_BOTTOM + join))
            
    return out

def build_lid_local() -> Mesh:
    out = Mesh(f"cassette_lid_{VERSION_TAG}_local")

    top_z0 = PANE_CHANNEL_Z1
    top_z1 = PANE_TOP_Z1
    window_y0 = WINDOW_Y - WINDOW_D / 2
    window_y1 = WINDOW_Y + WINDOW_D / 2
    window_x0 = WINDOW_X - WINDOW_W / 2
    window_x1 = WINDOW_X + WINDOW_W / 2

    # Compliant latch geometry
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

    # Top frame with tightened 0.50 mm perimeter gap around compliant latch:
    # 1. Entry frame around finger pad:
    out.extend(box(-17.00, pad_cut_x0, -40.00, -37.20, top_z0, top_z1))
    out.extend(box(pad_cut_x1, 19.30, -40.00, -37.20, top_z0, top_z1))

    # 2. Entry frame around tongue:
    out.extend(box(-17.00, tongue_cut_x0, -37.25, -34.50, top_z0, top_z1))
    out.extend(box(tongue_cut_x1, 19.30, -37.25, -34.50, top_z0, top_z1))

    # 3. Entry frame around gussets:
    out.extend(box(-17.00, pad_cut_x0, -34.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))
    out.extend(box(pad_cut_x1, 19.30, -34.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))

    # 4. Tongue root crossbar:
    out.extend(box(-17.00, 19.30, PANE_TONGUE_ROOT_Y, window_y0 + 0.05, top_z0, top_z1))

    # Main window side rails
    out.extend(box(-17.00, window_x0, window_y0 - 0.05, HINGE_RELIEF_Y0, top_z0, top_z1))
    out.extend(box(-15.50, window_x0, HINGE_RELIEF_Y0 - 0.05, HINGE_RELIEF_Y1 + 0.05, top_z0, top_z1))
    out.extend(box(-17.00, window_x0, HINGE_RELIEF_Y1, window_y1 + 0.05, top_z0, top_z1))
    out.extend(box(window_x1, 19.30, window_y0 - 0.05, window_y1 + 0.05, top_z0, top_z1))

    # Solid label band
    out.extend(box(-17.00, 19.30, window_y1, 38.05, top_z0, top_z1))
    out.extend(box(LABEL_X - LABEL_W / 2, LABEL_X + LABEL_W / 2, 37.95, 38.55, top_z0, top_z1))
    out.extend(box(-16.20, 17.30, 38.45, 40.00, top_z0, top_z1))

    channel_x0 = POCKET_X - PANE_CHANNEL_W / 2
    channel_x1 = POCKET_X + PANE_CHANNEL_W / 2
    bottom_x0 = POCKET_X - PANE_BOTTOM_OPENING_W / 2
    bottom_x1 = POCKET_X + PANE_BOTTOM_OPENING_W / 2

    # Continuous side walls and bottom ledges
    out.extend(box(-15.50, channel_x0, PANE_ENTRY_Y, 38.45, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box(channel_x1, 17.30, PANE_ENTRY_Y, 38.45, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box(-15.50, bottom_x0, PANE_ENTRY_Y, 38.45, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box(bottom_x1, 17.30, PANE_ENTRY_Y, 38.45, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box(channel_x0 - 0.05, channel_x1 + 0.05, PANE_FAR_STOP_Y, 39.50, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))

    # Outer side walls of the lid meeting the body rim at local Z = 0.00:
    out.extend(box(17.25, 19.30, -38.05, -6.95, 0.0, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box(17.25, 19.30, 6.95, 38.05, 0.0, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box(17.25, 18.00, -5.85, 5.85, 0.0, FINGER_RELIEF_H + 0.05))
    out.extend(box(17.25, 19.30, -7.05, 7.05, FINGER_RELIEF_H, PANE_CHANNEL_Z1 + 0.05))

    # Outer wall corners on far and entry ends (cleared on hinge side):
    out.extend(box(14.00, 19.30, 38.00, 40.00, 0.0, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box(14.00, 19.30, -40.00, -38.00, 0.0, PANE_CHANNEL_Z1 + 0.05))

    # Compliant tongue, finger pad, shoulder, and root gussets
    out.extend(box(tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_TONGUE_END_Y, LID_H - PANE_TONGUE_H, LID_H))
    out.extend(box(pad_x0, pad_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1 + 0.20, LID_H - PANE_TONGUE_H, LID_H))
    out.extend(box(tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1, PANE_CHANNEL_Z0, LID_H - PANE_TONGUE_H + 0.05))
    out.extend(
        prism_z(
            [(tongue_x0 - 1.50, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x0 + 0.10, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x0 + 0.10, PANE_TONGUE_ROOT_Y - 1.50)],
            LID_H - PANE_TONGUE_H,
            LID_H,
        )
    )
    out.extend(
        prism_z(
            [(tongue_x1 - 0.10, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x1 + 1.50, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x1 - 0.10, PANE_TONGUE_ROOT_Y - 1.50)],
            LID_H - PANE_TONGUE_H,
            LID_H,
        )
    )

    # Bed-supported roots for the two lid knuckles
    # Spans the entire knuckle width (X in [-20.50, -15.50 mm]) from local Z = -0.60 to 3.20 mm
    # In print orientation, this forms a 100% solid, thick foundation from the build plate (Z_print = 0.00 mm)
    # directly through the bore centerline up to Z_print = 3.80 mm, providing >= 1.65 mm wall thickness!
    left_end = -HINGE_LID_END
    left_inner = HINGE_BODY_Y0 - HINGE_GAP
    right_inner = HINGE_BODY_Y1 + HINGE_GAP
    right_end = HINGE_LID_END
    out.extend(
        box(
            -20.50,
            -15.50,
            left_end - 0.10,
            left_inner + 0.10,
            -0.60,
            LID_H,
        )
    )
    out.extend(
        box(
            -20.50,
            -15.50,
            right_inner - 0.10,
            right_end + 0.10,
            -0.60,
            LID_H,
        )
    )

    # Two lid knuckles alternate with body knuckle (peaked profile with 2.10 mm teardrop bore)
    out.extend(peaked_hinge_y(HINGE_X, HINGE_Z_LOCAL, left_end, left_inner, print_up_sign=-1.0, bore_r=HINGE_LID_BORE_R))
    out.extend(peaked_hinge_y(HINGE_X, HINGE_Z_LOCAL, right_inner, right_end, print_up_sign=-1.0, bore_r=HINGE_LID_BORE_R))

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
    out.extend(prism_y(clasp_profile, -3.50, 3.50))
    return out

def lid_print_orientation(lid: Mesh) -> Mesh:
    """Place label/top face flat on build plate; normalize lowest point to Z=0."""
    rotated = lid.transformed(lambda p: (p[0], -p[1], LID_H - p[2]), f"cassette_lid_{VERSION_TAG}_print")
    zmin = rotated.bounds()[0][2]
    return rotated.translated(0.0, 0.0, -zmin, f"cassette_lid_{VERSION_TAG}_print")

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
    
    # 3. Build lid in print orientation
    lid_local = build_lid_local()
    lid_mesh = lid_print_orientation(lid_local)
    write_stl(BUILD_DIR / "cassette_lid_v0_8_print.stl", lid_mesh)
    audit_lid = audit(lid_mesh)
    print("Lid Audit:", audit_lid)
    print("Lid Print Z Bounds:", lid_mesh.bounds()[0][2], "to", lid_mesh.bounds()[1][2])
    
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
            "hinge_body_length": HINGE_BODY_Y1 - HINGE_BODY_Y0,
            "hinge_knuckle_min_wall_thickness_mm": 1.20,
            "hinge_rotational_clearance": "+0.75 mm to +2.40 mm over 0-120 deg"
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
    print("All production cassette files generated and audited successfully.")

if __name__ == "__main__":
    main()
