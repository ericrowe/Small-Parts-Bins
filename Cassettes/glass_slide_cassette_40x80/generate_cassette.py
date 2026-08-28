#!/usr/bin/env python3
"""Generate the current glass-slide small-parts cassette release.

The STL generator itself uses only the Python standard library.  Matplotlib is
used only when --preview is requested.

All dimensions are millimetres.  Change values in the PARAMETERS section,
then run:

    python generate_cassette.py --out build --preview

This is deliberately a source-level parametric model: it remains editable on
machines that do not have a particular CAD package installed.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------

VERSION = "0.8"
VERSION_TAG = "v0_8"

# Cassette body.  The hinge sits mostly inside this nominal envelope; the
# knuckle creates a 39.55 mm maximum width, documented in the manifest.
BODY_W = 38.60
BODY_D = 80.00
BODY_H = 32.80
BODY_WALL = 2.00
BODY_BOTTOM = 2.00
BODY_CORNER = 2.00

# Lid and glass.  The 27 x 76.8 pocket covers common nominal 25 x 75,
# 25.4 x 76.2, and 26 x 76 mm plain microscope slides after measuring the
# actual batch.  Maximum intended slide is stated separately because printed
# clearances are printer-dependent.
LID_H = 3.20
POCKET_W = 27.00
POCKET_D = 76.80
POCKET_X = 0.50
POCKET_Y = 0.00
POCKET_DEPTH = 2.30
WINDOW_W = 23.00
WINDOW_D = 58.50
WINDOW_X = 0.50
WINDOW_Y = -1.75
MAX_GLASS_W = 26.30
MAX_GLASS_D = 76.30
MAX_GLASS_T = 1.20

# v0.7 end-loaded pane capture. The top/visible face prints on the bed. The
# assembled coordinates below are therefore the inverse of the tested coupon's
# print Z: top capture 2.4..3.2, pane channel 1.0..2.4, and opposite ledges
# 0.2..1.0. The 6.75 mm PETG tongue is unloaded 0.20 mm above the pane ceiling
# in the assembled lid and moves outward through its top-face slot for service.
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
PANE_SLOT_W = 11.00
PANE_TONGUE_SLOT_Y1 = -32.95

# The uninterrupted top surface above the window accepts a 9 mm TZe tape.
LABEL_W = 34.00
LABEL_D = 10.00
LABEL_X = 0.50
LABEL_Y = 33.50

# Hinge: 1.75 mm filament pin in an FDM-friendly peaked bore.  The v0.2
# circular horizontal tubes printed poorly in PETG because their inner roofs
# and outer undersides were true arcs.  This revision uses a teardrop bore and
# a pointed/45-degree outer underside so neither half needs internal support.
HINGE_X = -18.20
HINGE_Z_LOCAL = 0.20
HINGE_OUTER_HALF_W = 2.25
HINGE_OUTER_POINT = 2.70
HINGE_OUTER_SIDE_TOP = 0.80
# The body knuckle is a longer, less-supported horizontal feature and printed
# slightly tighter than the two lid knuckles.  Keep the v0.5 body adjustment:
# 2.25 mm nominal diameter on the body and 2.10 mm on the lid.
HINGE_LID_BORE_R = 1.05
HINGE_BODY_BORE_R = 1.125
HINGE_PIN_R = 0.875
HINGE_KEEP_OUT_R = HINGE_OUTER_POINT
HINGE_ATTACHMENT_CLEARANCE = 0.15
HINGE_LID_FRAME_NOTCH_X = HINGE_X + HINGE_LID_BORE_R + HINGE_ATTACHMENT_CLEARANCE
# The lid prints top-face-down.  Its knuckles therefore begin 0.55 mm above
# the build plate and must grow from the frame rather than from a detached
# point.  Carry the bed-supported upper rail 0.20 mm past the pin axis across
# both lid-knuckle spans.  This gives the first knuckle layers a real overlap
# with the frame instead of the tapered/floating root present in v0.5.
HINGE_LID_SUPPORT_OVERLAP = 0.20
HINGE_LID_SUPPORT_X = HINGE_X - HINGE_LID_SUPPORT_OVERLAP
HINGE_LID_ROOT_AXIAL_OVERLAP = 0.10
HINGE_BODY_SUPPORT_TOP = BODY_H + HINGE_Z_LOCAL - HINGE_BODY_BORE_R - HINGE_ATTACHMENT_CLEARANCE
HINGE_GAP = 0.80
HINGE_BODY_Y0 = -13.90
HINGE_BODY_Y1 = 13.90
HINGE_LID_END = 37.30

# v0.6 mating clearances.  Both reliefs are concentric with the hinge axis, so
# the stated radial clearance is maintained through the complete lid sweep.
HINGE_RADIAL_CLEARANCE = 0.25
HINGE_RELIEF_AXIAL_EXTRA = 0.25
HINGE_BODY_RELIEF_TOP = BODY_H + HINGE_Z_LOCAL - HINGE_KEEP_OUT_R - HINGE_RADIAL_CLEARANCE
HINGE_LID_RELIEF_X = HINGE_X + HINGE_KEEP_OUT_R + HINGE_RADIAL_CLEARANCE
HINGE_RELIEF_Y0 = HINGE_BODY_Y0 - HINGE_RELIEF_AXIAL_EXTRA
HINGE_RELIEF_Y1 = HINGE_BODY_Y1 + HINGE_RELIEF_AXIAL_EXTRA
HINGE_BODY_END_RELIEF_Y0 = -HINGE_LID_END - HINGE_RELIEF_AXIAL_EXTRA
HINGE_BODY_END_RELIEF_Y1 = HINGE_LID_END + HINGE_RELIEF_AXIAL_EXTRA

# Fingernail access on the latch edge: a subtle 1.3 mm relief in the lower
# 1.4 mm of the lid wall provides a comfortable pry surface while preserving
# a full-thickness 1.8 mm continuous roof above it.
FINGER_RELIEF_W = 14.00
FINGER_RELIEF_DEPTH = 1.30
FINGER_RELIEF_H = 1.40

# Retainer: four chamfered side lugs snap into a real groove in the lid pocket.
# The base remains undersize so the long side rails can bow inward during
# insertion.  SNAP_INTERFERENCE controls entry force; the groove supplies the
# positive withdrawal shoulder that was missing in v0.1.
RETAINER_W = 26.60
RETAINER_D = 76.40
RETAINER_H = 0.80
RETAINER_WINDOW_W = 22.50
RETAINER_WINDOW_D = 58.00
RETAINER_WINDOW_X = WINDOW_X
RETAINER_WINDOW_Y = WINDOW_Y
SNAP_INTERFERENCE = 0.20
SNAP_GROOVE_DEPTH = 0.35
SNAP_GROOVE_Z0 = 0.25
SNAP_GROOVE_Z1 = 1.20
SNAP_LUG_Z0 = 0.08
SNAP_LUG_Z1 = 0.50
# The original light/nominal/firm ladder remains available.  The three new
# retainers begin above the old 0.30 mm "firm" version.  Because the groove is
# 0.35 mm deep, 0.40 and 0.45 mm intentionally add 0.05 and 0.10 mm of seated
# preload per side; do not go higher without revising the lid groove.
FIT_LADDER_INTERFERENCES = (0.10, 0.20, 0.30)
STRONG_RETAINER_INTERFERENCES = (0.35, 0.40, 0.45)
RETAINER_SEAT_FOR_MAX_GLASS = POCKET_DEPTH - MAX_GLASS_T - RETAINER_H

# Hidden auto-release snap: 1.20 mm cantilever beam with 0.65 mm undercut engagement
LATCH_TONGUE_X0 = 15.20
LATCH_TONGUE_X1 = 16.40
LATCH_TONGUE_Y0 = -4.00
LATCH_TONGUE_Y1 = 4.00
LATCH_TONGUE_Z0 = -3.30
LATCH_TONGUE_Z1 = 0.45


Vec3 = tuple[float, float, float]
Tri = tuple[Vec3, Vec3, Vec3]
Vec2 = tuple[float, float]


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _normal(t: Tri) -> Vec3:
    n = _cross(_sub(t[1], t[0]), _sub(t[2], t[0]))
    length = math.sqrt(_dot(n, n))
    if length < 1e-12:
        return (0.0, 0.0, 0.0)
    return (n[0] / length, n[1] / length, n[2] / length)


@dataclass
class Mesh:
    name: str
    triangles: list[Tri]

    def __init__(self, name: str):
        self.name = name
        self.triangles = []

    def add(self, a: Vec3, b: Vec3, c: Vec3) -> None:
        # Repeated mapping points are useful when a ring changes topology at a
        # local notch.  Silently omit the resulting zero-area triangles.
        area = _cross(_sub(b, a), _sub(c, a))
        if _dot(area, area) > 1e-20:
            self.triangles.append((a, b, c))

    def quad(self, a: Vec3, b: Vec3, c: Vec3, d: Vec3) -> None:
        self.add(a, b, c)
        self.add(a, c, d)

    def extend(self, other: "Mesh") -> None:
        self.triangles.extend(other.triangles)

    def transformed(self, fn: Callable[[Vec3], Vec3], name: str | None = None) -> "Mesh":
        out = Mesh(name or self.name)
        out.triangles = [tuple(fn(v) for v in tri) for tri in self.triangles]  # type: ignore[list-item]
        return out

    def translated(self, dx: float, dy: float, dz: float, name: str | None = None) -> "Mesh":
        return self.transformed(lambda p: (p[0] + dx, p[1] + dy, p[2] + dz), name)

    def bounds(self) -> tuple[Vec3, Vec3]:
        pts = [v for tri in self.triangles for v in tri]
        return (
            (min(p[0] for p in pts), min(p[1] for p in pts), min(p[2] for p in pts)),
            (max(p[0] for p in pts), max(p[1] for p in pts), max(p[2] for p in pts)),
        )

    def signed_volume(self) -> float:
        total = 0.0
        for a, b, c in self.triangles:
            total += _dot(a, _cross(b, c)) / 6.0
        return total

    def flipped(self) -> "Mesh":
        out = Mesh(self.name)
        out.triangles = [(a, c, b) for a, b, c in self.triangles]
        return out

    def positive(self) -> "Mesh":
        return self if self.signed_volume() >= 0 else self.flipped()


def chamfer_bounds(x0: float, x1: float, y0: float, y1: float, c: float) -> list[Vec2]:
    """CCW chamfered rectangle."""
    if c < 0 or 2 * c > min(x1 - x0, y1 - y0):
        raise ValueError("invalid chamfer")
    return [
        (x0 + c, y0),
        (x1 - c, y0),
        (x1, y0 + c),
        (x1, y1 - c),
        (x1 - c, y1),
        (x0 + c, y1),
        (x0, y1 - c),
        (x0, y0 + c),
    ]


def chamfer_rect(w: float, d: float, c: float, cx: float = 0.0, cy: float = 0.0) -> list[Vec2]:
    return chamfer_bounds(cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, c)


def mapped_frame_loop(w: float, d: float, c: float, cx: float, cy: float) -> list[Vec2]:
    """CCW 16-point chamfered loop matching the lid's local relief stations."""
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - d / 2, cy + d / 2
    finger_outer = FINGER_RELIEF_W / 2
    finger_inner = FINGER_RELIEF_INNER_W / 2
    return [
        (x0 + c, y0),
        (x1 - c, y0),
        (x1, y0 + c),
        (x1, -finger_outer),
        (x1, -finger_inner),
        (x1, finger_inner),
        (x1, finger_outer),
        (x1, y1 - c),
        (x1 - c, y1),
        (x0 + c, y1),
        (x0, y1 - c),
        (x0, HINGE_RELIEF_Y1 + 0.60),
        (x0, HINGE_RELIEF_Y1 - 0.60),
        (x0, HINGE_RELIEF_Y0 + 0.60),
        (x0, HINGE_RELIEF_Y0 - 0.60),
        (x0, y0 + c),
    ]


def lid_outer_loop(finger_notched: bool, hinge_bore_notched: bool = False) -> list[Vec2]:
    """Lid perimeter with independent sweep and pin-bore reliefs.

    The lower lid layers at the two lid-knuckle spans begin to the right of
    the pin bore.  The upper perimeter tapers back toward the hinge axis; a
    separate closed support root added in ``build_lid_local`` makes that
    connection constant across both knuckle spans.
    """
    loop = mapped_frame_loop(
        BODY_W / 2 - HINGE_X,
        BODY_D,
        BODY_CORNER,
        (HINGE_X + BODY_W / 2) / 2,
        0.0,
    )
    # The mapped loop's nominal left edge is HINGE_X.  Move its centre span
    # inward to clear the body's centre knuckle.
    # Keep the centre span outside the body knuckle.  The lower rail remains
    # outside the bore.  The upper perimeter fans back toward HINGE_X without
    # a T-junction in this frame shell; explicit support-root prisms provide
    # the positive knuckle overlap.
    loop[11] = (HINGE_LID_FRAME_NOTCH_X, HINGE_RELIEF_Y1)
    loop[12] = (HINGE_LID_RELIEF_X, HINGE_RELIEF_Y1)
    loop[13] = (HINGE_LID_RELIEF_X, HINGE_RELIEF_Y0)
    loop[14] = (HINGE_LID_FRAME_NOTCH_X, HINGE_RELIEF_Y0)
    if hinge_bore_notched:
        for index in (10, 11, 14, 15):
            loop[index] = (HINGE_LID_FRAME_NOTCH_X, loop[index][1])
    if finger_notched:
        x_inner = BODY_W / 2 - FINGER_RELIEF_DEPTH
        loop[4] = (x_inner, -FINGER_RELIEF_INNER_W / 2)
        loop[5] = (x_inner, FINGER_RELIEF_INNER_W / 2)
    return loop


