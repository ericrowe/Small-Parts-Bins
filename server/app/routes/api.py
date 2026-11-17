import uuid
import base64
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File, Form
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from server.app.database import get_db
from server.app.models import (
    CategoryRecord,
    PartRecord,
    BinRecord,
    BinCompartmentRecord,
    CarrierRecord,
    StorageLocationRecord,
    StockTransferLogRecord,
)
from server.app.services.label_service import get_labels_for_parts, export_labels_to_format
from server.app.services.homebox_service import (
    get_next_sequential_bin_name,
    commit_cartridge_to_homebox,
    list_ingested_bins,
    resolve_homebox_paths,
    login_to_homebox,
    get_homebox_connection_status,
    list_qr_forwarding_entries,
    register_qr_forwarding_entry,
    delete_qr_forwarding_entry,
    set_bins_printed_status,
    _get_qr_forwarding_file_path,
)
from server.app.services.part_ingestor_service import (
    analyze_cartridge_photo,
    lookup_fastener_specs,
)

router = APIRouter(prefix="/api", tags=["API"])


class BatchLabelExportRequest(BaseModel):
    part_ids: Optional[List[str]] = None
    category_id: Optional[str] = None
    custom_labels: Optional[List[Dict[str, Any]]] = None
    format: str = "split_vertical_12x35"
    title: Optional[str] = "Homebox Cartridge Labels"
    include_qr: bool = True
    mark_printed: bool = False


class LabelPrintedStatusUpdateRequest(BaseModel):
    bin_codes: List[str]
    printed: bool = True


# Pydantic Request Schemas
class QuantityUpdateRequest(BaseModel):
    delta: Optional[int] = None
    set_quantity: Optional[int] = None


class CompartmentAssignmentPayload(BaseModel):
    compartment_index: int  # 1, 2, or 3
    part_id: Optional[str] = None
    quantity_on_hand: Optional[int] = None
    reorder_threshold: Optional[int] = None
    storage_role: Optional[str] = "PRIMARY"


class InventoryTransferRequest(BaseModel):
    from_compartment_id: str
    to_compartment_id: str
    quantity: int
    reason: Optional[str] = "Restock"


class CompartmentRoleUpdateRequest(BaseModel):
    storage_role: str


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """Return catalog health and runtime telemetry."""
    return {
        "status": "online",
        "service": "Parts-Database Catalog Microservice",
        "version": "0.3.0",
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
    """List parts with optional search query, category filtering, and multi-tier stock quantities."""
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
            "primary_quantity": sum(c.quantity_on_hand for c in p.compartments if getattr(c, "storage_role", "PRIMARY") == "PRIMARY"),
            "bulk_quantity": sum(c.quantity_on_hand for c in p.compartments if getattr(c, "storage_role", "PRIMARY") in ("BULK_RESERVE", "OVERFLOW")),
            "total_quantity": sum(c.quantity_on_hand for c in p.compartments),
            "compartments_count": len(p.compartments),
        }
        for p in parts
    ]


