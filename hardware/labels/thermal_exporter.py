"""Thermal Continuous Roll and Tape Stream Exporter.

Supports continuous thermal label printers (Brother QL series, Dymo LabelWriter, Rollo)
generating a continuous vertical strip of canonical fastener labels with optional cut lines.
"""

from __future__ import annotations

import datetime
from typing import List

from hardware.labels.canonical_label import (
    STRIP_H,
    STRIP_R,
    STRIP_W,
    LabelData,
    escape_xml,
    render_canonical_label_svg,
)


def generate_thermal_roll_svg(
    labels: List[LabelData],
    label_width: float = STRIP_W,
    label_height: float = STRIP_H,
    gap_y: float = 3.0,
    margin_x: float = 2.0,
    margin_y: float = 2.0,
    include_qr: bool = True,
) -> str:
    """
    Generate a continuous thermal roll stream containing multiple sequential labels.
    """
    if not labels:
        labels = []

    count = len(labels)
    if count == 0:
        total_w = label_width + 2 * margin_x
        total_h = label_height + 2 * margin_y
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.2f}mm" height="{total_h:.2f}mm" '
            f'viewBox="0 0 {total_w:.2f} {total_h:.2f}"></svg>'
        )

    total_w = label_width + 2 * margin_x
    total_h = 2 * margin_y + count * label_height + (count - 1) * gap_y
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w:.2f}mm" height="{total_h:.2f}mm" '
        f'viewBox="0 0 {total_w:.2f} {total_h:.2f}">',
        f'<!-- Thermal Roll Stream • {count} labels • Generated {ts} -->',
        f'<g id="thermal-stream">',
    ]

    for idx, spec in enumerate(labels):
        ly = margin_y + idx * (label_height + gap_y)
        lbl_svg = render_canonical_label_svg(
            spec,
            x=margin_x,
            y=ly,
            width=label_width,
            height=label_height,
            corner_radius=STRIP_R,
            include_bleed=False,
            include_qr=include_qr,
        )
        svg_parts.append(lbl_svg)

        # Optional dashed cut line between labels
        if idx < count - 1 and gap_y > 1.0:
            cut_y = ly + label_height + gap_y / 2.0
            svg_parts.append(
                f'<line x1="0" y1="{cut_y:.2f}" x2="{total_w:.2f}" y2="{cut_y:.2f}" '
                f'stroke="#AAAAAA" stroke-width="0.2" stroke-dasharray="1,1"/>'
            )

    svg_parts.append('</g>')
    svg_parts.append('</svg>')

    return "\n".join(svg_parts)
