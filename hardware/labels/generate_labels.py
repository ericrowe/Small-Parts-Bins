#!/usr/bin/env python3
"""Generate High-Density, Printable, Cricut-Ready Fastener Label Sheets with Bleed Protection.

Features:
  - Print-Then-Cut Bleed Protection: +1.0 mm full bleed on all sides (36 x 12 mm artwork envelope)
    to prevent white edge slivers and misaligned cuts from printer/Cricut mechanical shift.
  - Safe Text & Icon Inset: Keeps all typography and silhouettes safely inside the cut perimeter.
  - High-Density Tiling: Packs up to 72 labels (4 columns x 18 rows) per Letter sheet to eliminate wasted paper.
  - Master Combined Sheets:
      * Master Sheet 1 (Metric & Inserts - 70 Labels): All M2–M6 socket screws, nuts, washers, and heat-set inserts.
      * Master Sheet 2 (Imperial & Specialty/Wood - 72 Labels): All SAE #4-40–1/4" screws, grub screws, wood & sheet metal.
  - Standard 34 x 10 mm Finished Strip Size with R = 1.0 mm rounded corners.
"""

from __future__ import annotations

import json
import math
import re
import xml.etree.ElementTree as ET
import xml.sax.saxutils as sax
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from vector_icons import get_component_icon_svg, get_drive_icon_svg, get_head_icon_svg

# ==============================================================================
# DIMENSIONAL CONSTANTS (millimeters)
# ==============================================================================

# Finished Cut Label:
STRIP_W = 34.00
STRIP_H = 10.00
STRIP_R = 1.00  # Corner radius

# Bleed Geometry (extends 1.0 mm beyond cut line on all sides):
BLEED = 1.00
BLEED_W = STRIP_W + 2 * BLEED  # 36.00 mm
BLEED_H = STRIP_H + 2 * BLEED  # 12.00 mm
BLEED_R = STRIP_R + BLEED      # 2.00 mm

# Safe Text & Icon Inset:
TEXT_X0 = 4.20  # Safe clearance past 2.6 mm accent bar + 1.0 mm bleed shift

# Standard Paper Sizes (mm):
PAPER_LETTER = (215.9, 279.4)  # 8.5 x 11 in
PAPER_A4 = (210.0, 297.0)

# Cricut Print-Then-Cut Safe Printable Area:
CRICUT_MAX_W = 171.45
CRICUT_MAX_H = 234.95

# Grid Geometry:
GAP_X = 3.00
GAP_Y = 3.00
GRID_COLS = int((CRICUT_MAX_W + GAP_X) / (STRIP_W + GAP_X))  # 4 columns
GRID_ROWS = int((CRICUT_MAX_H + GAP_Y) / (STRIP_H + GAP_Y))  # 18 rows
MAX_LABELS_PER_SHEET = GRID_COLS * GRID_ROWS                  # 72 labels per sheet

# Standard Typography Constants (Uniform across all labels):
FONT_TITLE_SIZE_MM = 3.0   # Standard title font size
FONT_SUB1_SIZE_MM = 1.7    # Standard subtext 1 font size
FONT_SUB2_SIZE_MM = 1.7    # Standard subtext 2 font size

# ==============================================================================
# XML ESCAPING & SLUG HELPERS
# ==============================================================================

def clean_id(prefix: str, *parts: Any) -> str:
    """Generate a 100% valid XML ID slug without spaces, quotes, slashes, or hashes."""
    raw = "_".join(str(p) for p in parts if p)
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{prefix}_{raw}")
    return re.sub(r"_+", "_", slug).strip("_")


def escape_xml(s: Any) -> str:
    """Escape XML special characters in text nodes (&, <, >, quotes)."""
    return sax.escape(str(s), {'"': "&quot;", "'": "&apos;"})


# ==============================================================================
# FASTENER SPECIFICATION DATA MODEL & FORMATTING
# ==============================================================================