@router.get("/parts/{part_id}")
async def get_part_detail(part_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve full technical specs, multi-tier stock aggregation, and containing bins for a fastener part."""
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
    primary_qty = sum(c.quantity_on_hand for c in primary_comps)
    bulk_qty = sum(c.quantity_on_hand for c in bulk_comps)
    total_qty = sum(c.quantity_on_hand for c in part.compartments)

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
        "primary_quantity": primary_qty,
        "bulk_quantity": bulk_qty,
        "total_quantity": total_qty,
        "total_stock": total_qty,
        "compartments": [
            {
                "id": c.id,
                "bin_id": c.bin_id,
                "compartment_index": c.compartment_index,
                "storage_role": getattr(c, "storage_role", "PRIMARY"),
                "quantity_on_hand": c.quantity_on_hand,
                "reorder_threshold": c.reorder_threshold,
                "is_low_stock": c.quantity_on_hand <= c.reorder_threshold,
                "cassette_type": c.bin.cassette_type if c.bin else "",
                "carrier_id": c.bin.carrier_id if c.bin else "",
                "location_name": c.bin.carrier.location.name if c.bin and c.bin.carrier and c.bin.carrier.location else "",
                "location_tier": c.bin.carrier.location.tier if c.bin and c.bin.carrier and c.bin.carrier.location else "PRIMARY_BENCH",
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
    if payload.storage_role is not None:
        comp.storage_role = payload.storage_role.upper()

    comp.updated_at = datetime.now(timezone.utc)
    bin_rec.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "status": "success",
        "bin_id": bin_id,
        "compartment_id": comp.id,
        "compartment_index": comp.compartment_index,
        "part_id": comp.part_id,
        "storage_role": comp.storage_role,
        "quantity_on_hand": comp.quantity_on_hand,
    }


@router.api_route("/compartments/{comp_id}/quantity", methods=["POST", "PATCH"])
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
        "storage_role": getattr(comp, "storage_role", "PRIMARY"),
        "updated_at": comp.updated_at.isoformat(),
    }


@router.post("/compartments/{comp_id}/role")
async def update_compartment_role(
    comp_id: str,
    payload: CompartmentRoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Update a compartment's storage role (PRIMARY, BULK_RESERVE, OVERFLOW)."""
    valid_roles = {"PRIMARY", "BULK_RESERVE", "OVERFLOW"}
    role_upper = payload.storage_role.upper()
    if role_upper not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid storage role '{payload.storage_role}'. Must be one of {valid_roles}")

    stmt = select(BinCompartmentRecord).where(BinCompartmentRecord.id == comp_id)
    res = await db.execute(stmt)
    comp = res.scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Compartment '{comp_id}' not found")

    comp.storage_role = role_upper
    comp.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(comp)

    return {
        "status": "success",
        "id": comp.id,
        "compartment_index": comp.compartment_index,
        "storage_role": comp.storage_role,
        "updated_at": comp.updated_at.isoformat(),
    }


@router.post("/inventory/transfer")
async def transfer_inventory(
    req: InventoryTransferRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Atomically transfer fastener hardware from one compartment to another (e.g. Bulk -> Primary)."""
    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="Transfer quantity must be greater than 0")

    stmt_from = select(BinCompartmentRecord).where(BinCompartmentRecord.id == req.from_compartment_id)
    stmt_to = select(BinCompartmentRecord).where(BinCompartmentRecord.id == req.to_compartment_id)

    from_comp = (await db.execute(stmt_from)).scalars().first()
    to_comp = (await db.execute(stmt_to)).scalars().first()

    if not from_comp:
        raise HTTPException(status_code=404, detail=f"Source compartment '{req.from_compartment_id}' not found")
    if not to_comp:
        raise HTTPException(status_code=404, detail=f"Destination compartment '{req.to_compartment_id}' not found")

    if not from_comp.part_id:
        raise HTTPException(status_code=400, detail="Source compartment has no part assigned")

    if not to_comp.part_id:
        to_comp.part_id = from_comp.part_id
    elif to_comp.part_id != from_comp.part_id:
        p1 = from_comp.part_id.lower().replace("-", "_").replace("mm", "")
        p2 = to_comp.part_id.lower().replace("-", "_").replace("mm", "")
        if p1 != p2:
            raise HTTPException(
                status_code=400,
                detail=f"Part mismatch: Source holds '{from_comp.part_id}' but destination holds '{to_comp.part_id}'"
            )

    if from_comp.quantity_on_hand < req.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock in source compartment '{req.from_compartment_id}': available {from_comp.quantity_on_hand}, requested {req.quantity}"
        )

    # Atomic stock modification
    from_comp.quantity_on_hand -= req.quantity
    to_comp.quantity_on_hand += req.quantity
    now = datetime.now(timezone.utc)
    from_comp.updated_at = now
    to_comp.updated_at = now

    transfer_log = StockTransferLogRecord(
        id=str(uuid.uuid4()),
        part_id=from_comp.part_id,
        from_compartment_id=from_comp.id,
        to_compartment_id=to_comp.id,
        quantity=req.quantity,
        reason=req.reason or "Restock",
        created_at=now,
    )
    db.add(transfer_log)
    await db.commit()

    return {
        "status": "success",
        "transfer_id": transfer_log.id,
        "part_id": from_comp.part_id,
        "from_compartment_id": from_comp.id,
        "to_compartment_id": to_comp.id,
        "transferred_quantity": req.quantity,
        "from_remaining_quantity": from_comp.quantity_on_hand,
        "to_new_quantity": to_comp.quantity_on_hand,
        "timestamp": now.isoformat(),
    }


@router.get("/inventory/replenish-alerts")
async def get_replenishment_alerts(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """Return all primary compartments that are low on stock and have available bulk/overflow inventory."""
    stmt = select(BinCompartmentRecord).options(
        selectinload(BinCompartmentRecord.part).selectinload(PartRecord.category),
        selectinload(BinCompartmentRecord.bin).selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
    ).where(
        BinCompartmentRecord.storage_role == "PRIMARY",
        BinCompartmentRecord.part_id.isnot(None),
        BinCompartmentRecord.quantity_on_hand <= BinCompartmentRecord.reorder_threshold,
    )
    res = await db.execute(stmt)
    low_primary_comps = res.scalars().all()

    alerts = []
    for comp in low_primary_comps:
        # Find bulk or overflow sources for this part
        p_clean = comp.part_id.lower().replace("-", "_").replace("mm", "")
        all_comps_stmt = select(BinCompartmentRecord).options(
            selectinload(BinCompartmentRecord.bin).selectinload(BinRecord.carrier).selectinload(CarrierRecord.location),
        ).where(
            BinCompartmentRecord.id != comp.id,
            BinCompartmentRecord.storage_role.in_(["BULK_RESERVE", "OVERFLOW"]),
            BinCompartmentRecord.quantity_on_hand > 0,
        )
        bulk_res = await db.execute(all_comps_stmt)
        candidate_sources = bulk_res.scalars().all()
        
        sources = [
            s for s in candidate_sources
            if s.part_id and (s.part_id == comp.part_id or s.part_id.lower().replace("-", "_").replace("mm", "") == p_clean)
        ]

        if sources:
            bulk_available_qty = sum(s.quantity_on_hand for s in sources)
            alerts.append({
                "part_id": comp.part_id,
                "part_name": comp.part.name if comp.part else comp.part_id,
                "primary_compartment_id": comp.id,
                "primary_bin_id": comp.bin_id,
                "primary_quantity": comp.quantity_on_hand,
                "reorder_threshold": comp.reorder_threshold,
                "bulk_available_quantity": bulk_available_qty,
                "category_name": comp.part.category.name if comp.part and comp.part.category else "",
                "category_color": comp.part.category.color_hex if comp.part and comp.part.category else "#64748b",
                "available_sources": [
                    {
                        "compartment_id": s.id,
                        "bin_id": s.bin_id,
                        "storage_role": s.storage_role,
                        "quantity_on_hand": s.quantity_on_hand,
                        "location_name": s.bin.carrier.location.name if s.bin and s.bin.carrier and s.bin.carrier.location else "",
                    }
                    for s in sources
                ],
            })

    return alerts


@router.post("/labels/export-batch")
async def export_batch_labels_post(
    req: BatchLabelExportRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate and return batch label SVG package (11x34 Split Pair, Cricut, Avery, or Thermal) via POST."""
    labels = await get_labels_for_parts(
        db,
        part_ids=req.part_ids,
        category_id=req.category_id,
        custom_labels=req.custom_labels,
    )
    try:
        export_res = export_labels_to_format(
            labels=labels,
            export_format=req.format,
            title=req.title or "Homebox Cartridge Labels",
            include_qr=req.include_qr,
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Homebox API error: {e}")

    headers: Dict[str, str] = {
        "Content-Disposition": f'attachment; filename="{export_res["filename"]}"',
    }
    if req.mark_printed:
        page_count = int(export_res.get("label_count") or len(labels))
        page_bins = [lbl.bin_id for lbl in labels[:page_count] if getattr(lbl, "bin_id", "")]
        if page_bins:
            updated = set_bins_printed_status(page_bins, printed=True)
            headers["X-Marked-Printed-Bins"] = ",".join(u["code"] for u in updated)

    return Response(
        content=export_res["content"],
        media_type=export_res["media_type"],
        headers=headers,
    )


@router.post("/labels/printed-status")
async def update_labels_printed_status_endpoint(req: LabelPrintedStatusUpdateRequest) -> Dict[str, Any]:
    """Mark one or more 4-digit bin codes as printed or unprinted."""
    updated = set_bins_printed_status(req.bin_codes, printed=req.printed)
    return {
        "status": "ok",
        "printed": req.printed,
        "updated": updated,
        "entries": list_qr_forwarding_entries(),
    }


@router.get("/labels/export-batch")
async def export_batch_labels_get(
    format: str = Query("cricut_print_cut", description="Target format: cricut_print_cut, avery_5160, avery_5167, thermal_roll"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    part_ids: Optional[List[str]] = Query(None, description="Specific list of part IDs"),
    title: Optional[str] = Query("Hardware Labels", description="Sheet header title"),
    include_qr: bool = Query(True, description="Include QR codes on labels"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate and return batch label SVG package via GET URL parameters."""
    labels = await get_labels_for_parts(db, part_ids=part_ids, category_id=category_id)
    try:
        export_res = export_labels_to_format(
            labels=labels,
            export_format=format,
            title=title or "Hardware Labels",
            include_qr=include_qr,
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Homebox API error: {e}")

    return Response(
        content=export_res["content"],
        media_type=export_res["media_type"],
        headers={"Content-Disposition": f'attachment; filename="{export_res["filename"]}"'},
    )


class IngestGroupItemPayload(BaseModel):
    name: Optional[str] = None
    size: Optional[str] = ""
    length: Optional[str] = ""
    pitch: Optional[str] = ""
    head: Optional[str] = "shcs"
    drive: Optional[str] = "hex"
    comp_type: Optional[str] = "bolt"
    finish: Optional[str] = "Black Oxide Steel"
    finish_key: Optional[str] = ""
    quantity: int = 1
    tool_key: Optional[str] = ""
    tap_drill: Optional[str] = ""
    clearance_drill: Optional[str] = ""
    notes: Optional[str] = ""


class IngestCartridgeCommitRequest(BaseModel):
    bin_id: Optional[str] = None
    cartridge_label: Optional[str] = ""
    mode: str = "photo"
    notes: Optional[str] = ""
    photo_base64: Optional[str] = None
    groups: List[IngestGroupItemPayload]


class HomeboxLoginRequest(BaseModel):
    username: str
    password: str
    base_url: Optional[str] = None


@router.post("/ingest/homebox-login")
async def ingest_homebox_login(req: HomeboxLoginRequest) -> Dict[str, Any]:
    """Authenticate against Homebox REST API (/api/v1/users/login) and cache the Bearer token."""
    try:
        auth_res = login_to_homebox(
            username=req.username,
            password=req.password,
            base_url=req.base_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Homebox API connection error: {e}")

    next_bin = get_next_sequential_bin_name(auth_res["base_url"])
    return {
        **auth_res,
        "next_bin_id": next_bin,
    }


@router.get("/ingest/next-bin")
async def get_ingest_next_bin() -> Dict[str, Any]:
    """Return the next sequential temporary bin ID (e.g. BIN-001) and Homebox REST API connection status."""
    paths = resolve_homebox_paths()
    conn_status = get_homebox_connection_status()
    next_bin = get_next_sequential_bin_name(paths["base_url"])
    return {
        "status": "ok",
        "next_bin_id": next_bin,
        "homebox_base_url": paths["base_url"],
        "homebox_api_url": paths["api_url"],
        "authenticated": conn_status["authenticated"],
        "connection_message": conn_status["message"],
    }


@router.get("/ingest/specs")
async def get_fastener_engineering_specs(
    size: str = Query(..., description="Thread size, e.g. M3, M4, #6-32"),
    head: str = Query("shcs", description="Head style: shcs, bhcs, fhcs, hex, pan"),
    drive: str = Query("hex", description="Drive type: hex, torx, phillips"),
) -> Dict[str, Any]:
    """Look up canonical pitch, tap drill, clearance drill, and hex key for a thread size & head."""
    specs = lookup_fastener_specs(size=size, head=head, drive=drive)
    return {
        "size": size,
        "head": head,
        "drive": drive,
        **specs,
    }


@router.post("/ingest/analyze-photo")
async def analyze_ingest_photo_endpoint(
    photo: UploadFile = File(...),
    size_hint: Optional[str] = Form(None),
    length_hint: Optional[str] = Form(None),
    pitch_hint: Optional[str] = Form(None),
    ruler_mm_per_px: Optional[float] = Form(None),
) -> Dict[str, Any]:
    """Analyze an uploaded cartridge photo (label cutout OCR, Black/Silver clustering, piece counts, head ID)."""
    image_bytes = await photo.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded photo is empty.")

    hints: Dict[str, Any] = {}
    if size_hint:
        hints["size"] = size_hint.strip()
    if length_hint:
        hints["length"] = length_hint.strip()
    if pitch_hint:
        hints["pitch"] = pitch_hint.strip()

    try:
        analysis = analyze_cartridge_photo(
            image_bytes=image_bytes,
            user_hints=hints,
            ruler_mm_per_px=ruler_mm_per_px,
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Homebox API error: {e}")

    next_bin = get_next_sequential_bin_name()
    return {
        "status": "success",
        "next_bin_id": next_bin,
        **analysis,
    }


@router.post("/ingest/commit")
async def commit_ingest_cartridge_endpoint(req: IngestCartridgeCommitRequest) -> Dict[str, Any]:
    """Commit a cataloged cartridge (from Photo Mode or Form Entry Mode) into Homebox (:7745)."""
    if not req.groups:
        raise HTTPException(status_code=400, detail="At least one hardware group must be provided.")

    photo_bytes: Optional[bytes] = None
    if req.photo_base64:
        raw_b64 = req.photo_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        try:
            photo_bytes = base64.b64decode(raw_b64)
        except Exception:
            photo_bytes = None

    groups_dicts: List[Dict[str, Any]] = []
    for g in req.groups:
        g_dict = g.model_dump()
        # Enrich missing drill/key specs from fasteners.json if size is known
        if g_dict.get("size") and not g_dict.get("tap_drill"):
            specs = lookup_fastener_specs(g_dict["size"], head=g_dict.get("head") or "shcs", drive=g_dict.get("drive") or "hex")
            g_dict["pitch"] = g_dict.get("pitch") or specs.get("pitch", "")
            g_dict["tap_drill"] = g_dict.get("tap_drill") or specs.get("tap_drill", "")
            g_dict["clearance_drill"] = g_dict.get("clearance_drill") or specs.get("clearance_drill", "")
            g_dict["tool_key"] = g_dict.get("tool_key") or specs.get("tool_key", "")
        groups_dicts.append(g_dict)

    try:
        result = commit_cartridge_to_homebox(
            payload={
                "bin_id": req.bin_id,
                "cartridge_label": req.cartridge_label,
                "mode": req.mode,
                "notes": req.notes,
                "groups": groups_dicts,
            },
            photo_bytes=photo_bytes,
            photo_filename="cartridge.jpg" if photo_bytes else None,
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Homebox API error: {e}")

    return result


@router.get("/ingest/history")
async def get_ingest_history_endpoint(limit: int = Query(50, ge=1, le=200)) -> Dict[str, Any]:
    """List sequential BIN-XXX cartridge locations and their hardware items in Homebox."""
    return list_ingested_bins(limit=limit)


class QrForwardingUpdateRequest(BaseModel):
    bin_code: str
    target_url: str
    label: Optional[str] = ""


@router.get("/qr-forwarding")
async def get_qr_forwarding_table_endpoint() -> Dict[str, Any]:
    """Return all 4-digit QR code forwarding rules and the qr_forwarding.json path."""
    return {
        "status": "ok",
        "file_path": _get_qr_forwarding_file_path(),
        "entries": list_qr_forwarding_entries(),
    }


@router.post("/qr-forwarding")
async def update_qr_forwarding_entry_endpoint(req: QrForwardingUpdateRequest) -> Dict[str, Any]:
    """Create or update a 4-digit QR forwarding rule (and mark it as a manual override)."""
    if not req.bin_code.strip() or not req.target_url.strip():
        raise HTTPException(status_code=400, detail="Both bin_code and target_url are required.")
    entry = register_qr_forwarding_entry(
        bin_code=req.bin_code,
        target_url=req.target_url,
        label=req.label or "",
        manual_override=True,
        preserve_existing=False,
    )
    return {
        "status": "ok",
        "entry": entry,
        "entries": list_qr_forwarding_entries(),
    }


@router.delete("/qr-forwarding/{bin_code}")
async def delete_qr_forwarding_entry_endpoint(bin_code: str) -> Dict[str, Any]:
    """Remove a 4-digit QR forwarding rule so it resets or re-syncs from Homebox."""
    deleted = delete_qr_forwarding_entry(bin_code)
    return {
        "status": "ok",
        "deleted": deleted,
        "entries": list_qr_forwarding_entries(),
    }


