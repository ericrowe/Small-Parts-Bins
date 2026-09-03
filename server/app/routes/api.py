from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from server.app.database import get_db
from server.app.models import CategoryRecord, PartRecord, BinRecord, CarrierRecord, StorageLocationRecord

router = APIRouter(prefix="/api", tags=["API"])


# Pydantic Schemas
class QuantityUpdateRequest(BaseModel):
    delta: Optional[int] = None
    set_quantity: Optional[int] = None


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """Return catalog health and runtime telemetry."""
    return {
        "status": "online",
        "service": "Parts-Database Catalog Microservice",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """List all hardware taxonomy categories."""
    stmt = select(CategoryRecord).order_by(CategoryRecord.id)
    res = await db.execute(stmt)
    categories = res.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "filament": c.filament,
            "color_name": c.color_name,
            "color_hex": c.color_hex,
            "color_bg": c.color_bg,
            "prefix": c.prefix,
        }
        for c in categories
    ]


@router.get("/parts")
async def list_parts(
    q: Optional[str] = Query(None, description="Search query across name, size, thread, or material"),
    category: Optional[str] = Query(None, description="Filter by category ID"),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List parts with optional search query and category filtering."""
    stmt = select(PartRecord).options(selectinload(PartRecord.category)).order_by(PartRecord.size, PartRecord.length)
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
    return [
        {
            "id": p.id,
            "name": p.name,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else "",
            "category_color": p.category.color_hex if p.category else "#0077CC",
            "size": p.size,
            "length": p.length,
            "head": p.head,
            "drive": p.drive,
            "comp_type": p.comp_type,
            "material": p.material,
            "tool_key": p.tool_key,
            "tap_drill": p.tap_drill,
            "clearance_drill": p.clearance_drill,
            "pitch": p.pitch,
            "extra_note": p.extra_note,
        }
        for p in parts
    ]


@router.get("/parts/{part_id}")
async def get_part_detail(part_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve full detail for a single fastener part."""
    stmt = select(PartRecord).options(selectinload(PartRecord.category), selectinload(PartRecord.bins)).where(PartRecord.id == part_id)
    res = await db.execute(stmt)
    part = res.scalars().first()
    if not part:
        raise HTTPException(status_code=404, detail=f"Part '{part_id}' not found")

    return {
        "id": part.id,
        "name": part.name,
        "category_id": part.category_id,
        "category_name": part.category.name if part.category else "",
        "category_color": part.category.color_hex if part.category else "#0077CC",
        "size": part.size,
        "length": part.length,
        "head": part.head,
        "drive": part.drive,
        "comp_type": part.comp_type,
        "material": part.material,
        "tool_key": part.tool_key,
        "tap_drill": part.tap_drill,
        "clearance_drill": part.clearance_drill,
        "pitch": part.pitch,
        "extra_note": part.extra_note,
        "bins": [
            {
                "id": b.id,
                "carrier_id": b.carrier_id,
                "slot_index": b.slot_index,
                "quantity_on_hand": b.quantity_on_hand,
                "reorder_threshold": b.reorder_threshold,
                "cassette_type": b.cassette_type,
                "qr_code_payload": b.qr_code_payload,
            }
            for b in part.bins
        ],
    }


@router.get("/bins")
async def list_bins(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """List all physical storage bins with assigned parts and locations."""
    stmt = select(BinRecord).options(
        selectinload(BinRecord.part).selectinload(PartRecord.category),
        selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
    ).order_by(BinRecord.id)
    res = await db.execute(stmt)
    bins = res.scalars().all()
    return [
        {
            "id": b.id,
            "part_id": b.part_id,
            "part_name": b.part.name if b.part else "",
            "category_name": b.part.category.name if b.part and b.part.category else "",
            "category_color": b.part.category.color_hex if b.part and b.part.category else "#0077CC",
            "carrier_id": b.carrier_id,
            "location_name": b.carrier.location.name if b.carrier and b.carrier.location else "",
            "slot_index": b.slot_index,
            "quantity_on_hand": b.quantity_on_hand,
            "reorder_threshold": b.reorder_threshold,
            "is_low_stock": b.quantity_on_hand <= b.reorder_threshold,
            "cassette_type": b.cassette_type,
            "qr_code_payload": b.qr_code_payload,
            "updated_at": b.updated_at.isoformat(),
        }
        for b in bins
    ]


@router.get("/bins/{bin_id}")
async def get_bin_detail(bin_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve full detail for a physical bin (scanned via QR code)."""
    stmt = select(BinRecord).options(
        selectinload(BinRecord.part).selectinload(PartRecord.category),
        selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
    ).where(BinRecord.id == bin_id)
    res = await db.execute(stmt)
    bin_rec = res.scalars().first()
    if not bin_rec:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_id}' not found")

    return {
        "id": bin_rec.id,
        "part_id": bin_rec.part_id,
        "part_name": bin_rec.part.name if bin_rec.part else "",
        "size": bin_rec.part.size if bin_rec.part else "",
        "length": bin_rec.part.length if bin_rec.part else "",
        "tool_key": bin_rec.part.tool_key if bin_rec.part else "",
        "tap_drill": bin_rec.part.tap_drill if bin_rec.part else "",
        "category_name": bin_rec.part.category.name if bin_rec.part and bin_rec.part.category else "",
        "category_color": bin_rec.part.category.color_hex if bin_rec.part and bin_rec.part.category else "#0077CC",
        "category_bg": bin_rec.part.category.color_bg if bin_rec.part and bin_rec.part.category else "#E6F3FA",
        "carrier_id": bin_rec.carrier_id,
        "location_name": bin_rec.carrier.location.name if bin_rec.carrier and bin_rec.carrier.location else "",
        "slot_index": bin_rec.slot_index,
        "quantity_on_hand": bin_rec.quantity_on_hand,
        "reorder_threshold": bin_rec.reorder_threshold,
        "is_low_stock": bin_rec.quantity_on_hand <= bin_rec.reorder_threshold,
        "cassette_type": bin_rec.cassette_type,
        "qr_code_payload": bin_rec.qr_code_payload,
        "updated_at": bin_rec.updated_at.isoformat(),
    }


@router.patch("/bins/{bin_id}/quantity")
async def update_bin_quantity(
    bin_id: str,
    payload: QuantityUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Adjust quantity on hand for a bin via delta (+/-) or absolute set."""
    stmt = select(BinRecord).where(BinRecord.id == bin_id)
    res = await db.execute(stmt)
    bin_rec = res.scalars().first()
    if not bin_rec:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_id}' not found")

    if payload.set_quantity is not None:
        bin_rec.quantity_on_hand = max(0, payload.set_quantity)
    elif payload.delta is not None:
        bin_rec.quantity_on_hand = max(0, bin_rec.quantity_on_hand + payload.delta)
    else:
        raise HTTPException(status_code=400, detail="Must provide 'delta' or 'set_quantity'")

    bin_rec.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(bin_rec)

    return {
        "id": bin_rec.id,
        "quantity_on_hand": bin_rec.quantity_on_hand,
        "updated_at": bin_rec.updated_at.isoformat(),
        "status": "success",
    }
