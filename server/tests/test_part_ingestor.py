import io
import json
import os
import tempfile
import uuid
import pytest
import pytest_asyncio
import cv2
import httpx
import numpy as np
from httpx import AsyncClient, ASGITransport

from server.app.main import app
from server.app.database import init_db, configure_db_engine
from server.app.services.homebox_service import set_homebox_mock_transport


class FakeHomeboxApiServer:
    """In-memory mock of Homebox v0.27.1 official REST API (/api/v1/entities & /api/v1/entity-types)."""

    LOCATION_TYPE_ID = "loc-type-uuid-0001"
    ITEM_TYPE_ID = "item-type-uuid-0002"

    def __init__(self) -> None:
        self.entity_types = [
            {"id": self.LOCATION_TYPE_ID, "name": "Location", "isLocation": True},
            {"id": self.ITEM_TYPE_ID, "name": "Item", "isLocation": False},
        ]
        self.locations = [
            {
                "id": "7768d1a1-823c-4634-8e75-e8e09ec0025a",
                "name": "Garage",
                "description": "Workshop & Garage",
                "parentId": None,
                "entityTypeId": self.LOCATION_TYPE_ID,
                "updatedAt": "2026-11-11T00:00:00Z",
            }
        ]
        self.tags = []
        self.items = []
        self.attachments = []
        self._next_asset_id = 1

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        method = request.method.upper()

        if path == "/api/v1/users/login" and method == "POST":
            body = json.loads(request.content.decode("utf-8"))
            if body.get("username") and body.get("password"):
                return httpx.Response(
                    200,
                    json={"token": "Bearer test-jwt-token-123", "expiresAt": "2099-01-01T00:00:00Z"},
                )
            return httpx.Response(401, json={"error": "Invalid credentials"})

        if path == "/api/v1/entity-types" and method == "GET":
            return httpx.Response(200, json=self.entity_types)

        if path == "/api/v1/entity-types" and method == "POST":
            body = json.loads(request.content.decode("utf-8"))
            new_et = {
                "id": str(uuid.uuid4()),
                "name": body.get("name", ""),
                "isLocation": bool(body.get("isLocation", False)),
            }
            self.entity_types.append(new_et)
            return httpx.Response(201, json=new_et)

        if path == "/api/v1/entities" and method == "GET":
            is_loc = request.url.params.get("isLocation", "").lower()
            if is_loc == "true":
                return httpx.Response(
                    200,
                    json={"items": self.locations, "total": len(self.locations), "page": 1, "pageSize": 500},
                )
            return httpx.Response(
                200,
                json={"items": self.items, "total": len(self.items), "page": 1, "pageSize": 500},
            )

        if path == "/api/v1/entities" and method == "POST":
            body = json.loads(request.content.decode("utf-8"))
            et_id = body.get("entityTypeId")
            is_loc_entity = et_id == self.LOCATION_TYPE_ID or any(
                et["id"] == et_id and et.get("isLocation") for et in self.entity_types
            )
            parent_id = body.get("parentId") or body.get("locationId")
            if is_loc_entity:
                new_loc = {
                    "id": str(uuid.uuid4()),
                    "name": body.get("name", ""),
                    "description": body.get("description", ""),
                    "parentId": parent_id,
                    "entityTypeId": et_id,
                    "updatedAt": "2026-11-11T12:00:00Z",
                }
                self.locations.append(new_loc)
                return httpx.Response(201, json=new_loc)
            else:
                loc_obj = next((l for l in self.locations if l["id"] == parent_id), {"id": parent_id, "name": ""})
                new_item = {
                    "id": str(uuid.uuid4()),
                    "assetId": self._next_asset_id,
                    "name": body.get("name", ""),
                    "description": body.get("description", ""),
                    "quantity": body.get("quantity", 1),
                    "parentId": parent_id,
                    "parent": loc_obj,
                    "locationId": parent_id,
                    "location": loc_obj,
                    "entityTypeId": et_id or self.ITEM_TYPE_ID,
                    "tagIds": body.get("tagIds", []),
                    "fields": body.get("fields", []),
                    "notes": body.get("notes", ""),
                    "serialNumber": body.get("serialNumber", ""),
                    "modelNumber": body.get("modelNumber", ""),
                    "manufacturer": body.get("manufacturer", ""),
                }
                self._next_asset_id += 1
                self.items.append(new_item)
                return httpx.Response(201, json=new_item)

        if path.startswith("/api/v1/entities/") and path.endswith("/attachments") and method == "POST":
            item_id = path.split("/")[4]
            att = {"id": str(uuid.uuid4()), "itemId": item_id}
            self.attachments.append(att)
            return httpx.Response(201, json=att)

        if path.startswith("/api/v1/entities/") and method in ("GET", "PUT"):
            item_id = path.split("/")[4]
            existing = next((it for it in self.items if it["id"] == item_id), None)
            if not existing:
                existing = next((loc for loc in self.locations if loc["id"] == item_id), None)
            if not existing:
                return httpx.Response(404, json={"error": "Not found"})
            if method == "GET":
                return httpx.Response(200, json=existing)
            body = json.loads(request.content.decode("utf-8"))
            existing.update(body)
            parent_id = existing.get("parentId") or existing.get("locationId")
            loc_obj = next((l for l in self.locations if l["id"] == parent_id), {"id": parent_id, "name": ""})
            existing["parent"] = loc_obj
            existing["locationId"] = parent_id
            existing["location"] = loc_obj
            return httpx.Response(200, json=existing)

        if path == "/api/v1/tags" and method == "GET":
            return httpx.Response(200, json=self.tags)

        if path == "/api/v1/tags" and method == "POST":
            body = json.loads(request.content.decode("utf-8"))
            new_tag = {
                "id": str(uuid.uuid4()),
                "name": body.get("name", ""),
                "description": body.get("description", ""),
                "color": body.get("color", "#0284c7"),
            }
            self.tags.append(new_tag)
            return httpx.Response(201, json=new_tag)

        return httpx.Response(404, json={"error": f"Unhandled mock endpoint {method} {path}"})


