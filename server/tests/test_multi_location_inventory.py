import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.app.main import app
from server.app.database import init_db, configure_db_engine, AsyncSessionLocal
from server.app.models import (
    CategoryRecord,
    PartRecord,
    BinRecord,
    BinCompartmentRecord,
    CarrierRecord,
    StorageLocationRecord,
    StockTransferLogRecord,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Configure an isolated ephemeral SQLite database for each test."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_parts_s06.db")
    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine, SessionLocal = configure_db_engine(db_url)
    await init_db()
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_part_multi_location_aggregation():
    """Verify that a part stored across both primary bench and bulk storage reports correct aggregated quantities."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get details for m3_12_shcs (which has primary bench + bulk stock in updated seed)
        res = await client.get("/api/parts/m3_12_shcs")
        assert res.status_code == 200
        data = res.json()
        
        # Verify primary, bulk, and total quantities
        assert "primary_quantity" in data
        assert "bulk_quantity" in data
        assert "total_quantity" in data
        assert data["total_quantity"] == data["primary_quantity"] + data["bulk_quantity"]
        assert len(data["compartments"]) >= 2
        
        # Check that compartments have storage_role and location tier
        roles = [c.get("storage_role") for c in data["compartments"]]
        assert "PRIMARY" in roles
        assert "BULK_RESERVE" in roles


@pytest.mark.asyncio
async def test_compartment_storage_roles():
    """Verify updating a compartment's storage role via POST /api/compartments/{id}/role."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Update BIN-001-C1 role to OVERFLOW
        res = await client.post(
            "/api/compartments/BIN-001-C1/role",
            json={"storage_role": "OVERFLOW"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["storage_role"] == "OVERFLOW"
        
        # Verify in DB
        from server.app import database
        async with database.AsyncSessionLocal() as session:
            stmt = select(BinCompartmentRecord).where(BinCompartmentRecord.id == "BIN-001-C1")
            rec = (await session.execute(stmt)).scalars().first()
            assert rec.storage_role == "OVERFLOW"


@pytest.mark.asyncio
async def test_atomic_inventory_transfer_success():
    """Verify transferring stock from a bulk compartment to a primary compartment."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check initial state for m3_12_shcs
        res_initial = await client.get("/api/parts/m3_12_shcs")
        initial_data = res_initial.json()
        
        primary_comp = next(c for c in initial_data["compartments"] if c["storage_role"] == "PRIMARY")
        bulk_comp = next(c for c in initial_data["compartments"] if c["storage_role"] == "BULK_RESERVE")
        
        init_primary_qty = primary_comp["quantity_on_hand"]
        init_bulk_qty = bulk_comp["quantity_on_hand"]
        transfer_qty = 25
        
        # Execute Transfer
        transfer_payload = {
            "from_compartment_id": bulk_comp["id"],
            "to_compartment_id": primary_comp["id"],
            "quantity": transfer_qty,
            "reason": "Restock primary bench bin from bulk overstock",
        }
        res_transfer = await client.post("/api/inventory/transfer", json=transfer_payload)
        assert res_transfer.status_code == 200
        transfer_res = res_transfer.json()
        assert transfer_res["status"] == "success"
        assert transfer_res["transferred_quantity"] == transfer_qty
        
        # Check updated quantities
        res_updated = await client.get("/api/parts/m3_12_shcs")
        updated_data = res_updated.json()
        
        upd_primary_comp = next(c for c in updated_data["compartments"] if c["id"] == primary_comp["id"])
        upd_bulk_comp = next(c for c in updated_data["compartments"] if c["id"] == bulk_comp["id"])
        
        assert upd_primary_comp["quantity_on_hand"] == init_primary_qty + transfer_qty
        assert upd_bulk_comp["quantity_on_hand"] == init_bulk_qty - transfer_qty
        assert updated_data["total_quantity"] == initial_data["total_quantity"]
        
        # Verify transfer log record
        from server.app import database
        async with database.AsyncSessionLocal() as session:
            stmt = select(StockTransferLogRecord).where(
                StockTransferLogRecord.from_compartment_id == bulk_comp["id"],
                StockTransferLogRecord.to_compartment_id == primary_comp["id"],
            )
            log = (await session.execute(stmt)).scalars().first()
            assert log is not None
            assert log.quantity == transfer_qty


@pytest.mark.asyncio
async def test_atomic_inventory_transfer_insufficient_stock():
    """Verify transfer fails with HTTP 400 when transfer quantity exceeds source stock."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get primary and bulk compartments for m3_12_shcs
        res = await client.get("/api/parts/m3_12_shcs")
        data = res.json()
        primary_comp = next(c for c in data["compartments"] if c["storage_role"] == "PRIMARY")
        bulk_comp = next(c for c in data["compartments"] if c["storage_role"] == "BULK_RESERVE")

        # Attempt to transfer 99999 units from bulk compartment
        payload = {
            "from_compartment_id": bulk_comp["id"],
            "to_compartment_id": primary_comp["id"],
            "quantity": 99999,
            "reason": "Invalid excessive transfer",
        }
        res_xfer = await client.post("/api/inventory/transfer", json=payload)
        assert res_xfer.status_code == 400
        assert "Insufficient stock" in res_xfer.json()["detail"]


@pytest.mark.asyncio
async def test_atomic_inventory_transfer_part_mismatch():
    """Verify transfer fails with HTTP 400 when source and target hold different parts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # BIN-001-C1 vs BIN-002-C1
        payload = {
            "from_compartment_id": "BIN-001-C1",
            "to_compartment_id": "BIN-002-C1",
            "quantity": 5,
        }
        res = await client.post("/api/inventory/transfer", json=payload)
        assert res.status_code == 400
        assert "Part mismatch" in res.json()["detail"]


@pytest.mark.asyncio
async def test_replenishment_alert_trigger():
    """Verify GET /api/inventory/replenish-alerts identifies primary bins below threshold with bulk stock available."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get details for m3_12_shcs (which has bulk stock in BIN-081)
        res_part = await client.get("/api/parts/m3_12_shcs")
        part_data = res_part.json()
        primary_comp = next(c for c in part_data["compartments"] if c["storage_role"] == "PRIMARY")
        
        # Set primary compartment to 5 pieces (threshold is 15)
        await client.post(
            f"/api/compartments/{primary_comp['id']}/quantity",
            json={"set_quantity": 5}
        )
        
        res = await client.get("/api/inventory/replenish-alerts")
        assert res.status_code == 200
        alerts = res.json()
        
        # Verify primary_comp appears in alerts because bulk stock exists in BIN-081
        alert_comp_ids = [a["primary_compartment_id"] for a in alerts]
        assert primary_comp["id"] in alert_comp_ids
        
        target_alert = next(a for a in alerts if a["primary_compartment_id"] == primary_comp["id"])
        assert target_alert["primary_quantity"] == 5
        assert target_alert["reorder_threshold"] >= 5
        assert target_alert["bulk_available_quantity"] > 0
        assert len(target_alert["available_sources"]) >= 1


@pytest.mark.asyncio
async def test_part_detail_view_multi_location_context():
    """Verify /p/{part_id} HTML view context renders both primary and bulk storage cards."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/p/m3_12_shcs")
        assert res.status_code == 200
        assert "Primary Workstation Bins" in res.text or "Primary Storage" in res.text
        assert "Bulk Overstock" in res.text or "Deep Storage" in res.text
        assert "Transfer from Bulk" in res.text or "Restock" in res.text
