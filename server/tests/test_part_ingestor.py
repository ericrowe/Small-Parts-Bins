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
    """Verify GET /ingest renders the Photo + Form Entry web UI both when empty and when populated with bins."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_empty = await client.get("/ingest")
        assert res_empty.status_code == 200
        assert "BIN-001" in res_empty.text

        # Commit a populated bin so ingested_bins is non-empty when rendering ingest.html
        commit_res = await client.post(
            "/api/ingest/commit",
            json={
                "mode": "form",
                "cartridge_label": "M4 × 6",
                "groups": [
                    {
                        "name": "M4 × 6 mm Socket Head Cap Screw",
                        "size": "M4",
                        "length": "6 mm",
                        "pitch": "0.7 mm",
                        "head": "shcs",
                        "drive": "hex",
                        "comp_type": "bolt",
                        "finish": "Black Oxide Steel",
                        "finish_key": "black",
                        "quantity": 25,
                    }
                ],
            },
        )
        assert commit_res.status_code == 200

        res = await client.get("/ingest")
        assert res.status_code == 200
        assert "Parts Ingestor" in res.text
        assert "BIN-001" in res.text
        assert "25 pcs" in res.text
        assert "BIN-002" in res.text
        # Plan S09: Verify #photo-file-input has accept="image/*" and NO capture= attribute so iPhone shows native Take/Choose sheet
        assert 'id="photo-file-input" type="file" accept="image/*"' in res.text
        assert 'capture="environment"' not in res.text


@pytest.mark.asyncio
async def test_analyze_cartridge_photo_uses_agy_gemini_vision_callback(monkeypatch):
    """Plan S10: Verify analyze_cartridge_photo() invokes guarded AGY Gemini Vision endpoint when configured."""
    from server.app.services.part_ingestor_service import analyze_cartridge_photo

    monkeypatch.setenv("AGY_BRIDGE_URL", "http://127.0.0.1:18765")
    monkeypatch.setenv("AGY_BRIDGE_API_KEY", "test-agy-vision-key")

    captured_req = {}

    def fake_post(url, **kwargs):
        captured_req["url"] = url
        captured_req["headers"] = kwargs.get("headers", {})
        captured_req["json"] = kwargs.get("json", {})
        return httpx.Response(
            200,
            json={
                "status": "success",
                "analysis": {
                    "label_detected": True,
                    "label_ocr_text": "M3 x 8 FHCS + Brass Inserts",
                    "detected_specs": {"size": "M3", "length": "8 mm", "pitch": "0.5 mm"},
                    "groups": [
                        {
                            "finish_key": "black",
                            "finish": "Black Oxide Steel",
                            "comp_type": "bolt",
                            "head": "fhcs",
                            "drive": "hex",
                            "size": "M3",
                            "length": "8 mm",
                            "count": 15,
                            "notes": "Black countersunk flat head screws",
                        },
                        {
                            "finish_key": "brass",
                            "finish": "Brass",
                            "comp_type": "insert",
                            "head": "insert",
                            "drive": "none",
                            "size": "M3",
                            "length": "4 mm",
                            "count": 22,
                            "notes": "Brass knurled heat-set inserts",
                        },
                    ],
                    "questions": [],
                },
            },
        )

    monkeypatch.setattr("httpx.post", fake_post)
    syn_bytes = _generate_synthetic_cartridge_photo(include_label=False, black_count=4, silver_count=0)
    res = analyze_cartridge_photo(syn_bytes, user_hints={"size": "M3"})

    assert captured_req["url"] == "http://127.0.0.1:18765/api/vision/analyze-parts"
    assert captured_req["headers"].get("Authorization") == "Bearer test-agy-vision-key"
    assert res["analysis_source"] == "agy_gemini_vision"
    assert res["label_detected"] is True
    assert res["detected_specs"]["size"] == "M3"
    assert len(res["groups"]) == 2
    assert res["groups"][0]["head"] == "fhcs"
    assert res["groups"][0]["quantity"] == 15
    assert "2.0 mm" in res["groups"][0]["tool_key"]
    assert res["groups"][1]["head"] == "insert"
    assert res["groups"][1]["finish"] == "Brass"
    assert res["groups"][1]["quantity"] == 22


@pytest.mark.asyncio
async def test_analyze_cartridge_photo_falls_back_to_opencv_when_agy_bridge_offline(monkeypatch):
    """Plan S10: Verify analyze_cartridge_photo() falls back to local OpenCV when AGY bridge is unreachable."""
    from server.app.services.part_ingestor_service import analyze_cartridge_photo

    monkeypatch.setenv("AGY_BRIDGE_URL", "http://127.0.0.1:19999")
    monkeypatch.setenv("AGY_BRIDGE_API_KEY", "test-agy-vision-key")

    def fake_offline_post(url, **kwargs):
        raise httpx.ConnectError("Workstation bridge offline")

    monkeypatch.setattr("httpx.post", fake_offline_post)
    syn_bytes = _generate_synthetic_cartridge_photo(include_label=True, black_count=6, silver_count=8)
    res = analyze_cartridge_photo(syn_bytes)

    assert res["analysis_source"] == "opencv_fallback"
    assert res["label_detected"] is True
    assert res["detected_specs"]["size"] == "M4"


@pytest.mark.asyncio
async def test_ruler_exclusion_and_vision_bbox_overlay_on_img_6354(monkeypatch):
    """Plan S10: Verify edge steel ruler is never flagged as bolts and overlay matches Gemini Vision count on IMG_6354.jpeg."""
    import base64
    from server.app.services.part_ingestor_service import analyze_cartridge_photo

    img_6354_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "Temp", "IMG_6354.jpeg")
    )
    if not os.path.exists(img_6354_path):
        return

    monkeypatch.setenv("AGY_BRIDGE_URL", "http://127.0.0.1:18765")
    monkeypatch.setenv("AGY_BRIDGE_API_KEY", "test-agy-vision-key")

    def fake_gemini_6354(url, **kwargs):
        return httpx.Response(
            200,
            json={
                "status": "success",
                "analysis": {
                    "label_detected": True,
                    "label_ocr_text": "M4 x 8 Pitch 0.7",
                    "detected_specs": {"size": "M4", "length": "8 mm", "pitch": "0.7 mm"},
                    "groups": [
                        {
                            "finish_key": "black",
                            "finish": "Black Oxide Steel",
                            "comp_type": "bolt",
                            "head": "shcs",
                            "drive": "hex",
                            "size": "M4",
                            "length": "8 mm",
                            "count": 20,
                            "notes": "20 M4x8 black oxide socket head cap screws",
                        }
                    ],
                    "questions": [],
                },
            },
        )

    monkeypatch.setattr("httpx.post", fake_gemini_6354)
    with open(img_6354_path, "rb") as f:
        raw_bytes = f.read()

    res = analyze_cartridge_photo(raw_bytes)
    preview_out = os.path.join(os.path.dirname(img_6354_path), "img_6354_preview.jpeg")
    b64_str = res["annotated_image_base64"].split(",", 1)[-1]
    with open(preview_out, "wb") as out_f:
        out_f.write(base64.b64decode(b64_str))

    assert res["analysis_source"] == "agy_gemini_vision"
    assert res["detected_specs"]["size"] == "M4"
    assert res["detected_specs"]["length"] == "8 mm"
    assert len(res["groups"]) == 1
    assert res["groups"][0]["count"] == 20


@pytest.mark.asyncio
async def test_analyze_cartridge_photo_nuts_and_dual_diameter_washers(monkeypatch):
    """Plan S11: Verify nut ingestion (blank length, external wrench size, no length question) and IDxOD washer ingestion."""
    from server.app.services.part_ingestor_service import analyze_cartridge_photo, parse_label_ocr_text

    # 1. Verify standalone nut label OCR (no 'x <length>') and dual-diameter washer OCR
    parsed_nut = parse_label_ocr_text("M2.5\nPitch 0.45")
    assert parsed_nut["size"] == "M2.5"
    assert parsed_nut["length"] is None
    assert parsed_nut["pitch"] == "0.45 mm"

    parsed_washer = parse_label_ocr_text("M4 x 9 Washer")
    assert parsed_washer["size"] == "M4"
    assert parsed_washer["length"] == "9 mm"

    monkeypatch.setenv("AGY_BRIDGE_URL", "http://127.0.0.1:18765")
    monkeypatch.setenv("AGY_BRIDGE_API_KEY", "test-agy-vision-key")

    # 2. Verify Gemini Vision callback for Hex Nuts & Nyloc Nuts
    def fake_nut_post(url, **kwargs):
        return httpx.Response(
            200,
            json={
                "status": "success",
                "analysis": {
                    "label_detected": False,
                    "label_ocr_text": "",
                    "detected_specs": {"size": "M2.5", "length": "", "pitch": "0.45 mm"},
                    "groups": [
                        {
                            "finish_key": "silver",
                            "finish": "Stainless Steel",
                            "comp_type": "nut",
                            "head": "nut",
                            "drive": "hex",
                            "size": "M2.5",
                            "length": "",
                            "count": 25,
                            "notes": "M2.5 stainless hex nuts",
                        }
                    ],
                    "questions": [],
                },
            },
        )

    monkeypatch.setattr("httpx.post", fake_nut_post)
    syn_bytes = _generate_synthetic_cartridge_photo(include_label=False, black_count=0, silver_count=6)
    nut_res = analyze_cartridge_photo(syn_bytes)

    assert nut_res["detected_specs"]["size"] == "M2.5"
    assert nut_res["detected_specs"]["length"] == ""
    assert nut_res["cartridge_label"] == "M2.5 Nut"
    assert nut_res["groups"][0]["head"] == "nut"
    assert nut_res["groups"][0]["comp_type"] == "nut"
    assert nut_res["groups"][0]["finish_key"] == "silver"
    assert nut_res["groups"][0]["finish"] == "Stainless Steel (Silver)"
    assert nut_res["groups"][0]["length"] == ""
    assert nut_res["groups"][0]["tool_key"] == "5.0 mm"
    assert nut_res["groups"][0]["name"] == "M2.5 Hex Nut (Stainless Steel (Silver))"
    assert "Screw" not in nut_res["groups"][0]["name"]
    # Must NOT ask a bolt thread length question for nuts
    q_fields = [q["field"] for q in nut_res["questions"]]
    assert "length" not in q_fields

    # 2b. Verify Pre-Insert and Post-Insert T-Nuts with Nickel Plated finish
    def fake_tnut_post(url, **kwargs):
        return httpx.Response(
            200,
            json={
                "status": "success",
                "analysis": {
                    "label_detected": True,
                    "label_ocr_text": "M3 T-Nut",
                    "detected_specs": {"size": "M3", "length": "", "pitch": "0.5 mm"},
                    "groups": [
                        {
                            "finish_key": "nickel",
                            "finish": "Nickel Plated",
                            "comp_type": "nut",
                            "head": "tnut_post",
                            "drive": "hex",
                            "size": "M3",
                            "length": "",
                            "count": 40,
                            "notes": "M3 post-insert hammer T-nuts",
                        },
                        {
                            "finish_key": "zinc",
                            "finish": "Zinc Plated",
                            "comp_type": "nut",
                            "head": "tnut_pre",
                            "drive": "hex",
                            "size": "M3",
                            "length": "",
                            "count": 20,
                            "notes": "M3 pre-insert slide-in T-nuts",
                        },
                    ],
                    "questions": [],
                },
            },
        )

    monkeypatch.setattr("httpx.post", fake_tnut_post)
    tnut_res = analyze_cartridge_photo(syn_bytes)
    assert tnut_res["cartridge_label"] == "M3 Post-Insert T-Nut"
    assert tnut_res["groups"][0]["head"] == "tnut_post"
    assert tnut_res["groups"][0]["finish"] == "Nickel Plated (Silver)"
    assert tnut_res["groups"][0]["name"] == "M3 Post-Insert T-Nut (Nickel Plated (Silver))"
    assert tnut_res["groups"][1]["head"] == "tnut_pre"
    assert tnut_res["groups"][1]["finish"] == "Zinc Plated (Silver)"
    assert tnut_res["groups"][1]["name"] == "M3 Pre-Insert T-Nut (Zinc Plated (Silver))"

    # 3. Verify Dual-Diameter Washers (Size/ID x Outer Diameter OD)
    def fake_washer_post(url, **kwargs):
        return httpx.Response(
            200,
            json={
                "status": "success",
                "analysis": {
                    "label_detected": True,
                    "label_ocr_text": "M4 x 9",
                    "detected_specs": {"size": "M4", "length": "9 mm", "pitch": ""},
                    "groups": [
                        {
                            "finish_key": "silver",
                            "finish": "Stainless Steel (Silver)",
                            "comp_type": "washer",
                            "head": "fender_washer",
                            "drive": "none",
                            "size": "M4",
                            "length": "9 mm",
                            "count": 32,
                            "notes": "M4 x 9mm OD stainless fender washers",
                        }
                    ],
                    "questions": [],
                },
            },
        )

    monkeypatch.setattr("httpx.post", fake_washer_post)
    washer_res = analyze_cartridge_photo(syn_bytes)
    assert washer_res["detected_specs"]["size"] == "M4"
    assert washer_res["detected_specs"]["length"] == "9 mm"
    assert washer_res["cartridge_label"] == "M4 × 9 Washer"
    assert washer_res["groups"][0]["head"] == "fender_washer"
    assert washer_res["groups"][0]["comp_type"] == "washer"
    assert washer_res["groups"][0]["length"] == "9 mm"
    assert washer_res["groups"][0]["name"] == "M4 × 9 mm Fender Washer (Stainless Steel (Silver))"


@pytest.mark.asyncio
async def test_img_6399_multi_screw_cluster_patch_mask_shape_regression(monkeypatch):
    """Plan S12: Reproduce & verify fix for boolean mask shape mismatch when a multi-screw cluster falls back to comp_mask."""
    from server.app.services.part_ingestor_service import analyze_cartridge_photo, classify_bolt_head_type

    # 1. Direct unit test of classify_bolt_head_type with mismatched mask vs crop dimensions (165x140 vs 22x22)
    mismatched_mask = np.ones((165, 140), dtype=np.uint8) * 255
    small_crop = np.full((22, 22, 3), 30, dtype=np.uint8)
    head = classify_bolt_head_type(mismatched_mask, small_crop, "black")
    assert head in ("shcs", "bhcs", "fhcs")

    # 2. End-to-end test on Temp/IMG_6399.jpeg with Gemini Vision returning 18 M2.5x16 black SHCS screws
    img_6399_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "Temp", "IMG_6399.jpeg")
    )
    if not os.path.exists(img_6399_path):
        return

    monkeypatch.setenv("AGY_BRIDGE_URL", "http://127.0.0.1:18765")
    monkeypatch.setenv("AGY_BRIDGE_API_KEY", "test-agy-vision-key")

    def fake_gemini_6399(url, **kwargs):
        return httpx.Response(
            200,
            json={
                "status": "success",
                "analysis": {
                    "label_detected": True,
                    "label_ocr_text": "M2.5 x 16 Pitch 0.45",
                    "label_bbox_pct": [72.0, 31.0, 10.0, 43.0],
                    "detected_specs": {"size": "M2.5", "length": "16 mm", "pitch": "0.45 mm"},
                    "groups": [
                        {
                            "finish_key": "black",
                            "finish": "Black Oxide Steel",
                            "comp_type": "bolt",
                            "head": "shcs",
                            "drive": "hex",
                            "size": "M2.5",
                            "length": "16 mm",
                            "count": 18,
                            "notes": "18 M2.5x16 black oxide socket head cap screws",
                        }
                    ],
                    "questions": [],
                },
            },
        )

    monkeypatch.setattr("httpx.post", fake_gemini_6399)
    with open(img_6399_path, "rb") as f:
        raw_bytes = f.read()

    res = analyze_cartridge_photo(raw_bytes)
    assert res["analysis_source"] == "agy_gemini_vision"
    assert res["detected_specs"]["size"] == "M2.5"
    assert res["detected_specs"]["length"] == "16 mm"
    assert res["groups"][0]["count"] == 18


def test_list_ingested_bins_single_pass_efficiency_and_loopback_api(monkeypatch, tmp_path):
    """
    Verify list_ingested_bins() performs at most 2 HTTP requests (locations + items)
    by computing cartridges_root_id and next_bin_id directly from the fetched locations list,
    and batch-updates qr_forwarding.json in a single pass.
    """
    from server.app.services.homebox_service import (
        list_ingested_bins,
        set_homebox_mock_transport,
    )

    fwd_file = tmp_path / "qr_forwarding.json"
    monkeypatch.setenv("QR_FORWARDING_FILE", str(fwd_file))
    monkeypatch.setenv("HOMEBOX_API_TOKEN", "test-token")

    request_log = []

    def handler(request: httpx.Request) -> httpx.Response:
        request_log.append((request.method, request.url.path, str(request.url.query)))
        if request.url.path == "/api/v1/entities" and "isLocation=true" in str(request.url.query):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {"id": "loc-root", "name": "Gridfinity Cartridges", "description": "Root"},
                        {"id": "loc-001", "name": "BIN-001 (M4 × 6)", "description": "Bin 1", "parentId": "loc-root"},
                        {"id": "loc-002", "name": "BIN-002 (M4 × 9 Washer)", "description": "Bin 2", "parentId": "loc-root"},
                    ]
                },
            )
        if request.url.path == "/api/v1/entities" and "isLocation=false" in str(request.url.query):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {"id": "item-1", "name": "M4 × 6 mm Socket Head Cap Screw (Black Oxide Steel)", "quantity": 20, "parentId": "loc-001"},
                        {"id": "item-2", "name": "M4 × 9 mm Flat Washer (Black Oxide Steel)", "quantity": 25, "parentId": "loc-002"},
                        {"id": "item-3", "name": "M4 × 20 mm Fender Washer (Stainless Steel)", "quantity": 10, "parentId": "loc-002"},
                    ]
                },
            )
        return httpx.Response(404, json={"error": "unexpected call"})

    set_homebox_mock_transport(httpx.MockTransport(handler))
    try:
        res = list_ingested_bins(limit=50)
        assert res["authenticated"] is True
        assert res["total_bins"] == 2
        assert res["next_bin_id"] == "BIN-003"
        assert res["homebox_locations_url"].endswith("/location/loc-root")
        # Must make ONLY 2 HTTP requests (locations + items), not 4!
        assert len(request_log) == 2
    finally:
        set_homebox_mock_transport(None)



