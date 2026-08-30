# Printable Fastener Label System (High-Density Master Sheets)

This toolchain generates high-density, standardized, professional hardware labels for the **Gridfinity Glass-Window Cassette System**.

Labels are formatted in the standard **$34.0 \times 10.0\text{ mm}$ strip layout** with $R = 1.0\text{ mm}$ rounded corners, designed to fit the front solid label band on all cassette lids (`cassette_lid_v0_8_print.stl`).

---

## Master Combined Sheets (Print Your Entire Shop on 2 Sheets!)

By packing labels into a **4-column × 18-row grid (up to 72 labels per Letter sheet)**, your entire shop's hardware collection can be printed and cut on **just 2 sheets of sticker paper**:

### Sheet 1: Master Metric Fasteners & Heat-Set Inserts (70 Labels)
* **Print Artwork Layer (Color Laser):** [`Labels/build/master_metric_and_inserts_assortment_print.svg`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/Labels/build/master_metric_and_inserts_assortment_print.svg)
* **Cut Path Layer (Cricut Kiss-Cut):** [`Labels/build/master_metric_and_inserts_assortment_cut.svg`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/Labels/build/master_metric_and_inserts_assortment_cut.svg)

![Master Metric Sheet Preview](../../docs/images/master_metric_and_inserts_assortment_preview.png)

#### Contents of Sheet 1:
1. **M2 & M2.5 Micro Screws (Elegoo Blue):** SHCS $4\text{ to }16\text{ mm}$, Hex Nuts, Flat Washers (16 labels).
2. **M3 Complete Assortment (Elegoo Blue):** SHCS $4\text{ to }30\text{ mm}$, BHCS $6\text{ to }16\text{ mm}$, Hex Nuts, Nylocs, Flat Washers, Split Lock Washers (22 labels).
3. **M4, M5, M6 Structural Screws (Elegoo Blue):** SHCS $8\text{ to }30\text{ mm}$, Hex Nuts, Nylocs, Flat Washers (25 labels).
4. **Brass Heat-Set Inserts (Black Body / Gold):** M2, M2.5, M3 (Short/Std/Voron), M4, M5 inserts with hole diameter and depth specifications (9 labels).

---

### Sheet 2: Master Imperial Hardware & Wood / Specialty (72 Labels)
* **Print Artwork Layer (Color Laser):** [`Labels/build/master_imperial_and_wood_specialty_assortment_print.svg`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/Labels/build/master_imperial_and_wood_specialty_assortment_print.svg)
* **Cut Path Layer (Cricut Kiss-Cut):** [`Labels/build/master_imperial_and_wood_specialty_assortment_cut.svg`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/Labels/build/master_imperial_and_wood_specialty_assortment_cut.svg)

![Master Imperial & Wood Sheet Preview](../../docs/images/master_imperial_and_wood_specialty_assortment_preview.png)

#### Contents of Sheet 2:
1. **Imperial #4-40, #6-32, #8-32, 1/4"-20 Screws (Elegoo Orange):** SHCS $1/4"\text{ to }1-1/4"$, Hex Nuts, Nyloc Nuts, Flat Washers (37 labels).
2. **Set / Grub Screws (Elegoo Yellow):** Metric M3, M4, M5 and Imperial #4, #6, #8, 1/4" cup point grub screws with hex wrench sizes (12 labels).
3. **Countersunk Wood Screws (Elegoo Yellow):** #4, #6, #8 flat head wood screws (13 labels).
4. **Dowel Pins, Standoffs & Plastic Screws (Elegoo Yellow):** Ground dowel pins, brass hex standoffs, and plastic thread-forming screws (10 labels).

---

## Hardware Taxonomy & Filament Color Mapping

| Category | Primary Hardware | Filament Material / Color | Label Accent Color |
|---|---|---|---|
| **Metric Hardware (ISO)** | M1.6, M2, M2.5, M3, M4, M5, M6, M8 (SHCS, BHCS, FHCS) | **Elegoo Blue PETG** | Blue (`#0077CC`) |
| **Imperial Hardware (SAE)** | #2-56, #4-40, #6-32, #8-32, #10-24, #10-32, 1/4"-20 | **Elegoo Orange PETG** | Orange (`#E65100`) |
| **Washers & Spacers** | Flat washers, Split lock washers, Star washers, Spacers | **Elegoo / Geeetech Green PETG** | Green (`#2E7D32`) |
| **Specialty & Wood/Pins** | Wood screws, sheet metal screws, grub screws, pins | **Elegoo / Overture Yellow PETG** | Yellow (`#D4A017`) |
| **Carrier Trays & Lids** | 3×4 7U Carrier Trays & Cassette Lids | **Elegoo Black PETG** | Neutral Black Base |
| **Heat-Set Inserts** | M2, M2.5, M3 (Short/Std/Voron), M4, M5 Brass Inserts | **Elegoo Black PETG** | Brass / Gold (`#C5A059`) |

---

## Fabrication & Cricut Print-Then-Cut Workflow

1. **Generate Sheets:**
   ```bash
   python3 Labels/generate_labels.py
   ```
2. **Load into Cricut Design Space:**
   * Import `master_*_print.svg` as the **Print Artwork Layer**.
   * Import `master_*_cut.svg` as the **Cut Path Layer** (Operation: "Basic Cut").
   * Align the two layers over the matching corner registration frame and click **Attach**.
3. **Print:**
   * Print on full-sheet printable vinyl/polyester sticker paper with color laser printer at 100% scale ("Actual Size").
4. **Cut:**
   * Place printed sheet on Cricut mat. Optical sensor registers fiducial corner frame and performs precision kiss-cutting ($R = 1.0\text{ mm}$ corners).
5. **Apply:**
   * Peel and apply directly to the $34 \times 10\text{ mm}$ front recessed zone of assembled cassette lids.