def _generate_synthetic_cartridge_photo(include_label: bool = True, black_count: int = 8, silver_count: int = 12) -> bytes:
    """Generate a synthetic wood-background cartridge photo with an optional M4x6 label, black SHCS, and silver BHCS."""
    # Warm tan wood background (BGR: ~155, 190, 210)
    img = np.full((800, 1000, 3), (155, 190, 210), dtype=np.uint8)

    if include_label:
        # Draw white label card (x=150..320, y=550..650) with blue metric header bar
        cv2.rectangle(img, (150, 550), (320, 650), (250, 250, 250), -1)
        cv2.rectangle(img, (155, 555), (315, 580), (204, 119, 0), -1)  # BGR for #0077CC
        cv2.putText(img, "M4 x 6", (165, 612), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (15, 15, 15), 2, cv2.LINE_AA)
        cv2.putText(img, "Pitch 0.7", (165, 638), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 50, 50), 1, cv2.LINE_AA)

    # Draw black oxide SHCS bolts on the left (tall cylindrical head + shank)
    for idx in range(black_count):
        row = idx // 3
        col = idx % 3
        cx = 140 + col * 85
        cy = 150 + row * 95
        # Cylindrical socket head (nearly square/tall block) + threaded shank
        cv2.rectangle(img, (cx - 18, cy - 16), (cx + 18, cy + 8), (22, 22, 24), -1)
        cv2.rectangle(img, (cx - 11, cy + 8), (cx + 11, cy + 32), (30, 30, 34), -1)

    # Draw silver stainless BHCS bolts on the right (wider low-profile dome head + bright metallic highlights)
    for idx in range(silver_count):
        row = idx // 4
        col = idx % 4
        cx = 520 + col * 105
        cy = 140 + row * 95
        # Domed wide button head (ellipse) + bright silver shank
        cv2.ellipse(img, (cx, cy - 4), (24, 11), 0, 0, 360, (225, 228, 232), -1)
        cv2.circle(img, (cx - 6, cy - 6), 5, (252, 252, 255), -1)  # Specular reflection
        cv2.rectangle(img, (cx - 10, cy + 6), (cx + 10, cy + 30), (200, 205, 210), -1)

    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


