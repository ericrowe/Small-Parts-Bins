#!/usr/bin/env python3
"""Generate experimental sliding pull tab prototype models for the 40x80 cassette.

This script creates an experimental sliding pull tab variant that extends vertically
upon lifting to provide an elongated finger handle and retracts flush under gravity
when released.

The canonical baseline cassette models (generate_cassette.py) remain unchanged.
"""

from __future__ import annotations
import argparse
from pathlib import Path
import math

from generate_cassette import (
    Mesh, box, prism, prism_y, chamfer_rect, clip_polygon_y, combine, write_binary_stl, write_obj,
    BODY_W, BODY_D, BODY_H, BODY_BOTTOM, BODY_WALL, BODY_CORNER,
    HINGE_BODY_RELIEF_TOP, HINGE_RELIEF_Y0, HINGE_RELIEF_Y1,
    HINGE_BODY_END_RELIEF_Y0, HINGE_BODY_END_RELIEF_Y1, HINGE_BODY_SUPPORT_TOP,
    HINGE_X, HINGE_BODY_Y0, HINGE_BODY_Y1, HINGE_BODY_BORE_R, HINGE_Z_LOCAL,
    peaked_hinge_y, build_lid_local, lid_print_orientation, build_divider_card
)

PROTOTYPE_DIR = Path(__file__).resolve().parent / "build"


def build_sliding_boss_keyway(name_prefix: str) -> Mesh:
    """Build the full-height internal sliding track boss with top retaining stop collar."""
    m = Mesh(f"{name_prefix}_sliding_keyway_boss")
    z_floor = 3.00
    z_stop = 27.50
    z_top = BODY_H
    join = 0.05

    # 1. 45° Lead-in under-shelf taper (Z in [1.50, 3.00 mm]):
    under_shelf_xz = [
        (14.80, z_floor + join),
        (17.30 + join, z_floor + join),
        (17.30 + join, 1.50),
    ]
    m.extend(prism_y(f"{name_prefix}_under_shelf", under_shelf_xz, 15.00, 28.00))

    # 2. Solid 1.50 mm outer back wall (X in [17.80, 19.30 mm]) from floor to top:
    m.extend(box(f"{name_prefix}_back_wall", 17.80 - join, 19.30, 15.00, 28.00, z_floor, z_top))

    # 3. Solid lower sidewall flank with 45° lead-in chamfer (Y in [15.00, 17.50 mm]):
    m.extend(box(f"{name_prefix}_lower_sidewall", 14.80, 17.80 + join, 16.50 - join, 17.50 + join, z_floor, z_top))
    chamfer_lower = [(17.30, 15.00), (14.80, 16.50), (17.80, 16.50), (17.80, 15.00)]
    m.extend(prism(f"{name_prefix}_lower_chamfer", chamfer_lower, z_floor, z_top))

    # 4. Solid upper sidewall flank with 45° lead-in chamfer (Y in [25.50, 28.00 mm]):
    m.extend(box(f"{name_prefix}_upper_sidewall", 14.80, 17.80 + join, 25.50 - join, 26.50 + join, z_floor, z_top))
    chamfer_upper = [(14.80, 26.50), (17.30, 28.00), (17.80, 28.00), (17.80, 26.50)]
    m.extend(prism(f"{name_prefix}_upper_chamfer", chamfer_upper, z_floor, z_top))

    # 5. Continuous front retaining lips (X in [14.80, 15.80 mm]):
    lip_lower = [(14.80, 17.50), (14.80, 18.50), (15.80, 17.50)]
    lip_upper = [(14.80, 25.50), (15.80, 25.50), (14.80, 24.50)]
    m.extend(prism(f"{name_prefix}_lip_lower", lip_lower, z_floor, z_top))
    m.extend(prism(f"{name_prefix}_lip_upper", lip_upper, z_floor, z_top))

    # 6. Top Stop Internal Catch Lugs (narrowing internal base from 8.00 to 6.80 mm at top collar):
    lug_lower = [(15.80, 17.50), (17.80, 17.50), (17.80, 18.20), (15.80, 18.20)]
    lug_upper = [(15.80, 24.80), (17.80, 24.80), (17.80, 25.50), (15.80, 25.50)]
    m.extend(prism(f"{name_prefix}_top_stop_lower", lug_lower, z_stop, z_top))
    m.extend(prism(f"{name_prefix}_top_stop_upper", lug_upper, z_stop, z_top))
    return m


