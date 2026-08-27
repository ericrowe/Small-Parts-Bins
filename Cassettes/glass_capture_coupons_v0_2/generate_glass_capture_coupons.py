#!/usr/bin/env python3
"""Generate the Plan 009 v0.2 selected-fit end-gate mechanics coupon."""

from __future__ import annotations

import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V01_PATH = HERE.parent / "glass_capture_coupons_v0_1" / "generate_glass_capture_coupons.py"
SPEC = importlib.util.spec_from_file_location("glass_capture_v01", V01_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load v0.1 coupon geometry from {V01_PATH}")
v01 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = v01
SPEC.loader.exec_module(v01)

Mesh = v01.Mesh
box = v01.box
write_binary_stl = v01.write_binary_stl
mesh_record = v01.mesh_record

SELECTED_BORE_D = 2.05
SELECTED_SLOT_H = 1.4
GATE_Z0 = 0.85
GATE_Z1 = 2.15


def add(mesh: Mesh, part: Mesh) -> None:
    mesh.extend(part)


def build_selected_frame() -> Mesh:
    """Full-length mechanics frame using both physically selected ladder fits."""
    m = v01.channel_rails("endload_frame_v0_2", -37.0, 41.0, SELECTED_SLOT_H)
    top = v01.FLOOR_TOP + SELECTED_SLOT_H + v01.ROOF_H
    add(m, box("far_positive_stop", -v01.OUTER_W / 2, v01.OUTER_W / 2,
               v01.STOP_INNER_Y, 41.0, 0.0, top))
    add(m, v01.build_pin_boss("left_pin_boss", SELECTED_BORE_D,
                              -v01.OUTER_W / 2, -12.35, v01.PIN_Y))
    add(m, v01.build_pin_boss("right_pin_boss", SELECTED_BORE_D,
                              12.35, v01.OUTER_W / 2, v01.PIN_Y))
    # Positive overlaps join each boss to the rail. Both bridges remain 0.125 mm
    # clear of the selected octagonal bore at its upper and lower vertices.
    for x0, x1 in ((-v01.OUTER_W / 2, -12.35), (12.35, v01.OUTER_W / 2)):
        add(m, box("pin_boss_lower_bridge", x0, x1, -38.0, -36.9, 0.0, 0.65))
        add(m, box("pin_boss_upper_bridge", x0, x1, -38.0, -36.9, 2.95, 3.60))
    return m


def build_selected_gate_print() -> Mesh:
    """Gate fitted inside the selected 1.4 mm clear channel."""
    functional = box("end_gate_v0_2", -13.3, 13.3, -0.5, 0.5, GATE_Z0, GATE_Z1)
    return functional.transformed(
        lambda p: (p[0], p[2] - GATE_Z0, p[1] + 0.5),
        "end_gate_v0_2_print",
    ).positive()


def design_validation() -> dict[str, object]:
    pin_to_stop = v01.STOP_INNER_Y - (v01.PIN_Y + v01.PIN_D / 2)
    return {
        "selected_from_physical_v0_1_ladder": True,
        "selected_pin_bore_mm": SELECTED_BORE_D,
        "intended_pin_mm": v01.PIN_D,
        "selected_channel_slot_height_mm": SELECTED_SLOT_H,
        "channel_width_mm": v01.CHANNEL_W,
        "maximum_intended_pane_width_mm": v01.PANE_MAX_W,
        "lateral_clearance_total_mm": round(v01.CHANNEL_W - v01.PANE_MAX_W, 3),
        "maximum_intended_pane_length_mm": v01.PANE_MAX_D,
        "pin_surface_to_far_stop_mm": round(pin_to_stop, 3),
        "printed_gate_thickness_mm": v01.GATE_T,
        "pane_length_clearance_with_gate_mm": round(
            pin_to_stop - v01.GATE_T - v01.PANE_MAX_D, 3
        ),
        "gate_functional_height_mm": round(GATE_Z1 - GATE_Z0, 3),
        "gate_vertical_clearance_in_channel_mm": round(
            SELECTED_SLOT_H - (GATE_Z1 - GATE_Z0), 3
        ),
        "boss_bridge_to_bore_clearance_mm": 0.125,
        "retention": "continuous roof rails + printed end gate + transverse 1.75 mm filament pin",
        "coupon_depth_note": "The v0.2 mechanics coupon remains intentionally longer than the 80 mm cassette envelope.",
    }


def audit_exported_stl(path: Path) -> dict[str, object]:
    """Re-read the binary artifact and check count, finiteness, and degenerates."""
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"truncated binary STL: {path}")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_bytes = 84 + 50 * triangle_count
    if len(data) != expected_bytes:
        raise ValueError(f"binary STL size mismatch: {path}")
    degenerate = 0
    finite = True
    for i in range(triangle_count):
        values = struct.unpack_from("<12fH", data, 84 + 50 * i)
        coords = values[3:12]
        finite = finite and all(math.isfinite(value) for value in coords)
        a, b, c = coords[0:3], coords[3:6], coords[6:9]
        u = tuple(b[j] - a[j] for j in range(3))
        v = tuple(c[j] - a[j] for j in range(3))
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


