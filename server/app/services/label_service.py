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
from server.app.services.homebox_service import list_ingested_bins
from server.app.services.part_ingestor_service import lookup_fastener_specs
from hardware.labels.canonical_label import (
    LabelData,
    format_four_digit_bin,
    generate_split_vertical_sheet_svg,
)
from hardware.labels.cricut_exporter import generate_cricut_sheet
from hardware.labels.avery_templates import generate_avery_sheet, AVERY_5160, AVERY_5167
from hardware.labels.thermal_exporter import generate_thermal_roll_svg

CATEGORY_COLOR_MAP: Dict[str, str] = {
    "metric": "#0077CC",
    "imperial": "#E65100",
    "nuts_washers": "#2E7D32",
    "inserts": "#C5A059",
}


def homebox_bin_to_label_data(hb_bin: Dict[str, Any]) -> LabelData:
    """Convert a Homebox cartridge bin dictionary (from list_ingested_bins) into a LabelData instance."""
    bin_4d = format_four_digit_bin(
        hb_bin.get("bin_4digit") or hb_bin.get("bin_code") or "",
        fallback_num=1,
    )
    size = (hb_bin.get("size") or hb_bin.get("bin_code") or "M3").strip()
    length = (hb_bin.get("length") or "").strip()
    head = (hb_bin.get("head") or "shcs").strip().lower()
    enriched = lookup_fastener_specs(size=size, head=head)
    accent_color = (
        hb_bin.get("accent_color")
        or CATEGORY_COLOR_MAP.get(str(hb_bin.get("category_id") or "metric"), "#0077CC")
    )
    return LabelData(
        part_id=hb_bin.get("bin_code") or f"BIN-{bin_4d}",
        name=hb_bin.get("name") or f"{size} × {length}".strip(" ×"),
        size=size,
        length=length,
        head=head,
        drive=enriched.get("drive") or "hex",
        comp_type=hb_bin.get("comp_type") or "bolt",
        pitch=hb_bin.get("pitch") or enriched.get("pitch") or "",
        tap_drill=hb_bin.get("tap_drill") or enriched.get("tap_drill") or "",
        clearance_drill=hb_bin.get("clearance_drill") or enriched.get("clearance_drill") or "",
        tool_key=hb_bin.get("tool_key") or enriched.get("tool_key") or "",
        material=hb_bin.get("material") or hb_bin.get("finishes_summary") or "",
        accent_color=accent_color,
        bg_color="#FFFFFF",
        extra_note=hb_bin.get("extra_note") or "",
        bin_id=bin_4d,
        qr_payload=hb_bin.get("qr_short_url") or f"HTTP://TASKER-PI.LOCAL:8090/{bin_4d}",
    )


def custom_spec_to_label_data(spec: Dict[str, Any], index: int = 1) -> LabelData:
    """Convert an ad-hoc / custom Homebox bin label dictionary into a LabelData instance with fastener spec enrichment."""
    raw_bin = str(spec.get("bin_id") or spec.get("bin_code") or f"{index:04d}").strip()
    bin_4d = format_four_digit_bin(raw_bin, fallback_num=index)
    size = str(spec.get("size") or "M3").strip()
    length = str(spec.get("length") or "").strip()
    head = str(spec.get("head") or "shcs").strip().lower()
    enriched = lookup_fastener_specs(size=size, head=head)
    cat_key = str(spec.get("category_id") or spec.get("category") or "").strip().lower()
    if not cat_key:
        cat_key = "metric" if size.upper().startswith("M") else "imperial"
    accent_color = str(spec.get("accent_color") or CATEGORY_COLOR_MAP.get(cat_key, "#0077CC")).strip()
    extra_note = str(spec.get("extra_note") or "").strip()

    return LabelData(
        part_id=str(spec.get("part_id") or f"BIN-{bin_4d}"),
        name=str(spec.get("name") or f"{size} × {length}".strip(" ×")),
        size=size,
        length=length,
        head=head,
        drive=str(spec.get("drive") or enriched.get("drive") or "hex"),
        comp_type=str(spec.get("comp_type") or "bolt"),
        pitch=str(spec.get("pitch") or enriched.get("pitch") or ""),
        tap_drill=str(spec.get("tap_drill") or enriched.get("tap_drill") or ""),
        clearance_drill=str(spec.get("clearance_drill") or enriched.get("clearance_drill") or ""),
        tool_key=str(spec.get("tool_key") or enriched.get("tool_key") or ""),
        material=str(spec.get("material") or ""),
        accent_color=accent_color,
        bg_color="#FFFFFF",
        extra_note=extra_note,
        bin_id=bin_4d,
        qr_payload=str(spec.get("qr_payload") or f"HTTP://TASKER-PI.LOCAL:8090/{bin_4d}"),
    )


