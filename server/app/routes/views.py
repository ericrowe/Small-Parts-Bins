import asyncio
import os
import re
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.database import get_db
from server.app.models import CategoryRecord, PartRecord, BinRecord, BinCompartmentRecord, CarrierRecord, StorageLocationRecord
from server.app.services.homebox_service import (
    list_ingested_bins,
    resolve_qr_forwarding_target,
    has_qr_forwarding_entry,
    list_qr_forwarding_entries,
    _get_qr_forwarding_file_path,
)

router = APIRouter(include_in_schema=False)

templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request, db: AsyncSession = Depends(get_db)):
    """Render main workshop dashboard with inventory stats, category pills, quick search, and restock alerts."""
    total_parts = (await db.execute(select(func.count(PartRecord.id)))).scalar() or 0
    total_bins = (await db.execute(select(func.count(BinRecord.id)))).scalar() or 0
    total_stock = (await db.execute(select(func.sum(BinCompartmentRecord.quantity_on_hand)))).scalar() or 0
    low_stock = (await db.execute(select(func.count(BinCompartmentRecord.id)).where(BinCompartmentRecord.quantity_on_hand <= BinCompartmentRecord.reorder_threshold))).scalar() or 0

    cats_res = await db.execute(select(CategoryRecord).order_by(CategoryRecord.id))
    categories = cats_res.scalars().all()

    recent_bins_res = await db.execute(
        select(BinRecord)
        .options(
            selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
            selectinload(BinRecord.compartments).selectinload(BinCompartmentRecord.part).selectinload(PartRecord.category),
        )
        .order_by(BinRecord.id)
        .limit(12)
    )
    recent_bins = recent_bins_res.scalars().all()

    # Replenishment Alerts
    alerts_stmt = select(BinCompartmentRecord).options(
        selectinload(BinCompartmentRecord.part).selectinload(PartRecord.category),
        selectinload(BinCompartmentRecord.bin).selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
    ).where(
        BinCompartmentRecord.storage_role == "PRIMARY",
        BinCompartmentRecord.part_id.isnot(None),
        BinCompartmentRecord.quantity_on_hand <= BinCompartmentRecord.reorder_threshold,
    )
    res_alerts = await db.execute(alerts_stmt)
    low_primary_comps = res_alerts.scalars().all()
    replenish_alerts = []
    for comp in low_primary_comps:
        p_clean = comp.part_id.lower().replace("-", "_").replace("mm", "")
        bulk_stmt = select(BinCompartmentRecord).options(
            selectinload(BinCompartmentRecord.bin).selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
        ).where(
            BinCompartmentRecord.id != comp.id,
            BinCompartmentRecord.storage_role.in_(["BULK_RESERVE", "OVERFLOW"]),
            BinCompartmentRecord.quantity_on_hand > 0,
        )
        bulk_res = await db.execute(bulk_stmt)
        sources = [
            s for s in bulk_res.scalars().all()
            if s.part_id and (s.part_id == comp.part_id or s.part_id.lower().replace("-", "_").replace("mm", "") == p_clean)
        ]
        if sources:
            replenish_alerts.append({
                "part": comp.part,
                "primary_compartment": comp,
                "bulk_sources": sources,
                "bulk_total": sum(s.quantity_on_hand for s in sources),
            })

    hb_summary = await asyncio.to_thread(list_ingested_bins, limit=12)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "total_parts": total_parts,
            "total_bins": total_bins,
            "total_stock": total_stock,
            "low_stock": low_stock,
            "categories": categories,
            "recent_bins": recent_bins,
            "replenish_alerts": replenish_alerts,
            "homebox_bins": hb_summary.get("bins", []),
            "homebox_base_url": hb_summary.get("homebox_base_url", "http://tasker-pi.local:7745"),
            "homebox_authenticated": hb_summary.get("authenticated", False),
            "next_bin_id": hb_summary.get("next_bin_id", "BIN-001"),
        },
    )