def write_preview(path: Path) -> None:
    path.write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="390" viewBox="0 0 900 390">
<rect width="100%" height="100%" fill="#f7f4ed"/><text x="28" y="34" font-family="sans-serif" font-size="20" font-weight="bold">Plan 009 selected-fit mechanics coupon v0.2</text>
<g transform="translate(45 70)"><rect x="0" y="0" width="186" height="280" rx="8" fill="#d8d1c2" stroke="#222" stroke-width="2"/><rect x="18" y="18" width="150" height="245" fill="#9ed5e5" stroke="#174c5b"/><rect x="0" y="0" width="186" height="22" fill="#c5bdac" stroke="#222"/><line x1="8" y1="38" x2="178" y2="38" stroke="#b22" stroke-width="6"/><rect x="15" y="43" width="156" height="8" fill="#e7a84f" stroke="#6d4610"/></g>
<g transform="translate(270 92)" font-family="sans-serif"><text x="0" y="0" font-size="16" font-weight="bold">Exact selected dimensions</text><text x="0" y="31" font-size="15">Pin bore: 2.05 mm</text><text x="0" y="57" font-size="15">Pane channel: 1.4 mm clear</text><text x="0" y="83" font-size="15">Pin: straight 1.75 mm filament</text><text x="0" y="125" font-size="15" font-weight="bold">This print tests</text><text x="0" y="154" font-size="14">pane insertion to the far stop</text><text x="0" y="178" font-size="14">gate fit and removal</text><text x="0" y="202" font-size="14">cross-pin insertion and containment</text><text x="0" y="226" font-size="14">positive blocking of the pane escape path</text><text x="0" y="266" font-size="13" fill="#9b2020">Mechanics coupon only; not an envelope-compatible lid.</text></g></svg>''')


def main() -> None:
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    meshes = [
        ("endload_crosspin_frame_v0_2.stl", build_selected_frame()),
        ("endload_crosspin_gate_v0_2_print.stl", build_selected_gate_print()),
    ]
    records = []
    for filename, mesh in meshes:
        path = out / filename
        write_binary_stl(path, mesh)
        record = mesh_record(mesh, filename)
        record["exported_stl_audit"] = audit_exported_stl(path)
        records.append(record)
    write_preview(out / "glass_capture_coupons_preview_v0_2.svg")
    manifest = {
        "design": "Plan 009 selected-fit end-loaded pane-capture mechanics coupon",
        "version": "0.2",
        "units": "mm",
        "status": "provisional mechanics test; positive capture not yet physically verified",
        "source_baseline": "v0.1 coupon geometry with physically selected fit dimensions",
        "design_validation": design_validation(),
        "files": records,
    }
    (out / "manifest_v0_2.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