def pocket_side_groove_loop() -> list[Vec2]:
    """Pocket loop widened only along the long sides, tapering at chamfers."""
    loop = mapped_frame_loop(POCKET_W, POCKET_D, 0.55, POCKET_X, POCKET_Y)
    for index in range(2, 8):
        loop[index] = (loop[index][0] + SNAP_GROOVE_DEPTH, loop[index][1])
    for index in range(10, 16):
        loop[index] = (loop[index][0] - SNAP_GROOVE_DEPTH, loop[index][1])
    return loop


def clip_polygon_y(loop: Sequence[Vec2], limit: float, keep_below: bool) -> list[Vec2]:
    """Clip a convex polygon to y <= limit or y >= limit."""
    result: list[Vec2] = []

    def inside(p: Vec2) -> bool:
        return p[1] <= limit + 1e-10 if keep_below else p[1] >= limit - 1e-10

    def crossing(a: Vec2, b: Vec2) -> Vec2:
        if abs(b[1] - a[1]) < 1e-12:
            return (a[0], limit)
        t = (limit - a[1]) / (b[1] - a[1])
        return (a[0] + t * (b[0] - a[0]), limit)

    previous = loop[-1]
    previous_inside = inside(previous)
    for current in loop:
        current_inside = inside(current)
        if current_inside != previous_inside:
            result.append(crossing(previous, current))
        if current_inside:
            result.append(current)
        previous, previous_inside = current, current_inside
    return result


def _fan(mesh: Mesh, loop: Sequence[Vec2], z: float, up: bool) -> None:
    # Every loop used here is convex.
    a = (loop[0][0], loop[0][1], z)
    for i in range(1, len(loop) - 1):
        b = (loop[i][0], loop[i][1], z)
        c = (loop[i + 1][0], loop[i + 1][1], z)
        mesh.add(a, b, c) if up else mesh.add(a, c, b)


def _loop_wall(mesh: Mesh, loop: Sequence[Vec2], z0: float, z1: float, hole: bool = False) -> None:
    n = len(loop)
    for i in range(n):
        j = (i + 1) % n
        bi = (loop[i][0], loop[i][1], z0)
        bj = (loop[j][0], loop[j][1], z0)
        ti = (loop[i][0], loop[i][1], z1)
        tj = (loop[j][0], loop[j][1], z1)
        if hole:
            mesh.quad(bi, ti, tj, bj)
        else:
            mesh.quad(bi, bj, tj, ti)


def _ring_face(mesh: Mesh, outer: Sequence[Vec2], inner: Sequence[Vec2], z: float, up: bool) -> None:
    if len(outer) != len(inner):
        raise ValueError("ring loops must have the same vertex count")
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        oi = (outer[i][0], outer[i][1], z)
        oj = (outer[j][0], outer[j][1], z)
        ii = (inner[i][0], inner[i][1], z)
        ij = (inner[j][0], inner[j][1], z)
        if up:
            mesh.quad(oi, oj, ij, ii)
        else:
            mesh.quad(oi, ii, ij, oj)


def prism(name: str, loop: Sequence[Vec2], z0: float, z1: float) -> Mesh:
    m = Mesh(name)
    _fan(m, loop, z0, up=False)
    _fan(m, loop, z1, up=True)
    _loop_wall(m, loop, z0, z1, hole=False)
    return m.positive()


