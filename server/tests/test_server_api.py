import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from server.app.main import app
from server.app.database import init_db, configure_db_engine
from server.app.models import CategoryRecord, PartRecord, BinRecord


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Configure an isolated ephemeral SQLite database for each test."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_parts.db")
    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine, SessionLocal = configure_db_engine(db_url)
    await init_db()
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_db_initialization_and_seed():
    """Verify that init_db() seeds taxonomy categories and sample fastener items."""
    from server.app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        cats = (await session.execute(select(CategoryRecord))).scalars().all()
        assert len(cats) >= 6
        cat_ids = [c.id for c in cats]
        assert "metric_coarse" in cat_ids
        assert "imperial_unc" in cat_ids
        assert "heat_set_inserts" in cat_ids

        parts = (await session.execute(select(PartRecord))).scalars().all()
        assert len(parts) > 10

        bins = (await session.execute(select(BinRecord))).scalars().all()
        assert len(bins) > 10


@pytest.mark.asyncio
async def test_api_get_parts_and_filtering():
    """Verify GET /api/parts returns JSON list and supports search query filtering."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # All parts
        res = await client.get("/api/parts")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Query filter for M3
        res_m3 = await client.get("/api/parts?q=M3")
        assert res_m3.status_code == 200
        m3_data = res_m3.json()
        assert len(m3_data) > 0
        for p in m3_data:
            assert "M3" in p["name"] or "M3" in p["size"] or "M3" in p["id"]

        # Category filter
        res_cat = await client.get("/api/parts?category=heat_set_inserts")
        assert res_cat.status_code == 200
        cat_data = res_cat.json()
        assert len(cat_data) > 0
        for p in cat_data:
            assert p["category_id"] == "heat_set_inserts"


@pytest.mark.asyncio
async def test_api_get_part_detail():
    """Verify GET /api/parts/{part_id} returns part specifications and assigned bins."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First get list
        res_list = await client.get("/api/parts")
        first_part_id = res_list.json()[0]["id"]

        # Get detail
        res = await client.get(f"/api/parts/{first_part_id}")
        assert res.status_code == 200
        part = res.json()
        assert part["id"] == first_part_id
        assert "bins" in part
        assert "tap_drill" in part
        assert "tool_key" in part


@pytest.mark.asyncio
async def test_bin_quantity_patch():
    """Verify PATCH /api/bins/{bin_id}/quantity updates inventory correctly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_bins = await client.get("/api/bins")
        assert res_bins.status_code == 200
        first_bin = res_bins.json()[0]
        bin_id = first_bin["id"]
        initial_qty = first_bin["quantity_on_hand"]

        # 1. Delta increment
        res_inc = await client.patch(f"/api/bins/{bin_id}/quantity", json={"delta": 5})
        assert res_inc.status_code == 200
        assert res_inc.json()["quantity_on_hand"] == initial_qty + 5

        # 2. Delta decrement
        res_dec = await client.patch(f"/api/bins/{bin_id}/quantity", json={"delta": -3})
        assert res_dec.status_code == 200
        assert res_dec.json()["quantity_on_hand"] == initial_qty + 2

        # 3. Absolute set
        res_set = await client.patch(f"/api/bins/{bin_id}/quantity", json={"set_quantity": 42})
        assert res_set.status_code == 200
        assert res_set.json()["quantity_on_hand"] == 42


@pytest.mark.asyncio
async def test_html_view_rendering():
    """Verify that Jinja2 server-rendered views return HTTP 200 and valid HTML markup."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Dashboard
        res_dash = await client.get("/")
        assert res_dash.status_code == 200
        assert "Workshop Parts & Bin Catalog" in res_dash.text

        # Parts catalog
        res_parts = await client.get("/parts")
        assert res_parts.status_code == 200
        assert "Fastener Parts Catalog" in res_parts.text

        # Bin detail
        res_bins = await client.get("/api/bins")
        first_bin_id = res_bins.json()[0]["id"]
        res_bin_view = await client.get(f"/b/{first_bin_id}")
        assert res_bin_view.status_code == 200
        assert "Current Stock Level" in res_bin_view.text