@dataclass
class FastenerSpec:
    category: str           # "metric_coarse", "imperial_unc", "heat_set_inserts", "washers", "specialty", etc.
    size: str               # "M3", "#4-40", "1/4\"-20", "#6", etc.
    length: str = ""        # "12 mm", "1/2\"", "Standard", etc.
    head: str = "shcs"      # "shcs", "bhcs", "fhcs", "hex", "pan", "none"
    drive: str = "hex"      # "hex", "torx", "phillips", "none"
    comp_type: str = "bolt" # "bolt", "nut", "nyloc", "washer", "insert", "pin", "standoff", "wood"
    pitch: str = ""         # "0.5", "40 TPI", etc.
    tap_drill: str = ""     # "2.5 mm (#39)", "#43 (0.089\")", etc.
    clearance_drill: str = ""
    tool_key: str = ""      # "2.5 mm", "3/32\"", "T10", "PH2", etc.
    material: str = ""      # "SS 304", "12.9", "GR 8", "Brass", "Zinc", etc.
    accent_color: str = ""
    bg_color: str = ""
    extra_note: str = ""


def format_label_strings(spec: FastenerSpec) -> tuple[str, str, str]:
    """Format label text strings cleanly with standard concise nomenclature."""
    if spec.comp_type in ("nut", "nyloc"):
        suffix = spec.length.replace(" Nut", "").strip()
        title = f"{spec.size} {suffix}".strip()
        sub1 = spec.pitch if spec.pitch else ""
        sub2 = f"Key {spec.tool_key}" if spec.tool_key else spec.material
    elif spec.comp_type in ("washer", "split"):
        suffix = spec.length.replace(" Washer", "").strip()
        title = f"{spec.size} {suffix}".strip()
        sub1 = spec.extra_note or ""
        sub2 = spec.material or ""
    elif spec.comp_type == "insert":
        len_str = spec.length.replace("L: ", "").strip()
        title = f"{spec.size} × {len_str}".strip()
        sub1 = spec.extra_note.replace("Hole: ", "").strip() if spec.extra_note else ""
        sub2 = "Brass Insert"
    elif spec.comp_type == "pin":
        title = f"{spec.size} × {spec.length}".strip()
        sub1 = spec.extra_note or "Dowel Pin"
        sub2 = spec.material or "Hardened Steel"
    elif spec.comp_type == "standoff":
        title = f"{spec.size} × {spec.length}".strip()
        sub1 = spec.extra_note or "Hex Standoff"
        sub2 = f"Key {spec.tool_key}" if spec.tool_key else spec.material
    else:
        title = f"{spec.size} × {spec.length}".strip() if spec.length else spec.size
        p_str = spec.pitch if spec.pitch else ""
        tap_str = spec.tap_drill.split()[0] if (spec.tap_drill and spec.tap_drill.split()) else ""
        sub1 = f"{p_str} | Tap {tap_str}" if (p_str and tap_str) else (spec.extra_note or p_str or tap_str)
        sub2 = f"Key {spec.tool_key}" if spec.tool_key else spec.material

    return title, sub1, sub2


# ==============================================================================
# STANDALONE LABEL RENDERER (Pure Vector SVG with Bleed Support)
# ==============================================================================

