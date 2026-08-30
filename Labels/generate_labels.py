#!/usr/bin/env python3
"""Generate Printable, Cricut-Ready Fastener Label Sheets for Glass-Window Cassettes.

Supports:
  1. Standard 34 x 10 mm Strip Labels (fits solid cassette lid zone).
  2. Extended 38.6 x 76.0 mm Full-Lid Wrap Overlays (with 23.0 x 58.5 mm glass cutout & side length rulers).
  3. Batch Cricut Print-Then-Cut sheets (Letter & A4) with vector cut paths and fiducial registration frames.
  4. High-resolution PNG preview sheets for direct raster printing and visual inspection.
  5. Preset shop assortments: Metric (M2–M6), Imperial (#4-40–1/4"), Brass Heat-Set Inserts, and Washers.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from vector_icons import get_component_icon_svg, get_drive_icon_svg, get_head_icon_svg

# ==============================================================================
# DIMENSIONAL CONSTANTS (millimeters)
# ==============================================================================

# Standard Strip Label:
STRIP_W = 34.00
STRIP_H = 10.00
STRIP_R = 1.00  # Corner radius

# Full-Lid Wrap Label:
WRAP_W = 38.60
WRAP_H = 76.00
WRAP_R = 2.00
WRAP_CUTOUT_W = 23.00
WRAP_CUTOUT_H = 58.50
WRAP_CUTOUT_R = 1.50
WRAP_CUTOUT_X0 = (WRAP_W - WRAP_CUTOUT_W) / 2.0  # 7.80 mm
WRAP_CUTOUT_Y0 = 12.00                           # Window starts 12.0 mm from top

# Standard Paper Sizes (mm):
PAPER_LETTER = (215.9, 279.4)  # 8.5 x 11 in
PAPER_A4 = (210.0, 297.0)

# Cricut Print-Then-Cut Safe Printable Area:
CRICUT_MAX_W = 171.45
CRICUT_MAX_H = 234.95

# ==============================================================================
# FASTENER SPECIFICATION DATA MODEL
# ==============================================================================

@dataclass
class FastenerSpec:
    category: str           # "metric_coarse", "imperial_unc", "heat_set_inserts", "washers", etc.
    size: str               # "M3", "#4-40", "1/4\"-20", etc.
    length: str = ""        # "12 mm", "1/2\"", "Standard", etc.
    head: str = "shcs"      # "shcs", "bhcs", "fhcs", "hex", "pan", "none"
    drive: str = "hex"      # "hex", "torx", "phillips", "none"
    comp_type: str = "bolt" # "bolt", "nut", "nyloc", "washer", "insert"
    pitch: str = ""         # "0.5", "40 TPI", etc.
    tap_drill: str = ""     # "2.5 mm (#39)", "#43 (0.089\")", etc.
    clearance_drill: str = ""
    tool_key: str = ""      # "2.5 mm", "3/32\"", "T10", etc.
    material: str = ""      # "SS 304", "12.9", "GR 8", "Brass", etc.
    accent_color: str = ""
    bg_color: str = ""
    extra_note: str = ""


# ==============================================================================
# STANDALONE LABEL RENDERERS (Pure Vector SVG)
# ==============================================================================

def render_strip_label_svg(spec: FastenerSpec, x: float = 0.0, y: float = 0.0, include_cut_path: bool = True) -> str:
    """Render a standard 34.0 x 10.0 mm cassette lid strip label as SVG elements."""
    color = spec.accent_color or "#0077CC"
    bg = spec.bg_color or "#FFFFFF"

    # Main text line:
    if spec.comp_type in ("nut", "nyloc", "insert", "washer"):
        main_title = f"{spec.size} {spec.length}".strip()
        sub_text_1 = spec.extra_note or (f"Tap: {spec.tap_drill}" if spec.tap_drill else spec.pitch)
        sub_text_2 = f"Key: {spec.tool_key}" if spec.tool_key else (spec.material or "")
    else:
        main_title = f"{spec.size} × {spec.length}".strip() if spec.length else spec.size
        sub_text_1 = f"P: {spec.pitch}" if spec.pitch else ""
        if spec.tap_drill and spec.tap_drill.split():
            sub_text_1 += f" | Tap: {spec.tap_drill.split()[0]}"
        sub_text_2 = f"Key: {spec.tool_key}" if spec.tool_key else (spec.material or "")

    # Icons:
    icon_x = x + STRIP_W - 8.2

    svg_parts = [
        f'<g id="label_{spec.size}_{spec.length}" transform="translate({x:.2f},{y:.2f})">',
        # Background rect:
        f'<rect x="0" y="0" width="{STRIP_W}" height="{STRIP_H}" rx="{STRIP_R}" fill="{bg}" stroke="#CCCCCC" stroke-width="0.2"/>',
        # Left category color accent bar:
        f'<path d="M 0,{STRIP_R} A {STRIP_R},{STRIP_R} 0 0,1 {STRIP_R},0 L 2.8,0 L 2.8,{STRIP_H} L {STRIP_R},{STRIP_H} A {STRIP_R},{STRIP_R} 0 0,1 0,{STRIP_H - STRIP_R} Z" fill="{color}"/>',
        # Main Title (Bold):
        f'<text x="4.2" y="4.2" font-family="Arial, Helvetica, sans-serif" font-weight="900" font-size="3.8" fill="#111111">{main_title}</text>',
        # Subtext line 1 (Pitch / Tap):
        f'<text x="4.2" y="6.8" font-family="Arial, Helvetica, sans-serif" font-weight="600" font-size="1.9" fill="#444444">{sub_text_1}</text>',
        # Subtext line 2 (Drive Tool / Material):
        f'<text x="4.2" y="8.9" font-family="Arial, Helvetica, sans-serif" font-weight="700" font-size="1.9" fill="{color}">{sub_text_2}</text>',
    ]

    # Render silhouette icons:
    if spec.comp_type in ("nut", "nyloc", "insert", "washer"):
        svg_parts.append(get_component_icon_svg(spec.comp_type, icon_x - x, 1.5, 6.8, 6.8, color="#222222"))
    else:
        # Head icon:
        if spec.head and spec.head != "none":
            svg_parts.append(get_head_icon_svg(spec.head, icon_x - x, 0.8, 6.5, 4.2, color="#222222"))
        # Drive icon:
        if spec.drive and spec.drive != "none":
            svg_parts.append(get_drive_icon_svg(spec.drive, icon_x - x + 1.2, 5.2, 4.0, color=color))

    # Optional Kiss-Cut path boundary:
    if include_cut_path:
        svg_parts.append(f'<rect x="0" y="0" width="{STRIP_W}" height="{STRIP_H}" rx="{STRIP_R}" fill="none" stroke="#FF0055" stroke-width="0.15" stroke-dasharray="1,1" opacity="0.4"/>')

    svg_parts.append("</g>")
    return "\n".join(svg_parts)


def render_full_lid_wrap_svg(spec: FastenerSpec, x: float = 0.0, y: float = 0.0) -> str:
    """Render an extended 38.6 x 76.0 mm full-lid overlay with clear glass window cutout and length rulers."""
    color = spec.accent_color or "#0077CC"
    bg = spec.bg_color or "#FFFFFF"

    svg_parts = [
        f'<g id="wrap_{spec.size}_{spec.length}" transform="translate({x:.2f},{y:.2f})">',
        # Outer lid skin rect:
        f'<rect x="0" y="0" width="{WRAP_W}" height="{WRAP_H}" rx="{WRAP_R}" fill="{bg}" stroke="#CCCCCC" stroke-width="0.3"/>',
        # Glass window cutout keep-out area:
        f'<rect x="{WRAP_CUTOUT_X0}" y="{WRAP_CUTOUT_Y0}" width="{WRAP_CUTOUT_W}" height="{WRAP_CUTOUT_H}" rx="{WRAP_CUTOUT_R}" fill="#FFFFFF" stroke="#FF0055" stroke-width="0.2" stroke-dasharray="1,1"/>',
        # "CLEAR GLASS WINDOW" watermark in cutout:
        f'<text x="{WRAP_W/2.0}" y="{WRAP_CUTOUT_Y0 + WRAP_CUTOUT_H/2.0}" font-family="Arial, sans-serif" font-size="2.4" font-weight="bold" fill="#DDDDDD" text-anchor="middle" transform="rotate(-90, {WRAP_W/2.0}, {WRAP_CUTOUT_Y0 + WRAP_CUTOUT_H/2.0})">CLEAR GLASS WINDOW</text>',
        # Top front label strip integrated into wrap:
        render_strip_label_svg(spec, x=2.3, y=1.0, include_cut_path=False),
    ]

    # Side length ruler ticks on left rail (0 to 55 mm):
    ruler_x = 3.5
    for mm in range(0, 56, 5):
        tick_y = WRAP_CUTOUT_Y0 + mm
        tick_len = 2.5 if (mm % 10 == 0) else 1.5
        svg_parts.append(f'<line x1="{ruler_x}" y1="{tick_y}" x2="{ruler_x + tick_len}" y2="{tick_y}" stroke="#333333" stroke-width="0.3"/>')
        if mm % 10 == 0:
            svg_parts.append(f'<text x="{ruler_x - 0.5}" y="{tick_y + 0.8}" font-family="Arial, sans-serif" font-size="1.8" font-weight="bold" fill="#444444" text-anchor="end">{mm}</text>')

    # Bottom rear banner:
    bot_y = WRAP_CUTOUT_Y0 + WRAP_CUTOUT_H + 1.2
    svg_parts.append(f'<rect x="2.0" y="{bot_y}" width="{WRAP_W - 4.0}" height="3.5" rx="0.6" fill="{color}"/>')
    spec_banner = f"Tap: {spec.tap_drill}  |  Clearance: {spec.clearance_drill}" if spec.tap_drill else spec.extra_note
    svg_parts.append(f'<text x="{WRAP_W/2.0}" y="{bot_y + 2.5}" font-family="Arial, sans-serif" font-size="1.8" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{spec_banner}</text>')

    svg_parts.append("</g>")
    return "\n".join(svg_parts)


# ==============================================================================
# CRICUT PRINT-THEN-CUT SHEET COMPOSER & PNG RENDERER
# ==============================================================================

def render_png_sheet(
    labels: list[FastenerSpec],
    title: str,
    paper: tuple[float, float],
    out_path: Path,
    label_format: str = "strip"
):
    """Render a high-resolution 200 DPI PNG preview of the printable label sheet using matplotlib."""
    paper_w, paper_h = paper
    fig_w, fig_h = paper_w / 25.4, paper_h / 25.4

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=200)
    ax.set_xlim(0, paper_w)
    ax.set_ylim(0, paper_h)
    ax.invert_yaxis()
    ax.axis("off")

    # Paper background:
    ax.add_patch(patches.Rectangle((0, 0), paper_w, paper_h, fill=True, color="#FFFFFF"))

    # Sheet Header:
    margin_x = (paper_w - CRICUT_MAX_W) / 2.0
    margin_y = (paper_h - CRICUT_MAX_H) / 2.0
    ax.text(margin_x, margin_y - 8.0, title, fontsize=14, weight="bold", color="#111111")
    ax.text(margin_x, margin_y - 3.0, f"Gridfinity Glass-Window Cassette System — {label_format.upper()} ({STRIP_W if label_format=='strip' else WRAP_W} × {STRIP_H if label_format=='strip' else WRAP_H} mm)", fontsize=8, color="#666666")

    # Cricut registration boundary frame:
    ax.add_patch(patches.Rectangle((margin_x - 4.0, margin_y - 4.0), CRICUT_MAX_W + 8.0, CRICUT_MAX_H + 8.0, fill=False, edgecolor="#000000", linewidth=2.0))

    if label_format == "strip":
        item_w, item_h = STRIP_W, STRIP_H
        gap_x, gap_y = 3.0, 3.0
    else:
        item_w, item_h = WRAP_W, WRAP_H
        gap_x, gap_y = 4.0, 4.0

    cols = int((CRICUT_MAX_W + gap_x) / (item_w + gap_x))
    rows = int((CRICUT_MAX_H + gap_y) / (item_h + gap_y))

    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= len(labels):
                break
            spec = labels[idx]
            px = margin_x + c * (item_w + gap_x)
            py = margin_y + r * (item_h + gap_y)

            color = spec.accent_color or "#0077CC"
            bg = spec.bg_color or "#FFFFFF"

            if label_format == "strip":
                # Label box:
                ax.add_patch(patches.FancyBboxPatch((px, py), item_w, item_h, boxstyle=f"round,pad=0,rounding_size={STRIP_R}", facecolor=bg, edgecolor="#CCCCCC", linewidth=0.5))
                # Category bar:
                ax.add_patch(patches.Rectangle((px, py), 2.8, item_h, facecolor=color, edgecolor="none"))
                # Title:
                title_txt = f"{spec.size} × {spec.length}".strip() if spec.comp_type not in ("nut", "nyloc", "insert", "washer") else f"{spec.size} {spec.length}".strip()
                ax.text(px + 4.0, py + 3.8, title_txt, fontsize=8.5, weight="bold", color="#111111", va="center")
                # Subtext 1:
                sub1 = spec.extra_note if spec.extra_note else (f"P: {spec.pitch}" + (f" | Tap: {spec.tap_drill.split()[0]}" if spec.tap_drill and spec.tap_drill.split() else ""))
                ax.text(px + 4.0, py + 6.6, sub1, fontsize=5.0, weight="semibold", color="#555555", va="center")
                # Subtext 2:
                sub2 = f"Key: {spec.tool_key}" if spec.tool_key else spec.material
                ax.text(px + 4.0, py + 8.8, sub2, fontsize=5.0, weight="bold", color=color, va="center")
            else:
                # Full wrap box:
                ax.add_patch(patches.FancyBboxPatch((px, py), item_w, item_h, boxstyle=f"round,pad=0,rounding_size={WRAP_R}", facecolor=bg, edgecolor="#CCCCCC", linewidth=0.5))
                # Window cutout:
                ax.add_patch(patches.FancyBboxPatch((px + WRAP_CUTOUT_X0, py + WRAP_CUTOUT_Y0), WRAP_CUTOUT_W, WRAP_CUTOUT_H, boxstyle=f"round,pad=0,rounding_size={WRAP_CUTOUT_R}", facecolor="#FFFFFF", edgecolor="#FF0055", linewidth=0.5, linestyle="--"))
                # Label title:
                title_txt = f"{spec.size} × {spec.length}".strip() if spec.comp_type not in ("nut", "nyloc", "insert", "washer") else f"{spec.size} {spec.length}".strip()
                ax.text(px + 6.0, py + 4.5, title_txt, fontsize=9.0, weight="bold", color="#111111", va="center")
                # Category bar on top:
                ax.add_patch(patches.Rectangle((px + 2.0, py + 1.0), 2.5, 9.0, facecolor=color, edgecolor="none"))

            idx += 1
        if idx >= len(labels):
            break

    plt.savefig(out_path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def compose_cricut_sheet(
    labels: list[FastenerSpec],
    title: str,
    paper: tuple[float, float] = PAPER_LETTER,
    output_dir: Path = Path("Labels/build"),
    label_format: str = "strip"  # "strip" (34x10) or "wrap" (38.6x76)
) -> tuple[Path, Path, Path]:
    """Compose a full printable sheet with Cricut fiducial registration frames, print artwork, vector cut paths, and PNG preview."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paper_w, paper_h = paper

    if label_format == "strip":
        item_w, item_h = STRIP_W, STRIP_H
        gap_x, gap_y = 3.0, 3.0
    else:
        item_w, item_h = WRAP_W, WRAP_H
        gap_x, gap_y = 4.0, 4.0

    margin_x = (paper_w - CRICUT_MAX_W) / 2.0
    margin_y = (paper_h - CRICUT_MAX_H) / 2.0

    cols = int((CRICUT_MAX_W + gap_x) / (item_w + gap_x))
    rows = int((CRICUT_MAX_H + gap_y) / (item_h + gap_y))

    # 1. Print Artwork Layer:
    print_svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {paper_w:.2f} {paper_h:.2f}" width="{paper_w:.2f}mm" height="{paper_h:.2f}mm">',
        f'<rect width="{paper_w}" height="{paper_h}" fill="#FFFFFF"/>',
        f'<text x="{margin_x}" y="{margin_y - 8.0}" font-family="Arial, sans-serif" font-size="5.0" font-weight="900" fill="#111111">{title}</text>',
        f'<text x="{margin_x}" y="{margin_y - 3.5}" font-family="Arial, sans-serif" font-size="2.8" fill="#666666">Gridfinity Glass-Window Cassette System — Format: {label_format.upper()} ({item_w} × {item_h} mm)</text>',
        f'<rect x="{margin_x - 4.0}" y="{margin_y - 4.0}" width="{CRICUT_MAX_W + 8.0}" height="{CRICUT_MAX_H + 8.0}" fill="none" stroke="#000000" stroke-width="2.0"/>',
    ]

    # 2. Vector Cut Path Layer:
    cut_svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {paper_w:.2f} {paper_h:.2f}" width="{paper_w:.2f}mm" height="{paper_h:.2f}mm">',
        f'<rect width="{paper_w}" height="{paper_h}" fill="none"/>',
        f'<rect x="{margin_x - 4.0}" y="{margin_y - 4.0}" width="{CRICUT_MAX_W + 8.0}" height="{CRICUT_MAX_H + 8.0}" fill="none" stroke="#000000" stroke-width="0.5"/>',
    ]

    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= len(labels):
                break
            spec = labels[idx]
            px = margin_x + c * (item_w + gap_x)
            py = margin_y + r * (item_h + gap_y)

            if label_format == "strip":
                print_svg.append(render_strip_label_svg(spec, x=px, y=py, include_cut_path=False))
                cut_svg.append(f'<rect x="{px:.2f}" y="{py:.2f}" width="{STRIP_W}" height="{STRIP_H}" rx="{STRIP_R}" fill="none" stroke="#FF0000" stroke-width="0.2"/>')
            else:
                print_svg.append(render_full_lid_wrap_svg(spec, x=px, y=py))
                cut_svg.append(f'<rect x="{px:.2f}" y="{py:.2f}" width="{WRAP_W}" height="{WRAP_H}" rx="{WRAP_R}" fill="none" stroke="#FF0000" stroke-width="0.2"/>')
                cut_svg.append(f'<rect x="{px + WRAP_CUTOUT_X0:.2f}" y="{py + WRAP_CUTOUT_Y0:.2f}" width="{WRAP_CUTOUT_W}" height="{WRAP_CUTOUT_H}" rx="{WRAP_CUTOUT_R}" fill="none" stroke="#FF0000" stroke-width="0.2"/>')

            idx += 1
        if idx >= len(labels):
            break

    print_svg.append("</svg>")
    cut_svg.append("</svg>")

    slug = title.lower().replace(" ", "_").replace("/", "_").replace("—", "_").replace(".", "_")
    print_path = output_dir / f"{slug}_print_{label_format}.svg"
    cut_path = output_dir / f"{slug}_cut_{label_format}.svg"
    png_path = output_dir / f"{slug}_preview_{label_format}.png"

    with print_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(print_svg))

    with cut_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(cut_svg))

    # Render PNG preview:
    render_png_sheet(labels, title, paper, png_path, label_format=label_format)

    return print_path, cut_path, png_path