@pytest_asyncio.fixture(autouse=True)
async def setup_test_env(monkeypatch):
    """Configure isolated ephemeral Parts-Database and mock Homebox REST API v1."""
    temp_dir = tempfile.mkdtemp()
    parts_db_path = os.path.join(temp_dir, "test_parts.db")
    auth_file_path = os.path.join(temp_dir, "homebox_auth.json")

    fake_hb = FakeHomeboxApiServer()
    mock_transport = httpx.MockTransport(fake_hb.handle_request)
    set_homebox_mock_transport(mock_transport)
    monkeypatch.setenv("HOMEBOX_AUTH_FILE", auth_file_path)
    monkeypatch.setenv("QR_FORWARDING_FILE", os.path.join(temp_dir, "qr_forwarding.json"))
    monkeypatch.setenv("HOMEBOX_API_TOKEN", "test-jwt-token-123")

    engine, _ = configure_db_engine(f"sqlite+aiosqlite:///{parts_db_path}")
    await init_db()
    yield {
        "temp_dir": temp_dir,
        "fake_homebox": fake_hb,
    }
    set_homebox_mock_transport(None)
    await engine.dispose()


@pytest.mark.asyncio
async def test_detect_and_read_label_cutout_m4x6_example(monkeypatch):
    """Verify label cutout OCR and Black/Silver splitting on synthetic image and Temp/IMG_6334.jpeg if present."""
    import base64
    from server.app.services.part_ingestor_service import analyze_cartridge_photo

    syn_bytes = _generate_synthetic_cartridge_photo(include_label=True, black_count=6, silver_count=10)
    res = analyze_cartridge_photo(syn_bytes)
    assert res["label_detected"] is True
    assert res["detected_specs"]["size"] == "M4"
    assert "6" in res["detected_specs"]["length"]
    assert "0.7" in (res["detected_specs"].get("pitch") or "")
    assert len(res["groups"]) >= 2

    # Also test against real example photo in Temp/IMG_6334.jpeg if available on workstation
    # Force built-in OpenCV OCR (no external tesseract binary, matching tasker-pi environment)
    real_example_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "Temp", "IMG_6334.jpeg")
    )
    if os.path.exists(real_example_path):
        monkeypatch.setattr("shutil.which", lambda _: None)
        with open(real_example_path, "rb") as f:
            real_bytes = f.read()
        real_res = analyze_cartridge_photo(real_bytes)
        preview_out = os.path.join(os.path.dirname(real_example_path), "improved_output_preview.jpeg")
        b64_str = real_res["annotated_image_base64"].split(",", 1)[-1]
        with open(preview_out, "wb") as out_f:
            out_f.write(base64.b64decode(b64_str))

        assert real_res["label_detected"] is True
        assert real_res["detected_specs"]["size"] == "M4"
        assert "6" in real_res["detected_specs"]["length"]
        assert "0.7" in (real_res["detected_specs"].get("pitch") or "")
        finishes = {g["finish_key"]: g for g in real_res["groups"]}
        assert "black" in finishes
        assert "silver" in finishes
        assert 17 <= finishes["black"]["count"] <= 25
        assert 50 <= finishes["silver"]["count"] <= 75


@pytest.mark.asyncio
async def test_color_clustering_and_head_classification_black_vs_silver():
    """Verify Black vs Silver grouping, piece counting, and SHCS vs BHCS head classification."""
    from server.app.services.part_ingestor_service import analyze_cartridge_photo

    syn_bytes = _generate_synthetic_cartridge_photo(include_label=True, black_count=7, silver_count=9)
    res = analyze_cartridge_photo(syn_bytes)

    groups_by_finish = {g["finish_key"]: g for g in res["groups"]}
    assert "black" in groups_by_finish
    assert "silver" in groups_by_finish

    black_grp = groups_by_finish["black"]
    silver_grp = groups_by_finish["silver"]

    assert 5 <= black_grp["count"] <= 9
    assert 7 <= silver_grp["count"] <= 11
    assert black_grp["head"] in ("shcs", "socket")
    assert silver_grp["head"] in ("bhcs", "button", "pan")
    assert res.get("annotated_image_base64", "").startswith("data:image/jpeg;base64,")


