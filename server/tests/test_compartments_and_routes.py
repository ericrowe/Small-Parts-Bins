import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.app.main import app
from server.app.database import init_db, configure_db_engine
from server.app.models import CategoryRecord, PartRecord, BinRecord, BinCompartmentRecord


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Configure an isolated ephemeral SQLite database for each test."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_parts_m02.db")
    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine, SessionLocal = configure_db_engine(db_url)
    await init_db()
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_1_2_3_compartment_bin_creation():
    """Verify that seed populates 1-compartment, 2-compartment, and 3-compartment physical bins."""
    from server.app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        bins_res = await session.execute(
            select(BinRecord).options(selectinload(BinRecord.compartments))
        )
        bins = bins_res.scalars().all()
        assert len(bins) == 24

        comp_counts = {b.compartment_count for b in bins}
        assert 1 in comp_counts
        assert 2 in comp_counts
        assert 3 in comp_counts

        # Check a 3-compartment bin has exactly 3 compartments
        bin_3way = next(b for b in bins if b.compartment_count == 3)
        assert len(bin_3way.compartments) == 3
        assert bin_3way.cassette_type == "divided_3"


@pytest.mark.asyncio
async def test_dynamic_compartment_part_reassignment():
    """Verify POST /api/bins/{bin_id}/compartments dynamically assigns/swaps parts in slot 1, 2, or 3."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get list of parts
        res_parts = await client.get("/api/parts")
        parts = res_parts.json()
        target_part = parts[0]["id"]

        # Assign to Slot 2 of BIN-002 (2-way divided)
        payload = {
            "compartment_index": 2,
            "part_id": target_part,
            "quantity_on_hand": 75,
            "reorder_threshold": 12,
        }
        res_assign = await client.post("/api/bins/BIN-002/compartments", json=payload)
        assert res_assign.status_code == 200
        data = res_assign.json()
        assert data["status"] == "success"
        assert data["part_id"] == target_part
        assert data["quantity_on_hand"] == 75

        # Verify through GET /api/bins/BIN-002
        res_bin = await client.get("/api/bins/BIN-002")
        assert res_bin.status_code == 200
        bin_data = res_bin.json()
        comp2 = next(c for c in bin_data["compartments"] if c["compartment_index"] == 2)
        assert comp2["part_id"] == target_part
        assert comp2["quantity_on_hand"] == 75


@pytest.mark.asyncio
async def test_compartment_quantity_adjustment():
    """Verify PATCH /api/compartments/{comp_id}/quantity adjusts stock accurately."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check BIN-001 compartment 1
        comp_id = "BIN-001-C1"
        res_inc = await client.patch(f"/api/compartments/{comp_id}/quantity", json={"delta": 10})
        assert res_inc.status_code == 200
        new_qty = res_inc.json()["quantity_on_hand"]

        res_dec = await client.patch(f"/api/compartments/{comp_id}/quantity", json={"delta": -5})
        assert res_dec.status_code == 200
        assert res_dec.json()["quantity_on_hand"] == new_qty - 5


@pytest.mark.asyncio
async def test_part_detail_spec_view():
    """Verify GET /p/{part_id} renders fastener specs and lists containing bins."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_parts = await client.get("/api/parts")
        first_part_id = res_parts.json()[0]["id"]

        res_view = await client.get(f"/p/{first_part_id}")
        assert res_view.status_code == 200
        assert "Tap Drill" in res_view.text
        assert "Thread Pitch" in res_view.text
        assert "Physical Storage Bins" in res_view.text


@pytest.mark.asyncio
async def test_bin_detail_compartment_view():
    """Verify GET /b/{bin_id} renders 1, 2, or 3-compartment visual layout with part mapper."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1-compartment bin
        res_b1 = await client.get("/b/BIN-001")
        assert res_b1.status_code == 200
        assert "Slot 1 of 1" in res_b1.text

        # 2-compartment bin
        res_b2 = await client.get("/b/BIN-002")
        assert res_b2.status_code == 200
        assert "Slot 1 of 2" in res_b2.text
        assert "Slot 2 of 2" in res_b2.text

        # 3-compartment bin
        res_b3 = await client.get("/b/BIN-003")
        assert res_b3.status_code == 200
        assert "Slot 1 of 3" in res_b3.text
        assert "Slot 2 of 3" in res_b3.text
        assert "Slot 3 of 3" in res_b3.text
