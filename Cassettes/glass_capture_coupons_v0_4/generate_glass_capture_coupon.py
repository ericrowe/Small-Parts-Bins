#!/usr/bin/env python3
"""Generate the Plan 009 v0.4 directly shortened compliant-latch coupon."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V03_PATH = HERE.parent / "glass_capture_coupons_v0_3" / "generate_glass_capture_coupon.py"
SPEC = importlib.util.spec_from_file_location("glass_capture_v03", V03_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load v0.3 coupon geometry from {V03_PATH}")
v03 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = v03
SPEC.loader.exec_module(v03)

Mesh = v03.Mesh
box = v03.box
write_binary_stl = v03.write_binary_stl
mesh_record = v03.mesh_record

DEPTH = 20.0
Y0 = -14.0
Y1 = Y0 + DEPTH
TONGUE_Y0 = -13.0
FREE_LENGTH = 6.75
ROOT_Y0 = TONGUE_Y0 + FREE_LENGTH
ROOT_Y1 = ROOT_Y0 + 1.9
TONGUE_Y1 = ROOT_Y0 + 0.25


def add(mesh: Mesh, part: Mesh) -> None:
    mesh.extend(part)


def build_coupon() -> Mesh:
    """Repeat v0.3 capture geometry with only the straight flex length reduced."""
    m = Mesh("short_compliant_end_capture_coupon_v0_4")
    outer = v03.OUTER_W / 2
    channel = v03.CHANNEL_W / 2
    top_opening = v03.TOP_OPENING_W / 2
    bottom_opening = v03.BOTTOM_OPENING_W / 2

    for sign in (-1, 1):
        x_outer = sign * outer
        x_channel = sign * channel
        x_top = sign * top_opening
        x_bottom = sign * bottom_opening
        add(m, box("top_capture_ledge", *sorted((x_outer, x_top)), Y0, Y1,
                   0.0, v03.TOP_FACE_H))
        add(m, box("outer_wall", *sorted((x_outer, x_channel)), Y0, Y1,
                   v03.TOP_FACE_H - 0.05, v03.PANE_SLOT_TOP + 0.05))
        add(m, box("bottom_capture_ledge", *sorted((x_outer, x_bottom)), Y0, Y1,
                   v03.PANE_SLOT_TOP, v03.TOTAL_H))

    # Moving this crossbar close to the shoulder creates the requested 6.75 mm
    # straight free length while also joining and reinforcing both side rails.
    add(m, box("short_tongue_root_crossbar", -outer, outer, ROOT_Y0, ROOT_Y1,
               0.0, v03.TOP_FACE_H))
    add(m, box("short_compliant_tongue", -v03.TONGUE_W / 2, v03.TONGUE_W / 2,
               TONGUE_Y0, TONGUE_Y1, 0.0, v03.TONGUE_H))
    add(m, box("finger_pad", -6.0, 6.0, TONGUE_Y0, -10.0,
               0.0, v03.TONGUE_H))
    add(m, box("positive_end_shoulder", -v03.TONGUE_W / 2, v03.TONGUE_W / 2,
               v03.HOOK_Y0, v03.HOOK_Y1, v03.TONGUE_H - 0.05, v03.HOOK_TOP))
    return m


def design_validation() -> dict[str, object]:
    required_deflection = v03.HOOK_TOP - v03.TOP_FACE_H
    strain = 6.0 * required_deflection * v03.TONGUE_H / FREE_LENGTH**2
    return {
        "change_from_v0_3": "straight compliant free length reduced by 75%; successful capture dimensions unchanged",
        "print_orientation": "top/visible face down; supplied STL orientation",
        "loading_channel_width_mm": v03.CHANNEL_W,
        "top_capture_opening_mm": v03.TOP_OPENING_W,
        "bottom_capture_opening_mm": v03.BOTTOM_OPENING_W,
        "clear_channel_height_mm": v03.SLOT_H,
        "measured_pane_width_mm": v03.MEASURED_PANE_W,
        "compliant_tongue_width_mm": v03.TONGUE_W,
        "compliant_tongue_thickness_mm": v03.TONGUE_H,
        "compliant_tongue_free_length_mm": FREE_LENGTH,
        "free_length_reduction_from_v0_3_percent": 75.0,
        "required_nominal_release_deflection_mm": round(required_deflection, 3),
        "estimated_outer_fiber_strain": round(strain, 4),
        "estimated_outer_fiber_strain_percent": round(100.0 * strain, 2),
        "material_scope": "PETG; PLA excluded from this shortened latch geometry",
        "validation_note": "simple-beam strain is retained as metadata; physical PETG behavior is authoritative",
        "retention": "unchanged continuous side ledges + shortened integral positive end shoulder",
        "loose_parts": 0,
    }


def main() -> None:
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    filename = "short_compliant_end_capture_coupon_v0_4.stl"
    path = out / filename
    mesh = build_coupon()
    write_binary_stl(path, mesh)
    record = mesh_record(mesh, filename)
    record["exported_stl_audit"] = v03.v02.audit_exported_stl(path)
    manifest = {
        "design": "Plan 009 directly shortened compliant-latch coupon",
        "version": "0.4",
        "units": "mm",
        "status": "provisional PETG direct-shortening test; physical validation required",
        "design_validation": design_validation(),
        "files": [record],
    }
    (out / "manifest_v0_4.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
