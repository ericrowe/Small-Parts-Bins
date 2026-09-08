# Printable Fastener Label System & Multi-Medium Batch Exporter

This toolchain generates high-density, standardized, professional hardware labels for the **Gridfinity Glass-Window Cassette System** and workshop parts storage.

Labels adhere to the standard **$34.0 \times 10.0\text{ mm}$ strip layout** ($R = 1.0\text{ mm}$ rounded corners) with color-coded taxonomy bars, high-contrast typography, head/drive silhouette icons, and pure vector QR codes.

---

## 1. Supported Export Formats & Mediums

The batch generation engine supports 4 distinct physical output mediums:

1. **✂️ Cricut Print-Then-Cut (Letter SVG)**:
   - Multi-up Letter sheets (4 columns $\times$ 15 rows = up to 60 labels per sheet).
   - $+1.0\text{ mm}$ full bleed artwork envelope ($36 \times 12\text{ mm}$, $R=2.0\text{ mm}$) to absorb printer/Cricut mechanical drift.
   - Precision vector cut paths ($34 \times 10\text{ mm}$, $R=1.0\text{ mm}$) on red `#FF0000` stroke layer.
   - High-contrast optical registration bounding box for sensor tracking.
2. **📄 Avery 5160 / 8160 Pre-Cut Sheets (30-Up Letter)**:
   - Standard 3 columns $\times$ 10 rows on Letter paper ($1" \times 2-5/8"$ / $66.7 \times 25.4\text{ mm}$).
   - Fastener specs formatted to fit standard commercial laser/inkjet label sheets.
3. **📄 Avery 5167 / 8167 Pre-Cut Micro Sheets (80-Up Letter)**:
   - High-density 4 columns $\times$ 20 rows on Letter paper ($1/2" \times 1-3/4"$ / $44.5 \times 12.7\text{ mm}$).
   - Perfectly centers canonical $34 \times 10\text{ mm}$ labels within micro die-cut cells.
4. **📜 Continuous Thermal Roll Stream**:
   - Continuous vertical stream for Brother QL, Dymo LabelWriter, or Rollo thermal tape printers.
   - Configurable margins, gap spacing, and dashed cut guides.

---

## 2. Interactive Web Catalog Exporter (`:8090/labels`)

Access the batch export UI directly in your browser:
- Open [`http://tasker-pi.local:8090/labels`](http://tasker-pi.local:8090/labels) (or `http://localhost:8090/labels` in staging).
- Filter items by category (Metric, Imperial, Washers, Inserts, Specialty).
- Select individual parts or use "Select All".
- Choose output medium (Cricut, Avery 5160, Avery 5167, Thermal Roll).
- Preview live SVG sheet in-browser and 1-click download print-ready SVGs.

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
