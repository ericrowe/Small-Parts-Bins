"""Avery Standard Pre-Cut Label Sheet Templates and Grid Composer.

Supports standard Letter sheets:
- Avery 5160 / 8160 / 5260: 30-up (3 columns x 10 rows, 1" x 2-5/8" / 66.68 x 25.4mm)
- Avery 5167 / 8167: 80-up (4 columns x 20 rows, 1/2" x 1-3/4" / 44.45 x 12.7mm)
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List

from hardware.labels.canonical_label import (
    STRIP_H,
    STRIP_R,
    STRIP_W,
    LabelData,
    escape_xml,
    render_canonical_label_svg,
)


@dataclass(frozen=True)
class AveryTemplate:
    """Dimensions and grid parameters for an Avery standard sheet layout (all units in mm)."""
    name: str
    description: str
    cols: int
    rows: int
    page_w: float
    page_h: float
    label_w: float
    label_h: float
    margin_top: float
    margin_left: float
    gap_x: float
    gap_y: float

    @property
    def capacity(self) -> int:
        return self.cols * self.rows

    @property
    def pitch_x(self) -> float:
        return self.label_w + self.gap_x

    @property
    def pitch_y(self) -> float:
        return self.label_h + self.gap_y


# Avery 5160 / 8160: 30 labels per Letter page
AVERY_5160 = AveryTemplate(
    name="Avery 5160",
    description="30-up Standard Address/Fastener (1\" x 2-5/8\")",
    cols=3,
    rows=10,
    page_w=215.90,     # 8.5 in
    page_h=279.40,     # 11.0 in
    label_w=66.68,     # 2.625 in
    label_h=25.40,     # 1.0 in
    margin_top=12.70,  # 0.5 in
    margin_left=4.76,  # 0.1875 in
    gap_x=3.18,        # 0.125 in
    gap_y=0.00,
)

# Avery 5167 / 8167: 80 labels per Letter page
AVERY_5167 = AveryTemplate(
    name="Avery 5167",
    description="80-up Return Address/Micro Fastener (1/2\" x 1-3/4\")",
    cols=4,
    rows=20,
    page_w=215.90,     # 8.5 in
    page_h=279.40,     # 11.0 in
    label_w=44.45,     # 1.75 in
    label_h=12.70,     # 0.5 in
    margin_top=12.70,  # 0.5 in
    margin_left=7.62,  # 0.3 in
    gap_x=7.62,        # 0.3 in
    gap_y=0.00,
)


def generate_avery_sheet(
    labels: List[LabelData],
    template: AveryTemplate = AVERY_5160,
    title: str = "Avery Labels",
    include_qr: bool = True,
) -> str:
    """
    Generate an SVG sheet perfectly registered to an Avery pre-cut template.
    Centers canonical fastener labels within each pre-cut die cell.
    """
    active_labels = labels[:template.capacity]
    count = len(active_labels)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # SVG container
    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{template.page_w:.2f}mm" height="{template.page_h:.2f}mm" '
        f'viewBox="0 0 {template.page_w:.2f} {template.page_h:.2f}">',
        f'<!-- {escape_xml(title)} • {template.name} ({count}/{template.capacity} labels) • Generated {ts} -->',
        f'<g id="avery-grid-layer">',
    ]

    for idx, spec in enumerate(active_labels):
        col = idx % template.cols
        row = idx // template.cols

        cell_x = template.margin_left + col * template.pitch_x
        cell_y = template.margin_top + row * template.pitch_y

        # Center the canonical 34x10mm label inside the pre-cut cell
        # If template is Avery 5160, label is slightly expanded or centered
        if template == AVERY_5160:
            lbl_w = 62.00
            lbl_h = 22.00
            lbl_r = 1.50
            qr_sz = 14.0
            lbl_x = cell_x + (template.label_w - lbl_w) / 2.0
            lbl_y = cell_y + (template.label_h - lbl_h) / 2.0
            lbl_svg = render_canonical_label_svg(
                spec,
                x=lbl_x,
                y=lbl_y,
                width=lbl_w,
                height=lbl_h,
                corner_radius=lbl_r,
                include_bleed=False,
                include_qr=include_qr,
                qr_size=qr_sz,
            )
        else:
            # Avery 5167: center 34x10mm in 44.45x12.7mm cell
            lbl_x = cell_x + (template.label_w - STRIP_W) / 2.0
            lbl_y = cell_y + (template.label_h - STRIP_H) / 2.0
            lbl_svg = render_canonical_label_svg(
                spec,
                x=lbl_x,
                y=lbl_y,
                width=STRIP_W,
                height=STRIP_H,
                corner_radius=STRIP_R,
                include_bleed=False,
                include_qr=include_qr,
                qr_size=7.0,
            )

        svg_parts.append(lbl_svg)

    svg_parts.append('</g>')
    svg_parts.append('</svg>')

    return "\n".join(svg_parts)
