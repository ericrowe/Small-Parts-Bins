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


def write_preview(path: Path) -> None:
    path.write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420">
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#333"/></marker></defs>
<rect width="100%" height="100%" fill="#f7f4ed"/><text x="28" y="34" font-family="sans-serif" font-size="20" font-weight="bold">v0.4 latch — installed side section (diagrammatic)</text>
<g transform="translate(45 75)" font-family="sans-serif"><rect x="20" y="190" width="360" height="38" fill="#d8d1c2" stroke="#222"/><rect x="125" y="102" width="255" height="32" fill="#9ed5e5" stroke="#174c5b" stroke-width="2"/><text x="220" y="124" font-size="14">GLASS</text><path d="M105 190 L105 86 L125 86 L125 145 L116 145 L116 190 Z" fill="#b04b3f" stroke="#68251f" stroke-width="2"/><text x="42" y="72" font-size="13">positive shoulder</text><line x1="103" y1="76" x2="112" y2="96" stroke="#333" marker-end="url(#arrow)"/><rect x="105" y="166" width="180" height="14" fill="#e7a84f" stroke="#6d4610"/><text x="190" y="260" font-size="13">compliant PETG tongue — relaxed</text><line x1="245" y1="248" x2="245" y2="182" stroke="#333" marker-end="url(#arrow)"/><line x1="145" y1="149" x2="145" y2="163" stroke="#555"/><text x="154" y="160" font-size="12">0.20 mm nominal gap: tongue does not press on glass</text><line x1="170" y1="82" x2="325" y2="82" stroke="#333" stroke-width="2" marker-end="url(#arrow)"/><text x="198" y="70" font-size="13">installation direction while latch is depressed</text></g>
<g transform="translate(485 78)" font-family="sans-serif"><text x="0" y="0" font-size="16" font-weight="bold">Normal installed state</text><text x="0" y="32" font-size="14">• Blue is the glass.</text><text x="0" y="58" font-size="14">• Orange tongue is unloaded below it.</text><text x="0" y="84" font-size="14">• Red shoulder sits behind the glass end.</text><text x="0" y="110" font-size="14">• Shoulder blocks withdrawal geometrically.</text><text x="0" y="154" font-size="16" font-weight="bold">Installation / removal</text><text x="0" y="184" font-size="14">1. Manually depress the tongue.</text><text x="0" y="210" font-size="14">2. Slide glass completely past the shoulder.</text><text x="0" y="236" font-size="14">3. Release; shoulder returns behind glass.</text><text x="0" y="278" font-size="13" fill="#9b2020">The glass must not cam the latch aside.</text><text x="0" y="304" font-size="13">PETG only; 6.75 mm free tongue length.</text></g></svg>''')


def main() -> None:
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    filename = "short_compliant_end_capture_coupon_v0_4.stl"
    path = out / filename
    mesh = build_coupon()
    write_binary_stl(path, mesh)
    record = mesh_record(mesh, filename)
    record["exported_stl_audit"] = v03.v02.audit_exported_stl(path)
    write_preview(out / "short_compliant_end_capture_preview_v0_4.svg")
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