def build_prototype_body_divided() -> Mesh:
    """Build the divided cassette body with the full-height internal sliding track."""
    out = Mesh("prototype_body_divided_sliding_tab")
    hx = BODY_W / 2
    hy = BODY_D / 2
    c = BODY_CORNER
    relief_top = HINGE_BODY_RELIEF_TOP
    lx = -15.00
    rx = 17.30
    iy = 38.00
    slot_w = 1.40
    slot_recess_left = 1.20
    slot_recess_right = 0.60
    ridge_proj = 0.80
    ridge_w = 1.50
    floor_groove_d = 0.60
    slot_stations = [-12.87, 12.87]
    join = 0.05
    z_floor = BODY_BOTTOM - floor_groove_d

    # 1. Base floor slab:
    outer = chamfer_rect(BODY_W, BODY_D, BODY_CORNER)
    out.extend(prism("divided_base_floor", outer, 0.00, z_floor))

    # 2. Outer left wall:
    out.extend(box("divided_outer_left_wall", -hx, lx - slot_recess_left + join, -hy + c - join, hy - c + join, z_floor - join, relief_top + join))
    out.extend(box("divided_upper_left_centre", -hx, lx - slot_recess_left + join, HINGE_RELIEF_Y0, HINGE_RELIEF_Y1, relief_top, HINGE_BODY_SUPPORT_TOP))
    out.extend(box("divided_upper_left_lower_end", -hx, lx - slot_recess_left + join, -hy + c - join, HINGE_BODY_END_RELIEF_Y0, relief_top, BODY_H))
    out.extend(box("divided_upper_left_upper_end", -hx, lx - slot_recess_left + join, HINGE_BODY_END_RELIEF_Y1, hy - c + join, relief_top, BODY_H))

    # 3. Outer right wall: split around keyway boss at Y in [15.00, 28.00 mm]
    out.extend(box("div_outer_right_lower", rx + slot_recess_right - join, hx, -hy + c - join, 15.00 + join, z_floor - join, BODY_H))
    out.extend(box("div_outer_right_upper", rx + slot_recess_right - join, hx, 28.00 - join, hy - c + join, z_floor - join, BODY_H))
    out.extend(box("div_outer_right_boss_sub", rx + slot_recess_right - join, hx, 15.00 - join, 28.00 + join, z_floor - join, 3.00 + join))

    # 4. Front & Back walls:
    out.extend(box("divided_front_wall", -hx + c - join, hx - c + join, -hy, -iy + join, z_floor - join, BODY_H))
    out.extend(box("divided_back_wall", -hx + c - join, hx - c + join, iy - join, hy, z_floor - join, BODY_H))

    # 5. Outer corner chamfers
    lower_right = [outer[1], outer[2], (hx - c, -hy + c)]
    upper_right = [outer[3], outer[4], (hx - c, hy - c)]
    lower_left = [outer[7], outer[0], (-hx + c, -hy + c)]
    upper_left = [outer[5], outer[6], (-hx + c, hy - c)]
    out.extend(prism("corner_lr", lower_right, z_floor - join, BODY_H))
    out.extend(prism("corner_ur", upper_right, z_floor - join, BODY_H))
    out.extend(prism("corner_ll", lower_left, z_floor - join, BODY_H))
    out.extend(prism("corner_ul", upper_left, z_floor - join, BODY_H))

    # 6. Between-slot cavity segments:
    y_points = [-iy]
    for cy in sorted(slot_stations):
        y_points.extend([cy - slot_w / 2, cy + slot_w / 2])
    y_points.append(iy)

    for idx in range(0, len(y_points) - 1, 2):
        y0, y1 = y_points[idx], y_points[idx + 1]
        out.extend(box(f"div_floor_{idx}", lx - join, rx + join, y0 - join, y1 + join, z_floor - join, BODY_BOTTOM + join))
        out.extend(box(f"div_left_wall_{idx}", lx - slot_recess_left - join, lx, y0 - join, y1 + join, z_floor - join, relief_top + join))
        if y1 <= HINGE_BODY_END_RELIEF_Y0 or y0 >= HINGE_BODY_END_RELIEF_Y1:
            out.extend(box(f"div_left_upper_end_{idx}", lx - slot_recess_left - join, lx, y0 - join, y1 + join, relief_top, BODY_H))
        elif y0 >= HINGE_RELIEF_Y0 and y1 <= HINGE_RELIEF_Y1:
            out.extend(box(f"div_left_upper_centre_{idx}", lx - slot_recess_left - join, lx, y0 - join, y1 + join, relief_top, HINGE_BODY_SUPPORT_TOP))

        if y1 <= 15.00 + join:
            out.extend(box(f"div_right_wall_{idx}", rx, rx + slot_recess_right + join, y0 - join, y1 + join, z_floor - join, BODY_H))
        else:
            if y0 < 15.00:
                out.extend(box(f"div_right_wall_{idx}_pre", rx, rx + slot_recess_right + join, y0 - join, 15.00 + join, z_floor - join, BODY_H))
            out.extend(box(f"div_right_wall_{idx}_boss_sub", rx, rx + slot_recess_right + join, 15.00 - join, 28.00 + join, z_floor - join, 3.00 + join))
            if y1 > 28.00:
                out.extend(box(f"div_right_wall_{idx}_post", rx, rx + slot_recess_right + join, 28.00 - join, y1 + join, z_floor - join, BODY_H))

    # 7. Internal Flanking Ridges (Plan 010):
    for cy in slot_stations:
        y_slot_start = cy - slot_w / 2
        y_slot_end = cy + slot_w / 2
        out.extend(box(f"ridge_lower_{cy:.2f}", rx - ridge_proj, rx + join, y_slot_start - ridge_w, y_slot_start + join, BODY_BOTTOM, BODY_H))
        out.extend(box(f"ridge_upper_{cy:.2f}", rx - ridge_proj, rx + join, y_slot_end - join, y_slot_end + ridge_w, BODY_BOTTOM, BODY_H))

    # 8. Add Sliding Boss Keyway:
    out.extend(build_sliding_boss_keyway("divided_sliding"))

    # 9. Reinforced Closure Catch (0.85 mm):
    latch_z_base = BODY_H - 1.60
    catch_profile_xz = [
        (19.30, latch_z_base),
        (20.15, latch_z_base),
        (19.30, BODY_H),
    ]
    out.extend(prism_y("body_closure_catch_sliding", catch_profile_xz, -4.00, 4.00))

    # 10. Hinge centre knuckle:
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
    return out