def render_strip_label_svg(spec: FastenerSpec, x: float = 0.0, y: float = 0.0, include_bleed: bool = True) -> str:
    """Render a standard cassette lid strip label as SVG with +1.0 mm bleed protection."""
    color = spec.accent_color or "#0077CC"
    bg = spec.bg_color or "#FFFFFF"

    main_title, sub_text_1, sub_text_2 = format_label_strings(spec)
    icon_x = x + STRIP_W - 8.5
    node_id = clean_id("label", spec.size, spec.length, int(x), int(y))

    svg_parts = [
        f'<g id="{node_id}" transform="translate({x:.2f},{y:.2f})">'
    ]

    if include_bleed:
        # Full Bleed Background Rectangle (extends -1.0 mm to +35.0 mm):
        svg_parts.append(
            f'<rect x="{-BLEED:.2f}" y="{-BLEED:.2f}" width="{BLEED_W:.2f}" height="{BLEED_H:.2f}" rx="{BLEED_R:.2f}" fill="{bg}" stroke="none"/>'
        )
        # Bleed Left Accent Bar (extends from X=-1.0 to X=3.6 mm, Y=-1.0 to Y=11.0 mm with rounded outer corners):
        svg_parts.append(
            f'<path d="M {-BLEED:.2f},{BLEED_R - BLEED:.2f} A {BLEED_R:.2f},{BLEED_R:.2f} 0 0,1 {BLEED_R - BLEED:.2f},{-BLEED:.2f} L 3.60,{-BLEED:.2f} L 3.60,{STRIP_H + BLEED:.2f} L {BLEED_R - BLEED:.2f},{STRIP_H + BLEED:.2f} A {BLEED_R:.2f},{BLEED_R:.2f} 0 0,1 {-BLEED:.2f},{STRIP_H + BLEED - BLEED_R:.2f} Z" fill="{color}"/>'
        )
    else:
        # Exact Cut Box:
        svg_parts.append(
            f'<rect x="0" y="0" width="{STRIP_W}" height="{STRIP_H}" rx="{STRIP_R}" fill="{bg}" stroke="#CCCCCC" stroke-width="0.2"/>'
        )
        svg_parts.append(
            f'<path d="M 0,{STRIP_R} A {STRIP_R},{STRIP_R} 0 0,1 {STRIP_R},0 L 2.6,0 L 2.6,{STRIP_H} L {STRIP_R},{STRIP_H} A {STRIP_R},{STRIP_R} 0 0,1 0,{STRIP_H - STRIP_R} Z" fill="{color}"/>'
        )

    # Main Title (Safe Inset Bold Font with XML escaping):
    svg_parts.append(
        f'<text x="{TEXT_X0}" y="3.8" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="{FONT_TITLE_SIZE_MM:.1f}" fill="#111111">{escape_xml(main_title)}</text>'
    )
    # Subtext line 1 (Pitch / Tap):
    svg_parts.append(
        f'<text x="{TEXT_X0}" y="6.4" font-family="Arial, Helvetica, sans-serif" font-weight="normal" font-size="{FONT_SUB1_SIZE_MM:.1f}" fill="#444444">{escape_xml(sub_text_1)}</text>'
    )
    # Subtext line 2 (Drive Tool / Material):
    svg_parts.append(
        f'<text x="{TEXT_X0}" y="8.6" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="{FONT_SUB2_SIZE_MM:.1f}" fill="{color}">{escape_xml(sub_text_2)}</text>'
    )

    # Render silhouette icons (safely within cut perimeter):
    if spec.comp_type in ("nut", "nyloc", "insert", "washer", "split"):
        svg_parts.append(get_component_icon_svg(spec.comp_type, icon_x - x, 1.5, 6.8, 6.8, color="#222222"))
    else:
        # Head icon:
        if spec.head and spec.head != "none":
            svg_parts.append(get_head_icon_svg(spec.head, icon_x - x, 0.8, 6.5, 4.2, color="#222222"))
        # Drive icon:
        if spec.drive and spec.drive != "none":
            svg_parts.append(get_drive_icon_svg(spec.drive, icon_x - x + 1.2, 5.2, 4.0, color=color))

    svg_parts.append("</g>")
    return "\n".join(svg_parts)


# ==============================================================================
# HIGH-DENSITY CRICUT SHEET COMPOSER & PNG RENDERER
# ==============================================================================

