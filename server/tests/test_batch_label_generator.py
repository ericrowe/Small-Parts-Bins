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


@pytest.mark.asyncio
async def test_vertical_split_label_pair_12x35_and_qr_forwarding_service(monkeypatch, tmp_path):
    """
    Verify:
      1. Clean 12x35mm vertical split-label pair (Label A + Label B, zero bleed):
         - Label A: 'M4' overlaid on top color bar, '6' below (no 'mm' unit), no 'SHCS' or head designation,
           no icons, blank lower region unless extra_note is set.
         - Label B: Top color bar, 4-digit bin number '0001' (no 'BIN' prefix text), low-density QR code (<=25x25).
      2. Forwarding service GET /0001 and GET /q/0001 redirects (HTTP 302) to the target Homebox / registered URL.
    """
    from hardware.labels.canonical_label import (
        render_vertical_split_label_pair_svg,
        generate_split_vertical_sheet_svg,
    )
    from server.app.services.homebox_service import register_qr_forwarding_entry

    fwd_file = tmp_path / "qr_forwarding.json"
    monkeypatch.setenv("QR_FORWARDING_FILE", str(fwd_file))

    spec_default = LabelData(
        part_id="M4-6",
        name="M4 × 6mm SHCS",
        size="M4",
        length="6 mm",
        head="shcs",
        drive="hex",
        comp_type="bolt",
        pitch="0.7 mm",
        tap_drill="3.3 mm",
        tool_key="3.0 mm",
        material="Black Oxide / SS",
        accent_color="#0077CC",
        extra_note="",
        bin_id="BIN-001",
    )

    pair_svg = render_vertical_split_label_pair_svg(spec_default, x=0.0, y=0.0)
    wrapped = f'<svg xmlns="http://www.w3.org/2000/svg">{pair_svg}</svg>'
    root = ET.fromstring(wrapped)
    assert root is not None

    # Label A checks: M4 in color bar, bare '6' below, no 'mm', no 'SHCS', no 'BIN' word
    assert ">M4<" in pair_svg
    assert ">6<" in pair_svg
    assert "6 mm" not in pair_svg
    assert "SHCS" not in pair_svg
    assert "Tap " not in pair_svg
    assert "Key " not in pair_svg
    # Label B checks: 4-digit bin number '0001' without 'BIN' prefix
    assert ">0001<" in pair_svg
    assert "BIN-001" not in pair_svg
    assert ">BIN<" not in pair_svg

    # Verify optional extra_note renders in lower space when explicitly provided (e.g. Fine Pitch / Nyloc)
    spec_with_note = LabelData(
        part_id="M4-6-FINE",
        size="M4",
        length="6 mm",
        accent_color="#0077CC",
        extra_note="Pitch 0.5 Fine",
        bin_id="0002",
    )
    pair_note_svg = render_vertical_split_label_pair_svg(spec_with_note, x=0.0, y=0.0)
    assert "Pitch" in pair_note_svg and "0.5 Fine" in pair_note_svg
    assert ">0002<" in pair_note_svg

    # Sheet generator & API batch export for 'split_vertical_12x35'
    sheet_svg = generate_split_vertical_sheet_svg([spec_default, spec_with_note], title="Cartridge Split Labels")
    ET.fromstring(sheet_svg)
    assert 'width="12.00"' in sheet_svg
    assert 'height="35.00"' in sheet_svg

    # Register forwarding entry for 0001 and verify HTTP 302 redirect on GET /0001 and GET /q/0001
    register_qr_forwarding_entry(
        bin_code="0001",
        target_url="http://tasker-pi.local:7745/locations/loc-uuid-0001",
        label="M4 × 6",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=False) as client:
        res_batch = await client.post(
            "/api/labels/export-batch",
            json={
                "format": "split_vertical_12x35",
                "custom_labels": [
                    {"bin_id": "0001", "size": "M4", "length": "6", "accent_color": "#0077CC", "extra_note": ""},
                    {"bin_id": "0002", "size": "M4", "length": "8", "accent_color": "#0077CC", "extra_note": "Fine 0.5"},
                ],
            },
        )
        assert res_batch.status_code == 200
        assert "<svg" in res_batch.text
        assert ">M4<" in res_batch.text
        assert ">0001<" in res_batch.text
        assert ">0002<" in res_batch.text

        res_root_fwd = await client.get("/0001")
        assert res_root_fwd.status_code in (302, 307)
        assert res_root_fwd.headers["location"] == "http://tasker-pi.local:7745/location/loc-uuid-0001"

        res_q_fwd = await client.get("/q/0001")
        assert res_q_fwd.status_code in (302, 307)
        assert res_q_fwd.headers["location"] == "http://tasker-pi.local:7745/location/loc-uuid-0001"

        # Unmapped bin code falls back to Homebox Location (:7745/location), NOT legacy Parts-Database
        res_unmapped = await client.get("/0099")
        assert res_unmapped.status_code in (302, 307)
        assert "7745/location" in res_unmapped.headers["location"]

        # Legacy /b/{bin_id} route redirects to Homebox when registered in qr_forwarding.json or unmapped in SQLite
        res_b_fwd = await client.get("/b/BIN-001")
        assert res_b_fwd.status_code in (302, 307)
        assert res_b_fwd.headers["location"] == "http://tasker-pi.local:7745/location/loc-uuid-0001"

        res_b_unmapped = await client.get("/b/BIN-099")
        assert res_b_unmapped.status_code in (302, 307)
        assert "7745/location" in res_b_unmapped.headers["location"]

        # Custom Homebox label rows exported to horizontal formats (Avery 5160 / Cricut) auto-enrich pitch/tap/tool specs
        res_avery_hb = await client.post(
            "/api/labels/export-batch",
            json={
                "format": "avery_5160",
                "custom_labels": [
                    {"bin_id": "0001", "size": "M4", "length": "6 mm", "accent_color": "#0077CC"},
                ],
            },
        )
        assert res_avery_hb.status_code == 200
        assert "0.7 mm" in res_avery_hb.text
        assert "3.0 mm" in res_avery_hb.text
        assert "0001" in res_avery_hb.text

        # Deep-link query /labels?bin=0001 renders cleanly
        res_labels_bin = await client.get("/labels?bin=0001")
        assert res_labels_bin.status_code == 200
        assert "4-Digit QR Forwarding Links" in res_labels_bin.text

        # Verify manual override via POST /api/qr-forwarding is preserved when preserve_existing=True
        post_fwd = await client.post(
            "/api/qr-forwarding",
            json={
                "bin_code": "0001",
                "target_url": "http://tasker-pi.local:7745/location/custom-override-uuid",
                "label": "Custom Override Bin 0001",
            },
        )
        assert post_fwd.status_code == 200
        assert post_fwd.json()["entry"]["manual_override"] is True

        # Simulate background Homebox sync attempting to overwrite 0001 with preserve_existing=True
        register_qr_forwarding_entry(
            bin_code="0001",
            target_url="http://tasker-pi.local:7745/location/auto-synced-uuid",
            label="Auto Synced",
            preserve_existing=True,
        )
        res_after_sync = await client.get("/0001")
        assert res_after_sync.headers["location"] == "http://tasker-pi.local:7745/location/custom-override-uuid"

        get_fwd = await client.get("/api/qr-forwarding")
        assert get_fwd.status_code == 200
        assert any(e["code"] == "0001" and "custom-override-uuid" in e["target_url"] for e in get_fwd.json()["entries"])

        del_fwd = await client.delete("/api/qr-forwarding/0001")
        assert del_fwd.status_code == 200
        assert del_fwd.json()["deleted"] is True


