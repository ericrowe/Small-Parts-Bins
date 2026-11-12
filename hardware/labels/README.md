# Printable Fastener Label System & Homebox Multi-Medium Batch Exporter

This toolchain generates high-density, standardized hardware labels for the **Gridfinity Glass-Window Cassette System** backed by **Homebox (`http://tasker-pi.local:7745`)** and [`data/fasteners.json`](data/fasteners.json).

> [!NOTE]
> **Homebox Integration & Legacy Catalog Deprecation**: All active cartridge bin allocations (`BIN-001`, `BIN-002`, ...) and inventory items are managed in **Homebox (`:7745`)** via the **Parts Ingestor (`/ingest`)**. Printed QR codes encode compact 4-digit forwarding URLs (`HTTP://TASKER-PI.LOCAL:8090/0001`) served by the **QR Link Redirector**, which issues an `HTTP 302` redirect to the corresponding Homebox Location (`http://tasker-pi.local:7745/locations/<uuid>`).

---

## 1. Supported Export Formats & Mediums

The batch generation engine (`canonical_label.py` + `label_service.py`) supports **5 physical output mediums**:

1. **🔪 $12 \times 35\text{ mm}$ Vertical Split-Label Pairs (Zero-Bleed Paper Cutter Grid — Primary Cartridge Format)**:
   - Designed for horizontally oriented drawer cartridges ($80\text{ mm}$ long axis left-to-right), where each end cap receives a vertical $12.0 \times 35.0\text{ mm}$ label (`[Label A | Label B]` = $24.0 \times 35.0\text{ mm}$ per pair).
   - **Zero bleed** with shared straight cut borders: packs **56 cartridge pairs (112 labels)** on a single Letter sheet ($8\text{ pairs across} \times 7\text{ rows}$) for rapid straight-line paper cutter slicing.
   - **Label A (Left — Part Identity End)**:
     - Top category color bar ($9.0\text{ mm}$ tall) with the thread size (e.g. **`M4`**) overlaid in large high-contrast bold type.
     - Directly below the color bar: bare length number (e.g. **`6`** — no `mm` suffix, no `SHCS` head text, and no icons, since a single cartridge bin holds multiple finishes/head styles in Homebox).
     - Lower region left blank by default; renders an optional note (`extra_note`) only when explicitly entered for special hardware (e.g. `Fine 0.5`, `Left-Hand`, `Nyloc`).
   - **Label B (Right — Bin Number & QR Redirector End)**:
     - Matching top category color bar ($5.5\text{ mm}$ tall).
     - **4-digit bin number** (e.g. **`0001`** — no `BIN` prefix text) below the color bar.
     - Low-density Version 1/2 QR code ($\le 25 \times 25$ modules, $10.6\text{ mm}$ square) encoding `HTTP://TASKER-PI.LOCAL:8090/0001` for instant phone camera scanning.
2. **✂️ Cricut Print-Then-Cut (Letter SVG — $34 \times 10\text{ mm}$ Horizontal Strip)**:
   - Multi-up Letter sheets (4 columns $\times$ 15 rows = up to 60 labels per sheet).
   - $+1.0\text{ mm}$ full bleed artwork envelope ($36 \times 12\text{ mm}$, $R=2.0\text{ mm}$) to absorb printer/Cricut mechanical drift.
   - Precision vector cut paths ($34 \times 10\text{ mm}$, $R=1.0\text{ mm}$) on red `#FF0000` stroke layer with optical registration bounding box.
3. **📄 Avery 5160 / 8160 Pre-Cut Sheets (30-Up Letter)**:
   - Standard 3 columns $\times$ 10 rows on Letter paper ($1" \times 2-5/8"$ / $66.7 \times 25.4\text{ mm}$), auto-enriched with thread pitch, tap drill, and hex key specs from [`data/fasteners.json`](data/fasteners.json).
4. **📄 Avery 5167 / 8167 Pre-Cut Micro Sheets (80-Up Letter)**:
   - High-density 4 columns $\times$ 20 rows on Letter paper ($1/2" \times 1-3/4"$ / $44.5 \times 12.7\text{ mm}$).
5. **📜 Continuous Thermal Roll Stream**:
   - Continuous vertical stream for Brother QL, Dymo LabelWriter, or Rollo thermal tape printers.

---

## 2. Interactive Homebox Label Exporter (`:8090/labels`)

Access the Homebox-synced batch export UI directly in your browser:
- Open [`http://tasker-pi.local:8090/labels`](http://tasker-pi.local:8090/labels) (or `http://localhost:8090/labels` in staging, or deep-link a specific bin via `/labels?bin=0001`).
- **Live Homebox Sync**: Automatically loads all ingested `BIN-XXX` locations from Homebox (`/api/v1/locations` & `/api/v1/items`), displaying each bin's 4-digit code (`0001`), parsed thread size (`M4`), bare length (`6`), category color bar, and summarized Homebox item counts (e.g. `21× Black SHCS, 65× Silver BHCS`).
- **Quick-Add Custom or Series Builder**: Queue single labels or comma-separated length series (e.g. Size `M4`, Lengths `6, 8, 10, 12, 16, 20` starting at Bin `0002`) before or after physical ingestion.
- **Inline Editing & Live Preview**: Edit any row's 4-digit bin, size, bare length, color bar, or optional note in-place, preview the rendered SVG sheet in-browser, and download with 1 click.

---

## 3. Hardware Taxonomy & Filament Color Mapping

| Category | Primary Hardware | Filament Material / Color | Label Accent Color |
|---|---|---|---|
| **Metric Hardware (ISO)** | M1.6, M2, M2.5, M3, M4, M5, M6, M8 (SHCS, BHCS, FHCS) | **Elegoo Blue PETG** | Blue (`#0077CC`) |
| **Imperial Hardware (SAE)** | #2-56, #4-40, #6-32, #8-32, #10-24, #10-32, 1/4"-20 | **Elegoo Orange PETG** | Orange (`#E65100`) |
| **Washers & Spacers** | Flat washers, Split lock washers, Star washers, Spacers | **Elegoo / Geeetech Green PETG** | Green (`#2E7D32`) |
| **Specialty & Wood/Pins** | Wood screws, sheet metal screws, grub screws, pins | **Elegoo / Overture Yellow PETG** | Yellow (`#D4A017`) |
| **Carrier Trays & Lids** | 3×4 7U Carrier Trays & Cassette Lids | **Elegoo Black PETG** | Neutral Black Base |
| **Heat-Set Inserts** | M2, M2.5, M3 (Short/Std/Voron), M4, M5 Brass Inserts | **Elegoo Black PETG** | Brass / Gold (`#C5A059`) |

---

## 4. Fabrication & Cricut Print-Then-Cut Workflow

1. **Export Batch Sheet:**
   - Download SVG from `/labels` or generate via `generate_labels.py`.
2. **Load into Cricut Design Space / Silhouette Studio:**
   - Import the SVG into Cricut Design Space.
   - Ungroup layers: assign the `cut-lines` layer to **Basic Cut** and `print-artwork` to **Standard Print**.
   - Align both groups to $(0,0)$ and click **Attach**.
3. **Print:**
   - Print on full-sheet printable vinyl/polyester sticker paper with a color laser or inkjet printer at 100% scale ("Actual Size").
4. **Cut:**
   - Place printed sheet on Cricut mat. Optical sensor registers fiducial corner frame and performs precision kiss-cutting ($R = 1.0\text{ mm}$ corners).
5. **Apply:**
   - Peel and apply directly to the $34 \times 10\text{ mm}$ front recessed zone of assembled cassette lids.
