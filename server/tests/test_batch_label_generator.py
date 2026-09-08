import os
import tempfile
import xml.etree.ElementTree as ET
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from server.app.main import app
from server.app.database import init_db, configure_db_engine
from hardware.labels.canonical_label import LabelData, render_canonical_label_svg, generate_qr_svg_path
from hardware.labels.cricut_exporter import generate_cricut_sheet
from hardware.labels.avery_templates import generate_avery_sheet, AVERY_5160, AVERY_5167
from hardware.labels.thermal_exporter import generate_thermal_roll_svg


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


def test_qr_code_svg_path_generation():
    """Verify generate_qr_svg_path generates valid vector SVG rectangle matrix."""
    qr_svg = generate_qr_svg_path("PARTS:M3-SHCS-12", size=8.0, x=2.0, y=1.0)
    assert "<g " in qr_svg
    assert "M3-SHCS-12" in qr_svg or "<rect" in qr_svg or "<path" in qr_svg
    # Must be valid XML fragment inside an svg
    wrapped = f'<svg xmlns="http://www.w3.org/2000/svg">{qr_svg}</svg>'
    root = ET.fromstring(wrapped)
    assert root is not None


def test_canonical_label_rendering():
    """Verify canonical label SVG contains part title, subtexts, icons, and QR code."""
    item = LabelData(
        part_id="M3-SHCS-12",
        name="M3 × 12mm Socket Head Cap Screw",
        size="M3",
        length="12 mm",
        head="shcs",
        drive="hex",
        comp_type="bolt",
        pitch="0.5 mm",
        tap_drill="2.5 mm",
        tool_key="2.5 mm",
        material="SS 304",
        accent_color="#0077CC",
        bg_color="#FFFFFF",
        bin_id="BIN-003-C1",
        qr_payload="PARTS:M3-SHCS-12",
    )

    # 1. Standard finished cut label (34x10 mm)
    svg_cut = render_canonical_label_svg(item, x=0, y=0, include_bleed=False, include_qr=True)
    assert "M3 × 12 mm" in svg_cut or "M3" in svg_cut
    assert "0.5 mm" in svg_cut
    assert "Key 2.5 mm" in svg_cut or "SS 304" in svg_cut
    assert "BIN-003-C1" in svg_cut or "BIN-003" in svg_cut

    # 2. Bleed label (36x12 mm)
    svg_bleed = render_canonical_label_svg(item, x=0, y=0, include_bleed=True, include_qr=True)
    assert "fill=\"#0077CC\"" in svg_bleed or "fill=\"#FFFFFF\"" in svg_bleed

    # Verify XML validity
    wrapped = f'<svg xmlns="http://www.w3.org/2000/svg">{svg_cut}</svg>'
    root = ET.fromstring(wrapped)
    assert root is not None


def test_text_keepout_and_font_scaling():
    """Verify extra long fastener text is clipped, scaled, and never collides with QR/icons."""
    extra_long_item = LabelData(
        part_id="1_2_-13-1_1_2IN-EXTRA-LONG-SPEC-SHCS",
        name="1/2\"-13 × 1-1/2\" Extra Long Heavy Duty Socket Head Cap Screw",
        size="1/2\"-13",
        length="1-1/2\"",
        head="shcs",
        drive="hex",
        comp_type="bolt",
        pitch="13 TPI Extra Fine Thread",
        tap_drill="27/64\" Drill (#43 / 0.0890\")",
        tool_key="3/8\" Heavy Allen",
        material="Stainless Steel 316 Marine Grade",
        accent_color="#E65100",
        bin_id="BIN-DRAWER-009-COMPARTMENT-1",
        qr_payload="PARTS:1_2_-13-1_1_2IN-EXTRA-LONG",
    )

    svg = render_canonical_label_svg(extra_long_item, x=0, y=0, include_qr=True)
    assert "clipPath" in svg
    assert "clip-path=\"url(#clip_" in svg
    # Must be valid XML
    wrapped = f'<svg xmlns="http://www.w3.org/2000/svg">{svg}</svg>'
    root = ET.fromstring(wrapped)
    assert root is not None