@router.get("/parts", response_class=HTMLResponse)
async def parts_catalog_view(
    request: Request,
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Render searchable fastener parts catalog table with thread details, tap drills, and multi-tier stock."""
    stmt = select(PartRecord).options(
        selectinload(PartRecord.category),
        selectinload(PartRecord.compartments).selectinload(BinCompartmentRecord.bin).selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
    ).order_by(PartRecord.size, PartRecord.length)
    
    if category:
        stmt = stmt.where(PartRecord.category_id == category)
    if q:
        query_pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                PartRecord.name.ilike(query_pattern),
                PartRecord.size.ilike(query_pattern),
                PartRecord.id.ilike(query_pattern),
                PartRecord.material.ilike(query_pattern),
                PartRecord.tool_key.ilike(query_pattern),
            )
        )

    res = await db.execute(stmt)
    parts = res.scalars().all()

    cats_res = await db.execute(select(CategoryRecord).order_by(CategoryRecord.id))
    categories = cats_res.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="parts.html",
        context={
            "parts": parts,
            "categories": categories,
            "current_query": q or "",
            "current_category": category or "",
        },
    )


@router.get("/p/{part_id}", response_class=HTMLResponse)
async def part_detail_view(request: Request, part_id: str, db: AsyncSession = Depends(get_db)):
    """Render mobile-optimized technical specifications page for a single fastener part."""
    stmt = select(PartRecord).options(
        selectinload(PartRecord.category),
        selectinload(PartRecord.compartments).selectinload(BinCompartmentRecord.bin).selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
    ).where(
        or_(
            PartRecord.id == part_id,
            func.lower(PartRecord.id) == func.lower(part_id),
            func.replace(func.replace(func.lower(PartRecord.id), '-', '_'), 'mm', '') == func.replace(func.replace(func.lower(part_id), '-', '_'), 'mm', '')
        )
    )
    res = await db.execute(stmt)
    part = res.scalars().first()
    if not part:
        raise HTTPException(status_code=404, detail=f"Part '{part_id}' not found")

    primary_comps = [c for c in part.compartments if getattr(c, "storage_role", "PRIMARY") == "PRIMARY"]
    bulk_comps = [c for c in part.compartments if getattr(c, "storage_role", "PRIMARY") in ("BULK_RESERVE", "OVERFLOW")]
    primary_stock = sum(c.quantity_on_hand for c in primary_comps)
    bulk_stock = sum(c.quantity_on_hand for c in bulk_comps)
    total_stock = sum(c.quantity_on_hand for c in part.compartments)

    return templates.TemplateResponse(
        request=request,
        name="part_detail.html",
        context={
            "part": part,
            "primary_comps": primary_comps,
            "bulk_comps": bulk_comps,
            "primary_stock": primary_stock,
            "bulk_stock": bulk_stock,
            "total_stock": total_stock,
        },
    )


@router.get("/b/{bin_id}")
async def bin_detail_view(request: Request, bin_id: str, db: AsyncSession = Depends(get_db)):
    """Redirect Homebox-registered bins to Homebox, or render legacy fallback bin detail view."""
    if os.environ.get("QR_FORWARDING_FILE") and has_qr_forwarding_entry(bin_id):
        return RedirectResponse(url=resolve_qr_forwarding_target(bin_id), status_code=302)

    stmt = select(BinRecord).options(
        selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
        selectinload(BinRecord.compartments).selectinload(BinCompartmentRecord.part).selectinload(PartRecord.category),
    ).where(BinRecord.id == bin_id)
    res = await db.execute(stmt)
    bin_rec = res.scalars().first()
    if not bin_rec:
        if re.match(r"^(?:\d{1,6}|BIN-\d{1,6})$", bin_id.strip(), flags=re.IGNORECASE):
            return RedirectResponse(url=resolve_qr_forwarding_target(bin_id), status_code=302)
        raise HTTPException(status_code=404, detail=f"Bin '{bin_id}' not found")

    # Fetch all parts for assignment dropdown
    all_parts_res = await db.execute(select(PartRecord).order_by(PartRecord.size, PartRecord.length))
    all_parts = all_parts_res.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="bin_detail.html",
        context={
            "bin": bin_rec,
            "all_parts": all_parts,
        },
    )


@router.get("/labels", response_class=HTMLResponse)
async def label_batch_export_view(
    request: Request,
    category: Optional[str] = Query(None),
    bin: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Render interactive Homebox cartridge label generator and batch SVG exporter interface."""
    hb_summary = await asyncio.to_thread(list_ingested_bins, limit=200)
    hb_bins = list(hb_summary.get("bins") or [])
    hb_bins.sort(key=lambda b: b.get("bin_4digit") or b.get("bin_code") or "")
    if category:
        hb_bins = [b for b in hb_bins if b.get("category_id") == category]

    selected_bin_4d = ""
    if bin:
        m_sel = re.search(r"(\d+)", str(bin))
        selected_bin_4d = f"{int(m_sel.group(1)):04d}" if m_sel else str(bin).strip().upper()

    homebox_categories = [
        {"id": "metric", "name": "Metric (Blue Label — Blue/Black Bin)", "color_hex": "#0077CC"},
        {"id": "imperial", "name": "Imperial (Orange Label — Orange/Black Bin)", "color_hex": "#E65100"},
        {"id": "nuts_washers", "name": "Nuts & Washers (Green Bin)", "color_hex": "#2E7D32"},
        {"id": "inserts", "name": "Inserts, Standoffs & Specialty (Yellow Bin)", "color_hex": "#D4A017"},
    ]

    next_bin_raw = hb_summary.get("next_bin_id", "BIN-001")
    m_next = re.search(r"(\d+)", str(next_bin_raw))
    next_bin_4digit = f"{int(m_next.group(1)):04d}" if m_next else "0001"

    return templates.TemplateResponse(
        request=request,
        name="label_batch_export.html",
        context={
            "categories": homebox_categories,
            "homebox_bins": hb_bins,
            "homebox_base_url": hb_summary.get("homebox_base_url", "http://tasker-pi.local:7745"),
            "homebox_locations_url": hb_summary.get("homebox_locations_url") or hb_summary.get("homebox_base_url", "http://tasker-pi.local:7745"),
            "homebox_authenticated": hb_summary.get("authenticated", False),
            "next_bin_4digit": next_bin_4digit,
            "current_category": category or "",
            "selected_bin_4d": selected_bin_4d,
            "qr_forwarding_entries": list_qr_forwarding_entries(),
            "qr_forwarding_file_path": _get_qr_forwarding_file_path(),
        },
    )


@router.get("/ingest", response_class=HTMLResponse)
async def parts_ingestor_view(request: Request):
    """Render mobile and desktop Parts Ingestor (Photo OCR/CV + Form Entry) syncing to Homebox."""
    hb_summary = await asyncio.to_thread(list_ingested_bins, limit=25)
    return templates.TemplateResponse(
        request=request,
        name="ingest.html",
        context={
            "next_bin_id": hb_summary["next_bin_id"],
            "homebox_base_url": hb_summary["homebox_base_url"],
            "homebox_authenticated": hb_summary.get("authenticated", False),
            "ingested_bins": hb_summary["bins"],
            "total_ingested_bins": hb_summary["total_bins"],
        },
    )


@router.get("/q/{bin_code}")
async def qr_forwarding_subroute(bin_code: str):
    """Forwarding route (/q/0001 or /q/BIN-001) redirecting phone QR scans to Homebox or active catalog."""
    target_url = resolve_qr_forwarding_target(bin_code)
    return RedirectResponse(url=target_url, status_code=302)


@router.get("/{bin_code}")
async def qr_forwarding_root_route(bin_code: str):
    """ Ultra-short root forwarding route (/0001) keeping QR codes at Version 1/2 (<=25x25 modules)."""
    if not re.match(r"^(?:\d{1,6}|BIN-\d{1,6})$", bin_code.strip(), flags=re.IGNORECASE):
        raise HTTPException(status_code=404, detail="Not found")
    target_url = resolve_qr_forwarding_target(bin_code)
    return RedirectResponse(url=target_url, status_code=302)


