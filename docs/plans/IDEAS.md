# Parts-Database Idea Backlog & Design Intake

Persistent asynchronous backlog for database schema design, QR code generation, physical bin tagging, and inventory API endpoints for **Parts-Database**.

---

## 1. Master & Cross-Subsystem Backlog (`MNN`)

### [FEATURE] End-to-End QR Fastener Tagging & Camera Scanner Resolution
- **Context**: Need a seamless pipeline connecting vector SVG label generation with QR codes to immediate mobile camera scanning and SQLite record resolution.
- **Proposed Solution**: Standardize QR payload format (e.g. `https://parts.local/b/<bin_uuid>` or `PARTS:<id>`), inject dynamic QR codes into SVG label sheets, and decode instantly in the web catalog.
- **Status**: Prioritized for follow-up after Plan M01.

---

## 2. Server Subsystem Backlog (`SNN`)

### [FEATURE] FastAPI Catalog Server & SQLite Parts Database (`S01`)
- **Context**: Need a fast, lightweight, self-hosted web catalog to query fastener specs, thread pitches, quantities on hand, and bin slot assignments.
- **Proposed Solution**: FastAPI backend, SQLite WAL storage, Jinja2/Tailwind templates, and mobile-first responsive layout.
- **Status**: Queued for S01.

### [FEATURE] Camera QR Barcode Scanner (`S02`)
- **Context**: Scanning bin QR codes directly from a phone browser without installing a native app.
- **Proposed Solution**: Integrated HTML5 QR scanner using WebRTC / `html5-qrcode` library pointing to `/scan`.
- **Status**: Queued for S02.

### [FEATURE] Household Consumables & Fleet Maintenance Inventory Expansion (`S03`)
- **Context**: The database is currently focused on small modular fastener bins. Household maintenance items (HVAC air filters, water filters, LED light bulbs, lawnmower blades) and vehicle maintenance items (motor oil, oil filters, spark plugs, brake pads) require tracking larger items in shelves, cabinets, and closets.
- **Proposed Solution**: Expand schema to support broader location hierarchies (e.g. `Garage Shelf B2`, `Utility Closet Rack`), multi-pack quantities, item specification attributes (e.g. `16x25x1 MERV 11`, `5W-30 Full Synthetic`), and minimum stock reorder thresholds.
- **Status**: Triaged Idea (Backlog)

### [FEATURE] Computer Vision Camera Fastener Counter (Snapshot Piece Counting) (`S04`)
- **Context**: Counting small fasteners (screws, nuts, washers, pins) by hand is slow, and weight scales can suffer from tare/tolerance inaccuracies. Spreading fasteners across a tray or bin and taking a quick smartphone photo provides an instant, auditable count.
- **Proposed Solution**:
  1. Add a camera snapshot / file upload dialog on the restock page.
  2. Process the image using computer vision / contour blob detection (or local vision AI inference) to segment and count individual items.
  3. Overlay detected dot markers / count badges on the image with the calculated count (e.g. "Detected: 48 pieces"), allowing 1-tap manual adjustment before committing to `parts.db`.
- **Status**: Triaged Idea (Backlog)

### [FEATURE] Standardized Batch Label Sheet Generator & Cricut Print-Then-Cut Exporter (`S05`)
- **Context**: Setting up workshop storage requires batch-generating labels for dozens or hundreds of bins at once. The visual format must remain strictly standardized and consistent across all physical media types, whether using pre-cut label templates, continuous thermal tape, or uncut sticker paper cut on a digital crafting cutter.
- **Proposed Solution**:
  1. Define a strict canonical label specification (QR code placement, high-contrast typography, part description, pitch/drive icon, bin coordinate ID).
  2. Implement batch export in the web catalog supporting:
     - **Pre-cut Label Sheets**: Standard Avery templates (e.g. Avery 5160, 5167).
     - **Continuous Thermal Rolls**: Brother QL / Dymo label streams.
     - **Cricut "Print Then Cut"**: Full-sheet SVG/PDF generator with standard registration marks and precision cut-boundary vector paths for kiss-cutting on uncut vinyl/sticker sheets.
- **Status**: Triaged Idea (Backlog)

---

## 3. Hardware Subsystem Backlog (`HNN`)

### [FEATURE] Mixed-Layout Gridfinity Carriers & Deep Bin Cassettes (`H01`)
- **Context**: Expanding the 3D-printable modular hardware catalog for larger bolts (M8+) and mixed compartment carriers.
- **Proposed Solution**: Parametric OpenSCAD / Build123d generators for 2x2 and 3x3 deep Gridfinity carriers.
- **Status**: Queued in hardware backlog.
