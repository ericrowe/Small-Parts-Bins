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

---

## 3. Hardware Subsystem Backlog (`HNN`)

### [FEATURE] Mixed-Layout Gridfinity Carriers & Deep Bin Cassettes (`H01`)
- **Context**: Expanding the 3D-printable modular hardware catalog for larger bolts (M8+) and mixed compartment carriers.
- **Proposed Solution**: Parametric OpenSCAD / Build123d generators for 2x2 and 3x3 deep Gridfinity carriers.
- **Status**: Queued in hardware backlog.
