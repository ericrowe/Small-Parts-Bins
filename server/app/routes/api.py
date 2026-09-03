from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from server.app.database import get_db
from server.app.models import CategoryRecord, PartRecord, BinRecord, BinCompartmentRecord, CarrierRecord, StorageLocationRecord

router = APIRouter(prefix="/api", tags=["API"])


# Pydantic Request Schemas
class QuantityUpdateRequest(BaseModel):
    delta: Optional[int] = None
    set_quantity: Optional[int] = None


class CompartmentAssignmentPayload(BaseModel):
    compartment_index: int  # 1, 2, or 3
    part_id: Optional[str] = None
    quantity_on_hand: Optional[int] = None
    reorder_threshold: Optional[int] = None


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """Return catalog health and runtime telemetry."""
    return {
        "status": "online",
        "service": "Parts-Database Catalog Microservice",
        "version": "0.2.0",
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
    stmt = select(PartRecord).options(
        selectinload(PartRecord.category),
        selectinload(PartRecord.compartments).selectinload(BinCompartmentRecord.bin),
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
            "total_quantity": sum(c.quantity_on_hand for c in p.compartments),
            "compartments_count": len(p.compartments),
        }
        for p in parts
    ]


@router.get("/parts/{part_id}")
async def get_part_detail(part_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve full technical specs and containing bins/compartments for a fastener part."""
    stmt = select(PartRecord).options(
        selectinload(PartRecord.category),
        selectinload(PartRecord.compartments).selectinload(BinCompartmentRecord.bin).selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
    ).where(PartRecord.id == part_id)
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
        "category_bg": part.category.color_bg if part.category else "#E6F3FA",
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
        "total_stock": sum(c.quantity_on_hand for c in part.compartments),
        "compartments": [
            {
                "id": c.id,
                "bin_id": c.bin_id,
                "compartment_index": c.compartment_index,
                "quantity_on_hand": c.quantity_on_hand,
                "reorder_threshold": c.reorder_threshold,
                "is_low_stock": c.quantity_on_hand <= c.reorder_threshold,
                "cassette_type": c.bin.cassette_type if c.bin else "",
                "carrier_id": c.bin.carrier_id if c.bin else "",
                "location_name": c.bin.carrier.location.name if c.bin and c.bin.carrier and c.bin.carrier.location else "",
            }
            for c in part.compartments
        ],
    }


@router.get("/bins")
async def list_bins(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """List all physical cassette bins with their 1, 2, or 3 compartments."""
    stmt = select(BinRecord).options(
        selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
        selectinload(BinRecord.compartments).selectinload(BinCompartmentRecord.part).selectinload(PartRecord.category),
    ).order_by(BinRecord.id)
    res = await db.execute(stmt)
    bins = res.scalars().all()
    return [
        {
            "id": b.id,
            "carrier_id": b.carrier_id,
            "slot_index": b.slot_index,
            "compartment_count": b.compartment_count,
            "cassette_type": b.cassette_type,
            "label_title": b.label_title,
            "qr_code_payload": b.qr_code_payload,
            "location_name": b.carrier.location.name if b.carrier and b.carrier.location else "",
            "total_quantity": sum(c.quantity_on_hand for c in b.compartments),
            "compartments": [
                {
                    "id": c.id,
                    "compartment_index": c.compartment_index,
                    "part_id": c.part_id,
                    "part_name": c.part.name if c.part else "Unassigned / Empty",
                    "category_name": c.part.category.name if c.part and c.part.category else "",
                    "category_color": c.part.category.color_hex if c.part and c.part.category else "#64748b",
                    "quantity_on_hand": c.quantity_on_hand,
                    "reorder_threshold": c.reorder_threshold,
                    "is_low_stock": c.quantity_on_hand <= c.reorder_threshold,
                }
                for c in b.compartments
            ],
            "updated_at": b.updated_at.isoformat(),
        }
        for b in bins
    ]


@router.get("/bins/{bin_id}")
async def get_bin_detail(bin_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve full detail for a physical cassette bin (scanned via QR code / URL)."""
    stmt = select(BinRecord).options(
        selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
        selectinload(BinRecord.compartments).selectinload(BinCompartmentRecord.part).selectinload(PartRecord.category),
    ).where(BinRecord.id == bin_id)
    res = await db.execute(stmt)
    bin_rec = res.scalars().first()
    if not bin_rec:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_id}' not found")

    return {
        "id": bin_rec.id,
        "carrier_id": bin_rec.carrier_id,
        "slot_index": bin_rec.slot_index,
        "compartment_count": bin_rec.compartment_count,
        "cassette_type": bin_rec.cassette_type,
        "label_title": bin_rec.label_title,
        "qr_code_payload": bin_rec.qr_code_payload,
        "location_name": bin_rec.carrier.location.name if bin_rec.carrier and bin_rec.carrier.location else "",
        "compartments": [
            {
                "id": c.id,
                "compartment_index": c.compartment_index,
                "part_id": c.part_id,
                "part_name": c.part.name if c.part else "Unassigned / Empty",
                "size": c.part.size if c.part else "",
                "length": c.part.length if c.part else "",
                "tool_key": c.part.tool_key if c.part else "",
                "tap_drill": c.part.tap_drill if c.part else "",
                "category_name": c.part.category.name if c.part and c.part.category else "",
                "category_color": c.part.category.color_hex if c.part and c.part.category else "#64748b",
                "category_bg": c.part.category.color_bg if c.part and c.part.category else "#1e293b",
                "quantity_on_hand": c.quantity_on_hand,
                "reorder_threshold": c.reorder_threshold,
                "is_low_stock": c.quantity_on_hand <= c.reorder_threshold,
                "notes": c.notes,
            }
            for c in bin_rec.compartments
        ],
        "updated_at": bin_rec.updated_at.isoformat(),
    }