def render_png_page(
    labels: list[FastenerSpec],
    title: str,
    paper: tuple[float, float],
    out_path: Path,
    page_num: int = 1,
    total_pages: int = 1
):
    """Render a high-resolution 200 DPI PNG preview showing both printed bleed and overlaid cut paths."""
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
    header_txt = title if total_pages == 1 else f"{title} (Sheet {page_num} of {total_pages})"
    ax.text(margin_x, margin_y - 8.0, header_txt, fontsize=13, weight="bold", color="#111111")
    ax.text(margin_x, margin_y - 3.0, f"Gridfinity Cassette Labels (+1.0 mm Bleed Protected) — 34 × 10 mm Cut ({len(labels)} labels packed)", fontsize=8, color="#666666")

    # Cricut registration boundary frame:
    ax.add_patch(patches.Rectangle((margin_x - 4.0, margin_y - 4.0), CRICUT_MAX_W + 8.0, CRICUT_MAX_H + 8.0, fill=False, edgecolor="#000000", linewidth=2.0))

    idx = 0
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if idx >= len(labels):
                break
            spec = labels[idx]
            px = margin_x + c * (STRIP_W + GAP_X)
            py = margin_y + r * (STRIP_H + GAP_Y)

            color = spec.accent_color or "#0077CC"
            bg = spec.bg_color or "#FFFFFF"

            main_title, sub1, sub2 = format_label_strings(spec)

            # 1. Bleed Background Box (36 x 12 mm):
            ax.add_patch(patches.FancyBboxPatch((px - BLEED, py - BLEED), BLEED_W, BLEED_H, boxstyle=f"round,pad=0,rounding_size={BLEED_R}", facecolor=bg, edgecolor="none"))
            # 2. Bleed Category Bar (4.6 x 12 mm):
            ax.add_patch(patches.Rectangle((px - BLEED, py - BLEED), 3.6 + BLEED, BLEED_H, facecolor=color, edgecolor="none"))

            # 3. Vector Cut Line Overlay (Red Dashed Line at exact 34 x 10 mm):
            ax.add_patch(patches.FancyBboxPatch((px, py), STRIP_W, STRIP_H, boxstyle=f"round,pad=0,rounding_size={STRIP_R}", facecolor="none", edgecolor="#FF0055", linewidth=0.6, linestyle="--"))

            # Typography:
            ax.text(px + TEXT_X0, py + 3.6, main_title, fontsize=8.0, weight="bold", color="#111111", va="center")
            ax.text(px + TEXT_X0, py + 6.3, sub1, fontsize=4.8, weight="normal", color="#555555", va="center")
            ax.text(px + TEXT_X0, py + 8.5, sub2, fontsize=4.8, weight="bold", color=color, va="center")

            idx += 1
        if idx >= len(labels):
            break

    plt.savefig(out_path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def compose_high_density_sheets(
    labels: list[FastenerSpec],
    title: str,
    paper: tuple[float, float] = PAPER_LETTER,
    output_dir: Path = Path("hardware/labels/build"),
) -> list[dict[str, Any]]:
    """Chunk labels into high-density 72-label sheets with +1.0 mm bleed print artwork and exact vector cut paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paper_w, paper_h = paper

    margin_x = (paper_w - CRICUT_MAX_W) / 2.0
    margin_y = (paper_h - CRICUT_MAX_H) / 2.0

    total_items = len(labels)
    total_pages = max(1, math.ceil(total_items / MAX_LABELS_PER_SHEET))
    results = []

    for page_idx in range(total_pages):
        start_idx = page_idx * MAX_LABELS_PER_SHEET
        chunk = labels[start_idx : start_idx + MAX_LABELS_PER_SHEET]
        page_num = page_idx + 1

        page_title = title if total_pages == 1 else f"{title} (Sheet {page_num} of {total_pages})"
        slug_base = clean_id("", title).lower()
        slug = slug_base if total_pages == 1 else f"{slug_base}_sheet_{page_num}"

        # 1. Print Artwork Layer (With +1.0 mm Bleed Protection):
        print_svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {paper_w:.2f} {paper_h:.2f}" width="{paper_w:.2f}mm" height="{paper_h:.2f}mm">',
            f'<rect width="{paper_w}" height="{paper_h}" fill="#FFFFFF"/>',
            f'<text x="{margin_x}" y="{margin_y - 8.0}" font-family="Arial, sans-serif" font-size="5.0" font-weight="bold" fill="#111111">{escape_xml(page_title)}</text>',
            f'<text x="{margin_x}" y="{margin_y - 3.5}" font-family="Arial, sans-serif" font-size="2.8" fill="#666666">Gridfinity Glass-Window Cassette System — 34 × 10 mm Strips (+1.0 mm Bleed Protected, {len(chunk)} labels)</text>',
            f'<rect x="{margin_x - 4.0}" y="{margin_y - 4.0}" width="{CRICUT_MAX_W + 8.0}" height="{CRICUT_MAX_H + 8.0}" fill="none" stroke="#000000" stroke-width="2.0"/>',
        ]

        # 2. Vector Cut Path Layer (Exact 34.0 x 10.0 mm kiss-cut paths):
        cut_svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {paper_w:.2f} {paper_h:.2f}" width="{paper_w:.2f}mm" height="{paper_h:.2f}mm">',
            f'<rect width="{paper_w}" height="{paper_h}" fill="none"/>',
            f'<rect x="{margin_x - 4.0}" y="{margin_y - 4.0}" width="{CRICUT_MAX_W + 8.0}" height="{CRICUT_MAX_H + 8.0}" fill="none" stroke="#000000" stroke-width="0.5"/>',
        ]

        idx = 0
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if idx >= len(chunk):
                    break
                spec = chunk[idx]
                px = margin_x + c * (STRIP_W + GAP_X)
                py = margin_y + r * (STRIP_H + GAP_Y)

                # Print layer includes +1.0 mm bleed:
                print_svg.append(render_strip_label_svg(spec, x=px, y=py, include_bleed=True))
                # Cut layer stays exact 34 x 10 mm:
                cut_svg.append(f'<rect x="{px:.2f}" y="{py:.2f}" width="{STRIP_W}" height="{STRIP_H}" rx="{STRIP_R}" fill="none" stroke="#FF0000" stroke-width="0.2"/>')

                idx += 1
            if idx >= len(chunk):
                break

        print_svg.append("</svg>")
        cut_svg.append("</svg>")

        print_path = output_dir / f"{slug}_print.svg"
        cut_path = output_dir / f"{slug}_cut.svg"
        png_path = output_dir / f"{slug}_preview.png"

        with print_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(print_svg))

        with cut_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(cut_svg))

        # Render high-res PNG preview:
        render_png_page(chunk, title, paper, png_path, page_num=page_num, total_pages=total_pages)

        # Validate output XML:
        try:
            ET.parse(print_path)
            ET.parse(cut_path)
        except Exception as e:
            raise ValueError(f"Generated invalid XML for {page_title}: {e}")

        results.append({
            "sheet_title": page_title,
            "label_count": len(chunk),
            "print_svg": str(print_path.name),
            "cut_svg": str(cut_path.name),
            "preview_png": str(png_path.name),
        })

    return results


# ==============================================================================
# HARDWARE ASSORTMENTS
# ==============================================================================

def load_database() -> dict[str, Any]:
    db_path = Path(__file__).parent / "data" / "fasteners.json"
    with db_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_master_metric_sheet_72() -> list[FastenerSpec]:
    """Master Metric & Inserts Sheet (Exactly 70 labels packed for 1 Letter sheet)."""
    db = load_database()
    cat_metric = db["categories"]["metric_coarse"]
    cat_washers = db["categories"]["washers"]
    cat_inserts = db["categories"]["heat_set_inserts"]
    specs = []

    # 1. M2 (SHCS 4, 6, 8, 10, 12, 16 mm + Nut + Washer) = 8 labels
    for L in ["4 mm", "6 mm", "8 mm", "10 mm", "12 mm", "16 mm"]:
        specs.append(FastenerSpec(category="metric_coarse", size="M2", length=L, head="shcs", drive="hex", pitch="0.4", tap_drill="1.6 mm", tool_key="1.5 mm", material="SS 304", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="metric_coarse", size="M2", length="Hex Nut", comp_type="nut", pitch="0.4", material="SS 304", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="M2", length="Flat Washer", comp_type="washer", material="SS 304", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 2. M2.5 (SHCS 4, 6, 8, 10, 12, 16 mm + Nut + Washer) = 8 labels
    for L in ["4 mm", "6 mm", "8 mm", "10 mm", "12 mm", "16 mm"]:
        specs.append(FastenerSpec(category="metric_coarse", size="M2.5", length=L, head="shcs", drive="hex", pitch="0.45", tap_drill="2.05 mm", tool_key="2.0 mm", material="SS 304", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="metric_coarse", size="M2.5", length="Hex Nut", comp_type="nut", pitch="0.45", material="SS 304", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="M2.5", length="Flat Washer", comp_type="washer", material="SS 304", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 3. M3 Complete (SHCS 4 to 30 mm, BHCS 6 to 16 mm, Nuts, Nylocs, Washers) = 22 labels
    m3_shcs = ["4 mm", "6 mm", "8 mm", "10 mm", "12 mm", "14 mm", "16 mm", "20 mm", "25 mm", "30 mm"]
    for L in m3_shcs:
        specs.append(FastenerSpec(category="metric_coarse", size="M3", length=L, head="shcs", drive="hex", pitch="0.5", tap_drill="2.5 mm", tool_key="2.5 mm", material="SS 304", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    m3_bhcs = ["6 mm", "8 mm", "10 mm", "12 mm", "16 mm", "20 mm"]
    for L in m3_bhcs:
        specs.append(FastenerSpec(category="metric_coarse", size="M3", length=L, head="bhcs", drive="hex", pitch="0.5", tap_drill="2.5 mm", tool_key="2.0 mm", material="SS 304", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="metric_coarse", size="M3", length="Hex Nut", comp_type="nut", pitch="0.5", tool_key="5.5 mm", material="SS 304", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="metric_coarse", size="M3", length="Nyloc Nut", comp_type="nyloc", pitch="0.5", tool_key="5.5 mm", material="SS 304", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="M3", length="Flat Washer", comp_type="washer", extra_note="OD: 7.0 mm", material="SS 304", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="M3", length="Split Lock", comp_type="split", extra_note="DIN 127 Spring", material="SS 304", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 4. M4 Structural (SHCS 8, 10, 12, 16, 20, 25, 30 mm + Nut + Nyloc + Washer) = 10 labels
    for L in ["8 mm", "10 mm", "12 mm", "16 mm", "20 mm", "25 mm", "30 mm"]:
        specs.append(FastenerSpec(category="metric_coarse", size="M4", length=L, head="shcs", drive="hex", pitch="0.7", tap_drill="3.3 mm", tool_key="3.0 mm", material="12.9 Black", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="metric_coarse", size="M4", length="Hex Nut", comp_type="nut", pitch="0.7", material="Class 10", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="metric_coarse", size="M4", length="Nyloc Nut", comp_type="nyloc", pitch="0.7", material="Class 10", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="M4", length="Flat Washer", comp_type="washer", material="Steel", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 5. M5 Structural (SHCS 10, 12, 16, 20, 25, 30 mm + Nut + Washer) = 8 labels
    for L in ["10 mm", "12 mm", "16 mm", "20 mm", "25 mm", "30 mm"]:
        specs.append(FastenerSpec(category="metric_coarse", size="M5", length=L, head="shcs", drive="hex", pitch="0.8", tap_drill="4.2 mm", tool_key="4.0 mm", material="12.9 Black", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="metric_coarse", size="M5", length="Hex Nut", comp_type="nut", pitch="0.8", material="Class 10", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="M5", length="Flat Washer", comp_type="washer", material="Steel", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 6. M6 Structural (SHCS 12, 16, 20, 25, 30 mm + Nut + Washer) = 7 labels
    for L in ["12 mm", "16 mm", "20 mm", "25 mm", "30 mm"]:
        specs.append(FastenerSpec(category="metric_coarse", size="M6", length=L, head="shcs", drive="hex", pitch="1.0", tap_drill="5.0 mm", tool_key="5.0 mm", material="12.9 Black", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="metric_coarse", size="M6", length="Hex Nut", comp_type="nut", pitch="1.0", material="Class 10", accent_color=cat_metric["color_hex"], bg_color=cat_metric["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="M6", length="Flat Washer", comp_type="washer", material="Steel", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 7. Brass Heat-Set Inserts (M2, M2.5, M3 short/std/long, M4, M5) = 9 labels
    for item in db["heat_set_inserts"]:
        specs.append(FastenerSpec(
            category="heat_set_inserts",
            size=item["size"],
            length=f"L: {item['length']}",
            comp_type="insert",
            extra_note=f"Ø{item['print_hole_dia']} × {item['print_hole_depth']}",
            material="Brass",
            accent_color=cat_inserts["color_hex"],
            bg_color=cat_inserts["color_bg"]
        ))

    return specs  # 70 labels packed on 1 sheet


def build_master_imperial_and_wood_sheet_72() -> list[FastenerSpec]:
    """Master Imperial & Wood/Specialty Sheet (Exactly 72 labels packed for 1 Letter sheet)."""
    db = load_database()
    cat_imp = db["categories"]["imperial_unc"]
    cat_spec = db["categories"]["specialty"]
    cat_washers = db["categories"]["washers"]
    specs = []

    # 1. #4-40 (SHCS 1/4" to 1", Nut, Nyloc, Washer) = 9 labels
    for L in ["1/4\"", "3/8\"", "1/2\"", "5/8\"", "3/4\"", "1\""]:
        specs.append(FastenerSpec(category="imperial_unc", size="#4-40", length=L, head="shcs", drive="hex", pitch="40 TPI", tap_drill="#43", tool_key="3/32\"", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="imperial_unc", size="#4-40", length="Hex Nut", comp_type="nut", pitch="40 TPI", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="imperial_unc", size="#4-40", length="Nyloc Nut", comp_type="nyloc", pitch="40 TPI", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="#4", length="Flat Washer", comp_type="washer", material="18-8 SS", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 2. #6-32 (SHCS 1/4" to 1", Nut, Nyloc, Washer) = 9 labels
    for L in ["1/4\"", "3/8\"", "1/2\"", "5/8\"", "3/4\"", "1\""]:
        specs.append(FastenerSpec(category="imperial_unc", size="#6-32", length=L, head="shcs", drive="hex", pitch="32 TPI", tap_drill="#36", tool_key="7/64\"", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="imperial_unc", size="#6-32", length="Hex Nut", comp_type="nut", pitch="32 TPI", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="imperial_unc", size="#6-32", length="Nyloc Nut", comp_type="nyloc", pitch="32 TPI", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="#6", length="Flat Washer", comp_type="washer", material="18-8 SS", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 3. #8-32 (SHCS 1/4" to 1-1/4", Nut, Nyloc, Washer) = 10 labels
    for L in ["1/4\"", "3/8\"", "1/2\"", "5/8\"", "3/4\"", "1\"", "1-1/4\""]:
        specs.append(FastenerSpec(category="imperial_unc", size="#8-32", length=L, head="shcs", drive="hex", pitch="32 TPI", tap_drill="#29", tool_key="9/64\"", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="imperial_unc", size="#8-32", length="Hex Nut", comp_type="nut", pitch="32 TPI", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="imperial_unc", size="#8-32", length="Nyloc Nut", comp_type="nyloc", pitch="32 TPI", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="#8", length="Flat Washer", comp_type="washer", material="18-8 SS", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 4. 1/4"-20 (SHCS 3/8" to 1-1/4", Nut, Nyloc, Washer) = 9 labels
    for L in ["3/8\"", "1/2\"", "5/8\"", "3/4\"", "1\"", "1-1/4\""]:
        specs.append(FastenerSpec(category="imperial_unc", size="1/4\"-20", length=L, head="shcs", drive="hex", pitch="20 TPI", tap_drill="#7", tool_key="3/16\"", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="imperial_unc", size="1/4\"-20", length="Hex Nut", comp_type="nut", pitch="20 TPI", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="imperial_unc", size="1/4\"-20", length="Nyloc Nut", comp_type="nyloc", pitch="20 TPI", material="18-8 SS", accent_color=cat_imp["color_hex"], bg_color=cat_imp["color_bg"]))
    specs.append(FastenerSpec(category="washers", size="1/4\"", length="Flat Washer", comp_type="washer", material="18-8 SS", accent_color=cat_washers["color_hex"], bg_color=cat_washers["color_bg"]))

    # 5. Set / Grub Screws (Cup Point Hex) = 12 labels
    for size, length, key in [
        ("M3", "3 mm", "1.5 mm"), ("M3", "4 mm", "1.5 mm"), ("M3", "6 mm", "1.5 mm"), ("M3", "8 mm", "1.5 mm"),
        ("M4", "4 mm", "2.0 mm"), ("M4", "6 mm", "2.0 mm"), ("M4", "8 mm", "2.0 mm"),
        ("M5", "5 mm", "2.5 mm"), ("M5", "8 mm", "2.5 mm"),
        ("#4-40", "1/8\"", "0.050\""), ("#6-32", "3/16\"", "1/16\""), ("#8-32", "1/4\"", "5/64\"")
    ]:
        specs.append(FastenerSpec(category="specialty", size=size, length=length, head="none", drive="hex", comp_type="bolt", extra_note="Grub Screw", tool_key=key, material="12.9 Steel", accent_color=cat_spec["color_hex"], bg_color=cat_spec["color_bg"]))

    # 6. Wood Screws (Countersunk Flat Head) = 13 labels
    for size, length, drive, key in [
        ("#4", "1/2\"", "phillips", "PH1"), ("#4", "3/4\"", "phillips", "PH1"), ("#4", "1\"", "phillips", "PH1"),
        ("#6", "1/2\"", "phillips", "PH2"), ("#6", "3/4\"", "phillips", "PH2"), ("#6", "1\"", "phillips", "PH2"), ("#6", "1-1/4\"", "phillips", "PH2"), ("#6", "1-1/2\"", "phillips", "PH2"),
        ("#8", "3/4\"", "torx", "T20"), ("#8", "1\"", "torx", "T20"), ("#8", "1-1/4\"", "torx", "T20"), ("#8", "1-1/2\"", "torx", "T20"), ("#8", "2\"", "torx", "T20")
    ]:
        specs.append(FastenerSpec(category="specialty", size=size, length=length, head="fhcs", drive=drive, comp_type="bolt", extra_note="Wood Screw", tool_key=key, material="Zinc Plated", accent_color=cat_spec["color_hex"], bg_color=cat_spec["color_bg"]))

    # 7. Dowel Pins & Standoffs = 10 labels
    for dia, length in [("Ø2.0", "10 mm"), ("Ø3.0", "12 mm"), ("Ø3.0", "16 mm"), ("Ø4.0", "20 mm"), ("Ø5.0", "25 mm")]:
        specs.append(FastenerSpec(category="specialty", size=dia, length=length, head="none", drive="none", comp_type="pin", extra_note="Dowel Pin", material="Hardened Steel", accent_color=cat_spec["color_hex"], bg_color=cat_spec["color_bg"]))
    for length in ["6+6 mm", "10+6 mm", "15+6 mm", "20+6 mm"]:
        specs.append(FastenerSpec(category="specialty", size="M3", length=length, head="hex", drive="none", comp_type="standoff", extra_note="Hex Standoff", tool_key="5.0 mm", material="Brass", accent_color=cat_spec["color_hex"], bg_color=cat_spec["color_bg"]))
    specs.append(FastenerSpec(category="specialty", size="M3", length="8 mm", head="pan", drive="torx", comp_type="bolt", extra_note="Plastic Thread", tool_key="T10", material="Black", accent_color=cat_spec["color_hex"], bg_color=cat_spec["color_bg"]))

    return specs  # 72 labels packed on 1 sheet


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Generating High-Density Master Combined Fastener Sheets with +1.0 mm Bleed Protection...")

    sheets_to_generate = [
        ("Master Metric and Inserts Assortment", build_master_metric_sheet_72()),
        ("Master Imperial and Wood Specialty Assortment", build_master_imperial_and_wood_sheet_72()),
    ]

    manifest = {
        "format": "High-Density Cricut Print-Then-Cut Strip Sheets with Bleed",
        "paper_size_mm": list(PAPER_LETTER),
        "grid_layout": {"cols": GRID_COLS, "rows": GRID_ROWS, "max_labels_per_sheet": MAX_LABELS_PER_SHEET},
        "label_dimensions_mm": [STRIP_W, STRIP_H],
        "bleed_margin_mm": BLEED,
        "typography": {
            "title_size_mm": FONT_TITLE_SIZE_MM,
            "sub1_size_mm": FONT_SUB1_SIZE_MM,
            "sub2_size_mm": FONT_SUB2_SIZE_MM,
        },
        "master_sheets": []
    }

    for title, specs in sheets_to_generate:
        pages = compose_high_density_sheets(specs, title, PAPER_LETTER, out_dir)
        for p in pages:
            print(f"Generated {p['print_svg']}, {p['cut_svg']}, {p['preview_png']} ({p['label_count']} labels)")
            manifest["master_sheets"].append(p)

    manifest_path = out_dir / "manifest_labels.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nAll Master Combined sheets generated successfully! Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
