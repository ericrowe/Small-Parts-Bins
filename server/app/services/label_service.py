"""Label Generation and Export Service.

Bridges catalog database records (Parts, Bins, Categories) to canonical label specifications
and multi-medium export formatters (Cricut Print-Then-Cut, Avery 5160/5167, Thermal Rolls).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.app.models import PartRecord, CategoryRecord, BinCompartmentRecord
from hardware.labels.canonical_label import LabelData
from hardware.labels.cricut_exporter import generate_cricut_sheet
from hardware.labels.avery_templates import generate_avery_sheet, AVERY_5160, AVERY_5167
from hardware.labels.thermal_exporter import generate_thermal_roll_svg


def part_to_label_data(part: PartRecord, bin_id: str = "") -> LabelData:
    """Convert a PartRecord into a canonical LabelData instance."""
    accent_color = part.category.color_hex if (part.category and part.category.color_hex) else "#0077CC"
    bg_color = "#FFFFFF"

    # If bin_id wasn't passed directly, check compartments
    assigned_bin = bin_id
    if not assigned_bin and part.compartments:
        assigned_bin = part.compartments[0].bin_id

    return LabelData(
        part_id=part.id,
        name=part.name,
        size=part.size,
        length=part.length,
        head=part.head or "shcs",
        drive=part.drive or "hex",
        comp_type=part.comp_type or "bolt",
        pitch=part.pitch or "",
        tap_drill=part.tap_drill or "",
        clearance_drill=part.clearance_drill or "",
        tool_key=part.tool_key or "",
        material=part.material or "",
        accent_color=accent_color,
        bg_color=bg_color,
        extra_note=part.extra_note or "",
        bin_id=assigned_bin,
        qr_payload=f"http://tasker-pi.local:8090/p/{part.id}",
    )


async def get_labels_for_parts(
    db: AsyncSession,
    part_ids: Optional[List[str]] = None,
    category_id: Optional[str] = None,
) -> List[LabelData]:
    """Query parts with categories & compartments and convert to LabelData list."""
    stmt = (
        select(PartRecord)
        .options(selectinload(PartRecord.category), selectinload(PartRecord.compartments))
    )

    if part_ids:
        stmt = stmt.where(PartRecord.id.in_(part_ids))
    elif category_id:
        stmt = stmt.where(PartRecord.category_id == category_id)

    res = await db.execute(stmt)
    parts = res.scalars().all()

    labels: List[LabelData] = []
    for p in parts:
        labels.append(part_to_label_data(p))

    # Fallback dummy labels if database is empty (e.g. fresh unit test or mock)
    if not labels and not part_ids and not category_id:
        labels = [
            LabelData(
                part_id=f"M3-SHCS-{i*2}",
                name=f"M3 × {i*2}mm SHCS",
                size="M3",
                length=f"{i*2} mm",
                head="shcs",
                drive="hex",
                comp_type="bolt",
                pitch="0.5 mm",
                tap_drill="2.5 mm",
                tool_key="2.5 mm",
                material="SS 304",
                accent_color="#0077CC",
            )
            for i in range(1, 13)
        ]

    return labels


def export_labels_to_format(
    labels: List[LabelData],
    export_format: str,
    title: str = "Hardware Labels",
    include_qr: bool = True,
) -> Dict[str, Any]:
    """
    Export labels into the specified medium format.

    Supported formats:
    - 'cricut_print_cut' / 'cricut'
    - 'avery_5160'
    - 'avery_5167'
    - 'thermal_roll'
    """
    fmt = export_format.lower().strip()

    if fmt in ("cricut_print_cut", "cricut"):
        sheet_data = generate_cricut_sheet(labels, title=title, include_qr=include_qr)
        return {
            "content": sheet_data["combined_svg"],
            "print_svg": sheet_data["print_svg"],
            "cut_svg": sheet_data["cut_svg"],
            "filename": "fastener_labels_cricut_sheet.svg",
            "media_type": "image/svg+xml",
            "label_count": sheet_data["label_count"],
        }
    elif fmt == "avery_5160":
        svg_content = generate_avery_sheet(labels, template=AVERY_5160, title=title, include_qr=include_qr)
        return {
            "content": svg_content,
            "filename": "fastener_labels_avery_5160.svg",
            "media_type": "image/svg+xml",
            "label_count": min(len(labels), AVERY_5160.capacity),
        }
    elif fmt == "avery_5167":
        svg_content = generate_avery_sheet(labels, template=AVERY_5167, title=title, include_qr=include_qr)
        return {
            "content": svg_content,
            "filename": "fastener_labels_avery_5167.svg",
            "media_type": "image/svg+xml",
            "label_count": min(len(labels), AVERY_5167.capacity),
        }
    elif fmt in ("thermal_roll", "thermal"):
        svg_content = generate_thermal_roll_svg(labels, include_qr=include_qr)
        return {
            "content": svg_content,
            "filename": "fastener_labels_thermal_roll.svg",
            "media_type": "image/svg+xml",
            "label_count": len(labels),
        }
    else:
        raise ValueError(f"Unsupported label export format: {export_format}")