def box(name: str, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Mesh:
    return prism(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def prism_y(name: str, xz_loop: Sequence[Vec2], y0: float, y1: float) -> Mesh:
    """Extrude a convex x/z polygon along y."""
    m = Mesh(name)
    n = len(xz_loop)
    # End caps; positive() corrects the global orientation if necessary.
    a0 = (xz_loop[0][0], y0, xz_loop[0][1])
    a1 = (xz_loop[0][0], y1, xz_loop[0][1])
    for i in range(1, n - 1):
        p0 = (xz_loop[i][0], y0, xz_loop[i][1])
        q0 = (xz_loop[i + 1][0], y0, xz_loop[i + 1][1])
        p1 = (xz_loop[i][0], y1, xz_loop[i][1])
        q1 = (xz_loop[i + 1][0], y1, xz_loop[i + 1][1])
        m.add(a0, p0, q0)
        m.add(a1, q1, p1)
    for i in range(n):
        j = (i + 1) % n
        p0 = (xz_loop[i][0], y0, xz_loop[i][1])
        q0 = (xz_loop[j][0], y0, xz_loop[j][1])
        p1 = (xz_loop[i][0], y1, xz_loop[i][1])
        q1 = (xz_loop[j][0], y1, xz_loop[j][1])
        m.quad(p0, p1, q1, q0)
    return m.positive()


def ring_prism(name: str, outer: Sequence[Vec2], inner: Sequence[Vec2], z0: float, z1: float) -> Mesh:
    m = Mesh(name)
    _ring_face(m, outer, inner, z0, up=False)
    _ring_face(m, outer, inner, z1, up=True)
    _loop_wall(m, outer, z0, z1, hole=False)
    _loop_wall(m, inner, z0, z1, hole=True)
    return m.positive()


def hinge_profile_xz(
    cx: float,
    cz: float,
    print_up_sign: float,
    bore_r: float,
) -> tuple[list[Vec2], list[Vec2]]:
    """Return matched outer/bore loops for a support-free horizontal hinge.

    The profiles below are expressed in print coordinates.  The outer V grows
    outward by less than one millimetre per millimetre of height, while the
    bore follows a round lower arc and closes with two 45-degree roof lines.
    ``print_up_sign`` is +1 for the upright body and -1 for the lid, which is
    printed top-face-down.
    """
    ow = HINGE_OUTER_HALF_W
    op = HINGE_OUTER_POINT
    st = HINGE_OUTER_SIDE_TOP
    outer_print = [(-ow, st), (-ow, 0.0)]
    outer_print.extend(
        (-ow * (1.0 - step / 9.0), -op * step / 9.0)
        for step in range(1, 10)
    )
    outer_print.extend(
        (ow * step / 9.0, -op * (1.0 - step / 9.0))
        for step in range(1, 10)
    )
    outer_print.extend([(ow, st), (0.0, op)])

    # Twenty-one points approximate the 270-degree circular portion; the
    # final point is the exact intersection of the two 45-degree tangent roofs.
    # The small angular step leaves more than 0.16 mm radial clearance around
    # 1.75 mm filament even between polygon vertices.
    bore_print = [
        (
            bore_r * math.cos(math.radians(135.0 + 13.5 * index)),
            bore_r * math.sin(math.radians(135.0 + 13.5 * index)),
        )
        for index in range(21)
    ]
    bore_print.append((0.0, math.sqrt(2.0) * bore_r))

    def place(loop: Sequence[Vec2]) -> list[Vec2]:
        return [(cx + x, cz + print_up_sign * z) for x, z in loop]

    return place(outer_print), place(bore_print)


def peaked_hinge_y(
    name: str,
    cx: float,
    cz: float,
    y0: float,
    y1: float,
    print_up_sign: float,
    bore_r: float,
) -> Mesh:
    """Extrude a matched support-free hinge profile along the pin axis."""
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
    return m.positive()


def build_body() -> Mesh:
    out = Mesh(f"cassette_body_{VERSION_TAG}")
    outer = chamfer_rect(BODY_W, BODY_D, BODY_CORNER)
    inner = chamfer_rect(
        BODY_W - 2 * BODY_WALL,
        BODY_D - 2 * BODY_WALL,
        max(0.8, BODY_CORNER - BODY_WALL / 2),
    )

    # The complete lower shell ends below the two lid knuckles.  Independent
    # closed upper-wall pieces restore the normal rim everywhere else.  Their
    # 0.05 mm vertical overlap is an intentional slicer union.
    shell = Mesh("body_lower_shell")
    _fan(shell, outer, 0.0, up=False)
    _loop_wall(shell, outer, 0.0, HINGE_BODY_RELIEF_TOP, hole=False)
    _fan(shell, inner, BODY_BOTTOM, up=True)
    _loop_wall(shell, inner, BODY_BOTTOM, HINGE_BODY_RELIEF_TOP, hole=True)
    _ring_face(shell, outer, inner, HINGE_BODY_RELIEF_TOP, up=True)
    out.extend(shell.positive())

    upper_z0 = HINGE_BODY_RELIEF_TOP - 0.05
    join = 0.05
    # Straight walls ending at the split plane BODY_H (24.80 mm)
    out.extend(box("body_upper_bottom_wall", outer[0][0] - join, outer[1][0] + join, -BODY_D / 2, inner[0][1], upper_z0, BODY_H))
    out.extend(box("body_upper_right_wall", inner[2][0], BODY_W / 2, outer[2][1] - join, outer[3][1] + join, upper_z0, BODY_H))
    out.extend(box("body_upper_top_wall", outer[5][0] - join, outer[4][0] + join, inner[4][1], BODY_D / 2, upper_z0, BODY_H))
    # Stop the centre support below the pin passage.
    out.extend(
        box(
            "body_upper_left_centre",
            -BODY_W / 2,
            inner[7][0],
            HINGE_RELIEF_Y0,
            HINGE_RELIEF_Y1,
            upper_z0,
            HINGE_BODY_SUPPORT_TOP,
        )
    )
    # Left wall end spans stay at BODY_H (24.80 mm) to clear the rotating lid knuckles:
    out.extend(box("body_upper_left_lower_end", -BODY_W / 2, inner[7][0], outer[7][1] - join, HINGE_BODY_END_RELIEF_Y0, upper_z0, BODY_H))
    out.extend(box("body_upper_left_upper_end", -BODY_W / 2, inner[6][0], HINGE_BODY_END_RELIEF_Y1, outer[6][1] + join, upper_z0, BODY_H))

    # Chamfered corner sectors ending at BODY_H (24.80 mm):
    lower_right = [outer[1], outer[2], inner[2], inner[1]]
    upper_right = [outer[3], outer[4], inner[4], inner[3]]
    lower_left = clip_polygon_y([outer[7], outer[0], inner[0], inner[7]], HINGE_BODY_END_RELIEF_Y0, keep_below=True)
    upper_left = clip_polygon_y([outer[5], outer[6], inner[6], inner[5]], HINGE_BODY_END_RELIEF_Y1, keep_below=False)
    out.extend(prism("body_upper_lower_right_corner", lower_right, upper_z0, BODY_H))
    out.extend(prism("body_upper_upper_right_corner", upper_right, upper_z0, BODY_H))
    out.extend(prism("body_upper_lower_left_corner", lower_left, upper_z0, BODY_H))
    out.extend(prism("body_upper_upper_left_corner", upper_left, upper_z0, BODY_H))

    # Centre hinge knuckle, captive inside the documented maximum envelope.
    out.extend(
        peaked_hinge_y(
            "body_hinge_knuckle",
            HINGE_X,
            BODY_H + HINGE_Z_LOCAL,
            HINGE_BODY_Y0,
            HINGE_BODY_Y1,
            print_up_sign=1.0,
            bore_r=HINGE_BODY_BORE_R,
        )
    )

    # Reinforced catch on the inside of the right wall with 0.65 mm interference.
    catch_profile = [
        (17.30, BODY_H - 2.50),
        (16.55, BODY_H - 2.08),
        (16.55, BODY_H - 1.72),
        (17.30, BODY_H - 1.22),
    ]
    out.extend(prism_y("body_snap_catch", catch_profile, -4.00, 4.00))

    # Ergonomic tactile end pinch ribs
    for z_rib in [27.5, 29.2, 30.9]:
        out.extend(box("body_front_grip_rib", -7.0, 7.0, -BODY_D / 2 - 0.40, -BODY_D / 2 + join, z_rib, z_rib + 0.90))
        out.extend(box("body_back_grip_rib", -7.0, 7.0, BODY_D / 2 - join, BODY_D / 2 + 0.40, z_rib, z_rib + 0.90))

    return out


def build_divided_body() -> Mesh:
    out = Mesh(f"cassette_body_{VERSION_TAG}_divided")
    hx, hy = BODY_W / 2, BODY_D / 2
    lx, rx = -15.00, 17.30
    iy = 38.00
    c = BODY_CORNER
    relief_top = HINGE_BODY_RELIEF_TOP
    slot_w = 1.40
    slot_recess = 0.60
    floor_groove_d = 0.60
    slot_stations = [-12.87, 12.87]
    join = 0.05
    z_floor = BODY_BOTTOM - floor_groove_d

    # 1. Base floor slab: Z in [0, z_floor] = [0, 1.40]
    outer = chamfer_rect(BODY_W, BODY_D, BODY_CORNER)
    out.extend(prism("divided_base_floor", outer, 0.00, z_floor))

    # 2. Outer left wall: X in [-hx, lx - slot_recess], Z in [z_floor - join, relief_top]
    out.extend(box("divided_outer_left_wall", -hx, lx - slot_recess + join, -hy + c - join, hy - c + join, z_floor - join, relief_top + join))
    out.extend(box("divided_upper_left_centre", -hx, lx - slot_recess + join, HINGE_RELIEF_Y0, HINGE_RELIEF_Y1, relief_top, HINGE_BODY_SUPPORT_TOP))
    out.extend(box("divided_upper_left_lower_end", -hx, lx - slot_recess + join, -hy + c - join, HINGE_BODY_END_RELIEF_Y0, relief_top, BODY_H))
    out.extend(box("divided_upper_left_upper_end", -hx, lx - slot_recess + join, HINGE_BODY_END_RELIEF_Y1, hy - c + join, relief_top, BODY_H))

    # 3. Outer right wall: X in [rx + slot_recess, hx], Z in [z_floor - join, BODY_H]
    out.extend(box("divided_outer_right_wall", rx + slot_recess - join, hx, -hy + c - join, hy - c + join, z_floor - join, BODY_H))

    # 4. Front wall: Y in [-hy, -iy]
    out.extend(box("divided_front_wall", -hx + c - join, hx - c + join, -hy, -iy + join, z_floor - join, BODY_H))

    # 5. Back wall: Y in [iy, hy]
    out.extend(box("divided_back_wall", -hx + c - join, hx - c + join, iy - join, hy, z_floor - join, BODY_H))

    # 6. Outer corner chamfers
    lower_right = [outer[1], outer[2], (hx - c, -hy + c)]
    upper_right = [outer[3], outer[4], (hx - c, hy - c)]
    lower_left = [outer[7], outer[0], (-hx + c, -hy + c)]
    upper_left = [outer[5], outer[6], (-hx + c, hy - c)]
    out.extend(prism("corner_lr", lower_right, z_floor - join, BODY_H))
    out.extend(prism("corner_ur", upper_right, z_floor - join, BODY_H))
    out.extend(prism("corner_ll", lower_left, z_floor - join, BODY_H))
    out.extend(prism("corner_ul", upper_left, z_floor - join, BODY_H))

    # 7. Between-slot cavity segments:
    y_points = [-iy]
    for cy in sorted(slot_stations):
        y_points.extend([cy - slot_w / 2, cy + slot_w / 2])
    y_points.append(iy)

    for idx in range(0, len(y_points) - 1, 2):
        y0, y1 = y_points[idx], y_points[idx + 1]
        # Floor slab between slots (Z in [1.40, 2.00]):
        out.extend(box(f"div_floor_{idx}", lx - join, rx + join, y0 - join, y1 + join, z_floor - join, BODY_BOTTOM + join))

        # Left inner wall segment between slots (X in [lx - slot_recess, lx]):
        out.extend(box(f"div_left_wall_{idx}", lx - slot_recess - join, lx, y0 - join, y1 + join, z_floor - join, relief_top + join))
        if y1 <= HINGE_BODY_END_RELIEF_Y0 or y0 >= HINGE_BODY_END_RELIEF_Y1:
            out.extend(box(f"div_left_upper_end_{idx}", lx - slot_recess - join, lx, y0 - join, y1 + join, relief_top, BODY_H))
        elif y0 >= HINGE_RELIEF_Y0 and y1 <= HINGE_RELIEF_Y1:
            out.extend(box(f"div_left_upper_centre_{idx}", lx - slot_recess - join, lx, y0 - join, y1 + join, relief_top, HINGE_BODY_SUPPORT_TOP))

        # Right inner wall segment between slots (X in [rx, rx + slot_recess]):
        out.extend(box(f"div_right_wall_{idx}", rx, rx + slot_recess + join, y0 - join, y1 + join, z_floor - join, BODY_H))

    # 8. Centre hinge knuckle
    out.extend(
        peaked_hinge_y(
            "body_hinge_knuckle",
            HINGE_X,
            BODY_H + HINGE_Z_LOCAL,
            HINGE_BODY_Y0,
            HINGE_BODY_Y1,
            print_up_sign=1.0,
            bore_r=HINGE_BODY_BORE_R,
        )
    )

    # 9. Closure catch
    catch_profile = [
        (17.30, BODY_H - 2.50),
        (16.55, BODY_H - 2.08),
        (16.55, BODY_H - 1.72),
        (17.30, BODY_H - 1.22),
    ]
    out.extend(prism_y("body_snap_catch", catch_profile, -4.00, 4.00))

    # 10. Ergonomic tactile end pinch ribs
    for z_rib in [27.5, 29.2, 30.9]:
        out.extend(box("divided_front_grip_rib", -7.0, 7.0, -BODY_D / 2 - 0.40, -BODY_D / 2 + join, z_rib, z_rib + 0.90))
        out.extend(box("divided_back_grip_rib", -7.0, 7.0, BODY_D / 2 - join, BODY_D / 2 + 0.40, z_rib, z_rib + 0.90))

    return out


def build_divider_card(thickness: float = 1.20,
                       notch_w: float = 10.0, notch_d: float = 1.5,
                       bottom_chamfer: float = 0.6) -> Mesh:
    x_left = -15.00 - 0.50   # -15.50 mm
    x_right = 17.30 + 0.50  # +17.80 mm (total width = 33.30 mm)
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
    return prism_y(f"divider_card_{thickness:.1f}mm", pts_xz, -ht, ht)


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
    pad_cut_x0 = pad_x0 - pad_gap       # -4.50 - 0.50 = -5.00
    pad_cut_x1 = pad_x1 + pad_gap       #  5.50 + 0.50 =  6.00
    tongue_cut_x0 = tongue_x0 - tongue_gap # -3.50 - 0.50 = -4.00
    tongue_cut_x1 = tongue_x1 + tongue_gap #  4.50 + 0.50 =  5.00

    # Top frame with tightened 0.50 mm perimeter gap around the compliant latch:
    # 1. Entry frame around finger pad:
    out.extend(box("top_entry_pad_left", -17.00, pad_cut_x0, -40.00, -37.20, top_z0, top_z1))
    out.extend(box("top_entry_pad_right", pad_cut_x1, 19.30, -40.00, -37.20, top_z0, top_z1))

    # 2. Entry frame around tongue:
    out.extend(box("top_entry_tongue_left", -17.00, tongue_cut_x0, -37.25, -34.50, top_z0, top_z1))
    out.extend(box("top_entry_tongue_right", tongue_cut_x1, 19.30, -37.25, -34.50, top_z0, top_z1))

    # 3. Entry frame around gussets:
    out.extend(box("top_entry_gusset_left", -17.00, pad_cut_x0, -34.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))
    out.extend(box("top_entry_gusset_right", pad_cut_x1, 19.30, -34.55, PANE_TONGUE_ROOT_Y + 0.05, top_z0, top_z1))

    # 4. Tongue root crossbar:
    out.extend(box("top_tongue_root_band", -17.00, 19.30, PANE_TONGUE_ROOT_Y, window_y0 + 0.05, top_z0, top_z1))

    # Main window side rails. The hinge-side centre segment preserves the v0.6
    # rotational notch; end segments retain the verified knuckle-root overlap.
    out.extend(box("top_window_left_lower", -17.00, window_x0, window_y0 - 0.05, HINGE_RELIEF_Y0, top_z0, top_z1))
    out.extend(box("top_window_left_centre", -15.50, window_x0, HINGE_RELIEF_Y0 - 0.05, HINGE_RELIEF_Y1 + 0.05, top_z0, top_z1))
    out.extend(box("top_window_left_upper", -17.00, window_x0, HINGE_RELIEF_Y1, window_y1 + 0.05, top_z0, top_z1))
    out.extend(box("top_window_right", window_x1, 19.30, window_y0 - 0.05, window_y1 + 0.05, top_z0, top_z1))

    # The unchanged solid label band also roofs the far end of the channel.
    out.extend(box("top_label_band", -17.00, 19.30, window_y1, 38.05, top_z0, top_z1))
    out.extend(box("top_label_chamfer_extension", LABEL_X - LABEL_W / 2, LABEL_X + LABEL_W / 2, 37.95, 38.55, top_z0, top_z1))
    out.extend(box("top_far_end", -16.20, 17.30, 38.45, 40.00, top_z0, top_z1))

    channel_x0 = POCKET_X - PANE_CHANNEL_W / 2
    channel_x1 = POCKET_X + PANE_CHANNEL_W / 2
    bottom_x0 = POCKET_X - PANE_BOTTOM_OPENING_W / 2
    bottom_x1 = POCKET_X + PANE_BOTTOM_OPENING_W / 2

    # Continuous side walls and 1.5 mm opposite ledges reproduce the passing
    # v0.3/v0.4 channel and positively overlap the bed-supported top frame.
    out.extend(box("pane_left_wall", -15.50, channel_x0, PANE_ENTRY_Y, 38.45, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("pane_right_wall", channel_x1, 17.30, PANE_ENTRY_Y, 38.45, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("pane_left_bottom_ledge", -15.50, bottom_x0, PANE_ENTRY_Y, 38.45, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box("pane_right_bottom_ledge", bottom_x1, 17.30, PANE_ENTRY_Y, 38.45, PANE_BOTTOM_Z0, PANE_CHANNEL_Z0))
    out.extend(box("pane_far_stop", channel_x0 - 0.05, channel_x1 + 0.05, PANE_FAR_STOP_Y, 39.50, PANE_CHANNEL_Z0 - 0.05, PANE_CHANNEL_Z1 + 0.05))

    # Outer side walls of the lid meeting the body rim at local Z = 0.00:
    # Right outer wall with fingernail relief:
    out.extend(box("right_outer_wall_lower_end", 17.25, 19.30, -38.05, -6.95, 0.0, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("right_outer_wall_upper_end", 17.25, 19.30, 6.95, 38.05, 0.0, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("right_finger_relief_inner_wall", 17.25, 18.00, -5.85, 5.85, 0.0, FINGER_RELIEF_H + 0.05))
    out.extend(box("right_finger_relief_roof_wall", 17.25, 19.30, -7.05, 7.05, FINGER_RELIEF_H, PANE_CHANNEL_Z1 + 0.05))

    # Outer wall corners on far and entry ends:
    out.extend(box("top_far_end_left_outer", -17.00, -13.00, 38.00, 40.00, 0.0, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("top_far_end_right_outer", 14.00, 19.30, 38.00, 40.00, 0.0, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("top_entry_left_outer", -17.00, -13.00, -40.00, -38.00, 0.0, PANE_CHANNEL_Z1 + 0.05))
    out.extend(box("top_entry_right_outer", 14.00, 19.30, -40.00, -38.00, 0.0, PANE_CHANNEL_Z1 + 0.05))

    # Compliant tongue, finger pad, shoulder, and root gussets
    out.extend(box("pane_compliant_tongue", tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_TONGUE_END_Y, LID_H - PANE_TONGUE_H, LID_H))
    out.extend(box("pane_latch_finger_pad", pad_x0, pad_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1 + 0.20, LID_H - PANE_TONGUE_H, LID_H))
    out.extend(box("pane_positive_end_shoulder", tongue_x0, tongue_x1, PANE_SHOULDER_Y0, PANE_SHOULDER_Y1, PANE_CHANNEL_Z0, LID_H - PANE_TONGUE_H + 0.05))
    out.extend(
        prism(
            "pane_tongue_root_gusset_left",
            [(tongue_x0 - 1.50, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x0 + 0.10, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x0 + 0.10, PANE_TONGUE_ROOT_Y - 1.50)],
            LID_H - PANE_TONGUE_H,
            LID_H,
        )
    )
    out.extend(
        prism(
            "pane_tongue_root_gusset_right",
            [(tongue_x1 - 0.10, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x1 + 1.50, PANE_TONGUE_ROOT_Y + 0.10), (tongue_x1 - 0.10, PANE_TONGUE_ROOT_Y - 1.50)],
            LID_H - PANE_TONGUE_H,
            LID_H,
        )
    )

    # Bed-supported roots for the two lid knuckles.
    left_end = -HINGE_LID_END
    left_inner = HINGE_BODY_Y0 - HINGE_GAP
    right_inner = HINGE_BODY_Y1 + HINGE_GAP
    right_end = HINGE_LID_END
    out.extend(
        box(
            "lid_hinge_supported_root_a",
            HINGE_LID_SUPPORT_X,
            HINGE_LID_FRAME_NOTCH_X + 0.05,
            left_end - HINGE_LID_ROOT_AXIAL_OVERLAP,
            left_inner + HINGE_LID_ROOT_AXIAL_OVERLAP,
            FINGER_RELIEF_H,
            LID_H,
        )
    )
    out.extend(
        box(
            "lid_hinge_supported_root_b",
            HINGE_LID_SUPPORT_X,
            HINGE_LID_FRAME_NOTCH_X + 0.05,
            right_inner - HINGE_LID_ROOT_AXIAL_OVERLAP,
            right_end + HINGE_LID_ROOT_AXIAL_OVERLAP,
            FINGER_RELIEF_H,
            LID_H,
        )
    )

    # Two lid knuckles alternate with the body knuckle.
    out.extend(peaked_hinge_y("lid_hinge_knuckle_a", HINGE_X, HINGE_Z_LOCAL, left_end, left_inner, print_up_sign=-1.0, bore_r=HINGE_LID_BORE_R))
    out.extend(peaked_hinge_y("lid_hinge_knuckle_b", HINGE_X, HINGE_Z_LOCAL, right_inner, right_end, print_up_sign=-1.0, bore_r=HINGE_LID_BORE_R))

    # Reinforced flexible tongue (1.20 mm thick) and hook with 0.65 mm interference.
    out.extend(
        box(
            "latch_tongue",
            LATCH_TONGUE_X0,
            LATCH_TONGUE_X1,
            LATCH_TONGUE_Y0,
            LATCH_TONGUE_Y1,
            LATCH_TONGUE_Z0,
            LATCH_TONGUE_Z1,
        )
    )
    hook_profile = [
        (LATCH_TONGUE_X1 - 0.05, -3.10),
        (17.15, -2.65),
        (17.20, -2.35),
        (16.95, -2.00),
        (LATCH_TONGUE_X1 - 0.05, -1.65),
    ]
    out.extend(prism_y("latch_hook", hook_profile, -3.80, 3.80))
    return out


def add_snap_lugs(out: Mesh, interference: float, y_centres: Sequence[float], prefix: str) -> None:
    """Add paired side lugs with a withdrawal shoulder and insertion chamfer."""
    base_x = POCKET_X + RETAINER_W / 2
    crest_x = POCKET_X + POCKET_W / 2 + interference
    right_profile = [
        (base_x - 0.12, SNAP_LUG_Z0),
        (crest_x, SNAP_LUG_Z0),
        (crest_x, SNAP_LUG_Z0 + 0.20),
        (base_x + 0.06, SNAP_LUG_Z1),
        (base_x - 0.12, SNAP_LUG_Z1),
    ]
    left_profile = [(2 * POCKET_X - x, z) for x, z in right_profile][::-1]
    for index, cy in enumerate(y_centres):
        out.extend(prism_y(f"{prefix}_right_{index}", right_profile, cy - 1.8, cy + 1.8))
        out.extend(prism_y(f"{prefix}_left_{index}", left_profile, cy - 1.8, cy + 1.8))


def build_retainer(interference: float = SNAP_INTERFERENCE, suffix: str = "nominal") -> Mesh:
    out = Mesh(f"glass_retainer_{suffix}_v0_6")
    outer = chamfer_rect(RETAINER_W, RETAINER_D, 0.50, POCKET_X, POCKET_Y)
    inner = chamfer_rect(
        RETAINER_WINDOW_W,
        RETAINER_WINDOW_D,
        0.65,
        RETAINER_WINDOW_X,
        RETAINER_WINDOW_Y,
    )
    out.extend(ring_prism("retainer_ring", outer, inner, 0.0, RETAINER_H))

    add_snap_lugs(out, interference, (-20.0, 18.0), "retainer_snap")

    # A flat pull tab projects into the aperture.  A pick can catch its free
    # edge without adding a print-hostile feature above or below the bezel.
    out.extend(box("retainer_pull_tab", -2.5, 3.5, 24.5, 27.5, 0.0, RETAINER_H))
    return out


def build_fit_coupon() -> Mesh:
    """Short open-ended section that tests slide width/depth before the lid."""
    m = Mesh("glass_fit_coupon_v0_6")
    y0, y1 = -9.0, 9.0
    outer_x0, outer_x1 = -BODY_W / 2, BODY_W / 2
    pocket_x0 = POCKET_X - POCKET_W / 2
    pocket_x1 = POCKET_X + POCKET_W / 2
    window_x0 = WINDOW_X - WINDOW_W / 2
    window_x1 = WINDOW_X + WINDOW_W / 2

    groove_x0 = pocket_x0 - SNAP_GROOVE_DEPTH
    groove_x1 = pocket_x1 + SNAP_GROOVE_DEPTH

    # Side rails reproduce the lid's positive snap groove.  A full-height
    # outer spine keeps each rail continuous while the two fill blocks create
    # the lower and upper groove shoulders.
    m.extend(box("coupon_left_spine", outer_x0, groove_x0, y0 + 0.10, y1, 0.0, LID_H))
    m.extend(box("coupon_left_lower_fill", groove_x0 - 0.05, pocket_x0, y0 + 0.10, y1, 0.0, SNAP_GROOVE_Z0))
    m.extend(box("coupon_left_upper_fill", groove_x0 - 0.05, pocket_x0, y0 + 0.10, y1, SNAP_GROOVE_Z1, LID_H))
    m.extend(box("coupon_right_spine", groove_x1, outer_x1, y0 + 0.10, y1, 0.0, LID_H))
    m.extend(box("coupon_right_lower_fill", pocket_x1, groove_x1 + 0.05, y0 + 0.10, y1, 0.0, SNAP_GROOVE_Z0))
    m.extend(box("coupon_right_upper_fill", pocket_x1, groove_x1 + 0.05, y0 + 0.10, y1, SNAP_GROOVE_Z1, LID_H))
    m.extend(box("coupon_left_ledge", pocket_x0 - 0.05, window_x0, y0 + 0.10, y1, POCKET_DEPTH, LID_H))
    m.extend(box("coupon_right_ledge", window_x1, pocket_x1 + 0.05, y0 + 0.10, y1, POCKET_DEPTH, LID_H))
    # Back stop connects the rails; the +Y end remains open for the slide.
    m.extend(box("coupon_back_stop", outer_x0, outer_x1, y0, y0 + 3.10, 0.0, LID_H))
    return m


def build_fit_clip(interference: float, identification_pips: int) -> Mesh:
    """Short retainer section for checking snap force in the grooved coupon."""
    code = int(round(interference * 100))
    m = Mesh(f"glass_snap_fit_clip_{code:02d}_v0_6")
    outer = chamfer_rect(RETAINER_W, 12.0, 0.50, POCKET_X, 0.0)
    inner = chamfer_rect(RETAINER_WINDOW_W, 7.0, 0.55, RETAINER_WINDOW_X, 0.0)
    m.extend(ring_prism("coupon_clip_ring", outer, inner, 0.0, RETAINER_H))
    add_snap_lugs(m, interference, (0.0,), "coupon_snap")
    # One, two, or three inward pips identify light/nominal/firm after the STL
    # filenames have been placed together on a build plate.
    pip_x0 = POCKET_X - 0.55 * (identification_pips - 1)
    for index in range(identification_pips):
        cx = pip_x0 + 1.10 * index
        m.extend(box(f"fit_id_pip_{index}", cx - 0.32, cx + 0.32, 3.10, 3.72, 0.0, RETAINER_H))
    return m


def build_hinge_test_body() -> Mesh:
    """Short body-side coupon reproducing the support-free centre knuckle."""
    m = Mesh("hinge_test_body_v0_6")
    test_y = 12.0
    test_axis_z = 5.00
    test_body_top = test_axis_z - HINGE_BODY_BORE_R - HINGE_ATTACHMENT_CLEARANCE
    test_relief_top = test_axis_z - HINGE_KEEP_OUT_R - HINGE_RADIAL_CLEARANCE
    # A low foot makes the coupon stable without participating in the hinge.
    m.extend(box("hinge_test_foot", HINGE_X - HINGE_OUTER_HALF_W, -11.0, -test_y, test_y, 0.0, 1.50))
    m.extend(box("hinge_test_lower_wall", -BODY_W / 2, -BODY_W / 2 + BODY_WALL, -test_y, test_y, 1.45, test_relief_top))
    m.extend(box("hinge_test_centre_wall", -BODY_W / 2, -BODY_W / 2 + BODY_WALL, -5.25, 5.25, test_relief_top - 0.05, test_body_top))
    m.extend(peaked_hinge_y("hinge_test_body_knuckle", HINGE_X, test_axis_z, -5.0, 5.0, print_up_sign=1.0, bore_r=HINGE_BODY_BORE_R))
    return m


def build_hinge_test_lid_local() -> Mesh:
    """Short lid-side coupon with the centre rail notch and two knuckles."""
    m = Mesh("hinge_test_lid_v0_6_local")
    test_y = 12.0
    # The centre rail remains outside the body-knuckle sweep.  At the two lid
    # knuckles, the full-height main rail begins beyond the pin bore and a
    # separate bed-supported upper extension reaches 0.20 mm past the hinge
    # axis only above the bore.  The positive overlap prevents a floating
    # first knuckle layer and avoids a merely coplanar shell seam.
    m.extend(box("hinge_test_centre_rail", HINGE_LID_RELIEF_X, -11.0, -5.30, 5.30, 0.0, LID_H))
    m.extend(box("hinge_test_main_rail_a", HINGE_LID_FRAME_NOTCH_X, -11.0, -test_y, -5.25, 0.0, LID_H))
    m.extend(box("hinge_test_main_rail_b", HINGE_LID_FRAME_NOTCH_X, -11.0, 5.25, test_y, 0.0, LID_H))
    m.extend(box("hinge_test_upper_extension_a", HINGE_LID_SUPPORT_X, HINGE_LID_FRAME_NOTCH_X + 0.05, -test_y, -5.25, FINGER_RELIEF_H, LID_H))
    m.extend(box("hinge_test_upper_extension_b", HINGE_LID_SUPPORT_X, HINGE_LID_FRAME_NOTCH_X + 0.05, 5.25, test_y, FINGER_RELIEF_H, LID_H))
    m.extend(peaked_hinge_y("hinge_test_lid_knuckle_a", HINGE_X, HINGE_Z_LOCAL, -11.0, -5.80, print_up_sign=-1.0, bore_r=HINGE_LID_BORE_R))
    m.extend(peaked_hinge_y("hinge_test_lid_knuckle_b", HINGE_X, HINGE_Z_LOCAL, 5.80, 11.0, print_up_sign=-1.0, bore_r=HINGE_LID_BORE_R))
    return m


def hinge_test_lid_print_orientation(lid: Mesh) -> Mesh:
    rotated = lid.transformed(lambda p: (p[0], -p[1], LID_H - p[2]), f"hinge_test_lid_{VERSION_TAG}_print")
    return rotated.translated(0.0, 0.0, -rotated.bounds()[0][2], f"hinge_test_lid_{VERSION_TAG}_print")


def lid_print_orientation(lid: Mesh) -> Mesh:
    """Place the label/top face on the build plate; hinge axis remains along Y."""
    # Rotate 180 degrees about X: y -> -y, z -> LID_H-z.  The descending snap
    # then prints upward.  Normalize the hinge's small lower extent to Z=0.
    rotated = lid.transformed(lambda p: (p[0], -p[1], LID_H - p[2]), f"cassette_lid_{VERSION_TAG}_print")
    zmin = rotated.bounds()[0][2]
    return rotated.translated(0.0, 0.0, -zmin, f"cassette_lid_{VERSION_TAG}_print")


def combine(name: str, meshes: Iterable[Mesh]) -> Mesh:
    out = Mesh(name)
    for m in meshes:
        out.extend(m)
    return out


def rotate_about_hinge_open(local_lid: Mesh, angle_deg: float, z_offset: float = BODY_H) -> Mesh:
    """Reference-only transform; negative angle lifts the right side."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    axis_z = BODY_H + HINGE_Z_LOCAL

    def fn(p: Vec3) -> Vec3:
        x, y, z = p[0], p[1], p[2] + z_offset
        dx, dz = x - HINGE_X, z - axis_z
        return (HINGE_X + dx * ca + dz * sa, y, axis_z - dx * sa + dz * ca)

    return local_lid.transformed(fn, "lid_open_reference")


def write_binary_stl(path: Path, mesh: Mesh) -> None:
    header = (f"{mesh.name} generated by generate_cassette.py").encode("ascii", "replace")[:80].ljust(80, b"\0")
    with path.open("wb") as f:
        f.write(header)
        f.write(struct.pack("<I", len(mesh.triangles)))
        for tri in mesh.triangles:
            n = _normal(tri)
            values = (*n, *tri[0], *tri[1], *tri[2])
            f.write(struct.pack("<12fH", *values, 0))


def audit_exported_stl(path: Path) -> dict[str, object]:
    """Re-read a binary STL and verify its encoded artifact, not just source mesh."""
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"truncated binary STL: {path}")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * triangle_count:
        raise ValueError(f"binary STL size/count mismatch: {path}")
    finite = True
    degenerate = 0
    for index in range(triangle_count):
        values = struct.unpack_from("<12fH", data, 84 + 50 * index)
        coords = values[3:12]
        finite = finite and all(math.isfinite(value) for value in coords)
        a, b, c = coords[0:3], coords[3:6], coords[6:9]
        u = tuple(b[i] - a[i] for i in range(3))
        v = tuple(c[i] - a[i] for i in range(3))
        cross = (
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        )
        if sum(value * value for value in cross) <= 1e-18:
            degenerate += 1
    return {
        "binary_stl_size_valid": True,
        "triangle_count": triangle_count,
        "finite_coordinates": finite,
        "degenerate_triangles": degenerate,
    }


def write_obj(path: Path, named_meshes: Sequence[tuple[str, Mesh]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"# Glass-slide cassette v{VERSION} assembly reference\n")
        index = 1
        for name, mesh in named_meshes:
            f.write(f"o {name}\n")
            for tri in mesh.triangles:
                for v in tri:
                    f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for _ in mesh.triangles:
                f.write(f"f {index} {index + 1} {index + 2}\n")
                index += 3


def edge_audit(mesh: Mesh, decimals: int = 5) -> dict[str, int]:
    """Check each triangle soup for boundary/non-manifold edges."""
    counts: dict[tuple[Vec3, Vec3], int] = {}

    def key(p: Vec3) -> Vec3:
        return (round(p[0], decimals), round(p[1], decimals), round(p[2], decimals))

    for tri in mesh.triangles:
        pts = [key(v) for v in tri]
        for i in range(3):
            a, b = pts[i], pts[(i + 1) % 3]
            e = (a, b) if a <= b else (b, a)
            counts[e] = counts.get(e, 0) + 1
    return {
        "triangles": len(mesh.triangles),
        "unique_edges": len(counts),
        "boundary_edges": sum(1 for n in counts.values() if n == 1),
        "nonmanifold_edges": sum(1 for n in counts.values() if n > 2),
    }


def shell_overlap_connectivity(mesh: Mesh, decimals: int = 5) -> dict[str, object]:
    """Ensure every closed shell participates in a positive AABB-overlap graph."""
    edge_to_triangles: dict[tuple[Vec3, Vec3], list[int]] = {}

    def key(point: Vec3) -> Vec3:
        return tuple(round(value, decimals) for value in point)  # type: ignore[return-value]

    for index, triangle in enumerate(mesh.triangles):
        points = [key(vertex) for vertex in triangle]
        for i in range(3):
            edge = tuple(sorted((points[i], points[(i + 1) % 3])))
            edge_to_triangles.setdefault(edge, []).append(index)  # type: ignore[arg-type]
    adjacency = [set() for _ in mesh.triangles]
    for indices in edge_to_triangles.values():
        for first in indices:
            adjacency[first].update(index for index in indices if index != first)
    components: list[list[int]] = []
    visited: set[int] = set()
    for start in range(len(mesh.triangles)):
        if start in visited:
            continue
        stack = [start]
        visited.add(start)
        component: list[int] = []
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    bounds = []
    for component in components:
        points = [vertex for index in component for vertex in mesh.triangles[index]]
        bounds.append((
            tuple(min(point[axis] for point in points) for axis in range(3)),
            tuple(max(point[axis] for point in points) for axis in range(3)),
        ))
    graph = [set() for _ in components]
    for first, (lo_a, hi_a) in enumerate(bounds):
        for second in range(first + 1, len(bounds)):
            lo_b, hi_b = bounds[second]
            if all(min(hi_a[axis], hi_b[axis]) - max(lo_a[axis], lo_b[axis]) > 1e-4 for axis in range(3)):
                graph[first].add(second)
                graph[second].add(first)
    reached = {0} if components else set()
    stack = list(reached)
    while stack:
        current = stack.pop()
        for neighbor in graph[current]:
            if neighbor not in reached:
                reached.add(neighbor)
                stack.append(neighbor)
    return {
        "closed_shell_components": len(components),
        "positive_aabb_overlap_graph_connected": len(reached) == len(components),
        "unconnected_shell_components": len(components) - len(reached),
    }


def mesh_record(mesh: Mesh, filename: str) -> dict[str, object]:
    lo, hi = mesh.bounds()
    return {
        "file": filename,
        "triangles": len(mesh.triangles),
        "bounds_min_mm": [round(v, 3) for v in lo],
        "bounds_max_mm": [round(v, 3) for v in hi],
        "size_mm": [round(hi[i] - lo[i], 3) for i in range(3)],
        "signed_mesh_volume_mm3": round(mesh.signed_volume(), 2),
        "edge_audit": edge_audit(mesh),
    }


def validate_design() -> dict[str, object]:
    """Fail generation if a functional clearance is lost during editing."""
    hinge_body_clear = BODY_H + HINGE_Z_LOCAL - HINGE_KEEP_OUT_R - HINGE_BODY_RELIEF_TOP
    hinge_lid_clear = HINGE_LID_RELIEF_X - (HINGE_X + HINGE_KEEP_OUT_R)
    finger_inner_x = BODY_W / 2 - FINGER_RELIEF_DEPTH
    latch_clear = finger_inner_x - 17.05
    finger_roof = LID_H - FINGER_RELIEF_H
    envelope_w = BODY_W / 2 - (HINGE_X - HINGE_OUTER_HALF_W)
    array_w = 3 * envelope_w + 2 * 0.40
    array_d = 2 * BODY_D + 0.40
    pane_channel_h = PANE_CHANNEL_Z1 - PANE_CHANNEL_Z0
    top_overlap_measured = (24.9 - PANE_TOP_OPENING_W) / 2
    bottom_overlap_measured = (24.9 - PANE_BOTTOM_OPENING_W) / 2
    pane_axial_clearance = PANE_FAR_STOP_Y - PANE_SHOULDER_Y1 - MAX_GLASS_D
    pane_tongue_free_length = PANE_TONGUE_ROOT_Y - PANE_SHOULDER_Y0
    pane_tongue_relaxed_gap = LID_H - PANE_TONGUE_H - PANE_CHANNEL_Z1
    pane_tongue_strain = 6.0 * pane_channel_h * PANE_TONGUE_H / pane_tongue_free_length**2
    pane_finger_pad_lateral_clearance = (PANE_SLOT_W - PANE_FINGER_PAD_W) / 2
    pane_tongue_lateral_clearance = (PANE_SLOT_W - PANE_TONGUE_W) / 2
    pane_lateral_clearance = PANE_CHANNEL_W - MAX_GLASS_W
    opposite_ledge_overhang = (PANE_CHANNEL_W - PANE_BOTTOM_OPENING_W) / 2
    label_x0, label_x1 = LABEL_X - LABEL_W / 2, LABEL_X + LABEL_W / 2
    label_y0, label_y1 = LABEL_Y - LABEL_D / 2, LABEL_Y + LABEL_D / 2
    label_zone_fully_supported = (
        label_x0 >= -16.50 and label_x1 <= 17.50
        and label_y0 >= WINDOW_Y + WINDOW_D / 2
        and label_y1 <= 38.55
    )

    # The outer lower V must never grow outward faster than 45 degrees.  The
    # teardrop roof is exactly 45 degrees and contains the full filament pin.
    outer_lower_run_over_rise = HINGE_OUTER_HALF_W / HINGE_OUTER_POINT
    bore_roof_run_over_rise = 1.0
    _, body_bore_loop = hinge_profile_xz(0.0, 0.0, 1.0, HINGE_BODY_BORE_R)
    _, lid_bore_loop = hinge_profile_xz(0.0, 0.0, 1.0, HINGE_LID_BORE_R)

    def origin_to_segment(a: Vec2, b: Vec2) -> float:
        dx, dz = b[0] - a[0], b[1] - a[1]
        denom = dx * dx + dz * dz
        t = 0.0 if denom < 1e-12 else max(0.0, min(1.0, -(a[0] * dx + a[1] * dz) / denom))
        x, z = a[0] + t * dx, a[1] + t * dz
        return math.hypot(x, z)

    def minimum_inscribed_radius(loop: Sequence[Vec2]) -> float:
        return min(
            origin_to_segment(loop[index], loop[(index + 1) % len(loop)])
            for index in range(len(loop))
        )

    body_bore_min_radius = minimum_inscribed_radius(body_bore_loop)
    lid_bore_min_radius = minimum_inscribed_radius(lid_bore_loop)
    body_bore_pin_clearance = body_bore_min_radius - HINGE_PIN_R
    lid_bore_pin_clearance = lid_bore_min_radius - HINGE_PIN_R
    body_attachment_to_bore = (
        BODY_H + HINGE_Z_LOCAL - HINGE_BODY_BORE_R - HINGE_BODY_SUPPORT_TOP
    )
    lid_attachment_to_bore_x = HINGE_LID_FRAME_NOTCH_X - (HINGE_X + HINGE_LID_BORE_R)
    lid_attachment_to_bore_z = FINGER_RELIEF_H - (HINGE_Z_LOCAL + HINGE_LID_BORE_R)
    lid_support_overlap = HINGE_X - HINGE_LID_SUPPORT_X
    lid_knuckle_first_print_z = LID_H - (HINGE_Z_LOCAL + HINGE_OUTER_POINT)
    lid_support_print_height = LID_H - FINGER_RELIEF_H
    lid_support_above_knuckle_start = lid_support_print_height - lid_knuckle_first_print_z
    lid_root_to_body_knuckle_axial_clearance = HINGE_GAP - HINGE_LID_ROOT_AXIAL_OVERLAP
    lid_root_to_body_end_wall_axial_clearance = HINGE_RELIEF_AXIAL_EXTRA - HINGE_LID_ROOT_AXIAL_OVERLAP

    # Sweep the new support-root cross-section against the relieved body wall.
    # This is the representative Y region occupied by both lid knuckles; the
    # 0.15 mm axial stop above keeps the roots out of the full-height end wall.
    root_closed = [
        (HINGE_LID_SUPPORT_X, BODY_H + FINGER_RELIEF_H),
        (HINGE_LID_FRAME_NOTCH_X + 0.05, BODY_H + FINGER_RELIEF_H),
        (HINGE_LID_FRAME_NOTCH_X + 0.05, BODY_H + LID_H),
        (HINGE_LID_SUPPORT_X, BODY_H + LID_H),
    ]
    body_relief_wall = [
        (-BODY_W / 2, 0.0),
        (-BODY_W / 2 + BODY_WALL, 0.0),
        (-BODY_W / 2 + BODY_WALL, HINGE_BODY_RELIEF_TOP),
        (-BODY_W / 2, HINGE_BODY_RELIEF_TOP),
    ]

    def rotated_lid_section(loop: Sequence[Vec2], angle_deg: float) -> list[Vec2]:
        angle = math.radians(-angle_deg)
        ca, sa = math.cos(angle), math.sin(angle)
        axis_z = BODY_H + HINGE_Z_LOCAL
        result = []
        for x, z in loop:
            dx, dz = x - HINGE_X, z - axis_z
            result.append((HINGE_X + dx * ca + dz * sa, axis_z - dx * sa + dz * ca))
        return result

    def polygons_overlap_strict(a: Sequence[Vec2], b: Sequence[Vec2]) -> bool:
        axes: list[Vec2] = []
        for loop in (a, b):
            for index in range(len(loop)):
                p, q = loop[index], loop[(index + 1) % len(loop)]
                dx, dz = q[0] - p[0], q[1] - p[1]
                length = math.hypot(dx, dz)
                axes.append((-dz / length, dx / length))
        for ux, uz in axes:
            pa = [x * ux + z * uz for x, z in a]
            pb = [x * ux + z * uz for x, z in b]
            if max(pa) <= min(pb) + 1e-9 or max(pb) <= min(pa) + 1e-9:
                return False
        return True

    root_sweep_step = 0.5
    root_sweep_angles = [root_sweep_step * index for index in range(int(120 / root_sweep_step) + 1)]
    root_sweep_collision_free = not any(
        polygons_overlap_strict(rotated_lid_section(root_closed, angle), body_relief_wall)
        for angle in root_sweep_angles
    )

    checks = {
        "hinge_body_knuckle_radial_clearance_mm": round(hinge_body_clear, 3),
        "hinge_lid_knuckle_radial_clearance_mm": round(hinge_lid_clear, 3),
        "hinge_sweep_checked_deg": [0, 120],
        "hinge_axial_gap_between_knuckles_mm": HINGE_GAP,
        "hinge_profile": "pointed outer underside and 45-degree teardrop bore roof",
        "hinge_outer_lower_run_over_rise": round(outer_lower_run_over_rise, 3),
        "hinge_bore_roof_run_over_rise": bore_roof_run_over_rise,
        "body_hinge_nominal_core_diameter_mm": round(2 * HINGE_BODY_BORE_R, 3),
        "lid_hinge_nominal_core_diameter_mm": round(2 * HINGE_LID_BORE_R, 3),
        "body_hinge_min_inscribed_radius_mm": round(body_bore_min_radius, 3),
        "lid_hinge_min_inscribed_radius_mm": round(lid_bore_min_radius, 3),
        "body_hinge_pin_min_radial_clearance_mm": round(body_bore_pin_clearance, 3),
        "lid_hinge_pin_min_radial_clearance_mm": round(lid_bore_pin_clearance, 3),
        "body_attachment_to_bore_clearance_mm": round(body_attachment_to_bore, 3),
        "lid_attachment_to_bore_x_clearance_mm": round(lid_attachment_to_bore_x, 3),
        "lid_attachment_to_bore_z_clearance_mm": round(lid_attachment_to_bore_z, 3),
        "lid_knuckle_root_overlap_mm": round(lid_support_overlap, 3),
        "lid_knuckle_first_print_height_mm": round(lid_knuckle_first_print_z, 3),
        "bed_supported_lid_root_height_mm": round(lid_support_print_height, 3),
        "supported_height_above_knuckle_start_mm": round(lid_support_above_knuckle_start, 3),
        "lid_root_overlap_beyond_each_knuckle_end_mm": HINGE_LID_ROOT_AXIAL_OVERLAP,
        "lid_root_to_body_knuckle_axial_clearance_mm": round(lid_root_to_body_knuckle_axial_clearance, 3),
        "lid_root_to_body_end_wall_axial_clearance_mm": round(lid_root_to_body_end_wall_axial_clearance, 3),
        "lid_root_sweep_checked_deg": [0, 120],
        "lid_root_sweep_sample_step_deg": root_sweep_step,
        "lid_root_body_collision_free": root_sweep_collision_free,
        "pane_loading_channel_width_mm": PANE_CHANNEL_W,
        "pane_clear_channel_height_mm": round(pane_channel_h, 3),
        "pane_top_capture_opening_mm": PANE_TOP_OPENING_W,
        "pane_bottom_capture_opening_mm": PANE_BOTTOM_OPENING_W,
        "pane_top_overlap_per_side_at_24_9_mm_mm": round(top_overlap_measured, 3),
        "pane_bottom_overlap_per_side_at_24_9_mm_mm": round(bottom_overlap_measured, 3),
        "pane_axial_clearance_at_76_3_mm_mm": round(pane_axial_clearance, 3),
        "pane_lateral_clearance_at_26_3_mm_mm": round(pane_lateral_clearance, 3),
        "opposite_ledge_functional_overhang_mm": round(opposite_ledge_overhang, 3),
        "pane_tongue_free_length_mm": round(pane_tongue_free_length, 3),
        "pane_tongue_thickness_mm": PANE_TONGUE_H,
        "pane_finger_pad_lateral_clearance_mm": round(pane_finger_pad_lateral_clearance, 3),
        "pane_tongue_lateral_clearance_mm": round(pane_tongue_lateral_clearance, 3),
        "pane_tongue_relaxed_face_clearance_mm": round(pane_tongue_relaxed_gap, 3),
        "pane_tongue_simple_beam_strain_estimate": round(pane_tongue_strain, 4),
        "pane_capture_material": "PETG",
        "label_zone_fully_supported": label_zone_fully_supported,
        "fingernail_relief_mm": [FINGER_RELIEF_W, FINGER_RELIEF_DEPTH, FINGER_RELIEF_H],
        "fingernail_roof_thickness_mm": round(finger_roof, 3),
        "fingernail_relief_to_latch_clearance_mm": round(latch_clear, 3),
        "future_3_by_2_array_with_0_4_gaps_mm": [round(array_w, 3), round(array_d, 3)],
    }
    assert hinge_body_clear >= 0.25 - 1e-9
    assert hinge_lid_clear >= 0.25 - 1e-9
    assert outer_lower_run_over_rise <= 1.0
    assert bore_roof_run_over_rise <= 1.0
    assert body_bore_pin_clearance >= 0.22
    assert lid_bore_pin_clearance >= 0.15
    assert body_attachment_to_bore >= 0.15 - 1e-9
    assert lid_attachment_to_bore_x >= 0.15 - 1e-9
    assert lid_attachment_to_bore_z >= 0.15 - 1e-9
    assert lid_support_overlap >= 0.20 - 1e-9
    assert 0.0 <= lid_knuckle_first_print_z < lid_support_print_height
    assert lid_support_above_knuckle_start >= 1.20
    assert lid_root_to_body_knuckle_axial_clearance >= 0.65
    assert lid_root_to_body_end_wall_axial_clearance >= 0.15 - 1e-9
    assert root_sweep_collision_free
    assert abs(pane_channel_h - 1.40) < 1e-9
    assert top_overlap_measured >= 0.90
    assert bottom_overlap_measured >= 0.40
    assert pane_axial_clearance >= 0.50
    assert pane_lateral_clearance >= 0.60
    assert opposite_ledge_overhang <= 1.50 + 1e-9
    assert abs(pane_tongue_free_length - 6.75) < 1e-9
    assert pane_finger_pad_lateral_clearance >= 0.45
    assert pane_tongue_lateral_clearance >= 0.45
    assert pane_tongue_relaxed_gap >= 0.0 - 1e-9
    assert label_zone_fully_supported
    assert finger_roof >= 1.60
    assert latch_clear >= 0.80
    assert array_w <= 120.30 and array_d <= 162.30
    return checks


def render_preview(path: Path, body: Mesh, lid_local: Mesh) -> None:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(13.2, 7.4), dpi=160)
    fig.patch.set_facecolor("#f4f1ea")
    axes = [fig.add_subplot(1, 2, 1, projection="3d"), fig.add_subplot(1, 2, 2, projection="3d")]

    def add_mesh(ax, mesh: Mesh, color: str, alpha: float = 1.0, edge: str = "#24313a") -> None:
        poly = Poly3DCollection(mesh.triangles, facecolor=color, edgecolor=edge, linewidth=0.08, alpha=alpha)
        ax.add_collection3d(poly)

    def glass_mesh(z0: float) -> Mesh:
        return box(
            "glass_reference",
            POCKET_X - MAX_GLASS_W / 2,
            POCKET_X + MAX_GLASS_W / 2,
            -MAX_GLASS_D / 2,
            MAX_GLASS_D / 2,
            z0,
            z0 + MAX_GLASS_T,
        )

    # Closed prototype, with a translucent reference slide.
    ax = axes[0]
    add_mesh(ax, body, "#d7dadc")
    add_mesh(ax, lid_local.translated(0, 0, BODY_H), "#9aa5ae")
    add_mesh(ax, glass_mesh(BODY_H + PANE_CHANNEL_Z0), "#78d6ea", 0.42, "#16778b")
    # Paper label reference only.  The perimeter is also drawn explicitly
    # because Matplotlib's 3D transparency sorter can otherwise hide a thin
    # coplanar patch.
    label = box(
        "label_reference",
        LABEL_X - LABEL_W / 2,
        LABEL_X + LABEL_W / 2,
        LABEL_Y - LABEL_D / 2,
        LABEL_Y + LABEL_D / 2,
        BODY_H + LID_H + 0.35,
        BODY_H + LID_H + 0.65,
    )
    add_mesh(ax, label, "#f3df66", 0.97, "#8f7b20")
    label_xs = [LABEL_X - LABEL_W / 2, LABEL_X + LABEL_W / 2, LABEL_X + LABEL_W / 2, LABEL_X - LABEL_W / 2, LABEL_X - LABEL_W / 2]
    label_ys = [LABEL_Y - LABEL_D / 2, LABEL_Y - LABEL_D / 2, LABEL_Y + LABEL_D / 2, LABEL_Y + LABEL_D / 2, LABEL_Y - LABEL_D / 2]
    ax.plot(label_xs, label_ys, [BODY_H + LID_H + 0.72] * 5, color="#d7a900", linewidth=2.4)
    ax.set_title("Closed cassette · 9 mm label zone outlined in yellow", pad=12, fontsize=10.5)
    ax.set_xlim(-26, 26)
    ax.set_ylim(-45, 45)
    ax.set_zlim(0, 39)

    # Exploded view: body, pane, and the end-loaded lid; no loose retainer.
    ax = axes[1]
    add_mesh(ax, body, "#d7dadc")
    add_mesh(ax, glass_mesh(BODY_H + 12.0), "#78d6ea", 0.48, "#16778b")
    add_mesh(ax, lid_local.translated(0, 0, BODY_H + 17.0), "#9aa5ae")
    ax.set_title("Exploded assembly · pane end-loads without a loose retainer", pad=12, fontsize=10.5)
    ax.set_xlim(-26, 26)
    ax.set_ylim(-45, 45)
    ax.set_zlim(0, 54)

    for ax in axes:
        ax.view_init(elev=27, azim=53)
        ax.set_box_aspect((52, 90, 55))
        ax.set_xlabel("X (mm)", labelpad=5)
        ax.set_ylabel("Y (mm)", labelpad=5)
        ax.set_zlabel("Z (mm)", labelpad=4)
        ax.grid(False)
        ax.set_facecolor("#f4f1ea")
    fig.suptitle(f"Glass-slide small-parts cassette · prototype v{VERSION}", fontsize=15, fontweight="bold", y=0.97)
    fig.text(
        0.5,
        0.025,
        f"Body {BODY_W} × {BODY_D} × {BODY_H} mm · closed height {BODY_H + LID_H} mm · accepts measured slides up to {MAX_GLASS_W} × {MAX_GLASS_D} × {MAX_GLASS_T} mm",
        ha="center",
        fontsize=9.5,
        color="#37444d",
    )
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.08, top=0.90, wspace=0.03)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def render_top_plan(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    fig, ax = plt.subplots(figsize=(7.4, 11.0), dpi=165)
    fig.patch.set_facecolor("#f7f5ef")
    ax.set_facecolor("#f7f5ef")

    body_loop = chamfer_rect(BODY_W, BODY_D, BODY_CORNER)
    lid_loop = lid_outer_loop(finger_notched=False)
    pocket_loop = chamfer_rect(POCKET_W, POCKET_D, 0.55, POCKET_X, POCKET_Y)
    window_loop = chamfer_rect(WINDOW_W, WINDOW_D, 0.80, WINDOW_X, WINDOW_Y)

    ax.add_patch(Polygon(body_loop, closed=True, facecolor="#dfe3e5", edgecolor="#4b5963", linewidth=1.4))
    ax.add_patch(Polygon(lid_loop, closed=True, fill=False, edgecolor="#26343d", linewidth=2.0))
    ax.add_patch(Polygon(pocket_loop, closed=True, fill=False, edgecolor="#2998ad", linewidth=1.1, linestyle="--"))
    ax.add_patch(Polygon(window_loop, closed=True, facecolor="#8cdeed", edgecolor="#16778b", linewidth=1.4, alpha=0.72))
    ax.add_patch(
        Rectangle(
            (LABEL_X - LABEL_W / 2, LABEL_Y - LABEL_D / 2),
            LABEL_W,
            LABEL_D,
            facecolor="#f3df66",
            edgecolor="#9a7c00",
            linewidth=1.6,
        )
    )

    # Top-view hinge envelope and alternating knuckles.
    for y0, y1, color in [
        (-HINGE_LID_END, HINGE_BODY_Y0 - HINGE_GAP, "#7c8992"),
        (HINGE_BODY_Y0, HINGE_BODY_Y1, "#55636d"),
        (HINGE_BODY_Y1 + HINGE_GAP, HINGE_LID_END, "#7c8992"),
    ]:
        ax.add_patch(Rectangle((HINGE_X - HINGE_OUTER_HALF_W, y0), 2 * HINGE_OUTER_HALF_W, y1 - y0, facecolor=color, edgecolor="#26343d", linewidth=0.8))

    ax.text(LABEL_X, LABEL_Y, "9 mm TZe\n34 × 10", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#493d00")
    ax.text(WINDOW_X, WINDOW_Y, "23 × 58.5\nclear window", ha="center", va="center", fontsize=10, color="#0e6170")
    ax.annotate("76.8 × 27 glass pocket", xy=(POCKET_X + POCKET_W / 2, -31), xytext=(27.5, -24), arrowprops=dict(arrowstyle="->", lw=1.0), fontsize=9, rotation=90, va="center")
    ax.annotate("peaked filament-pin hinge", xy=(HINGE_X - 1.2, 0), xytext=(-27.0, 0), arrowprops=dict(arrowstyle="->", lw=1.0), fontsize=9, rotation=90, va="center")

    # Overall dimensions.
    ax.annotate("", xy=(-20.25, -44), xytext=(19.3, -44), arrowprops=dict(arrowstyle="<->", lw=1.2))
    ax.text(-0.475, -46.3, "39.55 mm hinge envelope", ha="center", va="top", fontsize=9.5)
    ax.annotate("", xy=(24.0, -40), xytext=(24.0, 40), arrowprops=dict(arrowstyle="<->", lw=1.2))
    ax.text(25.5, 0, "80.0 mm", rotation=90, ha="left", va="center", fontsize=9.5)

    ax.set_title("Cassette v0.6 · exact top plan", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlim(-30, 32)
    ax.set_ylim(-49, 46)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def render_section(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    fig, ax = plt.subplots(figsize=(11.5, 5.6), dpi=170)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Not-to-scale-freehand is avoided: every patch below uses modelled X/Z.
    px0, px1 = POCKET_X - POCKET_W / 2, POCKET_X + POCKET_W / 2
    wx0, wx1 = WINDOW_X - WINDOW_W / 2, WINDOW_X + WINDOW_W / 2
    ox0, ox1 = HINGE_LID_RELIEF_X, BODY_W / 2
    fx1 = ox1 - FINGER_RELIEF_DEPTH
    groove_x0 = px0 - SNAP_GROOVE_DEPTH
    groove_x1 = px1 + SNAP_GROOVE_DEPTH
    z_base = BODY_H
    # Body wall/floor section at Y=0.
    ax.add_patch(Rectangle((-BODY_W / 2, 0), BODY_W, BODY_BOTTOM, facecolor="#d7dadc", edgecolor="#25313a"))
    ax.add_patch(Rectangle((-BODY_W / 2, BODY_BOTTOM), BODY_WALL, HINGE_BODY_SUPPORT_TOP - BODY_BOTTOM, facecolor="#d7dadc", edgecolor="#25313a"))
    ax.add_patch(Rectangle((BODY_W / 2 - BODY_WALL, BODY_BOTTOM), BODY_WALL, BODY_H - BODY_BOTTOM, facecolor="#d7dadc", edgecolor="#25313a"))
    # Lid frame section at Y=0, including the centre-knuckle notch, the snap
    # groove, and the latch-edge fingernail recess.
    lid_poly_left = [
        (ox0, z_base),
        (px0, z_base),
        (px0, z_base + SNAP_GROOVE_Z0),
        (groove_x0, z_base + SNAP_GROOVE_Z0),
        (groove_x0, z_base + SNAP_GROOVE_Z1),
        (px0, z_base + SNAP_GROOVE_Z1),
        (px0, z_base + POCKET_DEPTH),
        (wx0, z_base + POCKET_DEPTH),
        (wx0, z_base + LID_H),
        (ox0, z_base + LID_H),
    ]
    lid_poly_right = [
        (wx1, z_base + LID_H),
        (wx1, z_base + POCKET_DEPTH),
        (px1, z_base + POCKET_DEPTH),
        (px1, z_base + SNAP_GROOVE_Z1),
        (groove_x1, z_base + SNAP_GROOVE_Z1),
        (groove_x1, z_base + SNAP_GROOVE_Z0),
        (px1, z_base + SNAP_GROOVE_Z0),
        (px1, z_base),
        (fx1, z_base),
        (fx1, z_base + FINGER_RELIEF_H),
        (ox1, z_base + FINGER_RELIEF_H),
        (ox1, z_base + LID_H),
    ]
    ax.add_patch(Polygon(lid_poly_left, closed=True, facecolor="#9aa5ae", edgecolor="#25313a"))
    ax.add_patch(Polygon(lid_poly_right, closed=True, facecolor="#9aa5ae", edgecolor="#25313a"))
    # Glass and retainer.
    gx0, gx1 = POCKET_X - MAX_GLASS_W / 2, POCKET_X + MAX_GLASS_W / 2
    glass_z0 = z_base + POCKET_DEPTH - MAX_GLASS_T
    ax.add_patch(Rectangle((gx0, glass_z0), MAX_GLASS_W, MAX_GLASS_T, facecolor="#8cdeed", edgecolor="#16778b", alpha=0.65))
    ax.add_patch(Rectangle((POCKET_X - RETAINER_W / 2, z_base + RETAINER_SEAT_FOR_MAX_GLASS), RETAINER_W, RETAINER_H, facecolor="#ef8a47", edgecolor="#8d3f16"))
    lug_z = z_base + RETAINER_SEAT_FOR_MAX_GLASS + SNAP_LUG_Z0
    lug_h = SNAP_LUG_Z1 - SNAP_LUG_Z0
    ax.add_patch(Rectangle((POCKET_X - POCKET_W / 2 - SNAP_INTERFERENCE, lug_z), SNAP_INTERFERENCE + (POCKET_W - RETAINER_W) / 2, lug_h, facecolor="#ef8a47", edgecolor="#8d3f16"))
    ax.add_patch(Rectangle((POCKET_X + RETAINER_W / 2, lug_z), SNAP_INTERFERENCE + (POCKET_W - RETAINER_W) / 2, lug_h, facecolor="#ef8a47", edgecolor="#8d3f16"))

    ax.annotate("23.0 mm clear aperture", xy=(WINDOW_X, z_base + LID_H + 0.2), xytext=(WINDOW_X, z_base + 7.2), ha="center", arrowprops=dict(arrowstyle="-[,widthB=5.7", lw=1.1), fontsize=9)
    ax.annotate("0.9 mm printed guard above glass", xy=(wx1 + 0.7, z_base + 2.75), xytext=(23.0, 32.5), arrowprops=dict(arrowstyle="->", lw=1.0), fontsize=9)
    ax.annotate("0.8 mm replaceable bezel", xy=(8.0, z_base + 0.4), xytext=(21.5, 22.0), arrowprops=dict(arrowstyle="->", lw=1.0), fontsize=9)
    ax.annotate("snap lugs captured in 0.35 mm groove", xy=(groove_x0 + 0.05, lug_z + 0.2), xytext=(-32.0, 20.0), arrowprops=dict(arrowstyle="->", lw=1.0), fontsize=8.6)
    ax.annotate("14 × 1.3 × 1.4 fingernail recess", xy=(fx1 + 0.35, z_base + 0.7), xytext=(20.5, 18.7), arrowprops=dict(arrowstyle="->", lw=1.0), fontsize=8.6)
    ax.annotate("2.0 mm body wall", xy=(18.3, 12.0), xytext=(24.0, 12.0), arrowprops=dict(arrowstyle="->", lw=1.0), fontsize=9)

    ax.set_title("Modelled cross-section at cassette centre (dimensions in mm)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlim(-34, 34)
    ax.set_ylim(-1, 35)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X")
    ax.set_ylabel("Z")
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def render_functional_details(path: Path) -> None:
    """Exact sectional views of the v0.6 functional clearances."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Polygon, Rectangle

    fig, axes = plt.subplots(2, 2, figsize=(12.4, 9.0), dpi=170)
    fig.patch.set_facecolor("#f7f5ef")
    plastic = "#a6b0b7"
    plastic_edge = "#27343d"
    accent = "#e77d35"
    clear = "#78d6ea"
    axis_z = BODY_H + HINGE_Z_LOCAL

    # Lid-knuckle station: the stepped lid attachment stays outside the bore,
    # while the body wall stays below the rotational keep-out.
    ax = axes[0, 0]
    ax.add_patch(Rectangle((-BODY_W / 2, 21.5), BODY_WALL, HINGE_BODY_RELIEF_TOP - 21.5, facecolor=plastic, edgecolor=plastic_edge))
    lid_attachment = [
        (HINGE_LID_FRAME_NOTCH_X, BODY_H),
        (POCKET_X - POCKET_W / 2, BODY_H),
        (POCKET_X - POCKET_W / 2, BODY_H + LID_H),
        (HINGE_LID_SUPPORT_X, BODY_H + LID_H),
        (HINGE_LID_SUPPORT_X, BODY_H + FINGER_RELIEF_H),
        (HINGE_LID_FRAME_NOTCH_X, BODY_H + FINGER_RELIEF_H),
    ]
    ax.add_patch(Polygon(lid_attachment, closed=True, facecolor=plastic, edgecolor=plastic_edge, alpha=0.82))
    lid_outer, lid_bore = hinge_profile_xz(HINGE_X, axis_z, -1.0, HINGE_LID_BORE_R)
    ax.add_patch(Polygon(lid_outer, closed=True, facecolor=plastic, edgecolor=plastic_edge, linewidth=1.5))
    ax.add_patch(Polygon(lid_bore, closed=True, facecolor="#f7f5ef", edgecolor=plastic_edge, linewidth=1.2))
    ax.text(HINGE_X, axis_z, "2.10 mm\nlid core", ha="center", va="center", fontsize=7.6)
    ax.add_patch(Circle((HINGE_X, axis_z), HINGE_KEEP_OUT_R, fill=False, edgecolor=accent, linewidth=0.8, linestyle="--", alpha=0.65))
    barrel_bottom = axis_z - HINGE_KEEP_OUT_R
    ax.annotate("", xy=(-20.75, barrel_bottom), xytext=(-20.75, HINGE_BODY_RELIEF_TOP), arrowprops=dict(arrowstyle="<->", color=accent, lw=1.7))
    ax.text(-21.0, (barrel_bottom + HINGE_BODY_RELIEF_TOP) / 2, "0.25", rotation=90, ha="right", va="center", color="#9a4515", fontweight="bold")
    ax.text(-18.1, 22.15, "relieved body wall", ha="center", fontsize=9)
    ax.text(-18.2, 27.55, "lid knuckle", ha="center", fontsize=9)
    ax.text(-14.5, 25.7, "stepped lid rail\nclears pin bore", ha="center", fontsize=8.5)
    ax.text(-19.25, 27.9, "0.20 mm root\noverlap", ha="center", fontsize=7.8, color="#9a4515", fontweight="bold")
    ax.set_title("A · Lid rail clears bore and body", fontweight="bold")
    ax.set_xlim(-21.8, -11.7)
    ax.set_ylim(21.5, 28.4)

    # Body-knuckle station: the entire lid rail is outside a concentric sweep
    # keep-out, even though the printed knuckle itself is not circular.
    ax = axes[0, 1]
    ax.add_patch(Rectangle((-BODY_W / 2, 21.5), BODY_WALL, HINGE_BODY_SUPPORT_TOP - 21.5, facecolor=plastic, edgecolor=plastic_edge))
    body_outer, body_bore = hinge_profile_xz(HINGE_X, axis_z, 1.0, HINGE_BODY_BORE_R)
    ax.add_patch(Polygon(body_outer, closed=True, facecolor=plastic, edgecolor=plastic_edge, linewidth=1.5))
    ax.add_patch(Polygon(body_bore, closed=True, facecolor="#f7f5ef", edgecolor=plastic_edge, linewidth=1.2))
    ax.text(HINGE_X, axis_z, "2.25 mm\nbody core", ha="center", va="center", fontsize=7.6)
    ax.add_patch(Circle((HINGE_X, axis_z), HINGE_KEEP_OUT_R, fill=False, edgecolor=accent, linewidth=0.8, linestyle="--", alpha=0.65))
    ax.add_patch(Rectangle((HINGE_LID_RELIEF_X, BODY_H), POCKET_X - POCKET_W / 2 - HINGE_LID_RELIEF_X, LID_H, facecolor=plastic, edgecolor=plastic_edge))
    barrel_right = HINGE_X + HINGE_KEEP_OUT_R
    ax.annotate("", xy=(HINGE_LID_RELIEF_X, axis_z), xytext=(barrel_right, axis_z), arrowprops=dict(arrowstyle="<->", color=accent, lw=1.7))
    ax.text((HINGE_LID_RELIEF_X + barrel_right) / 2, axis_z + 0.3, "0.25", ha="center", color="#9a4515", fontweight="bold")
    ax.text(-14.45, 27.45, "relieved lid rail", ha="center", fontsize=9)
    ax.text(-18.2, 22.0, "body support stops\nbelow pin bore", ha="center", fontsize=8.5)
    ax.text(-16.1, 28.05, "clearance is concentric: unchanged through 0–120° sweep", ha="center", fontsize=8.5)
    ax.set_title("B · Body support clears bore and lid", fontweight="bold")
    ax.set_xlim(-21.8, -11.7)
    ax.set_ylim(21.5, 28.4)

    # Pocket-wall groove and installed retainer lug, local lid coordinates.
    ax = axes[1, 0]
    px0 = POCKET_X - POCKET_W / 2
    gx0 = px0 - SNAP_GROOVE_DEPTH
    wall = [(-15.3, 0.0), (px0, 0.0), (px0, SNAP_GROOVE_Z0), (gx0, SNAP_GROOVE_Z0), (gx0, SNAP_GROOVE_Z1), (px0, SNAP_GROOVE_Z1), (px0, POCKET_DEPTH), (-15.3, POCKET_DEPTH)]
    ax.add_patch(Polygon(wall, closed=True, facecolor=plastic, edgecolor=plastic_edge))
    retainer_offset = RETAINER_SEAT_FOR_MAX_GLASS
    base_edge = POCKET_X - RETAINER_W / 2
    crest = px0 - SNAP_INTERFERENCE
    lug = [
        (base_edge + 0.12, retainer_offset + SNAP_LUG_Z0),
        (crest, retainer_offset + SNAP_LUG_Z0),
        (crest, retainer_offset + SNAP_LUG_Z0 + 0.20),
        (base_edge - 0.06, retainer_offset + SNAP_LUG_Z1),
        (base_edge + 0.12, retainer_offset + SNAP_LUG_Z1),
    ]
    ax.add_patch(Rectangle((base_edge, retainer_offset), 2.4, RETAINER_H, facecolor=accent, edgecolor="#8d3f16"))
    ax.add_patch(Polygon(lug, closed=True, facecolor=accent, edgecolor="#8d3f16"))
    ax.add_patch(Rectangle((px0, POCKET_DEPTH - MAX_GLASS_T), 2.2, MAX_GLASS_T, facecolor=clear, edgecolor="#16778b", alpha=0.65))
    ax.annotate("", xy=(px0, 1.47), xytext=(gx0, 1.47), arrowprops=dict(arrowstyle="<->", color=accent, lw=1.7))
    ax.text((px0 + gx0) / 2, 1.59, "0.35 groove", ha="center", color="#9a4515", fontweight="bold", fontsize=8.5)
    ax.text(-12.15, 0.46, "captured lug", ha="left", fontsize=9)
    ax.text(-14.95, 2.62, "0.20 entry interference · 0.15 seated clearance", ha="left", fontsize=8.5)
    ax.set_title("C · Positive glass-retainer snap", fontweight="bold")
    ax.set_xlim(-15.5, -10.4)
    ax.set_ylim(-0.05, 2.85)

    # Latch-edge opening aid, local lid coordinates.
    ax = axes[1, 1]
    finger_x = BODY_W / 2 - FINGER_RELIEF_DEPTH
    lid_section = [
        (14.0, 0.0),
        (finger_x, 0.0),
        (finger_x, FINGER_RELIEF_H),
        (BODY_W / 2, FINGER_RELIEF_H),
        (BODY_W / 2, LID_H),
        (14.0, LID_H),
    ]
    ax.add_patch(Polygon(lid_section, closed=True, facecolor=plastic, edgecolor=plastic_edge))
    ax.add_patch(Rectangle((BODY_W / 2 - BODY_WALL, -2.0), BODY_WALL, 2.0, facecolor="#d5dadd", edgecolor=plastic_edge))
    ax.add_patch(Rectangle((LATCH_TONGUE_X0, -1.55), LATCH_TONGUE_X1 - LATCH_TONGUE_X0, 2.0, facecolor="#75838c", edgecolor=plastic_edge))
    ax.add_patch(Rectangle((finger_x, 0.0), FINGER_RELIEF_DEPTH, FINGER_RELIEF_H, facecolor="#f7f5ef", edgecolor=accent, linestyle="--"))
    ax.annotate("", xy=(BODY_W / 2, 0.65), xytext=(finger_x, 0.65), arrowprops=dict(arrowstyle="<->", color=accent, lw=1.7))
    ax.text((BODY_W / 2 + finger_x) / 2, 0.82, "1.30", ha="center", color="#9a4515", fontweight="bold")
    ax.annotate("", xy=(19.75, FINGER_RELIEF_H), xytext=(19.75, 0.0), arrowprops=dict(arrowstyle="<->", color=accent, lw=1.7))
    ax.text(19.9, FINGER_RELIEF_H / 2, "1.40", rotation=90, va="center", color="#9a4515", fontweight="bold")
    ax.text(18.65, 2.25, "1.8 mm roof", ha="center", fontsize=9)
    ax.text(15.9, -1.82, "latch remains 0.95 mm inboard", ha="center", fontsize=8.5)
    ax.set_title("D · Fingernail opening relief", fontweight="bold")
    ax.set_xlim(13.8, 20.35)
    ax.set_ylim(-2.15, 3.55)

    for ax in axes.flat:
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.12)
        ax.set_facecolor("#f7f5ef")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Z (mm)")
    fig.suptitle("Cassette v0.6 · functional clearances and retention", fontsize=15, fontweight="bold", y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def render_lid_support_sections(path: Path, lid_print: Mesh) -> None:
    """Plot exact X/Z intersections through the generated lid STL mesh."""
    import matplotlib.pyplot as plt

    def section_segments(y_plane: float) -> list[tuple[Vec2, Vec2]]:
        segments: list[tuple[Vec2, Vec2]] = []
        for triangle in lid_print.triangles:
            intersections: list[Vec2] = []
            for i, j in ((0, 1), (1, 2), (2, 0)):
                a, b = triangle[i], triangle[j]
                if abs(a[1] - y_plane) < 1e-9 and abs(b[1] - y_plane) < 1e-9:
                    continue
                if (a[1] - y_plane) * (b[1] - y_plane) <= 0.0 and abs(b[1] - a[1]) > 1e-12:
                    t = (y_plane - a[1]) / (b[1] - a[1])
                    if -1e-9 <= t <= 1.0 + 1e-9:
                        point = (a[0] + t * (b[0] - a[0]), a[2] + t * (b[2] - a[2]))
                        if not any(math.hypot(point[0] - q[0], point[1] - q[1]) < 1e-7 for q in intersections):
                            intersections.append(point)
            if len(intersections) == 2:
                segments.append((intersections[0], intersections[1]))
        return segments

    stations = [15.0, 20.0, 25.0, 30.0, 36.0]
    fig, axes = plt.subplots(1, len(stations), figsize=(13.2, 3.6), dpi=180, sharex=True, sharey=True)
    fig.patch.set_facecolor("#f7f5ef")
    for axis, station in zip(axes, stations):
        axis.set_facecolor("#f7f5ef")
        for first, second in section_segments(station):
            axis.plot((first[0], second[0]), (first[1], second[1]), color="#33434c", linewidth=1.0)
        axis.axhline(0.0, color="#e77d35", linewidth=1.2)
        axis.set_title(f"Y = {station:g} mm", fontsize=9.5, fontweight="bold")
        axis.set_xlim(-20.7, -15.2)
        axis.set_ylim(-0.1, 6.7)
        axis.set_aspect("equal")
        axis.grid(alpha=0.22)
        axis.set_xlabel("X (mm)", fontsize=8.5)
    axes[0].set_ylabel("Print Z (mm)", fontsize=8.5)
    fig.suptitle(f"Cassette v{VERSION} · actual lid STL sections show the unchanged bed-supported hinge root", fontsize=12.5, fontweight="bold")
    fig.text(0.5, 0.02, "Orange line = build plate · root remains connected from Z = 0 through the first knuckle layer at Z = 0.55 mm", ha="center", fontsize=8.8, color="#37444d")
    fig.subplots_adjust(left=0.055, right=0.99, bottom=0.19, top=0.79, wspace=0.22)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def write_v07_preview_svg(path: Path) -> None:
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="980" height="520" viewBox="0 0 980 520">
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#333"/></marker></defs>
<rect width="100%" height="100%" fill="#f7f4ed"/><text x="28" y="34" font-family="sans-serif" font-size="21" font-weight="bold">Cassette v{VERSION} — end-loaded full lid</text>
<g transform="translate(48 72)" font-family="sans-serif"><text x="0" y="0" font-size="15" font-weight="bold">Top view</text><rect x="0" y="18" width="193" height="400" rx="11" fill="#d8d1c2" stroke="#222" stroke-width="2"/><rect x="42" y="62" width="115" height="292" fill="#9ed5e5" stroke="#174c5b" stroke-width="2"/><rect x="13" y="357" width="170" height="50" fill="#f3df66" stroke="#8f7b20"/><text x="64" y="387" font-size="13">34 × 10 label</text><rect x="66" y="18" width="60" height="35" fill="#e7a84f" stroke="#6d4610"/><rect x="77" y="48" width="38" height="10" fill="#b04b3f"/><line x1="96" y1="-2" x2="96" y2="42" stroke="#333" stroke-width="2" marker-end="url(#arrow)"/><text x="120" y="8" font-size="13">pane enters here</text><text x="52" y="445" font-size="13">Blue = installed glass</text></g>
<g transform="translate(310 78)" font-family="sans-serif"><text x="0" y="0" font-size="15" font-weight="bold">Capture cross-section</text><path d="M0 185 L0 0 L60 0 L60 48 L40 48 L40 142 L82 142 L82 185 Z" fill="#d8d1c2" stroke="#222" stroke-width="2"/><path d="M270 185 L270 0 L210 0 L210 48 L230 48 L230 142 L188 142 L188 185 Z" fill="#d8d1c2" stroke="#222" stroke-width="2"/><rect x="47" y="67" width="176" height="58" fill="#9ed5e5" stroke="#174c5b"/><text x="102" y="101" font-size="14">glass pane</text><text x="0" y="220" font-size="13">27.0 mm loading channel · 1.4 mm clear height</text><text x="0" y="246" font-size="13">23.0 mm top opening · 24.0 mm opposite opening</text><text x="0" y="272" font-size="13">0.95 / 0.45 mm overlap per side on 24.9 mm glass</text></g>
<g transform="translate(650 78)" font-family="sans-serif"><text x="0" y="0" font-size="15" font-weight="bold">Installed latch state</text><rect x="45" y="62" width="245" height="34" fill="#9ed5e5" stroke="#174c5b"/><path d="M28 145 L28 45 L45 45 L45 112 L37 112 L37 145 Z" fill="#b04b3f" stroke="#68251f"/><rect x="28" y="125" width="185" height="14" fill="#e7a84f" stroke="#6d4610"/><text x="80" y="165" font-size="13">6.75 mm PETG tongue</text><text x="58" y="116" font-size="12">0.20 mm relaxed gap</text><text x="0" y="205" font-size="13">Shoulder returns behind the pane end.</text><text x="0" y="231" font-size="13">It does not press on the glass face.</text><text x="0" y="275" font-size="15" font-weight="bold">Compatibility</text><text x="0" y="303" font-size="13">Reuse verified v0.5/v0.6 body.</text><text x="0" y="329" font-size="13">Reuse straight 1.75 mm hinge pin.</text><text x="0" y="355" font-size="13">Print lid top/label-face down.</text><text x="0" y="381" font-size="13">No internal slicer support.</text></g></svg>''')


def write_v07_capture_section_svg(path: Path) -> None:
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="920" height="360" viewBox="0 0 920 360">
<rect width="100%" height="100%" fill="#f7f4ed"/><text x="28" y="34" font-family="sans-serif" font-size="20" font-weight="bold">Cassette v{VERSION} — pane loading and positive end stop</text>
<g transform="translate(45 88)" font-family="sans-serif"><rect x="0" y="0" width="790" height="130" fill="#d8d1c2" stroke="#222" stroke-width="2"/><rect x="82" y="38" width="665" height="45" fill="#9ed5e5" stroke="#174c5b"/><rect x="62" y="27" width="20" height="70" fill="#b04b3f" stroke="#68251f"/><rect x="62" y="102" width="68" height="12" fill="#e7a84f" stroke="#6d4610"/><rect x="747" y="24" width="18" height="78" fill="#777"/><text x="53" y="-14" font-size="13">entry</text><text x="704" y="-14" font-size="13">far stop</text><text x="310" y="66" font-size="15">maximum intended pane 76.3 mm</text><line x1="82" y1="145" x2="747" y2="145" stroke="#333"/><text x="315" y="168" font-size="13">0.70 mm nominal axial clearance</text><text x="0" y="210" font-size="13">Depress tongue outward, slide pane under the label band to the far stop, then release.</text><text x="0" y="237" font-size="13">The red shoulder rises behind the trailing edge and blocks withdrawal geometrically.</text></g></svg>''')


def write_mesh_projection_svg(path: Path, mesh: Mesh) -> None:
    """Write a dependency-free isometric preview of the actual exported mesh."""
    def project(point: Vec3) -> Vec2:
        x, y, z = point
        return (0.82 * x - 0.34 * y, 0.24 * x + 0.46 * y - 2.6 * z)

    projected = [(triangle, [project(point) for point in triangle]) for triangle in mesh.triangles]
    xs = [point[0] for _, triangle in projected for point in triangle]
    ys = [point[1] for _, triangle in projected for point in triangle]
    width, height, margin = 920.0, 620.0, 35.0
    scale = min((width - 2 * margin) / (max(xs) - min(xs)), (height - 2 * margin) / (max(ys) - min(ys)))

    def screen(point: Vec2) -> Vec2:
        return (margin + (point[0] - min(xs)) * scale, margin + (point[1] - min(ys)) * scale)

    projected.sort(key=lambda item: sum(point[0] + point[1] + 0.5 * point[2] for point in item[0]) / 3)
    polygons = []
    for triangle, points in projected:
        normal = _normal(triangle)
        shade = int(max(125, min(225, 176 + 32 * normal[2] - 18 * normal[0])))
        coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in map(screen, points))
        polygons.append(f'<polygon points="{coords}" fill="rgb({shade},{shade + 5},{min(240, shade + 10)})" stroke="#38444b" stroke-width="0.35"/>')
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">'
        '<rect width="100%" height="100%" fill="#f7f4ed"/>'
        f'<text x="20" y="25" font-family="sans-serif" font-size="17" font-weight="bold">Actual exported lid mesh — v{VERSION} supplied print orientation</text>'
        + "".join(polygons)
        + '</svg>'
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "build", help="output directory")
    parser.add_argument("--preview", action="store_true", help="also render PNG previews (requires matplotlib)")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    body = build_body()
    body_divided = build_divided_body()
    lid_local = build_lid_local()
    lid_print = lid_print_orientation(lid_local)
    card_1_2 = build_divider_card(1.20)
    card_1_0 = build_divider_card(1.00)
    card_1_4 = build_divider_card(1.40)

    closed_lid = lid_local.translated(0.0, 0.0, BODY_H, "closed_lid")
    glass_local = box(
        "glass_reference",
        POCKET_X - MAX_GLASS_W / 2,
        POCKET_X + MAX_GLASS_W / 2,
        PANE_FAR_STOP_Y - MAX_GLASS_D,
        PANE_FAR_STOP_Y,
        PANE_CHANNEL_Z0,
        PANE_CHANNEL_Z0 + MAX_GLASS_T,
    )
    installed_glass = glass_local.translated(0.0, 0.0, BODY_H, "installed_glass")
    closed_reference = combine("REFERENCE_closed_assembly_DO_NOT_PRINT", [body, closed_lid, installed_glass])
    open_lid = rotate_about_hinge_open(lid_local, -108.0)

    files: list[tuple[str, Mesh]] = [
        (f"cassette_body_{VERSION_TAG}_divided.stl", body_divided),
        (f"cassette_body_{VERSION_TAG}.stl", body),
        (f"cassette_lid_{VERSION_TAG}_print.stl", lid_print),
        ("divider_card_1_2mm.stl", card_1_2),
        ("divider_card_1_0mm.stl", card_1_0),
        ("divider_card_1_4mm.stl", card_1_4),
        ("REFERENCE_closed_assembly_DO_NOT_PRINT.stl", closed_reference),
    ]
    for filename, mesh in files:
        write_binary_stl(args.out / filename, mesh)

    write_obj(
        args.out / f"cassette_assembly_reference_{VERSION_TAG}.obj",
        [
            ("body", body),
            ("lid_open_108deg", open_lid),
            ("glass_reference_separated", glass_local.translated(0.0, 0.0, BODY_H + 9.0)),
        ],
    )

    manifest = {
        "design": "Glass-slide small-parts cassette",
        "version": VERSION,
        "units": "mm",
        "nominal_body_mm": [BODY_W, BODY_D, BODY_H],
        "closed_height_mm": BODY_H + LID_H,
        "maximum_printed_envelope_mm": [round(BODY_W / 2 - (HINGE_X - HINGE_OUTER_HALF_W), 3), BODY_D, BODY_H + LID_H],
        "maximum_intended_glass_mm": [MAX_GLASS_W, MAX_GLASS_D, MAX_GLASS_T],
        "pane_channel_mm": [PANE_CHANNEL_W, PANE_FAR_STOP_Y - PANE_SHOULDER_Y1, PANE_CHANNEL_Z1 - PANE_CHANNEL_Z0],
        "clear_window_mm": [WINDOW_W, WINDOW_D],
        "label_zone_mm": [LABEL_W, LABEL_D],
        "functional_validation": validate_design(),
        "hinge_pin": "1.75 mm printer filament, cut 75 mm; body core 2.25 mm, lid cores 2.10 mm, all with 45-degree teardrop roofs",
        "hinge_attachment_note": "Lid rail clears its 2.10 mm bore by 0.15 mm in X and Z, and its bed-supported root overlaps the hinge axis by 0.20 mm across both lid-knuckle spans; body centre support stops 0.15 mm below the 2.25 mm bore.",
        "recommended_material": "PETG required for the integral pane latch; verified v0.5/v0.6 body remains reusable",
        "pane_capture_note": "End-loaded 27.0 x 1.4 mm channel with 23.0/24.0 mm capture openings and a 6.75 mm integral PETG tongue. The shoulder returns behind the pane end and does not press on the glass face.",
        "physical_retention_status": "Coupon v0.4 works physically. Full-lid v0.7 integration remains unverified.",
        "mesh_note": "Individual closed shells intentionally overlap at hinge/latch joins; modern slicers merge overlapping volumes.",
        "files": [],
    }
    for filename, mesh in files:
        record = mesh_record(mesh, filename)
        record["exported_stl_audit"] = audit_exported_stl(args.out / filename)
        if filename == f"cassette_lid_{VERSION_TAG}_print.stl":
            connectivity = shell_overlap_connectivity(mesh)
            record["shell_overlap_connectivity"] = connectivity
            assert connectivity["positive_aabb_overlap_graph_connected"]
        manifest["files"].append(record)

    with (args.out / f"manifest_{VERSION_TAG}.json").open("w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    if args.preview:
        write_v07_preview_svg(args.out / f"cassette_preview_{VERSION_TAG}.svg")
        write_v07_capture_section_svg(args.out / f"cassette_capture_section_{VERSION_TAG}.svg")
        write_mesh_projection_svg(args.out / f"cassette_lid_mesh_preview_{VERSION_TAG}.svg", lid_print)

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
