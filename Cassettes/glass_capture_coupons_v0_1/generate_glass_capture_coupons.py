#!/usr/bin/env python3
"""Generate Plan 009 v0.1 end-loaded pane-capture test articles."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE_PATH = HERE.parent / "glass_slide_cassette_40x80" / "generate_cassette.py"
SPEC = importlib.util.spec_from_file_location("cassette_v06_core", CORE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load cassette mesh utilities from {CORE_PATH}")
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)

Mesh = core.Mesh
box = core.box
ring_prism = core.ring_prism
write_binary_stl = core.write_binary_stl
mesh_record = core.mesh_record

OUTER_W = 31.0
FULL_D = 83.0
CHANNEL_W = 27.0
WINDOW_W = 23.0
PANE_MAX_W = 26.3
PANE_MAX_D = 76.3
PIN_D = 1.75
PIN_BORE_D = 2.15
FLOOR_TOP = 0.8
DEFAULT_SLOT_H = 2.0
ROOF_H = 0.8
PIN_Y = -40.1
PIN_Z = 1.8
STOP_INNER_Y = 38.4
GATE_T = 1.0


def add(mesh: Mesh, part: Mesh) -> None:
    mesh.extend(part)


def yz_octagon(cy: float, cz: float, ry: float, rz: float) -> list[tuple[float, float]]:
    """CCW support-free octagon in the Y/Z plane."""
    return [
        (cy - 0.50 * ry, cz - rz),
        (cy + 0.50 * ry, cz - rz),
        (cy + ry, cz - 0.50 * rz),
        (cy + ry, cz + 0.50 * rz),
        (cy + 0.50 * ry, cz + rz),
        (cy - 0.50 * ry, cz + rz),
        (cy - ry, cz + 0.50 * rz),
        (cy - ry, cz - 0.50 * rz),
    ]


def ring_prism_x(name: str, outer_yz, inner_yz, x0: float, x1: float) -> Mesh:
    raw = ring_prism(name, outer_yz, inner_yz, x0, x1)
    return raw.transformed(lambda p: (p[2], p[0], p[1]), name)


def channel_rails(name: str, y0: float, y1: float, slot_h: float) -> Mesh:
    """Two continuous pane rails; open at both ends until a stop/gate is added."""
    m = Mesh(name)
    outer = OUTER_W / 2
    channel = CHANNEL_W / 2
    window = WINDOW_W / 2
    roof_z0 = FLOOR_TOP + slot_h
    roof_z1 = roof_z0 + ROOF_H
    for sign in (-1, 1):
        x_outer = sign * outer
        x_wall_inner = sign * channel
        x_floor_inner = sign * window
        x_roof_inner = sign * 12.55
        x0, x1 = sorted((x_outer, x_floor_inner))
        add(m, box(f"{name}_ledge", x0, x1, y0, y1, 0.0, FLOOR_TOP))
        x0, x1 = sorted((x_outer, x_wall_inner))
        add(m, box(f"{name}_wall", x0, x1, y0 - 0.05, y1, FLOOR_TOP - 0.05, roof_z0 + 0.05))
        x0, x1 = sorted((x_outer, x_roof_inner))
        add(m, box(f"{name}_roof", x0, x1, y0 - 0.10, y1, roof_z0, roof_z1))
    return m


def build_channel_coupon(slot_h: float) -> Mesh:
    name = f"pane_channel_{int(round(slot_h * 10)):02d}"
    m = channel_rails(name, -12.0, 12.0, slot_h)
    top = FLOOR_TOP + slot_h + ROOF_H
    add(m, box(f"{name}_stop", -OUTER_W / 2, OUTER_W / 2, 10.45, 12.0, 0.0, top))
    return m


def build_pin_boss(name: str, bore_d: float, x0: float, x1: float, y: float) -> Mesh:
    outer = yz_octagon(y, PIN_Z, 2.25, 1.8)
    bore = yz_octagon(y, PIN_Z, bore_d / 2, bore_d / 2)
    return ring_prism_x(name, outer, bore, x0, x1)


def build_pin_fit_ladder() -> Mesh:
    m = Mesh("pin_fit_ladder")
    # Short/middle/long bosses correspond to 2.05/2.15/2.25 mm bores.
    for y, bore, length in ((-6.0, 2.05, 6.0), (0.0, 2.15, 8.0), (6.0, 2.25, 10.0)):
        add(m, build_pin_boss(f"pin_{bore:.2f}", bore, -length / 2, length / 2, y))
    return m


def build_full_endload_frame() -> Mesh:
    m = channel_rails("endload_frame", -37.0, 41.0, DEFAULT_SLOT_H)
    top = FLOOR_TOP + DEFAULT_SLOT_H + ROOF_H
    add(m, box("far_positive_stop", -OUTER_W / 2, OUTER_W / 2, STOP_INNER_Y, 41.0, 0.0, top))
    # Two support-free bosses carry a transverse filament pin behind the gate.
    add(m, build_pin_boss("left_pin_boss", PIN_BORE_D, -OUTER_W / 2, -12.35, PIN_Y))
    add(m, build_pin_boss("right_pin_boss", PIN_BORE_D, 12.35, OUTER_W / 2, PIN_Y))
    # Bed and roof bridges join each boss to the long rail while remaining
    # 0.125 mm clear of the nominal 2.15 mm octagonal bore.
    for x0, x1 in ((-OUTER_W / 2, -12.35), (12.35, OUTER_W / 2)):
        add(m, box("pin_boss_lower_bridge", x0, x1, -38.0, -36.9, 0.0, 0.60))
        add(m, box("pin_boss_upper_bridge", x0, x1, -38.0, -36.9, 3.0, 3.60))
    return m


def build_gate_print() -> Mesh:
    # Functional gate: X width 26.6, Y thickness 1.0, Z height 1.9. Rotate so
    # the 26.6 x 1.9 face is on the bed and the thin direction prints upward.
    functional = box("end_gate", -13.3, 13.3, -0.5, 0.5, 0.85, 2.75)
    return functional.transformed(lambda p: (p[0], p[2] - 0.85, p[1] + 0.5), "end_gate_print").positive()


def rect_loop(w: float, d: float) -> list[tuple[float, float]]:
    return [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]


def build_spacer(thickness: float) -> Mesh:
    return ring_prism(
        f"pane_spacer_{thickness:.1f}",
        rect_loop(26.6, 76.4),
        rect_loop(23.0, 70.0),
        0.0,
        thickness,
    )


def validate_design() -> dict[str, object]:
    pin_to_stop = STOP_INNER_Y - (PIN_Y + PIN_D / 2)
    return {
        "channel_width_mm": CHANNEL_W,
        "maximum_intended_pane_width_mm": PANE_MAX_W,
        "lateral_clearance_total_mm": round(CHANNEL_W - PANE_MAX_W, 3),
        "channel_slot_height_ladder_mm": [1.4, 1.8, 2.2],
        "full_frame_slot_height_mm": DEFAULT_SLOT_H,
        "maximum_intended_pane_length_mm": PANE_MAX_D,
        "pin_surface_to_far_stop_mm": round(pin_to_stop, 3),
        "length_clearance_at_maximum_pane_mm": round(pin_to_stop - PANE_MAX_D, 3),
        "printed_gate_thickness_mm": GATE_T,
        "pane_length_clearance_with_gate_mm": round(pin_to_stop - GATE_T - PANE_MAX_D, 3),
        "coupon_depth_note": "The v0.1 full-length mechanics coupon intentionally exceeds the 80 mm cassette depth; final envelope compaction is not yet validated.",
        "retention": "continuous roof rails + printed end gate + transverse 1.75 mm filament pin",
        "pin_bore_ladder_mm": [2.05, 2.15, 2.25],
        "full_frame_boss_bridge_to_bore_clearance_mm": 0.125,
        "spacer_thicknesses_mm": [0.4, 0.8, 1.2],
    }


def write_preview(path: Path) -> None:
    path.write_text(
        '''<svg xmlns="http://www.w3.org/2000/svg" width="980" height="540" viewBox="0 0 980 540">
<rect width="100%" height="100%" fill="#f7f4ed"/><text x="30" y="32" font-family="sans-serif" font-size="20" font-weight="bold">Plan 009 pane-capture coupons v0.1</text>
<g transform="translate(45 70)"><text x="0" y="-12" font-family="sans-serif" font-size="15">Full-length mechanics coupon — top view</text><rect x="0" y="0" width="186" height="500" rx="10" fill="#d8d1c2" stroke="#222" stroke-width="2"/><rect x="18" y="15" width="150" height="465" fill="#9ed5e5" stroke="#174c5b"/><rect x="0" y="0" width="186" height="24" fill="#c5bdac" stroke="#222"/><line x1="8" y1="39" x2="178" y2="39" stroke="#b22" stroke-width="6"/><rect x="15" y="43" width="156" height="8" fill="#e7a84f" stroke="#6d4610"/><text x="205" y="42" font-family="sans-serif" font-size="14">1.75 mm cross-pin</text><text x="205" y="62" font-family="sans-serif" font-size="14">printed end gate</text><text x="205" y="105" font-family="sans-serif" font-size="14">pane slides into continuous side rails</text><text x="205" y="470" font-family="sans-serif" font-size="14">solid far stop</text></g>
<g transform="translate(510 100)"><text x="0" y="-20" font-family="sans-serif" font-size="15">Rail cross-section</text><path d="M0 190 L0 0 L72 0 L72 50 L48 50 L48 150 L100 150 L100 190 Z" fill="#d8d1c2" stroke="#222" stroke-width="2"/><path d="M260 190 L260 0 L188 0 L188 50 L212 50 L212 150 L160 150 L160 190 Z" fill="#d8d1c2" stroke="#222" stroke-width="2"/><rect x="52" y="88" width="156" height="45" fill="#9ed5e5" stroke="#174c5b"/><text x="82" y="115" font-family="sans-serif" font-size="14">glass or plastic pane</text><line x1="130" y1="150" x2="130" y2="182" stroke="#777" stroke-width="8"/><text x="285" y="178" font-family="sans-serif" font-size="14">optional spacer controls play</text><text x="0" y="230" font-family="sans-serif" font-size="14">Roof rails prevent upward escape. Gate + pin prevent axial escape.</text></g>
<g transform="translate(510 385)"><text x="0" y="0" font-family="sans-serif" font-size="15" font-weight="bold">Print order</text><text x="0" y="28" font-family="sans-serif" font-size="14">1. Pin-bore ladder (2.05 / 2.15 / 2.25 mm)</text><text x="0" y="53" font-family="sans-serif" font-size="14">2. Channel ladder (1.4 / 1.8 / 2.2 mm)</text><text x="0" y="78" font-family="sans-serif" font-size="14">3. Full frame + gate; spacers only if needed</text><text x="0" y="112" font-family="sans-serif" font-size="13" fill="#9b2020">Provisional mechanics coupon; not an envelope-compatible lid.</text></g></svg>'''
    )


def main() -> None:
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    meshes: list[tuple[str, Mesh]] = []
    for slot_h in (1.4, 1.8, 2.2):
        meshes.append((f"pane_channel_fit_{int(round(slot_h * 10)):02d}_v0_1.stl", build_channel_coupon(slot_h)))
    meshes.extend(
        [
            ("pin_bore_fit_ladder_v0_1.stl", build_pin_fit_ladder()),
            ("endload_crosspin_frame_v0_1.stl", build_full_endload_frame()),
            ("endload_crosspin_gate_v0_1_print.stl", build_gate_print()),
            ("pane_spacer_04_v0_1.stl", build_spacer(0.4)),
            ("pane_spacer_08_v0_1.stl", build_spacer(0.8)),
            ("pane_spacer_12_v0_1.stl", build_spacer(1.2)),
        ]
    )
    records = []
    for filename, mesh in meshes:
        write_binary_stl(out / filename, mesh)
        records.append(mesh_record(mesh, filename))
    write_preview(out / "glass_capture_coupons_preview_v0_1.svg")
    manifest = {
        "design": "Plan 009 end-loaded pane-capture coupons",
        "version": "0.1",
        "units": "mm",
        "status": "provisional test articles; no glass-capture design is verified",
        "source_baseline": "v0.6 cassette pane width/length envelope",
        "design_validation": validate_design(),
        "print_order": [
            "pin_bore_fit_ladder_v0_1.stl",
            "pane_channel_fit_14_v0_1.stl, pane_channel_fit_18_v0_1.stl, pane_channel_fit_22_v0_1.stl",
            "endload_crosspin_frame_v0_1.stl + endload_crosspin_gate_v0_1_print.stl",
            "optional pane spacers only after measuring the pane and selected channel",
        ],
        "files": records,
    }
    (out / "manifest_v0_1.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