def part_to_label_data(part: PartRecord, bin_id: str = "") -> LabelData:
    """Convert a PartRecord into a canonical LabelData instance."""
    accent_color = part.category.color_hex if (part.category and part.category.color_hex) else "#0077CC"
    bg_color = "#FFFFFF"

    # If bin_id wasn't passed directly, check compartments
    assigned_bin = bin_id
    if not assigned_bin and part.compartments:
        assigned_bin = part.compartments[0].bin_id

    bin_4d = format_four_digit_bin(assigned_bin, fallback_num=1)
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
        bin_id=assigned_bin or bin_4d,
        qr_payload=f"HTTP://TASKER-PI.LOCAL:8090/{bin_4d}",
    )


async def get_labels_for_parts(
    db: AsyncSession,
    part_ids: Optional[List[str]] = None,
    category_id: Optional[str] = None,
    custom_labels: Optional[List[Dict[str, Any]]] = None,
) -> List[LabelData]:
    """Build LabelData list from custom Homebox label rows, live Homebox cartridge bins, or fallback records."""
    if custom_labels:
        return [
            custom_spec_to_label_data(spec, index=idx + 1)
            for idx, spec in enumerate(custom_labels)
        ]

    # 1. Primary source: Homebox cartridge bins (http://tasker-pi.local:7745)
    hb_summary = list_ingested_bins(limit=200)
    hb_bins = list(hb_summary.get("bins") or [])
    if hb_bins:
        # Sort ascending by 4-digit bin number so sheets print in order (0001, 0002, ...)
        hb_bins.sort(key=lambda b: b.get("bin_4digit") or b.get("bin_code") or "")
        selected_hb: List[Dict[str, Any]] = []
        id_set = {str(x).strip().upper() for x in (part_ids or []) if str(x).strip()}
        for b in hb_bins:
            if category_id and b.get("category_id") != category_id:
                continue
            if id_set:
                candidates = {
                    str(b.get("id") or "").upper(),
                    str(b.get("bin_code") or "").upper(),
                    str(b.get("bin_4digit") or "").upper(),
                }
                if not (id_set & candidates):
                    continue
            selected_hb.append(b)
        if selected_hb:
            return [homebox_bin_to_label_data(b) for b in selected_hb]

    # 2. Fallback: local SQLite PartRecord table (for legacy/hermetic test fixtures)
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
                part_id=f"BIN-{i:04d}",
                name=f"M3 × {i*2}",
                size="M3",
                length=f"{i*2}",
                head="shcs",
                drive="hex",
                comp_type="bolt",
                pitch="0.5 mm",
                tap_drill="2.5 mm",
                tool_key="2.5 mm",
                material="SS 304",
                accent_color="#0077CC",
                bin_id=f"{i:04d}",
                qr_payload=f"HTTP://TASKER-PI.LOCAL:8090/{i:04d}",
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
    elif fmt in ("split_vertical_12x35", "paper_cutter_split", "split_vertical"):
        svg_content = generate_split_vertical_sheet_svg(labels, title=title)
        return {
            "content": svg_content,
            "filename": "fastener_labels_split_12x35_sheet.svg",
            "media_type": "image/svg+xml",
            "label_count": min(len(labels), 56),
        }
    else:
        raise ValueError(f"Unsupported label export format: {export_format}")
