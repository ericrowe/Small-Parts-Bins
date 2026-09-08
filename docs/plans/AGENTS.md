# Instructions for `Parts-Database/docs/plans`

## 1. Directory Structure Conventions
- **`docs/plans/`**: Active plans currently in planning or execution for Parts-Database.
- **`docs/plans/complete/`**: Archived completed plans and walkthroughs (`YYYY-MM-DD-<plan_name>.md`).
- **`docs/plans/IDEAS.md`**: Asynchronous idea and bug backlog for Parts-Database.

---

## 2. Multi-Prefix Plan Lifecycle Standard

To cleanly manage both physical workshop fabrication and software engineering, `Parts-Database` uses a standardized 3-prefix hierarchy:

1. **`MNN_<name>_plan.md` (Master / Cross-Subsystem Plans)**:
   - Covers end-to-end integration across hardware, labels, web catalog, and server infrastructure (e.g. End-to-end QR code generation $\leftrightarrow$ camera scanning $\leftrightarrow$ SQLite database resolution).
2. **`HNN_<name>_plan.md` (Hardware Subsystem Plans)**:
   - Governs 3D CAD models, Gridfinity carriers, slide cassettes, divider cards, Cricut cut templates, and physical tolerances under `hardware/`.
3. **`SNN_<name>_plan.md` (Server Subsystem Plans)**:
   - Governs the FastAPI web application, SQLite schema/migrations, REST endpoints, HTML5 camera QR barcode scanner, and UI templates under `server/`.

Every plan MUST include all 7 mandatory sections:
1. `# Plan <Prefix><NN>: <Title>`
2. `## 1. Goal Description`
3. `## 2. Architecture & Workflow Diagram (Mermaid)`
4. `## 3. Code Modifications ([NEW], [MODIFY], [DELETE])`
5. `## 4. Test Updates & Specifications` (Unit/integration test methods, baseline regression matrices, and Red-Green bug reproduction tests)
6. `## 5. Documentation Updates`
7. `## 6. Verification Plan (Automated + Manual)`

### Test-First & Red-Green Regression Gating Standard:
- **Phase 3.1: Pre-Code Test Harness (RED / Baseline)**: Establish automated baseline tests verifying that existing behaviors work before making changes. For bug fixes, write a failing reproduction test demonstrating the reported issue (RED). Run `./run_tests.sh` to confirm baseline passes and bug test fails.
- **Phase 3.2: Minimal Blast Radius Implementation (GREEN)**: Implement root-cause code modifications and documentation updates. Run `./run_tests.sh` to confirm the reproduction test passes cleanly (GREEN).
- **Phase 3.3: Full Regression Retest & Coverage Verification**: Run the entire hermetic test suite (`./run_tests.sh`). All tests must pass (100% pass rate) with zero regressions.

---

## 3. Master Plan Registry

### Master Cross-Subsystem Plans (`MNN`):
- **`M01`**: Repository Categorization, Subsystem Restructuring & Web Catalog Server Staging ([`docs/plans/complete/2026-09-02-M01_repository_categorization_and_server_staging_plan.md`](complete/2026-09-02-M01_repository_categorization_and_server_staging_plan.md)) (`ARCHIVED`)
- **`M02`**: Cross-Subsystem URL Linkages & Dynamic 1/2/3-Compartment Bin Management ([`docs/plans/complete/2026-09-02-M02_qr_code_linking_and_bin_compartment_management_plan.md`](complete/2026-09-02-M02_qr_code_linking_and_bin_compartment_management_plan.md)) (`ARCHIVED`)

### Hardware Subsystem Plans (`HNN`):
- **`H01`**: Mixed-Layout Gridfinity Carriers & Deep Bin Cassettes ([`docs/plans/H01_mixed_gridfinity_carriers_and_cassettes_plan.md`](H01_mixed_gridfinity_carriers_and_cassettes_plan.md)) (`QUEUED`)

### Server Subsystem Plans (`SNN`):
- **`S01`**: FastAPI Web Catalog Server & SQLite Parts Database ([`docs/plans/complete/2026-09-02-S01_fastapi_web_catalog_server_and_sqlite_database_plan.md`](complete/2026-09-02-S01_fastapi_web_catalog_server_and_sqlite_database_plan.md)) (`ARCHIVED`)
- **`S02`**: Production Deployment & Provisioning on Node 02 (tasker-pi) ([`docs/plans/complete/2026-09-02-S02_production_deployment_and_provisioning_tasker_pi_plan.md`](complete/2026-09-02-S02_production_deployment_and_provisioning_tasker_pi_plan.md)) (`ARCHIVED`)
- **`S03`**: Household Consumables & Fleet Maintenance Inventory Expansion ([`docs/plans/S03_household_consumables_and_fleet_inventory_plan.md`](S03_household_consumables_and_fleet_inventory_plan.md)) (`QUEUED`)
- **`S04`**: Computer Vision Camera Fastener Counter (Snapshot Piece Counting) ([`docs/plans/S04_cv_camera_fastener_counter_plan.md`](S04_cv_camera_fastener_counter_plan.md)) (`QUEUED`)
- **`S05`**: Standardized Batch Label Sheet Generator & Cricut Print-Then-Cut Exporter ([`docs/plans/S05_standardized_batch_labels_and_cricut_exporter_plan.md`](S05_standardized_batch_labels_and_cricut_exporter_plan.md)) (`QUEUED`)

---

## 4. Prioritized Active Execution Queue

| Priority | Plan ID | Title | Target Scope | Status |
| :---: | :---: | :--- | :--- | :---: |
| **P1** | **S05** | Standardized Batch Label Sheet Generator & Cricut Exporter ([`docs/plans/S05_standardized_batch_labels_and_cricut_exporter_plan.md`](S05_standardized_batch_labels_and_cricut_exporter_plan.md)) | Canonical layout, Avery & Cricut Print-Then-Cut | `QUEUED` |
| **P2** | **S03** | Household Consumables & Fleet Maintenance Inventory Expansion ([`docs/plans/S03_household_consumables_and_fleet_inventory_plan.md`](S03_household_consumables_and_fleet_inventory_plan.md)) | Location hierarchy, large consumables & specs | `QUEUED` |
| **P3** | **S04** | Computer Vision Camera Fastener Counter ([`docs/plans/S04_cv_camera_fastener_counter_plan.md`](S04_cv_camera_fastener_counter_plan.md)) | Smartphone photo CV piece counting & overlay | `QUEUED` |
| **P4** | **H01** | Mixed-Layout Gridfinity Carriers & Deep Bin Cassettes ([`docs/plans/H01_mixed_gridfinity_carriers_and_cassettes_plan.md`](H01_mixed_gridfinity_carriers_and_cassettes_plan.md)) | Parametric Build123d CAD & large bolt bins | `QUEUED` |
