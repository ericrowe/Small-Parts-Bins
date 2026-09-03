import os
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from server.app.models import CategoryRecord, PartRecord, StorageLocationRecord, CarrierRecord, BinRecord

logger = logging.getLogger(__name__)


def find_fasteners_json() -> str:
    """Locate hardware/labels/data/fasteners.json dynamically relative to server directory."""
    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(server_dir)
    primary = os.path.join(root_dir, "hardware", "labels", "data", "fasteners.json")
    if os.path.exists(primary):
        return primary
    alt = os.path.join(root_dir, "Labels", "data", "fasteners.json")
    if os.path.exists(alt):
        return alt
    return primary


async def seed_database_from_json():
    """Ingest taxonomy and hardware specifications from fasteners.json into SQLite ledger."""
    from server.app.database import AsyncSessionLocal

    json_path = find_fasteners_json()
    if not os.path.exists(json_path):
        logger.warning(f"Fasteners JSON definition not found at {json_path}. Skipping automatic seed.")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read fasteners JSON: {e}")
        return

    async with AsyncSessionLocal() as session:
        # Check if categories already exist
        res = await session.execute(select(CategoryRecord))
        if res.scalars().first() is not None:
            logger.debug("Database already seeded. Skipping taxonomy ingestion.")
            return

        logger.info("Seeding categories and hardware inventory from fasteners.json...")

        # 1. Ingest Categories
        categories_dict = data.get("categories", {})
        threads_dict = data.get("threads", {})

        for cat_id, cat_info in categories_dict.items():
            category = CategoryRecord(
                id=cat_id,
                name=cat_info.get("name", cat_id.title()),
                filament=cat_info.get("filament"),
                color_name=cat_info.get("color_name"),
                color_hex=cat_info.get("color_hex", "#0077CC"),
                color_bg=cat_info.get("color_bg", "#E6F3FA"),
                prefix=cat_info.get("prefix"),
            )
            session.add(category)

        # 2. Ingest Storage Location & Default Carriers
        loc = StorageLocationRecord(
            id="DRAWER-01",
            name="Modular Fastener Drawer 01 (Gridfinity 14U Stack)",
            location_type="GRIDFINITY_DRAWER",
            notes="Target drawer with measured 111.125 mm ceiling. Houses 3x4 7U stacked carrier trays.",
        )
        session.add(loc)

        carrier_lower = CarrierRecord(
            id="CARRIER-TRAY-L01",
            location_id="DRAWER-01",
            layout="3x4",
            height_u=7,
            position_row=1,
            position_col=1,
        )
        session.add(carrier_lower)

        carrier_upper = CarrierRecord(
            id="CARRIER-TRAY-U01",
            location_id="DRAWER-01",
            layout="3x4",
            height_u=7,
            position_row=1,
            position_col=1,
        )
        session.add(carrier_upper)

        # 3. Ingest Metric Threads
        slot_idx = 1
        metric_threads = threads_dict.get("metric", [])
        for thread in metric_threads:
            sz = thread.get("size", "")
            pitch = thread.get("pitch_coarse", "")
            tap_drill = thread.get("tap_drill", "")
            clearance_drill = thread.get("clearance_drill", "")
            hex_keys = thread.get("hex_key", {})
            tool_key = hex_keys.get("shcs", "") if isinstance(hex_keys, dict) else str(hex_keys)

            for l in ["8 mm", "12 mm", "16 mm", "20 mm"]:
                part_id = f"{sz}-{l.replace(' ', '')}-SHCS"
                part_name = f"{sz} × {l} Socket Head Cap Screw"
                
                part = PartRecord(
                    id=part_id,
                    name=part_name,
                    category_id="metric_coarse",
                    size=sz,
                    length=l,
                    head="socket",
                    drive="hex",
                    comp_type="bolt",
                    material="Stainless Steel (304 / A2)",
                    tool_key=tool_key,
                    tap_drill=tap_drill,
                    clearance_drill=clearance_drill,
                    pitch=f"{pitch} mm" if pitch else "Standard Coarse",
                    extra_note="DIN 912 / ISO 4762 Standard",
                )
                session.add(part)

                bin_id = f"BIN-{part_id}"
                bin_record = BinRecord(
                    id=bin_id,
                    part_id=part_id,
                    carrier_id="CARRIER-TRAY-L01" if slot_idx <= 6 else "CARRIER-TRAY-U01",
                    slot_index=slot_idx,
                    quantity_on_hand=50,
                    reorder_threshold=15,
                    cassette_type="40x80_standard",
                    qr_code_payload=f"https://parts.local/b/{bin_id}",
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(bin_record)
                slot_idx += 1

        # 4. Ingest Imperial Threads
        imperial_threads = threads_dict.get("imperial", [])
        for thread in imperial_threads:
            sz = thread.get("size", "")
            tpi = thread.get("tpi_coarse", "")
            tap_drill = thread.get("tap_drill", "")
            clearance_drill = thread.get("clearance_drill", "")
            hex_keys = thread.get("hex_key", {})
            tool_key = hex_keys.get("shcs", "") if isinstance(hex_keys, dict) else str(hex_keys)

            for l in ["1/4\"", "1/2\"", "3/4\"", "1\""]:
                clean_sz = sz.replace("#", "NO_").replace("/", "_")
                clean_l = l.replace("\"", "IN").replace("/", "_")
                part_id = f"{clean_sz}-{clean_l}-SHCS"
                part_name = f"{sz} × {l} Socket Head Cap Screw"

                part = PartRecord(
                    id=part_id,
                    name=part_name,
                    category_id="imperial_unc",
                    size=sz,
                    length=l,
                    head="socket",
                    drive="hex",
                    comp_type="bolt",
                    material="Black Oxide Steel",
                    tool_key=tool_key,
                    tap_drill=tap_drill,
                    clearance_drill=clearance_drill,
                    pitch=f"{tpi} TPI" if tpi else "UNC Coarse",
                    extra_note="ASME B18.3 Standard",
                )
                session.add(part)

                bin_id = f"BIN-{part_id}"
                bin_record = BinRecord(
                    id=bin_id,
                    part_id=part_id,
                    carrier_id="CARRIER-TRAY-U01",
                    slot_index=slot_idx,
                    quantity_on_hand=40,
                    reorder_threshold=10,
                    cassette_type="40x80_standard",
                    qr_code_payload=f"https://parts.local/b/{bin_id}",
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(bin_record)
                slot_idx += 1

        # 5. Ingest Sample Heat-Set Inserts
        for sz, depth, hole in [("M2", "4.0 mm", "3.2 mm"), ("M2.5", "5.0 mm", "3.6 mm"), ("M3", "4.0 mm (Short)", "4.0 mm"), ("M3", "5.7 mm (Standard)", "4.0 mm"), ("M4", "8.0 mm", "5.6 mm"), ("M5", "9.5 mm", "7.1 mm")]:
            clean_sz = sz.replace(" ", "")
            clean_dp = depth.split()[0].replace(".", "_")
            part_id = f"INSERT-{clean_sz}-{clean_dp}"
            part_name = f"{sz} Brass Heat-Set Insert ({depth})"
            
            part = PartRecord(
                id=part_id,
                name=part_name,
                category_id="heat_set_inserts",
                size=sz,
                length=depth,
                head="insert",
                drive="none",
                comp_type="insert",
                material="Brass",
                tool_key="Soldering Iron Tip",
                tap_drill=f"Hole: {hole}",
                clearance_drill=None,
                pitch=None,
                extra_note=f"Recommended Hole Ø: {hole}",
            )
            session.add(part)

            bin_id = f"BIN-{part_id}"
            bin_record = BinRecord(
                id=bin_id,
                part_id=part_id,
                carrier_id="CARRIER-TRAY-U01",
                slot_index=slot_idx,
                quantity_on_hand=100,
                reorder_threshold=25,
                cassette_type="40x80_divided",
                qr_code_payload=f"https://parts.local/b/{bin_id}",
                updated_at=datetime.now(timezone.utc),
            )
            session.add(bin_record)
            slot_idx += 1

        await session.commit()
        logger.info(f"Database successfully seeded with {slot_idx - 1} fastener parts and bins.")
