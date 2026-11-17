# Walkthrough: Plan S11 — Nut & Dual-Diameter Washer Support in Cartridge Parts Ingestor (`/ingest` & `/labels`)

## 1. Summary of Changes
1. **Nut & Dual-Diameter Washer Vision & Ingestor Pipeline** ([`server/app/services/part_ingestor_service.py`](../../../server/app/services/part_ingestor_service.py), [`server/templates/ingest.html`](../../../server/templates/ingest.html)):
   - Added `NUT_HEAD_TYPES` (`nut`, `nyloc`, `flange_nut`, `square_nut`, `wing_nut`, `tnut`, `tnut_pre`, `tnut_post`), `WASHER_HEAD_TYPES` (`washer`, `fender_washer`, `split_washer`), and `NUT_WRENCH_FLATS_MAP` (`M2.5: 5.0 mm`, `M3: 5.5 mm`, `M4: 7.0 mm`, `M5: 8.0 mm`, `M6: 10.0 mm`, etc.).
   - Updated `parse_label_ocr_text()`, `build_clarification_questions()`, and `analyze_cartridge_photo()` so nuts preserve `length = ""` without a bogus `"6 mm"` fallback, and washers support both single-diameter (`M2.5 Washer`) and dual-diameter ID × OD (`M4 × 9 mm Flat Washer`) specifications.
   - Updated `/ingest` Part Variant Cards to dynamically adapt field labels for **Washers** (`Size / Inner Dia (ID)` + `Outer Dia (OD)`), **Nuts** (`Thread Size` + `Wrench / Socket`), and **Bolts/Screws** (`Thread Size` + `Length`).
2. **Standardized `"WASHER"` + OD Vertical Split Labels & Multi-Washer Bin Aggregation** ([`hardware/labels/canonical_label.py`](../../../hardware/labels/canonical_label.py), [`server/app/services/homebox_service.py`](../../../server/app/services/homebox_service.py)):
   - Updated `render_vertical_split_label_pair_svg()` to render `"WASHER"` in bold (`1.92 mm` with glyph-aware `_estimate_svg_text_width` keepout scaling) below the green header bar on every washer label, and list all known ODs (`"5mm"`, `"9mm"`, `"20mm"`, etc.) underneath.
   - Updated `_extract_cartridge_specs_from_homebox_bin()` to aggregate all known washer ODs across multi-washer bins in ascending order (`BIN-052`: `5mm`; `BIN-053`: `9mm, 20mm`; `BIN-054`: `12mm`; `BIN-055`: `7mm, 15mm`; `BIN-056`: `20mm, 25mm, 30mm`).
   - Repurposed duplicate `BIN-043` into `BIN-043 (M3 × 12)` containing `30× M3 × 12 mm Button Head Cap Screw (Stainless Steel (Silver))` (`printed=False`).
3. **Loopback API & Single-Pass `/labels` Performance Optimization** ([`server/app/services/homebox_service.py`](../../../server/app/services/homebox_service.py), [`server/app/routes/views.py`](../../../server/app/routes/views.py)):
   - Routed local Homebox REST API calls over `http://127.0.0.1:7745/api/v1`, reduced Homebox API round-trips in `list_ingested_bins()` from 4 to 2, batch-read `qr_forwarding.json` once per request, and wrapped `list_ingested_bins` in `asyncio.to_thread`.

---

## 2. Verification & Coverage Scorecard

- **Automated Tests**: `./Parts-Database/run_tests.sh` — **`44/44` passed (`100%` pass rate)**.
- **Coverage Scorecard**:
  - Statement Coverage: **`88%`** (Baseline: `88%`, Delta: `0.0%`)
  - Branch Coverage: **`82%`** (Baseline: `82%`, Delta: `0.0%`)
  - Behavioral Invariants Verified: **`100%`**
- **Live Validation**: Verified on `http://tasker-pi.local:8090/ingest` and `http://tasker-pi.local:8090/labels` (`HTTP 200 OK` in `0.45s`).
