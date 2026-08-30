# Printable Fastener Label System (Color Laser + Cricut Ready)

This directory provides an automated Python generator for producing high-density, standardized, professional hardware labels for the **Gridfinity Glass-Window Cassette System**.

Labels are formatted for:
1. **Standard 34.0 × 10.0 mm Strips:** Fits the solid front label zone on cassette lids (`cassette_lid_v0_8_print.stl`).
2. **Extended 38.6 × 76.0 mm Full-Lid Wraps:** Overlays the entire lid with an integrated 1:1 scale millimeter length ruler and technical specifications while leaving the **$23.0 \times 58.5\text{ mm}$ glass microscope slide window 100% clear**.

---

## Visual Previews

### 1. Metric M3 Fastener Assortment (Elegoo Blue Theme)
![Metric M3 Strip Sheet](../../docs/images/metric_m3_fastener_assortment_preview_strip.png)

### 2. Imperial SAE Socket Assortment (Elegoo Orange Theme)
![Imperial SAE Socket Strip Sheet](../../docs/images/imperial_sae_socket_assortment_preview_strip.png)

### 3. Brass Heat-Set Insert Assortment (Elegoo Black Body / Gold Accent Theme)
![Brass Heat-Set Insert Strip Sheet](../../docs/images/brass_heat_set_insert_assortment_preview_strip.png)

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

## Standard Typography & Design Hierarchy

* **No dynamic letter squishing:** All labels use consistent, uniform typography with natural letter tracking.
* **Main Size Header:** Bold $3.0\text{ mm}$ ($8.0\text{ pt}$) size and length callout (e.g. `M3 × 12 mm`, `#4-40 × 1/2"`).
* **Technical Subtext 1:** Regular $1.7\text{ mm}$ ($4.8\text{ pt}$) pitch / tap drill / hole sizing (e.g. `0.5 | Tap 2.5`, `40 TPI | Tap #43`, `Ø4.0 × 4.5 mm`).
* **Tool & Material Subtext 2:** Bold $1.7\text{ mm}$ ($4.8\text{ pt}$) category color drive key / material badge (e.g. `Key 2.5 mm`, `Key 3/32"`, `Brass Insert`).
* **Vector Silhouettes:** Scalable vector head profiles (Socket, Button, Flat, Pan, Hex) and drive sockets (Hex, Torx, Phillips, Slotted, Square).

---

## Fabrication & Cricut Print-Then-Cut Workflow

1. **Generate Sheets:**
   ```bash
   python3 Labels/generate_labels.py
   ```
2. **Load into Cricut Design Space:**
   * Import `*_print_strip.svg` (or `*_print_wrap.svg`) as the **Print Artwork Layer**.
   * Import `*_cut_strip.svg` as the **Cut Path Layer** (Basic Cut).
   * Align the two layers over the matching corner registration frame and click **Attach**.
3. **Print:**
   * Print on full-sheet printable vinyl/polyester sticker paper with color laser printer at 100% scale (no page scaling).
4. **Cut:**
   * Place printed sheet on Cricut mat. Optical sensor registers fiducial corner frame and performs precision kiss-cutting ($R = 1.0\text{ mm}$ corners).
5. **Apply:**
   * Apply directly to the $34 \times 10\text{ mm}$ front recessed zone of assembled cassette lids.
