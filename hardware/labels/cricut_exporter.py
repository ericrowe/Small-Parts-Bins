"""Cricut Print-Then-Cut Exporter for Fastener and Storage Labels.

Generates standard multi-up SVG sheets with optical sensor registration marks,
+1.0mm bleed artwork layer for high-tolerance printing, and exact 34x10mm cut path layers
for Cricut Design Space, Silhouette Studio, or Brother ScanNCut kiss-cutting.
"""

from __future__ import annotations

import datetime
from typing import Any, List
from hardware.labels.canonical_label import (
    BLEED,
    STRIP_H,
    STRIP_R,
    STRIP_W,
    LabelData,
    escape_xml,
    render_canonical_label_svg,
)

# Page Dimensions (mm)
PAGE_W_LETTER = 215.90  # 8.5 in
PAGE_H_LETTER = 279.40  # 11.0 in

# Cricut Print Then Cut Max Printable Area (Sensor Box)
SENSOR_BOX_W = 171.45   # 6.75 in
SENSOR_BOX_H = 234.95   # 9.25 in
SENSOR_BOX_X = (PAGE_W_LETTER - SENSOR_BOX_W) / 2.0  # 22.225 mm
SENSOR_BOX_Y = 24.00    # Top margin leaving room for sheet title header

# Grid Spacing
GRID_COLS = 4
GRID_ROWS = 15
COL_PITCH = 39.00       # 34mm cut + 2mm bleed + 3mm gap
ROW_PITCH = 14.50       # 10mm cut + 2mm bleed + 2.5mm gap

# Grid Offset within Sensor Box
GRID_START_X = SENSOR_BOX_X + (SENSOR_BOX_W - (GRID_COLS * COL_PITCH - (COL_PITCH - STRIP_W))) / 2.0
GRID_START_Y = SENSOR_BOX_Y + 8.00


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
        f'<text x="{PAGE_W_LETTER / 2.0:.2f}" y="17.00" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="2.2" fill="#666666">Cricut Print-Then-Cut Standard (34x10mm) • {count} Labels • Generated {ts}</text>'
        f'</g>'
    )

    reg_marks = render_registration_marks(SENSOR_BOX_X, SENSOR_BOX_Y, SENSOR_BOX_W, SENSOR_BOX_H)

    # 1. Generate Print Elements (with Bleed)
    print_elements: List[str] = [header_svg, reg_marks, '<g id="print-artwork">']
    # 2. Generate Cut Elements (Exact 34x10mm)
    cut_elements: List[str] = [f'<g id="cut-lines" fill="none" stroke="#FF0000" stroke-width="0.2">']

    for idx, spec in enumerate(active_labels):
        col = idx % GRID_COLS
        row = idx // GRID_COLS
        lx = GRID_START_X + col * COL_PITCH
        ly = GRID_START_Y + row * ROW_PITCH

        # Render Bleed Artwork for Print
        lbl_print_svg = render_canonical_label_svg(
            spec,
            x=lx,
            y=ly,
            width=STRIP_W,
            height=STRIP_H,
            corner_radius=STRIP_R,
            include_bleed=True,
            include_qr=include_qr,
        )
        print_elements.append(lbl_print_svg)

        # Render Exact Cut Boundary for Cricut Cut
        cut_elements.append(
            f'<rect x="{lx:.2f}" y="{ly:.2f}" width="{STRIP_W:.2f}" height="{STRIP_H:.2f}" rx="{STRIP_R:.2f}" />'
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
