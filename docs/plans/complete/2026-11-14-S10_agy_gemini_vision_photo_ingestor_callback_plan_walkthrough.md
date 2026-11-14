# Walkthrough: Plan S10 — AGY / Gemini Vision Callback Integration for Cartridge Photo Parts Ingestor (`/ingest`)

## 1. Summary of Changes
- **AGY Gemini Vision Callback ([`server/app/services/part_ingestor_service.py`](../../../server/app/services/part_ingestor_service.py))**:
  - Added `get_agy_bridge_config()` and `call_agy_vision_part_analyzer()` invoking `POST /api/vision/analyze-parts` on the Workstation Antigravity Bridge (`:8765`) with automatic fallback to local OpenCV (`analysis_source: "opencv_fallback"`).
- **Ruler Exclusion, Label Card Localization & Count-Aligned Overlay**:
  - Added `_detect_edge_ruler_mask()` + `ruler_bbox_pct` masking so edge rulers (such as the Westcott steel ruler in `IMG_6354.jpeg`) are never segmented as bolts.
  - Anchored `detect_and_read_label_cutout()` on blue/orange header bars and populated the green label overlay box with Gemini's resolved dimensions (`Label: M4 x 8 mm`).
  - Added `target_counts` alignment and single-screw separation radius in `segment_and_classify_fasteners()` so multi-screw clusters split cleanly to match Gemini Vision's count (`20` badges on `20` M4×8 SHCS screws).
- **UI Engine Badge ([`server/templates/ingest.html`](../../../server/templates/ingest.html))**:
  - Added `[🤖 AGY Gemini Vision]` / `[📷 Local CV]` status prefix in `#preview-status-badge`.

## 2. Test & Coverage Scorecard
- `Parts-Database`: **40 passed** (+3 new tests in `server/tests/test_part_ingestor.py`), **88% statement coverage**, **100% behavioral invariants verified**.
