#!/usr/bin/env python3
"""Generate rapid test inserts for carrier trays to physically evaluate push-to-tilt rocker ergonomics."""

from __future__ import annotations

import argparse
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

V = tuple[float, float, float]
T = tuple[V, V, V]


@dataclass
class Mesh:
    name: str
    triangles: list[T]

    def __init__(self, name: str = "mesh"):
        self.name = name
        self.triangles = []

    def tri(self, a: V, b: V, c: V) -> None:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        if nx * nx + ny * ny + nz * nz > 1e-18:
            self.triangles.append((a, b, c))

    def quad(self, a: V, b: V, c: V, d: V) -> None:
        self.tri(a, b, c)
        self.tri(a, c, d)

    def extend(self, other: Mesh) -> None:
        self.triangles.extend(other.triangles)

    def bounds(self) -> tuple[V, V]:
        xs = [p[0] for t in self.triangles for p in t]
        ys = [p[1] for t in self.triangles for p in t]
        zs = [p[2] for t in self.triangles for p in t]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def prism_x(name: str, profile_yz: Sequence[tuple[float, float]], x0: float, x1: float) -> Mesh:
    m = Mesh(name)
    n = len(profile_yz)
    # End caps at x0 (-X) and x1 (+X)
    for i in range(1, n - 1):
        m.tri((x0, profile_yz[0][0], profile_yz[0][1]),
              (x0, profile_yz[i + 1][0], profile_yz[i + 1][1]),
              (x0, profile_yz[i][0], profile_yz[i][1]))
        m.tri((x1, profile_yz[0][0], profile_yz[0][1]),
              (x1, profile_yz[i][0], profile_yz[i][1]),
              (x1, profile_yz[i + 1][0], profile_yz[i + 1][1]))
    # Side faces
    for i in range(n):
        j = (i + 1) % n
        y0, z0 = profile_yz[i]
        y1, z1 = profile_yz[j]
        m.quad((x0, y0, z0), (x1, y0, z0), (x1, y1, z1), (x0, y1, z1))
    return m


def build_single_slot_reversed_rocker_insert(width: float = 38.8, length: float = 79.6,
                                             shelf_h: float = 2.0, push_zone_len: float = 28.0) -> Mesh:
    """Build a 1-slot reversed rocker insert: push outer end down -> center end pops UP."""
    hx = width / 2.0
    y_min = -length / 2.0
    y_max = length / 2.0
    fulcrum_y = y_min + push_zone_len  # e.g. -39.8 + 28.0 = -11.8 mm

    # Profile in (Y, Z):
    # Outer push pocket: y_min to fulcrum_y slopes from Z = 0.20 to shelf_h
    # Center lift shelf: fulcrum_y to y_max is flat at Z = shelf_h
    profile_yz = [
        (y_min, 0.0),
        (y_max, 0.0),
        (y_max, shelf_h),
        (fulcrum_y, shelf_h),
        (y_min, 0.20),
    ]
    return prism_x("rocker_insert_single_slot_reversed", profile_yz, -hx, hx)


def build_dual_slot_reversed_rocker_insert(width: float = 38.8, total_length: float = 160.0,
                                           shelf_h: float = 2.0, push_zone_len: float = 28.0) -> Mesh:
    """Build a 2-slot back-to-back reversed rocker insert: push outer ends -> center pops UP."""
    hx = width / 2.0
    half_l = total_length / 2.0
    f1 = -half_l + push_zone_len  # -80 + 28 = -52 mm (front fulcrum)
    f2 = half_l - push_zone_len   # +80 - 28 = +52 mm (rear fulcrum)

    # Profile in (Y, Z):
    # Front push pocket: -half_l (Z=0.2) to f1 (Z=shelf_h)
    # Center resting bridge: f1 to f2 (Z=shelf_h) flat resting shelf
    # Rear push pocket: f2 (Z=shelf_h) to half_l (Z=0.2)
    profile_yz = [
        (-half_l, 0.0),
        (half_l, 0.0),
        (half_l, 0.20),
        (f2, shelf_h),
        (f1, shelf_h),
        (-half_l, 0.20),
    ]
    return prism_x("rocker_insert_dual_slot_reversed", profile_yz, -hx, hx)


def save_binary_stl(mesh: Mesh, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        header = f"Rocker Insert {mesh.name}".encode("utf-8")[:80].ljust(80, b"\0")
        f.write(header)
        f.write(struct.pack("<I", len(mesh.triangles)))
        for a, b, c in mesh.triangles:
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            if ln > 1e-12:
                nx, ny, nz = nx / ln, ny / ln, nz / ln
            else:
                nx, ny, nz = 0.0, 0.0, 1.0
            f.write(struct.pack("<fff", nx, ny, nz))
            f.write(struct.pack("<fff", *a))
            f.write(struct.pack("<fff", *b))
            f.write(struct.pack("<fff", *c))
            f.write(struct.pack("<H", 0))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate push-to-tilt rocker test inserts.")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "build")
    args = parser.parse_args()

    single_rev = build_single_slot_reversed_rocker_insert()
    dual_rev = build_dual_slot_reversed_rocker_insert()

    save_binary_stl(single_rev, args.out / "rocker_insert_single_slot_reversed.stl")
    save_binary_stl(dual_rev, args.out / "rocker_insert_dual_slot_reversed.stl")

    print(f"Generated single-slot reversed rocker insert: {args.out / 'rocker_insert_single_slot_reversed.stl'}")
    print(f"Generated dual-slot reversed rocker insert: {args.out / 'rocker_insert_dual_slot_reversed.stl'}")


if __name__ == "__main__":
    main()