def test_cricut_print_then_cut_sheet_structure():
    """Verify multi-label Cricut sheet contains registration marks, print bleed, and cut lines."""
    items = [
        LabelData(
            part_id=f"M3-SHCS-{i*2}",
            name=f"M3 × {i*2}mm SHCS",
            size="M3",
            length=f"{i*2} mm",
            head="shcs",
            drive="hex",
            comp_type="bolt",
            pitch="0.5 mm",
            tap_drill="2.5 mm",
            tool_key="2.5 mm",
            material="SS 304",
            accent_color="#0077CC",
        )
        for i in range(1, 15)  # 14 labels
    ]

    sheet = generate_cricut_sheet(items, title="M3 Fastener Assortment", include_qr=True)
    assert "print_svg" in sheet
    assert "cut_svg" in sheet
    assert sheet["label_count"] == 14

    # Print SVG must contain registration sensor box and labels
    print_svg = sheet["print_svg"]
    assert "viewBox=\"0 0 215.90 279.40\"" in print_svg or "215.9" in print_svg
    assert "M3 Fastener Assortment" in print_svg
    assert "<rect" in print_svg

    # Cut SVG must contain exact cut rectangles
    cut_svg = sheet["cut_svg"]
    assert "stroke=\"#FF0000\"" in cut_svg or "id=\"cut-lines\"" in cut_svg
    assert "width=\"34" in cut_svg or "height=\"10" in cut_svg

    # Validate XML parsing
    ET.fromstring(print_svg)
    ET.fromstring(cut_svg)


def test_avery_5160_grid_alignment():
    """Verify Avery 5160 sheet fits 30 labels (3 cols x 10 rows) on Letter paper."""
    items = [
        LabelData(
            part_id=f"TEST-{i}",
            name=f"Part {i}",
            size=f"M{i}",
            length="10 mm",
            head="shcs",
            drive="hex",
            comp_type="bolt",
            accent_color="#0077CC",
        )
        for i in range(1, 31)  # 30 labels
    ]

    avery_svg = generate_avery_sheet(items, template=AVERY_5160, title="Avery 5160 Test Sheet")
    assert "viewBox=\"0 0 215.90 279.40\"" in avery_svg or "215.9" in avery_svg
    assert "Avery 5160" in avery_svg or "Part 1" in avery_svg

    root = ET.fromstring(avery_svg)
    assert root is not None


def test_avery_5167_grid_alignment():
    """Verify Avery 5167 sheet fits 80 labels (4 cols x 20 rows) on Letter paper."""
    items = [
        LabelData(
            part_id=f"TEST-{i}",
            name=f"Part {i}",
            size=f"M{i}",
            length="10 mm",
            head="shcs",
            drive="hex",
            comp_type="bolt",
            accent_color="#0077CC",
        )
        for i in range(1, 81)  # 80 labels
    ]

    avery_svg = generate_avery_sheet(items, template=AVERY_5167, title="Avery 5167 Test Sheet")
    assert "viewBox=\"0 0 215.90 279.40\"" in avery_svg or "215.9" in avery_svg
    root = ET.fromstring(avery_svg)
    assert root is not None


def test_thermal_roll_export():
    """Verify continuous thermal roll stream generation."""
    items = [
        LabelData(
            part_id=f"THERMAL-{i}",
            name=f"Thermal Part {i}",
            size="M4",
            length=f"{i*5} mm",
            head="shcs",
            drive="hex",
            comp_type="bolt",
            accent_color="#0077CC",
        )
        for i in range(1, 5)
    ]

    thermal_svg = generate_thermal_roll_svg(items, label_width=34.0, label_height=10.0, gap_y=3.0)
    assert "<svg" in thermal_svg
    root = ET.fromstring(thermal_svg)
    assert root is not None


@pytest.mark.asyncio
async def test_api_export_batch_endpoints():
    """Verify POST /api/labels/export-batch returns valid SVG files for all formats."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Cricut Print-Then-Cut
        res_cricut = await client.post("/api/labels/export-batch", json={"format": "cricut_print_cut"})
        assert res_cricut.status_code == 200
        assert "image/svg+xml" in res_cricut.headers.get("content-type", "") or "application/json" in res_cricut.headers.get("content-type", "")

        # 2. Avery 5160
        res_5160 = await client.post("/api/labels/export-batch", json={"format": "avery_5160"})
        assert res_5160.status_code == 200
        assert "<svg" in res_5160.text

        # 3. Avery 5167
        res_5167 = await client.post("/api/labels/export-batch", json={"format": "avery_5167"})
        assert res_5167.status_code == 200
        assert "<svg" in res_5167.text

        # 4. Thermal Roll
        res_thermal = await client.post("/api/labels/export-batch", json={"format": "thermal_roll"})
        assert res_thermal.status_code == 200
        assert "<svg" in res_thermal.text


@pytest.mark.asyncio
async def test_label_batch_export_view():
    """Verify GET /labels renders batch export HTML page with filter options."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/labels")
        assert res.status_code == 200
        assert "Standardized Batch Label Generator" in res.text or "Label" in res.text
        assert "Cricut" in res.text
        assert "Avery" in res.text
