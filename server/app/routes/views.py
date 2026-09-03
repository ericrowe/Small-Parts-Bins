import os
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.database import get_db
from server.app.models import CategoryRecord, PartRecord, BinRecord, CarrierRecord, StorageLocationRecord

router = APIRouter(include_in_schema=False)

templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request, db: AsyncSession = Depends(get_db)):
    """Render main workshop dashboard with inventory stats, category pills, and quick search."""
    total_parts = (await db.execute(select(func.count(PartRecord.id)))).scalar() or 0
    total_bins = (await db.execute(select(func.count(BinRecord.id)))).scalar() or 0
    total_stock = (await db.execute(select(func.sum(BinRecord.quantity_on_hand)))).scalar() or 0
    low_stock = (await db.execute(select(func.count(BinRecord.id)).where(BinRecord.quantity_on_hand <= BinRecord.reorder_threshold))).scalar() or 0

    cats_res = await db.execute(select(CategoryRecord).order_by(CategoryRecord.id))
    categories = cats_res.scalars().all()

    recent_bins_res = await db.execute(
        select(BinRecord)
        .options(
            selectinload(BinRecord.part).selectinload(PartRecord.category),
            selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
        )
        .order_by(BinRecord.updated_at.desc())
        .limit(10)
    )
    recent_bins = recent_bins_res.scalars().all()

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
        },
    )


@router.get("/parts", response_class=HTMLResponse)
async def parts_catalog_view(
    request: Request,
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Render searchable fastener parts catalog table with thread details and tap drills."""
    stmt = select(PartRecord).options(selectinload(PartRecord.category), selectinload(PartRecord.bins)).order_by(PartRecord.size, PartRecord.length)
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


@router.get("/b/{bin_id}", response_class=HTMLResponse)
async def bin_detail_view(request: Request, bin_id: str, db: AsyncSession = Depends(get_db)):
    """Render mobile-optimized Bin landing page for QR barcode scans with quick quantity buttons."""
    stmt = select(BinRecord).options(
        selectinload(BinRecord.part).selectinload(PartRecord.category),
        selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
    ).where(BinRecord.id == bin_id)
    res = await db.execute(stmt)
    bin_rec = res.scalars().first()
    if not bin_rec:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_id}' not found")

    return templates.TemplateResponse(
        request=request,
        name="bin_detail.html",
        context={
            "bin": bin_rec,
        },
    )