def build_prototype_sliding_tab(clearance_delta: float = 0.0, suffix: str = "") -> Mesh:
    """Build the sliding pull tab with compliant cantilever snap legs and ergonomic grip head."""
    name = f"prototype_sliding_tab{suffix}"
    m = Mesh(name)
    neck_x = 15.10 + clearance_delta / 2
    back_x = 17.50 - clearance_delta / 2
    flank_x = 16.10
    base_y = 3.30 - clearance_delta
    neck_y = 2.70 - clearance_delta
    barb_y = 3.85 - clearance_delta
    join = 0.05

    # 1. Main upper shank body (Z in [8.00, 32.80]):
    shank_xy = [
        (neck_x, -neck_y),
        (neck_x, neck_y),
        (flank_x, base_y),
        (back_x, base_y),
        (back_x, -base_y),
        (flank_x, -base_y),
    ]
    m.extend(prism(f"shank_main{suffix}", shank_xy, 8.00, 32.80 + join))

    # 2. Lower compliant snap legs (Z in [3.50, 8.05]):
    # Left leg:
    leg_l = [
        (neck_x, -neck_y),
        (neck_x, -0.80),
        (back_x, -0.80),
        (back_x, -barb_y),
        (flank_x, -barb_y),
    ]
    m.extend(prism(f"leg_lower_l{suffix}", leg_l, 4.50, 8.05))

    # Left leg bottom lead-in taper (Z in [3.50, 4.55]):
    leg_l_tip = [
        (neck_x, -neck_y),
        (neck_x, -0.80),
        (back_x, -0.80),
        (back_x, -base_y),
        (flank_x, -base_y),
    ]
    m.extend(prism(f"leg_tip_l{suffix}", leg_l_tip, 3.50, 4.55))

    # Right leg:
    leg_r = [
        (neck_x, 0.80),
        (neck_x, neck_y),
        (flank_x, barb_y),
        (back_x, barb_y),
        (back_x, 0.80),
    ]
    m.extend(prism(f"leg_lower_r{suffix}", leg_r, 4.50, 8.05))

    # Right leg bottom lead-in taper:
    leg_r_tip = [
        (neck_x, 0.80),
        (neck_x, neck_y),
        (flank_x, base_y),
        (back_x, base_y),
        (back_x, 0.80),
    ]
    m.extend(prism(f"leg_tip_r{suffix}", leg_r_tip, 3.50, 4.55))

    # 3. Ergonomic Grip Head (Z in [32.80, 40.40]):
    head_xz = [
        (neck_x, 32.80),
        (back_x, 32.80),
        (back_x, 40.40),
        (16.00, 40.40),
        (15.60, 40.00),
        (16.80, 37.80),
        (16.00, 36.40),
    ]
    m.extend(prism_y(f"grip_head{suffix}", head_xz, -5.50, 5.50))
    m.extend(box(f"rib1{suffix}", 16.00, 16.50, -4.50, 4.50, 37.00, 37.60))
    m.extend(box(f"rib2{suffix}", 16.00, 16.50, -4.50, 4.50, 38.30, 38.90))

    # Rotate flat to print on back face directly on build plate:
    rot = m.transformed(lambda p: (p[1], p[2] - 3.50, back_x - p[0]), name).positive()
    zmin = rot.bounds()[0][2]
    return rot.translated(0.0, 0.0, -zmin, name).positive()