@pytest.mark.asyncio
async def test_dynamic_scale_small_m2_and_large_m6_fasteners():
    """Verify dynamic solidity + scale calibration counts both tiny M2 screws (with touching pairs) and large M6 bolts."""
    from server.app.services.part_ingestor_service import analyze_cartridge_photo

    # 1. Tiny M2 x 4 screws (~135 px each), including 5 isolated + 2 touching pairs = 9 total screws
    img_small = np.full((800, 1000, 3), (155, 190, 210), dtype=np.uint8)
    for i in range(5):
        cx, cy = 150 + i * 55, 200
        cv2.rectangle(img_small, (cx - 6, cy - 6), (cx + 6, cy + 2), (22, 22, 24), -1)
        cv2.rectangle(img_small, (cx - 4, cy + 2), (cx + 4, cy + 12), (26, 26, 28), -1)
    # Draw 2 touching pairs (4 more screws touching at a corner/neck)
    for p in range(2):
        cx, cy = 160 + p * 90, 310
        cv2.rectangle(img_small, (cx - 6, cy - 6), (cx + 6, cy + 2), (22, 22, 24), -1)
        cv2.rectangle(img_small, (cx - 4, cy + 2), (cx + 4, cy + 12), (26, 26, 28), -1)
        cv2.rectangle(img_small, (cx + 4, cy + 6), (cx + 16, cy + 14), (22, 22, 24), -1)
        cv2.rectangle(img_small, (cx + 6, cy + 14), (cx + 14, cy + 24), (26, 26, 28), -1)
    _, buf_small = cv2.imencode(".jpg", img_small)
    res_small = analyze_cartridge_photo(buf_small.tobytes())
    black_small = next(g for g in res_small["groups"] if g["finish_key"] == "black")
    assert 8 <= black_small["count"] <= 10

    # 2. Large M6 x 20 bolts (~2,200 px each): 5 isolated large bolts should count as 5 (not chopped into 15)
    img_large = np.full((800, 1000, 3), (155, 190, 210), dtype=np.uint8)
    for i in range(5):
        cx, cy = 150 + i * 140, 350
        cv2.rectangle(img_large, (cx - 24, cy - 30), (cx + 24, cy - 4), (22, 22, 24), -1)
        cv2.rectangle(img_large, (cx - 14, cy - 4), (cx + 14, cy + 52), (28, 28, 32), -1)
    _, buf_large = cv2.imencode(".jpg", img_large)
    res_large = analyze_cartridge_photo(buf_large.tobytes())
    black_large = next(g for g in res_large["groups"] if g["finish_key"] == "black")
    assert black_large["count"] == 5


@pytest.mark.asyncio
async def test_missing_label_generates_clarification_questions_and_ruler_estimation():
    """Verify unlabeled photos trigger clarification questions and support ruler mm-per-pixel estimation."""
    from server.app.services.part_ingestor_service import analyze_cartridge_photo

    unlabeled_bytes = _generate_synthetic_cartridge_photo(include_label=False, black_count=5, silver_count=0)
    # Suppose 40 pixels = 10 mm -> 4.0 px/mm
    res = analyze_cartridge_photo(unlabeled_bytes, ruler_mm_per_px=0.25)

    assert res["label_detected"] is False
    assert res["needs_clarification"] is True
    assert len(res["questions"]) >= 2
    q_fields = {q["field"] for q in res["questions"]}
    assert "size" in q_fields
    assert "length" in q_fields
    assert res["ruler_calibrated"] is True
    assert res["detected_specs"].get("estimated_length_mm") is not None


