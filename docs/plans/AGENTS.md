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
5. `## 4. Test Updates & Specifications`
6. `## 5. Documentation Updates`
7. `## 6. Verification Plan (Automated + Manual)`

---

## 3. Master Plan Registry

### Master Cross-Subsystem Plans (`MNN`):
- **`M01`**: Repository Categorization, Subsystem Restructuring & Web Catalog Server Staging ([`docs/plans/complete/2026-09-02-M01_repository_categorization_and_server_staging_plan.md`](complete/2026-09-02-M01_repository_categorization_and_server_staging_plan.md)) (`ARCHIVED`)
- **`M02`**: Cross-Subsystem URL Linkages & Dynamic 1/2/3-Compartment Bin Management ([`docs/plans/complete/2026-09-02-M02_qr_code_linking_and_bin_compartment_management_plan.md`](complete/2026-09-02-M02_qr_code_linking_and_bin_compartment_management_plan.md)) (`ARCHIVED`)

### Hardware Subsystem Plans (`HNN`):
- *(No active hardware plans)*

### Server Subsystem Plans (`SNN`):
- **`S01`**: FastAPI Web Catalog Server & SQLite Parts Database ([`docs/plans/complete/2026-09-02-S01_fastapi_web_catalog_server_and_sqlite_database_plan.md`](complete/2026-09-02-S01_fastapi_web_catalog_server_and_sqlite_database_plan.md)) (`ARCHIVED`)
- **`S02`**: Production Deployment & Provisioning on Node 02 (tasker-pi) ([`docs/plans/S02_production_deployment_and_provisioning_tasker_pi_plan.md`](S02_production_deployment_and_provisioning_tasker_pi_plan.md)) (`IN_PLANNING`)

---

## 4. Prioritized Active Execution Queue
1. **`S02`**: **Production Deployment & Provisioning on Node 02 (tasker-pi)** ([`docs/plans/S02_production_deployment_and_provisioning_tasker_pi_plan.md`](S02_production_deployment_and_provisioning_tasker_pi_plan.md))
