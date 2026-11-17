"""Cricut Print-Then-Cut Exporter for Fastener and Storage Labels.

Generates standard multi-up SVG sheets with optical sensor registration marks,
+1.0mm bleed artwork layer for high-tolerance printing, and exact 11x34mm cut path layers
for each [Label A | Label B] vertical split cartridge pair so the finished labels are
identical to the paper-cutter split pairs.
"""

from __future__ import annotations

import datetime
from typing import Any, List
from hardware.labels.canonical_label import (
    BLEED,
    VERT_LABEL_H,
    VERT_LABEL_W,
    LabelData,
    escape_xml,
    render_vertical_split_label_pair_svg,
)

# Page Dimensions (mm)
PAGE_W_LETTER = 215.90  # 8.5 in
PAGE_H_LETTER = 279.40  # 11.0 in

# Cricut Print Then Cut Max Printable Area (Sensor Box)
SENSOR_BOX_W = 171.45   # 6.75 in
SENSOR_BOX_H = 234.95   # 9.25 in
SENSOR_BOX_X = (PAGE_W_LETTER - SENSOR_BOX_W) / 2.0  # 22.225 mm
SENSOR_BOX_Y = 24.00    # Top margin leaving room for sheet title header

# Vertical Split-Pair Grid Spacing inside Cricut Sensor Box
# Each pair contains Label A (11x34mm) + 3.0mm gap + Label B (11x34mm) = 25.0mm cut span (27.0mm with +1.0mm bleed)
PAIR_GAP_X = 3.00
PAIR_CUT_SPAN_W = VERT_LABEL_W * 2.0 + PAIR_GAP_X  # 25.00 mm
GRID_COLS = 6           # 6 cartridge pairs = 12 individual 11x34mm labels per row
GRID_ROWS = 6           # 6 rows = 36 cartridge pairs (72 individual 11x34mm labels) per sheet
COL_PITCH = 28.20       # 25.0mm pair cut span + 2.0mm outer bleed + 1.2mm inter-pair gap
ROW_PITCH = 37.80       # 34.0mm cut height + 2.0mm bleed + 1.8mm vertical gap

# Grid Offset within Sensor Box
GRID_TOTAL_W = (GRID_COLS - 1) * COL_PITCH + PAIR_CUT_SPAN_W
GRID_TOTAL_H = (GRID_ROWS - 1) * ROW_PITCH + VERT_LABEL_H
GRID_START_X = SENSOR_BOX_X + (SENSOR_BOX_W - GRID_TOTAL_W) / 2.0
GRID_START_Y = SENSOR_BOX_Y + (SENSOR_BOX_H - GRID_TOTAL_H) / 2.0


def render_registration_marks(x: float, y: float, w: float, h: float) -> str:
    """Render high-contrast optical registration marks around the printable area."""
    line_w = 0.80
    corner_len = 8.00
    parts = [
        f'<g id="registration-marks" stroke="#000000" stroke-width="{line_w}" fill="none">',
        # Outer Bounding Box
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" stroke-width="{line_w}"/>',
        # Top-Left Corner L-mark
        f'<path d="M {x-2:.2f},{y+corner_len:.2f} L {x-2:.2f},{y-2:.2f} L {x+corner_len:.2f},{y-2:.2f}" stroke-width="1.2"/>',
        # Top-Right Corner L-mark
        f'<path d="M {x+w+2:.2f},{y+corner_len:.2f} L {x+w+2:.2f},{y-2:.2f} L {x+w-corner_len:.2f},{y-2:.2f}" stroke-width="1.2"/>',
        # Bottom-Left Corner L-mark
        f'<path d="M {x-2:.2f},{y+h-corner_len:.2f} L {x-2:.2f},{y+h+2:.2f} L {x+corner_len:.2f},{y+h+2:.2f}" stroke-width="1.2"/>',
        # Bottom-Right Corner L-mark
        f'<path d="M {x+w+2:.2f},{y+h-corner_len:.2f} L {x+w+2:.2f},{y+h+2:.2f} L {x+w-corner_len:.2f},{y+h+2:.2f}" stroke-width="1.2"/>',
        '</g>',
    ]
    return "\n".join(parts)