@pytest.mark.asyncio
async def test_sequential_bin_allocation_and_homebox_commit_dual_items(setup_test_env):
    """Verify sequential bin numbering (BIN-001 -> BIN-002) and separate Black/Silver items in Homebox."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Check initial next bin is BIN-001
        next_res = await client.get("/api/ingest/next-bin")
        assert next_res.status_code == 200
        assert next_res.json()["next_bin_id"] == "BIN-001"

        # 2. Commit a 2-group cartridge (Black SHCS + Silver BHCS in BIN-001)
        payload = {
            "bin_id": "BIN-001",
            "cartridge_label": "M4 × 6",
            "mode": "photo",
            "groups": [
                {
                    "name": "M4 × 6 mm Socket Head Cap Screw (Black Oxide)",
                    "size": "M4",
                    "length": "6 mm",
                    "pitch": "0.7 mm",
                    "head": "shcs",
                    "drive": "hex",
                    "comp_type": "bolt",
                    "finish": "Black Oxide Steel",
                    "finish_key": "black",
                    "quantity": 21,
                    "tool_key": "3.0 mm",
                    "tap_drill": "3.30 mm (#30)",
                    "clearance_drill": "4.5 mm (#16)",
                    "notes": "Black screws kept separately in BIN-001",
                },
                {
                    "name": "M4 × 6 mm Button Head Cap Screw (Stainless Steel)",
                    "size": "M4",
                    "length": "6 mm",
                    "pitch": "0.7 mm",
                    "head": "bhcs",
                    "drive": "hex",
                    "comp_type": "bolt",
                    "finish": "Stainless Steel (Silver)",
                    "finish_key": "silver",
                    "quantity": 65,
                    "tool_key": "2.5 mm",
                    "tap_drill": "3.30 mm (#30)",
                    "clearance_drill": "4.5 mm (#16)",
                    "notes": "Silver screws kept separately in BIN-001",
                },
            ],
        }
        commit_res = await client.post("/api/ingest/commit", json=payload)
        assert commit_res.status_code == 200
        commit_data = commit_res.json()
        assert commit_data["status"] == "success"
        assert commit_data["bin_id"] == "BIN-001"
        assert len(commit_data["created_items"]) == 2
        assert commit_data["next_bin_id"] == "BIN-002"

        # 3. Verify next-bin endpoint now returns BIN-002
        next_res2 = await client.get("/api/ingest/next-bin")
        assert next_res2.json()["next_bin_id"] == "BIN-002"

        # 4. Verify Homebox REST API state directly (Barn > Tool Chest A > Gridfinity Cartridges > BIN-001)
        fake_hb = setup_test_env["fake_homebox"]
        barn_loc = next(l for l in fake_hb.locations if l["name"] == "Barn")
        chest_loc = next(l for l in fake_hb.locations if l["name"] == "Tool Chest A")
        cart_loc = next(l for l in fake_hb.locations if l["name"] == "Gridfinity Cartridges")
        assert chest_loc["parentId"] == barn_loc["id"]
        assert cart_loc["parentId"] == chest_loc["id"]

        bin_locs = [l for l in fake_hb.locations if l["name"].startswith("BIN-001")]
        assert len(bin_locs) == 1
        assert bin_locs[0]["parentId"] == cart_loc["id"]

        items = sorted(
            [it for it in fake_hb.items if it["locationId"] == bin_locs[0]["id"]],
            key=lambda x: x["quantity"],
        )
        assert len(items) == 2
        assert items[0]["quantity"] == 21
        assert "Black" in items[0]["name"]
        assert any(f["name"] == "Temporary Bin" and f["textValue"] == "BIN-001" for f in items[0]["fields"])
        assert items[1]["quantity"] == 65
        assert "Stainless" in items[1]["name"] or "Silver" in items[1]["name"]


@pytest.mark.asyncio
async def test_manual_form_entry_mode_commit():
    """Verify user-choice manual Form Entry mode creates sequential bin and items in Homebox."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        form_payload = {
            "mode": "form",
            "cartridge_label": "M3 × 10",
            "groups": [
                {
                    "size": "M3",
                    "length": "10 mm",
                    "pitch": "0.5 mm",
                    "head": "shcs",
                    "drive": "hex",
                    "comp_type": "bolt",
                    "finish": "Black Oxide Steel",
                    "finish_key": "black",
                    "quantity": 40,
                }
            ],
        }
        res = await client.post("/api/ingest/commit", json=form_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["bin_id"] == "BIN-001"
        assert len(data["created_items"]) == 1

        hist_res = await client.get("/api/ingest/history")
        assert hist_res.status_code == 200
        bins = hist_res.json()["bins"]
        assert len(bins) == 1
        assert bins[0]["bin_code"] == "BIN-001"
        assert bins[0]["total_pieces"] == 40


@pytest.mark.asyncio
async def test_ingest_view_renders_html():
    """Verify GET /ingest renders the Photo + Form Entry web UI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/ingest")
        assert res.status_code == 200
        assert "Parts Ingestor" in res.text
        assert "Photo" in res.text
        assert "Form" in res.text
        assert "BIN-001" in res.text