@router.post("/bins/{bin_id}/compartments")
async def update_bin_compartment_assignment(
    bin_id: str,
    payload: CompartmentAssignmentPayload,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Assign or swap a part in compartment slot 1, 2, or 3 of a physical bin."""
    stmt = select(BinRecord).options(selectinload(BinRecord.compartments)).where(BinRecord.id == bin_id)
    res = await db.execute(stmt)
    bin_rec = res.scalars().first()
    if not bin_rec:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_id}' not found")

    # Find existing compartment or create if index within count
    comp = next((c for c in bin_rec.compartments if c.compartment_index == payload.compartment_index), None)
    if not comp:
        if payload.compartment_index > bin_rec.compartment_count or payload.compartment_index < 1:
            raise HTTPException(status_code=400, detail=f"Invalid compartment index {payload.compartment_index} for {bin_rec.cassette_type}")
        comp = BinCompartmentRecord(
            id=f"{bin_id}-C{payload.compartment_index}",
            bin_id=bin_id,
            compartment_index=payload.compartment_index,
        )
        db.add(comp)

    # If part_id provided, verify it exists
    if payload.part_id:
        p_res = await db.execute(select(PartRecord).where(PartRecord.id == payload.part_id))
        if not p_res.scalars().first():
            raise HTTPException(status_code=404, detail=f"Part '{payload.part_id}' not found")
        comp.part_id = payload.part_id
    elif payload.part_id == "":
        comp.part_id = None

    if payload.quantity_on_hand is not None:
        comp.quantity_on_hand = max(0, payload.quantity_on_hand)
    if payload.reorder_threshold is not None:
        comp.reorder_threshold = max(0, payload.reorder_threshold)

    comp.updated_at = datetime.now(timezone.utc)
    bin_rec.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "status": "success",
        "bin_id": bin_id,
        "compartment_id": comp.id,
        "compartment_index": comp.compartment_index,
        "part_id": comp.part_id,
        "quantity_on_hand": comp.quantity_on_hand,
    }


@router.patch("/compartments/{comp_id}/quantity")
async def update_compartment_quantity(
    comp_id: str,
    payload: QuantityUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Adjust inventory stock for an individual compartment via delta (+/-) or absolute set."""
    stmt = select(BinCompartmentRecord).where(BinCompartmentRecord.id == comp_id)
    res = await db.execute(stmt)
    comp = res.scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Compartment '{comp_id}' not found")

    if payload.set_quantity is not None:
        comp.quantity_on_hand = max(0, payload.set_quantity)
    elif payload.delta is not None:
        comp.quantity_on_hand = max(0, comp.quantity_on_hand + payload.delta)
    else:
        raise HTTPException(status_code=400, detail="Must provide 'delta' or 'set_quantity'")

    comp.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(comp)

    return {
        "status": "success",
        "id": comp.id,
        "compartment_index": comp.compartment_index,
        "quantity_on_hand": comp.quantity_on_hand,
        "updated_at": comp.updated_at.isoformat(),
    }
