import os
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.database import get_db
from server.app.models import CategoryRecord, PartRecord, BinRecord, BinCompartmentRecord, CarrierRecord, StorageLocationRecord

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


@router.get("/b/{bin_id}", response_class=HTMLResponse)
async def bin_detail_view(request: Request, bin_id: str, db: AsyncSession = Depends(get_db)):
    """Render mobile-optimized Bin landing page showing 1, 2, or 3 compartments and dynamic part mapper."""
    stmt = select(BinRecord).options(
        selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
        selectinload(BinRecord.compartments).selectinload(BinCompartmentRecord.part).selectinload(PartRecord.category),
    ).where(BinRecord.id == bin_id)
    res = await db.execute(stmt)
    bin_rec = res.scalars().first()
    if not bin_rec:
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
    db: AsyncSession = Depends(get_db),
):
    """Render interactive batch label generation and Cricut/Avery exporter interface."""
    cats_res = await db.execute(select(CategoryRecord).order_by(CategoryRecord.id))
    categories = cats_res.scalars().all()

    stmt = select(PartRecord).options(
        selectinload(PartRecord.category),
        selectinload(PartRecord.compartments).selectinload(BinCompartmentRecord.bin),
    ).order_by(PartRecord.size, PartRecord.length)
    if category:
        stmt = stmt.where(PartRecord.category_id == category)

    res = await db.execute(stmt)
    parts = res.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="label_batch_export.html",
        context={
            "categories": categories,
            "parts": parts,
            "current_category": category or "",
        },
    )
