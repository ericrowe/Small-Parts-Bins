# Printable Fastener Label System (Color Laser + Cricut Ready)

This directory provides an automated Python generator for producing high-density, standardized, professional hardware labels for the **Gridfinity Glass-Window Cassette System**.

Labels are formatted for:
1. **Standard 34.0 × 10.0 mm Strips:** Fits the solid front label zone on cassette lids (`cassette_lid_v0_8_print.stl`).
2. **Extended 38.6 × 76.0 mm Full-Lid Wraps:** Overlays the entire lid with an integrated 1:1 scale millimeter length ruler and technical specifications while leaving the **$23.0 \times 58.5\text{ mm}$ glass microscope slide window 100% unobstructed**.

---

## Visual Previews

### 1. Metric M3 Fastener Assortment (Standard 34 × 10 mm Strips)
![Metric M3 Strip Sheet](../../docs/images/metric_m3_fastener_assortment_preview_strip.png)

### 2. Imperial SAE Socket Assortment (Standard 34 × 10 mm Strips)
![Imperial SAE Socket Strip Sheet](../../docs/images/imperial_sae_socket_assortment_preview_strip.png)

### 3. Brass Heat-Set Insert Assortment (34 × 10 mm Strips with Hole Sizing Specs)
![Brass Heat-Set Insert Strip Sheet](../../docs/images/brass_heat_set_insert_assortment_preview_strip.png)

---

## Hardware Taxonomy & Color-Coding

| Category | Color Code | Hex Code | Fasteners Covered |
|---|---|---|---|
| **Metric Coarse (ISO)** | Electric Blue / Cyan | `#0077CC` | M1.6, M2, M2.5, M3, M4, M5, M6, M8, M10, M12 |
| **Metric Fine (ISO)** | Navy / Indigo | `#003366` | M8×1.0, M10×1.25, M12×1.5 |
| **Imperial Coarse (UNC)** | Red / Crimson | `#C8102E` | #0-80, #2-56, #4-40, #6-32, #8-32, #10-24, 1/4"-20, 5/16"-18, 3/8"-16, 1/2"-13 |
| **Imperial Fine (UNF)** | Orange / Amber | `#E65100` | #10-32, 1/4"-28, 5/16"-24, 3/8"-24, 1/2"-20 |
| **Brass Heat-Set Inserts** | Gold / Brass | `#C5A059` | M2, M2.5, M3 (Short/Std/Voron), M4, M5 (with 3D print hole recommendations) |
| **Washers & Spacers** | Green | `#2E7D32` | Flat washers, Split lock washers, Star washers |

---

## Technical Information on Every Label

1. **Size & Length Header:** Large, high-contrast bold typography (e.g. `M3 × 12`, `#4-40 × 1/2"`).
2. **Thread Pitch & Tap Drill:** Recommended tap drill size (e.g. `P: 0.5 | Tap: 2.5mm (#39)` or `40 TPI | Tap: #43`).
3. **Drive Key Size & Material:** Allen / Torx wrench size and material badge (e.g. `Key: 2.5 mm | SS 304`).
4. **Vector Silhouette Icons:**
   * Head profiles: Socket Head Cap (SHCS), Button Head (BHCS), Flat/Countersunk (FHCS), Pan Head, Hex Head.
   * Drive profiles: Hex / Allen, Torx / Star (6-lobe), Phillips, Slotted, Square / Robertson.
   * Component icons: Hex nuts, Nyloc lock nuts, Flanged nuts, Flat washers, Split lock washers, Knurled heat-set inserts.

---

## Fabrication & Cricut Print-Then-Cut Workflow

### Equipment & Materials:
* **Printer:** Color Laser or High-Resolution Inkjet printer.
* **Paper Stock:** Printable waterproof vinyl sticker paper or matte/gloss polyester laser label sheets (Letter 8.5 × 11 in or A4).
* **Cutting Machine:** Cricut Maker / Explore / Joy Xtra (or silhouette cutter / hobby knife).

### Step-by-Step Instructions:

1. **Generate Sheets:**
   ```bash
   python3 Labels/generate_labels.py
   ```
2. **Load Artwork into Cricut Design Space:**
   * Import `*_print_strip.svg` (or `*_print_wrap.svg`) as the **Print Artwork Layer**.
   * Import `*_cut_strip.svg` as the **Cut Path Layer** (set operation to "Basic Cut").
   * Align the two layers over the matching corner registration frame and click **Attach**.
3. **Print:**
   * Print to laser printer on full-sheet sticker paper with standard 100% scale (no page scaling / "Actual Size").
4. **Cut:**
   * Place printed sheet on Cricut cutting mat.
   * The optical sensor detects the black fiducial corner frame and performs precision kiss-cutting around each label perimeter ($R = 1.0\text{ mm}$ rounded corners).
5. **Apply:**
   * Peel and apply directly to the $34 \times 10\text{ mm}$ front recessed zone of any assembled v0.7 / v0.8 cassette lid.

---

## File Directory (`Labels/build/`)

* `metric_m3_fastener_assortment_print_strip.svg` & `*_cut_strip.svg`
* `metric_m2_and_m2_5_micro_assortment_print_strip.svg` & `*_cut_strip.svg`
* `metric_m4_m5_m6_structural_assortment_print_strip.svg` & `*_cut_strip.svg`
* `imperial_sae_socket_assortment_print_strip.svg` & `*_cut_strip.svg`
* `brass_heat_set_insert_assortment_print_strip.svg` & `*_cut_strip.svg`
* Matching `*_wrap.svg` full-lid overlays for all assortments.