# ==============================================================================
# PRESET HARDWARE ASSORTMENTS
# ==============================================================================

def load_database() -> dict[str, Any]:
    db_path = Path(__file__).parent / "data" / "fasteners.json"
    with db_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_metric_m3_assortment() -> list[FastenerSpec]:
    """Metric M3 Complete Shop Assortment (SHCS, BHCS, FHCS, Nuts, Washers)."""
    db = load_database()
    m_info = next(m for m in db["threads"]["metric"] if m["size"] == "M3")
    cat = db["categories"]["metric_coarse"]

    specs = []
    # M3 SHCS:
    for L in ["4 mm", "6 mm", "8 mm", "10 mm", "12 mm", "14 mm", "16 mm", "20 mm", "25 mm", "30 mm", "35 mm", "40 mm"]:
        specs.append(FastenerSpec(
            category="metric_coarse",
            size="M3",
            length=L,
            head="shcs",
            drive="hex",
            pitch=m_info["pitch_coarse"],
            tap_drill=m_info["tap_drill"],
            clearance_drill=m_info["clearance_drill"],
            tool_key=m_info["hex_key"]["shcs"],
            material="SS 304",
            accent_color=cat["color_hex"],
            bg_color=cat["color_bg"]
        ))

    # M3 BHCS:
    for L in ["6 mm", "8 mm", "10 mm", "12 mm", "16 mm", "20 mm"]:
        specs.append(FastenerSpec(
            category="metric_coarse",
            size="M3",
            length=L,
            head="bhcs",
            drive="hex",
            pitch=m_info["pitch_coarse"],
            tap_drill=m_info["tap_drill"],
            clearance_drill=m_info["clearance_drill"],
            tool_key=m_info["hex_key"]["bhcs"],
            material="SS 304",
            accent_color=cat["color_hex"],
            bg_color=cat["color_bg"]
        ))

    # M3 Nuts & Washers:
    specs.append(FastenerSpec(category="metric_coarse", size="M3", length="Hex Nut", comp_type="nut", pitch=m_info["pitch_coarse"], tool_key="5.5 mm", material="SS 304", accent_color=cat["color_hex"], bg_color=cat["color_bg"]))
    specs.append(FastenerSpec(category="metric_coarse", size="M3", length="Nyloc Nut", comp_type="nyloc", pitch=m_info["pitch_coarse"], tool_key="5.5 mm", material="SS 304", accent_color=cat["color_hex"], bg_color=cat["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="M3", length="Flat Washer", comp_type="washer", extra_note="OD: 7.0 mm | T: 0.5 mm", material="SS 304", accent_color="#2E7D32", bg_color="#EAF4EB"))
    specs.append(FastenerSpec(category="washers", size="M3", length="Split Lock", comp_type="split", extra_note="DIN 127 Spring Lock", material="SS 304", accent_color="#2E7D32", bg_color="#EAF4EB"))

    return specs


def build_metric_m2_m25_assortment() -> list[FastenerSpec]:
    """Metric M2 & M2.5 Micro-Fastener Assortment (Electronics & Drones)."""
    db = load_database()
    cat = db["categories"]["metric_coarse"]
    specs = []

    for size_name in ("M2", "M2.5"):
        m_info = next(m for m in db["threads"]["metric"] if m["size"] == size_name)
        for L in ["4 mm", "6 mm", "8 mm", "10 mm", "12 mm", "16 mm", "20 mm"]:
            specs.append(FastenerSpec(
                category="metric_coarse",
                size=size_name,
                length=L,
                head="shcs",
                drive="hex",
                pitch=m_info["pitch_coarse"],
                tap_drill=m_info["tap_drill"],
                clearance_drill=m_info["clearance_drill"],
                tool_key=m_info["hex_key"]["shcs"],
                material="SS 304",
                accent_color=cat["color_hex"],
                bg_color=cat["color_bg"]
            ))
        specs.append(FastenerSpec(category="metric_coarse", size=size_name, length="Hex Nut", comp_type="nut", pitch=m_info["pitch_coarse"], material="SS 304", accent_color=cat["color_hex"], bg_color=cat["color_bg"]))
        specs.append(FastenerSpec(category="washers", size=size_name, length="Flat Washer", comp_type="washer", material="SS 304", accent_color="#2E7D32", bg_color="#EAF4EB"))

    return specs


def build_metric_m4_m5_m6_assortment() -> list[FastenerSpec]:
    """Metric M4, M5, M6 Structural Hardware Assortment."""
    db = load_database()
    cat = db["categories"]["metric_coarse"]
    specs = []

    for size_name in ("M4", "M5", "M6"):
        m_info = next(m for m in db["threads"]["metric"] if m["size"] == size_name)
        for L in ["8 mm", "10 mm", "12 mm", "16 mm", "20 mm", "25 mm", "30 mm", "35 mm", "40 mm"]:
            specs.append(FastenerSpec(
                category="metric_coarse",
                size=size_name,
                length=L,
                head="shcs",
                drive="hex",
                pitch=m_info["pitch_coarse"],
                tap_drill=m_info["tap_drill"],
                clearance_drill=m_info["clearance_drill"],
                tool_key=m_info["hex_key"]["shcs"],
                material="12.9 Black",
                accent_color=cat["color_hex"],
                bg_color=cat["color_bg"]
            ))
        specs.append(FastenerSpec(category="metric_coarse", size=size_name, length="Hex Nut", comp_type="nut", pitch=m_info["pitch_coarse"], material="Class 10", accent_color=cat["color_hex"], bg_color=cat["color_bg"]))
        specs.append(FastenerSpec(category="metric_coarse", size=size_name, length="Nyloc Nut", comp_type="nyloc", pitch=m_info["pitch_coarse"], material="Class 10", accent_color=cat["color_hex"], bg_color=cat["color_bg"]))
        specs.append(FastenerSpec(category="washers", size=size_name, length="Flat Washer", comp_type="washer", material="Steel", accent_color="#2E7D32", bg_color="#EAF4EB"))

    return specs


def build_imperial_socket_assortment() -> list[FastenerSpec]:
    """Imperial / SAE (#4-40, #6-32, #8-32, 1/4\"-20) Assortment."""
    db = load_database()
    cat = db["categories"]["imperial_unc"]
    specs = []

    for size_name in ("#4-40", "#6-32", "#8-32", "1/4\"-20"):
        info = next(m for m in db["threads"]["imperial"] if m["size"] == size_name)
        for L in ["1/4\"", "3/8\"", "1/2\"", "5/8\"", "3/4\"", "1\"", "1-1/4\""]:
            specs.append(FastenerSpec(
                category="imperial_unc",
                size=size_name,
                length=L,
                head="shcs",
                drive="hex",
                pitch=f"{info['tpi_coarse']} TPI",
                tap_drill=info["tap_drill"],
                clearance_drill=info["clearance_drill"],
                tool_key=info["hex_key"]["shcs"],
                material="18-8 SS",
                accent_color=cat["color_hex"],
                bg_color=cat["color_bg"]
            ))
        specs.append(FastenerSpec(category="imperial_unc", size=size_name, length="Hex Nut", comp_type="nut", pitch=f"{info['tpi_coarse']} TPI", material="18-8 SS", accent_color=cat["color_hex"], bg_color=cat["color_bg"]))
        specs.append(FastenerSpec(category="imperial_unc", size=size_name, length="Nyloc Nut", comp_type="nyloc", pitch=f"{info['tpi_coarse']} TPI", material="18-8 SS", accent_color=cat["color_hex"], bg_color=cat["color_bg"]))
        specs.append(FastenerSpec(category="washers", size=size_name, length="Flat Washer", comp_type="washer", material="18-8 SS", accent_color="#2E7D32", bg_color="#EAF4EB"))

    return specs


def build_heat_set_insert_assortment() -> list[FastenerSpec]:
    """Brass Heat-Set Threaded Inserts (3D Printing Standard)."""
    db = load_database()
    cat = db["categories"]["heat_set_inserts"]
    specs = []

    for item in db["heat_set_inserts"]:
        specs.append(FastenerSpec(
            category="heat_set_inserts",
            size=item["size"],
            length=f"L: {item['length']}",
            comp_type="insert",
            extra_note=f"Hole: Ø{item['print_hole_dia']} × {item['print_hole_depth']}",
            material="Brass",
            accent_color=cat["color_hex"],
            bg_color=cat["color_bg"]
        ))
    return specs


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Generating Cricut-ready printable label sheets and PNG previews...")

    assortments = [
        ("Metric M3 Fastener Assortment", build_metric_m3_assortment()),
        ("Metric M2 and M2.5 Micro Assortment", build_metric_m2_m25_assortment()),
        ("Metric M4 M5 M6 Structural Assortment", build_metric_m4_m5_m6_assortment()),
        ("Imperial SAE Socket Assortment", build_imperial_socket_assortment()),
        ("Brass Heat Set Insert Assortment", build_heat_set_insert_assortment()),
    ]

    manifest = {
        "format": "Cricut Print-Then-Cut Fastener Label Sheets",
        "standard_strip_dimensions_mm": [STRIP_W, STRIP_H],
        "full_lid_wrap_dimensions_mm": [WRAP_W, WRAP_H],
        "glass_window_clearance_mm": [WRAP_CUTOUT_W, WRAP_CUTOUT_H],
        "sheets": []
    }

    for title, specs in assortments:
        # 1. Standard Strip Sheet (34 x 10 mm):
        p_print_strip, p_cut_strip, p_png_strip = compose_cricut_sheet(specs, title, PAPER_LETTER, out_dir, label_format="strip")
        print(f"Generated {p_print_strip.name}, {p_cut_strip.name}, {p_png_strip.name} ({len(specs)} labels)")

        # 2. Full-Lid Wrap Sheet (38.6 x 76.0 mm):
        p_print_wrap, p_cut_wrap, p_png_wrap = compose_cricut_sheet(specs, title, PAPER_LETTER, out_dir, label_format="wrap")
        print(f"Generated {p_print_wrap.name}, {p_cut_wrap.name}, {p_png_wrap.name} ({len(specs)} wraps)")

        manifest["sheets"].append({
            "title": title,
            "label_count": len(specs),
            "print_strip_svg": str(p_print_strip.name),
            "cut_strip_svg": str(p_cut_strip.name),
            "preview_strip_png": str(p_png_strip.name),
            "print_wrap_svg": str(p_print_wrap.name),
            "cut_wrap_svg": str(p_cut_wrap.name),
            "preview_wrap_png": str(p_png_wrap.name),
        })

    manifest_path = out_dir / "manifest_labels.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Label generation complete! Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
