# Walkthrough — Plan S05: Standardized Batch Label Sheet Generator & Cricut Print-Then-Cut Exporter

**Plan ID**: `S05`  
**Target Subsystem**: `Parts-Database` (Deployed on Node 02 `tasker-pi.local:8090`)  
**Status**: `COMPLETED & ARCHIVED`  
**Validation Date**: `2026-09-08`  

---

## 1. Overview & Objectives Achieved

Plan S05 implemented a unified, production-ready **Batch Label Sheet Generator and Multi-Medium Exporter** for `Parts-Database`:
1. **Canonical Label Specification (`hardware/labels/canonical_label.py`)**:
   - Standard $34.0 \times 10.0\text{ mm}$ finished cut label geometry ($R = 1.0\text{ mm}$) with $+1.0\text{ mm}$ full bleed artwork envelope ($36.0 \times 12.0\text{ mm}$, $R = 2.0\text{ mm}$).
   - Color-coded taxonomy accent bar matching physical Gridfinity filament colors (Metric Blue, Imperial Orange, Washers Green, Specialty Yellow, Inserts Gold).
   - Crisp, enlarged screw head and drive socket silhouette icons spanning $8.2\text{ mm}$ of vertical label height.
   - Vector QR code matrix generator with 1-module optical quiet zone (`border=1`) encoding actionable web catalog URLs (`http://tasker-pi.local:8090/p/{part_id}`) for instant smartphone scanning.
   - Triple-layer keepout protection (dynamic proportional font scaling, SVG `textLength` compression, and per-label SVG `<clipPath>` isolation) guaranteeing zero collision between text and graphics.
2. **Multi-Medium Layout Exporters**:
   - **✂️ Cricut Print-Then-Cut (`hardware/labels/cricut_exporter.py`)**: 60-up Letter sheets with optical registration sensor marks, bleed print layer, and red `#FF0000` basic cut paths.
   - **📄 Avery 5160 / 8160 (`hardware/labels/avery_templates.py`)**: 30-up Letter sheets (3 columns $\times$ 10 rows, $1" \times 2\text{-}5/8"$).
   - **📄 Avery 5167 / 8167 (`hardware/labels/avery_templates.py`)**: 80-up Letter sheets (4 columns $\times$ 20 rows, $1/2" \times 1\text{-}3/4"$).
   - **📜 Continuous Thermal Roll (`hardware/labels/thermal_exporter.py`)**: Continuous stream for Brother QL / Dymo tape printers.
3. **REST API Batch Endpoints (`server/app/routes/api.py`)**:
   - `POST /api/labels/export-batch` and `GET /api/labels/export-batch` returning on-demand SVG attachments.
4. **Interactive Web Catalog UI (`server/templates/label_batch_export.html`)**:
   - Dedicated `/labels` view with category filtering, search, select/deselect all, format selector, modal live SVG preview, and 1-click batch download.
   - Navigation link added to `server/templates/base.html`.

---

## 2. Changes & File Modifications

| Component | File | Description |
| :--- | :--- | :--- |
| **Core Spec** | [`hardware/labels/canonical_label.py`](../../../hardware/labels/canonical_label.py) | Canonical `LabelData`, `render_canonical_label_svg`, `generate_qr_svg_path`, keepout text renderer. |
| **Cricut Exporter** | [`hardware/labels/cricut_exporter.py`](../../../hardware/labels/cricut_exporter.py) | Cricut Print-Then-Cut multi-up sheet generator with registration bounding box and cut paths. |
| **Avery Exporter** | [`hardware/labels/avery_templates.py`](../../../hardware/labels/avery_templates.py) | Avery 5160 (30-up) and 5167 (80-up) grid composers. |
| **Thermal Exporter** | [`hardware/labels/thermal_exporter.py`](../../../hardware/labels/thermal_exporter.py) | Continuous vertical thermal tape stream exporter. |
| **Service Layer** | [`server/app/services/label_service.py`](../../../server/app/services/label_service.py) | Database mapping (`PartRecord` $\to$ `LabelData`) and format dispatch. |
| **API Routes** | [`server/app/routes/api.py`](../../../server/app/routes/api.py) | Added `POST /api/labels/export-batch` & `GET /api/labels/export-batch`. |
| **View Routes** | [`server/app/routes/views.py`](../../../server/app/routes/views.py) | Added `GET /labels` route rendering batch exporter view. |
| **Web UI** | [`server/templates/label_batch_export.html`](../../../server/templates/label_batch_export.html) | Interactive Tailwind web interface with live preview modal. |
| **Base Nav** | [`server/templates/base.html`](../../../server/templates/base.html) | Added `🏷️ Labels` navigation link. |
| **Standalone Script**| [`hardware/labels/generate_labels.py`](../../../hardware/labels/generate_labels.py) | Unified standalone CLI generator with canonical keepout renderer. |
| **Documentation** | [`hardware/labels/README.md`](../../../hardware/labels/README.md) | Multi-medium fabrication and Cricut workflow documentation. |
| **Test Suite** | [`server/tests/test_batch_label_generator.py`](../../../server/tests/test_batch_label_generator.py) | 9 automated hermetic unit tests covering QR codes, Avery grids, Cricut layers, keepout clipping, and API routes. |

---

## 3. Test & Coverage Scorecard

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: Parts-Database/server
collected 22 items

server/tests/test_backup_pipeline.py ....                                [ 18%]
server/tests/test_batch_label_generator.py .........                     [ 59%]
server/tests/test_compartments_and_routes.py .....                       [ 81%]
server/tests/test_server_api.py ....                                     [100%]

============================== 22 passed in 1.62s ==============================
```

### Coverage Ratchet Verification
- **Parts-Database Tests**: $13 \to 22$ passed (**+9 new tests**).
- **Statement Coverage**: $86\% \to 87\%$ (**+1.0% increase**).
- **Domain Invariants**: $4/4$ verified ($100.0\%$).
- **Workspace Master Total**: **790 tests passed across all 6 test suites (100% pass rate)**.
- **Coverage Ratchet**: PASSED (Zero regressions, improved coverage).

---

## 4. Production Deployment & Verification

- **Deployed Target**: Node 02 (`tasker-pi.local:8090`) via `./deploy.sh`.
- **Systemd Unit**: `parts-database.service` restarted and active.
- **Interactive Verification**:
  - Web UI tested at `http://tasker-pi.local:8090/labels`.
  - Smartphone optical QR code scanning validated (instant Safari prompt to `http://tasker-pi.local:8090/p/{part_id}`).
  - Live SVG modal preview and batch SVG export confirmed.
