# Walkthrough: Plan S07 — Homebox Cartridge Photo & Form Parts Ingestor, Split-Label Generator & QR Redirector

**Date**: 2026-11-12
**Status**: Complete & User-Validated (`ARCHIVED`)

---

## 1. Summary of Changes

1. **Homebox v0.27.1 REST API Integration ([`server/app/services/homebox_service.py`](../../../server/app/services/homebox_service.py))**:
   - Migrated all Homebox location and item queries/mutations to Homebox v0.26+/v0.27.1's unified `/api/v1/entities` and `/api/v1/entity-types` endpoints (`isLocation: true/false`).
   - Configured the default parent location hierarchy to **`Barn > Tool Chest A > Gridfinity Cartridges`** (`_get_or_create_cartridges_root_api()`), automatically reparenting any existing `Gridfinity Cartridges` container under `Tool Chest A`.
   - Fixed Homebox web UI redirect links to use singular Nuxt routes (`/location/<uuid>` and `/item/<uuid>`) and added `_normalize_homebox_web_url()` to upgrade legacy plural entries automatically.
2. **Hybrid Vision & Fastener Ingestor ([`server/app/services/part_ingestor_service.py`](../../../server/app/services/part_ingestor_service.py) & [`server/templates/ingest.html`](../../../server/templates/ingest.html))**:
   - Implemented label card detection & Tesseract OCR (`detect_and_read_label_cutout`), ruler scale calibration (`mm_per_px`), watershed fastener segmentation & finish clustering (`Black Oxide` vs. `Stainless Steel / Silver` vs. `Brass`), bolt head classification (`SHCS`, `BHCS`, `FHCS`, `Hex`), and annotated visual overlays.
   - Added sticky visual active state (`✓ ` checkmark, emerald highlight, `aria-pressed="true"`, and `✓ Applied` pill) for interactive Clarification Question buttons and resilient `parseApiJson(res)` response handling.
3. **12x35mm Vertical Split-Label Pair & 4-Digit QR Forwarding Editor ([`hardware/labels/exporter/canonical_label.py`](../../../hardware/labels/exporter/canonical_label.py) & [`server/templates/label_batch_export.html`](../../../server/templates/label_batch_export.html))**:
   - Implemented zero-bleed $12 \times 35\text{ mm}$ vertical split-label pairs (`[Label A | Label B]` = $24 \times 35\text{ mm}$) with low-density QR codes pointing to `HTTP://TASKER-PI.LOCAL:8090/0001`.
   - Added `GET /api/qr-forwarding`, `POST /api/qr-forwarding`, and `DELETE /api/qr-forwarding/{bin_code}` endpoints and the **🔗 4-Digit QR Forwarding Links (`/0001` → Target URL)** editor table on `/labels`, preserving custom overrides across Homebox background syncs (`preserve_existing=True`).
4. **Deployment Safety ([`deploy.sh`](../../../deploy.sh))**:
   - Excluded `server/data/homebox_auth.json` and `server/data/qr_forwarding.json` from `rsync --delete` so deployments never overwrite live Homebox credentials or custom QR forwarding mappings on Node 02 (`tasker-pi.local`).

---

## 2. Verification & Coverage Scorecard

- **Automated Hermetic Tests**:
  - Ran `./run_tests.sh` in `Parts-Database/`: **`37 passed in 5.87s` (100% pass rate, +8 new tests)**.
- **Live Hardware & Production Validation on Node 02 (`tasker-pi.local:8090`)**:
  - Deployed to `tasker-pi.local` via `./deploy.sh`.
  - User validated committing parts to Homebox (`:7745`) and confirmed `http://tasker-pi.local:8090/0001` redirects cleanly to the Homebox location page.

| Metric | Baseline (Pre-S07) | Final (Post-S07) | Delta |
| :--- | :---: | :---: | :---: |
| **Parts-Database Test Count** | 29 | **37** | **+8** |
| **Pass Rate** | 100% | **100%** | **0%** |
| **Workspace Total Tests** | 1,228 | **1,236** | **+8** |