def main():
    parser = argparse.ArgumentParser(description="Generate sliding pull tab prototype models")
    parser.add_argument("--out", type=Path, default=PROTOTYPE_DIR)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    body = build_prototype_body_divided()
    tab_standard = build_prototype_sliding_tab(0.0, "")
    tab_loose = build_prototype_sliding_tab(0.15, "_loose")
    tab_firm = build_prototype_sliding_tab(-0.10, "_firm")
    lid = build_lid_local()

    # Create reference assemblies in lowered and lifted states:
    tab_local_m = Mesh("tab_in_body")
    neck_x = 15.10
    back_x = 17.50
    flank_x = 16.10
    base_y = 3.30
    neck_y = 2.70
    barb_y = 3.85
    shank_xy = [(neck_x, -neck_y), (neck_x, neck_y), (flank_x, base_y), (back_x, base_y), (back_x, -base_y), (flank_x, -base_y)]
    tab_local_m.extend(prism("s", shank_xy, 8.0, 32.85))
    leg_l = [(neck_x, -neck_y), (neck_x, -0.80), (back_x, -0.80), (back_x, -barb_y), (flank_x, -barb_y)]
    tab_local_m.extend(prism("ll", leg_l, 3.50, 8.05))
    leg_r = [(neck_x, 0.80), (neck_x, neck_y), (flank_x, barb_y), (back_x, barb_y), (back_x, 0.80)]
    tab_local_m.extend(prism("lr", leg_r, 3.50, 8.05))
    head_xz = [(neck_x, 32.80), (back_x, 32.80), (back_x, 40.40), (16.00, 40.40), (15.60, 40.00), (16.80, 37.80), (16.00, 36.40)]
    tab_local_m.extend(prism_y("h", head_xz, -5.50, 5.50))
    tab_lowered = tab_local_m.translated(0.0, 21.50, 0.0, "tab_lowered")
    tab_lifted = tab_local_m.translated(0.0, 21.50, 19.0, "tab_lifted")
    closed_lid = lid.translated(0.0, 0.0, BODY_H, "closed_lid")

    ref_lowered = combine("REFERENCE_sliding_tab_lowered_DO_NOT_PRINT", [body, closed_lid, tab_lowered])
    ref_lifted = combine("REFERENCE_sliding_tab_lifted_DO_NOT_PRINT", [body, closed_lid, tab_lifted])

    files = [
        ("prototype_cassette_body_sliding_tab.stl", body),
        ("prototype_sliding_tab.stl", tab_standard),
        ("prototype_sliding_tab_loose.stl", tab_loose),
        ("prototype_sliding_tab_firm.stl", tab_firm),
        ("REFERENCE_sliding_tab_lowered_DO_NOT_PRINT.stl", ref_lowered),
        ("REFERENCE_sliding_tab_lifted_DO_NOT_PRINT.stl", ref_lifted),
    ]
    for fn, mesh in files:
        write_binary_stl(args.out / fn, mesh)
        print(f"Generated {fn}: {len(mesh.triangles)} triangles")


if __name__ == "__main__":
    main()