def generate_cricut_sheet(
    labels: List[LabelData],
    title: str = "Fastener Labels",
    paper: str = "Letter",
    include_qr: bool = True,
) -> dict[str, Any]:
    """
    Generate a full-sheet SVG package for Cricut Print-Then-Cut.

    Returns a dict containing:
    - 'print_svg': Printable sheet SVG with bleed artwork and optical registration marks.
    - 'cut_svg': Vector cut file containing exact 34x10mm cut rectangles.
    - 'combined_svg': Multi-layer SVG containing both print artwork and cut paths in named groups.
    - 'label_count': Number of labels included on the sheet.
    - 'max_capacity': Maximum labels per sheet (60).
    """
    max_per_sheet = GRID_COLS * GRID_ROWS
    active_labels = labels[:max_per_sheet]
    count = len(active_labels)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Header SVG
    header_svg = (
        f'<g id="header-text">'
        f'<text x="{PAGE_W_LETTER / 2.0:.2f}" y="12.00" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="4.5" fill="#111111">{escape_xml(title)}</text>'
        f'<text x="{PAGE_W_LETTER / 2.0:.2f}" y="17.00" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="2.2" fill="#666666">Cricut Print-Then-Cut Vertical Split Pairs (11×34mm + 1mm Bleed) • {count} Cartridge Pairs ({count * 2} Labels) • Generated {ts}</text>'
        f'</g>'
    )

    reg_marks = render_registration_marks(SENSOR_BOX_X, SENSOR_BOX_Y, SENSOR_BOX_W, SENSOR_BOX_H)

    # 1. Generate Print Elements (with +1.0mm Bleed)
    print_elements: List[str] = [header_svg, reg_marks, '<g id="print-artwork">']
    # 2. Generate Cut Elements (Exact 11.00 x 34.00 mm rectangles for Label A and Label B)
    cut_elements: List[str] = ['<g id="cut-lines" fill="none" stroke="#FF0000" stroke-width="0.2">']

    for idx, spec in enumerate(active_labels):
        col = idx % GRID_COLS
        row = idx // GRID_COLS
        lx = GRID_START_X + col * COL_PITCH
        ly = GRID_START_Y + row * ROW_PITCH
        bx = lx + VERT_LABEL_W + PAIR_GAP_X

        # Render Bleed Artwork for Print (identical design to paper-cutter vertical split pair, with +1mm bleed)
        lbl_print_svg = render_vertical_split_label_pair_svg(
            spec,
            x=lx,
            y=ly,
            label_w=VERT_LABEL_W,
            label_h=VERT_LABEL_H,
            fallback_bin_num=idx + 1,
            include_bleed=True,
            bleed=BLEED,
            pair_gap_x=PAIR_GAP_X,
            include_qr=include_qr,
        )
        print_elements.append(lbl_print_svg)

        # Render Exact Cut Boundaries for Cricut Cut (Label A + Label B)
        cut_elements.append(
            f'<rect x="{lx:.2f}" y="{ly:.2f}" width="{VERT_LABEL_W:.2f}" height="{VERT_LABEL_H:.2f}" />'
        )
        cut_elements.append(
            f'<rect x="{bx:.2f}" y="{ly:.2f}" width="{VERT_LABEL_W:.2f}" height="{VERT_LABEL_H:.2f}" />'
        )

    print_elements.append('</g>')
    cut_elements.append('</g>')

    svg_open = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{PAGE_W_LETTER:.2f}mm" height="{PAGE_H_LETTER:.2f}mm" '
        f'viewBox="0 0 {PAGE_W_LETTER:.2f} {PAGE_H_LETTER:.2f}">'
    )
    svg_close = '</svg>'

    print_svg = f'{svg_open}\n' + "\n".join(print_elements) + f'\n{svg_close}'
    cut_svg = f'{svg_open}\n{reg_marks}\n' + "\n".join(cut_elements) + f'\n{svg_close}'
    combined_svg = (
        f'{svg_open}\n'
        f'{header_svg}\n'
        f'{reg_marks}\n'
        + "\n".join(print_elements[2:]) + "\n"
        + "\n".join(cut_elements) + f'\n{svg_close}'
    )

    return {
        "print_svg": print_svg,
        "cut_svg": cut_svg,
        "combined_svg": combined_svg,
        "label_count": count,
        "max_capacity": max_per_sheet,
    }
