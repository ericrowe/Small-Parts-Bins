#!/usr/bin/env python3
"""Generate the Plan 009 v0.3 compliant-latch end-capture coupon."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V02_PATH = HERE.parent / "glass_capture_coupons_v0_2" / "generate_glass_capture_coupons.py"
SPEC = importlib.util.spec_from_file_location("glass_capture_v02", V02_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load coupon utilities from {V02_PATH}")
v02 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = v02
SPEC.loader.exec_module(v02)

Mesh = v02.Mesh
box = v02.box
write_binary_stl = v02.write_binary_stl
mesh_record = v02.mesh_record

OUTER_W = 31.0
DEPTH = 32.0
CHANNEL_W = 27.0
TOP_OPENING_W = 23.0
BOTTOM_OPENING_W = 24.0
SLOT_H = 1.4
TOP_FACE_H = 0.8
PANE_SLOT_TOP = TOP_FACE_H + SLOT_H
BOTTOM_LEDGE_H = 0.8
TOTAL_H = PANE_SLOT_TOP + BOTTOM_LEDGE_H
MEASURED_PANE_W = 24.9
MAX_PANE_W = 26.3
TONGUE_W = 8.0
TONGUE_H = 0.6
TONGUE_Y0 = -13.0
TONGUE_Y1 = 14.2
HOOK_Y0 = -11.5
HOOK_Y1 = -9.5
HOOK_TOP = PANE_SLOT_TOP


def add(mesh: Mesh, part: Mesh) -> None:
    mesh.extend(part)


def build_coupon() -> Mesh:
    """Top-face-down coupon with a bed-supported integral compliant tongue."""
    m = Mesh("compliant_end_capture_coupon_v0_3")
    outer = OUTER_W / 2
    channel = CHANNEL_W / 2
    top_opening = TOP_OPENING_W / 2
    bottom_opening = BOTTOM_OPENING_W / 2
    y0, y1 = -DEPTH / 2, DEPTH / 2

    # The 2.0 mm top capture ledges print directly on the bed. The opposite
    # 1.5 mm ledges are the only functional channel overhangs in this orientation.
    for sign in (-1, 1):
        x_outer = sign * outer
        x_channel = sign * channel
        x_top = sign * top_opening
        x_bottom = sign * bottom_opening
        add(m, box("top_capture_ledge", *sorted((x_outer, x_top)), y0, y1,
                   0.0, TOP_FACE_H))
        add(m, box("outer_wall", *sorted((x_outer, x_channel)), y0, y1,
                   TOP_FACE_H - 0.05, PANE_SLOT_TOP + 0.05))
        add(m, box("bottom_capture_ledge", *sorted((x_outer, x_bottom)), y0, y1,
                   PANE_SLOT_TOP, TOTAL_H))

    # A bed-supported far crossbar connects both rails without obstructing a
    # pane passing through the slot above it during this short coupon test.
    add(m, box("far_frame_crossbar", -outer, outer, 14.0, y1 - 0.1, 0.0, TOP_FACE_H))

    # The compliant tongue is printed flat on the bed and joins the far crossbar
    # with a positive 0.2 mm axial overlap. It is intentionally clear of the pane
    # underside in its relaxed state.
    add(m, box("compliant_tongue", -TONGUE_W / 2, TONGUE_W / 2,
               TONGUE_Y0, TONGUE_Y1, 0.0, TONGUE_H))
    add(m, box("finger_pad", -6.0, 6.0, TONGUE_Y0, -10.0, 0.0, TONGUE_H))
    # A square relaxed shoulder positively blocks the pane end. The user must
    # depress the tongue; the glass is not intended to cam this feature aside.
    add(m, box("positive_end_shoulder", -TONGUE_W / 2, TONGUE_W / 2,
               HOOK_Y0, HOOK_Y1, TONGUE_H - 0.05, HOOK_TOP))
    return m


def design_validation() -> dict[str, object]:
    tongue_free_length = 14.0 - TONGUE_Y0
    required_deflection = HOOK_TOP - TOP_FACE_H
    estimated_surface_strain = 6.0 * required_deflection * TONGUE_H / tongue_free_length**2
    return {
        "print_orientation": "top/visible face down; supplied STL orientation",
        "loading_channel_width_mm": CHANNEL_W,
        "top_capture_opening_mm": TOP_OPENING_W,
        "bottom_capture_opening_mm": BOTTOM_OPENING_W,
        "clear_channel_height_mm": SLOT_H,
        "top_ledge_overhang_from_channel_wall_mm": (CHANNEL_W - TOP_OPENING_W) / 2,
        "bottom_ledge_overhang_from_channel_wall_mm": (CHANNEL_W - BOTTOM_OPENING_W) / 2,
        "measured_pane_width_mm": MEASURED_PANE_W,
        "top_overlap_per_side_measured_pane_mm": round((MEASURED_PANE_W - TOP_OPENING_W) / 2, 3),
        "bottom_overlap_per_side_measured_pane_mm": round((MEASURED_PANE_W - BOTTOM_OPENING_W) / 2, 3),
        "top_overlap_per_side_max_pane_mm": round((MAX_PANE_W - TOP_OPENING_W) / 2, 3),
        "bottom_overlap_per_side_max_pane_mm": round((MAX_PANE_W - BOTTOM_OPENING_W) / 2, 3),
        "compliant_tongue_width_mm": TONGUE_W,
        "compliant_tongue_thickness_mm": TONGUE_H,
        "compliant_tongue_free_length_mm": tongue_free_length,
        "required_nominal_release_deflection_mm": required_deflection,
        "estimated_outer_fiber_strain": round(estimated_surface_strain, 4),
        "retention": "continuous side ledges + integral manually depressed positive end shoulder",
        "loose_parts": 0,
    }


def write_preview(path: Path) -> None:
    path.write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="430" viewBox="0 0 900 430">
<rect width="100%" height="100%" fill="#f7f4ed"/><text x="28" y="34" font-family="sans-serif" font-size="20" font-weight="bold">Plan 009 compliant end-capture coupon v0.3</text>
<g transform="translate(55 85)"><rect x="0" y="0" width="310" height="250" fill="#d8d1c2" stroke="#222" stroke-width="2"/><rect x="40" y="0" width="230" height="250" fill="#9ed5e5" stroke="#174c5b"/><rect x="115" y="90" width="80" height="160" fill="#e7a84f" stroke="#6d4610"/><rect x="95" y="80" width="120" height="32" fill="#e7a84f" stroke="#6d4610"/><rect x="115" y="96" width="80" height="20" fill="#b04b3f"/><text x="90" y="285" font-family="sans-serif" font-size="14">pane passes through the short coupon</text></g>
<g transform="translate(430 90)" font-family="sans-serif"><text x="0" y="0" font-size="16" font-weight="bold">Selected geometry</text><text x="0" y="30" font-size="14">27.0 mm loading channel</text><text x="0" y="55" font-size="14">23.0 mm top opening / 24.0 mm opposite opening</text><text x="0" y="80" font-size="14">1.4 mm clear channel height</text><text x="0" y="120" font-size="16" font-weight="bold">Operation</text><text x="0" y="150" font-size="14">1. Depress the orange tongue manually.</text><text x="0" y="175" font-size="14">2. Slide the pane past the red shoulder.</text><text x="0" y="200" font-size="14">3. Release; shoulder rises behind pane end.</text><text x="0" y="225" font-size="14">4. Pull gently to test positive retention.</text><text x="0" y="270" font-size="13" fill="#9b2020">Do not use the glass to force the latch aside.</text><text x="0" y="295" font-size="13" fill="#9b2020">Coupon only; not a cassette lid.</text></g></svg>''')


def main() -> None:
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    filename = "compliant_end_capture_coupon_v0_3.stl"
    path = out / filename
    mesh = build_coupon()
    write_binary_stl(path, mesh)
    record = mesh_record(mesh, filename)
    record["exported_stl_audit"] = v02.audit_exported_stl(path)
    write_preview(out / "compliant_end_capture_preview_v0_3.svg")
    manifest = {
        "design": "Plan 009 short compliant-latch end-capture coupon",
        "version": "0.3",
        "units": "mm",
        "status": "provisional test article; compliant latch and revised overlap are unverified",
        "design_validation": design_validation(),
        "files": [record],
    }
    (out / "manifest_v0_3.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
