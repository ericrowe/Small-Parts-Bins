import os
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from server.app.models import CategoryRecord, PartRecord, StorageLocationRecord, CarrierRecord, BinRecord, BinCompartmentRecord

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
    """Ingest taxonomy, parts, and numbered 1/2/3-compartment physical bins into SQLite ledger."""
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

        # 2. Ingest Storage Location & Carriers
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

        all_created_part_ids = []

        # 3. Ingest Metric Fastener Parts
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
                all_created_part_ids.append(part_id)

        # 4. Ingest Imperial Fastener Parts
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
                all_created_part_ids.append(part_id)

        # 5. Ingest Heat-Set Inserts
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
            all_created_part_ids.append(part_id)

        # 6. Instantiate Numbered Physical Bins (BIN-001 through BIN-024)
        # Mix of 1-compartment (single), 2-compartment (divided_2), and 3-compartment (divided_3)
        part_ptr = 0
        total_parts = len(all_created_part_ids)

        for bin_num in range(1, 25):
            bin_id = f"BIN-{bin_num:03d}"
            carrier_id = "CARRIER-TRAY-L01" if bin_num <= 12 else "CARRIER-TRAY-U01"
            slot_idx = ((bin_num - 1) % 12) + 1

            # Determine cassette compartment count (1, 2, or 3)
            if bin_num % 3 == 1:
                comp_count = 1
                cassette_type = "single"
                label_title = f"Bin #{bin_num:03d} (Single 40x80)"
            elif bin_num % 3 == 2:
                comp_count = 2
                cassette_type = "divided_2"
                label_title = f"Bin #{bin_num:03d} (2-Way Divided)"
            else:
                comp_count = 3
                cassette_type = "divided_3"
                label_title = f"Bin #{bin_num:03d} (3-Way Divided)"

            bin_record = BinRecord(
                id=bin_id,
                carrier_id=carrier_id,
                slot_index=slot_idx,
                compartment_count=comp_count,
                cassette_type=cassette_type,
                label_title=label_title,
                qr_code_payload=f"https://parts.local/b/{bin_id}",
                updated_at=datetime.now(timezone.utc),
            )
            session.add(bin_record)

            # Create 1, 2, or 3 compartments for this physical bin
            for c_idx in range(1, comp_count + 1):
                assigned_part = all_created_part_ids[part_ptr % total_parts] if total_parts > 0 else None
                part_ptr += 1

                comp_id = f"{bin_id}-C{c_idx}"
                comp_record = BinCompartmentRecord(
                    id=comp_id,
                    bin_id=bin_id,
                    compartment_index=c_idx,
                    part_id=assigned_part,
                    quantity_on_hand=50 if comp_count == 1 else (30 if comp_count == 2 else 20),
                    reorder_threshold=15,
                    notes=f"Compartment {c_idx} of {comp_count}",
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(comp_record)

        await session.commit()
        logger.info(f"Database seeded with {len(all_created_part_ids)} parts and 24 physical bins (1, 2, and 3 compartments).")
