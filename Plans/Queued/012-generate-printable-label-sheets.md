# Plan 012 — Generate printable label sheets

- Status: Queued
- Depends on: Baseline cassette lid geometry ($34 \times 10\text{ mm}$ label zone)
- Created: 2026-08-29
- Started: Not started
- Completed: Not completed
- Git start: Not committed
- Git completion: Not completed

## Outcome

Develop an automated Python generator that outputs high-density, printable, Cricut-ready
label sheets (PDF / SVG / PNG) for standard US (Imperial / SAE) and Metric fasteners
(nuts, bolts, machine screws, wood screws, flat/lock washers, and inserts). Labels
will display standardized technical specifications (size, pitch, length, head type,
drive type, material/grade, and silhouette iconography), tailored for the $34 \times 10\text{ mm}$
solid lid zone with optional full-lid wrap overlays, integrating seamlessly with bin body
color-coding for rapid visual retrieval in shop drawers.

## Requirements

### 1. Fastener Taxonomy and Data Architecture
- Build a structured JSON / YAML / Python hardware catalog covering standard shop fasteners:
  - **Metric Threads:** M1.6, M2, M2.5, M3, M4, M5, M6, M8, M10, M12 (standard coarse and common fine pitches).
  - **Imperial / SAE Threads:** #0-80, #2-56, #4-40, #6-32, #8-32, #10-24, #10-32, 1/4"-20, 1/4"-28, 5/16"-18, 3/8"-16, 1/2"-13.
  - **Fastener Classes:**
    - **Bolts & Machine Screws:** Standard lengths (e.g. 4 mm to 60 mm; 3/16" to 3").
    - **Nuts:** Hex, nylon-insert lock (Nyloc), flanged, wing, cap/acorn, square, coupling, and brass heat-set threaded inserts (M2–M8).
    - **Washers:** Flat (standard, fender, small OD), split lock, external/internal tooth star, countersunk finishing, and Belleville.
  - **Head Profiles (with vector silhouettes):**
    - Socket Head Cap (SHCS), Button Head (BHCS), Flat/Countersunk (FHCS), Pan Head, Truss Head, Round Head, Hex Head, Oval/Raised Countersunk, Flanged Hex.
  - **Drive Types (with vector icons):**
    - Hex (Allen), Torx (6-lobe star), Security Torx (tamper-resistant pin), Phillips, Slotted, Pozidriv, Robertson (Square).
  - **Material & Finish Badges:**
    - 304/316 Stainless Steel (18-8 / A2 / A4), Class 10.9 / 12.9 Alloy Steel (Black Oxide), Grade 5 / Grade 8 Zinc-Plated, Brass, Nylon.

### 2. Physical Layout & Dimensional Standards
- **Standard 9 mm Strip ($34.0 \times 9.0\text{--}10.0\text{ mm}$):**
  - Primary format fitted to the solid lid label band.
  - Optimized for 9 mm Brother TZe tape and kiss-cut vinyl/polyester sheets.
  - Layout: Bold size/length header on left, technical pitch/material subtext, vector drive/head silhouettes on right.
- **Extended / Full-Lid Wrap Overlay ($38.6 \times 76.0\text{ mm}$ with $23.0 \times 58.5\text{ mm}$ glass cutout):**
  - Optional full-top vinyl skin that covers the lid perimeter while leaving the microscope-slide glass window 100% unobstructed.
  - Provides expanded surface area for fastener diagrams, thread pitch gauges, drill bit tap recommendations (e.g. "Tap: 2.5 mm / Drill: #43"), and color-coded borders.
- **Color-Coding Hierarchy:**
  - Bin body color (PETG/ASA filament) serves as the macro-level visual category (e.g. Blue = Metric Coarse, Red = Imperial UNC, Yellow = Brass Inserts, Green = Washers).
  - Label color accents (color laser printing) reinforce categorization without obscuring high-contrast black technical text.

### 3. Print-and-Cut Fabrication Integration (Color Laser + Cricut)
- Output print sheets in standard **Letter (8.5 × 11 in)** and **A4** formats at 300 / 600 DPI.
- Multi-layer vector generation:
  - **Print Layer (PDF / PNG):** High-resolution color artwork with bleed margins.
  - **Cut Layer (SVG):** Precision vector cut paths (kiss-cut perimeters) and optional weeding borders.
  - **Registration Marks:** Cricut Print-Then-Cut fiducial registration corner frames and calibration marks.
- Support batch generation (e.g. full sheet of M3 assortment, complete SAE washer kit, or customized mixed assortments).

## Non-goals

- Do not modify the underlying cassette 3D CAD models or reduce the visible glass aperture.
- Do not require proprietary label-making cloud software; keep all rendering in local, open-source Python scripts (e.g. `reportlab`, `matplotlib`, `cairosvg`, or pure SVG).
- Do not generate single-use raster images that degrade when scaled.

## Reusable parts and compatibility

- 100% compatible with all v0.6, v0.7, and v0.8 cassette lids (`cassette_lid_v0_8_print.stl`) and larger cassette family lids.
- Usable on standard polyester/vinyl sticker sheets (matte, gloss, waterproof laser label paper).

## Implementation steps

1. [ ] **Hardware Taxonomy & Schema:** Define `Labels/data/fasteners.json` (or YAML) with comprehensive US and Metric fastener parameters, pitches, tap drills, and categories.
2. [ ] **Vector Iconography Library:** Create clean, scalable SVG vector silhouettes for head types (socket, button, flat, pan, hex, oval) and drive types (hex, torx, phillips, slotted, square).
3. [ ] **Parametric Label Renderer:** Write `Labels/generate_labels.py` to render individual labels (both $34 \times 10\text{ mm}$ strips and full-lid window wraps) with crisp typography, color badges, and icons.
4. [ ] **Cricut Sheet Composer:** Implement automated sheet tiling (Letter / A4) with Cricut Print-Then-Cut fiducial marks, bleed margins, and SVG cut path export.
5. [ ] **Assortment Presets:** Create turnkey assortment templates:
   - Metric Socket Assortment (M2, M2.5, M3, M4, M5, M6).
   - SAE Socket & Hex Assortment (#4-40 through 3/8"-16).
   - Metric & SAE Nut / Washer Assortment.
   - Brass Heat-Set Insert Assortment.
6. [ ] **Physical Print & Cut Validation:** Print test sheets on color laser printer with sticker stock, perform Cricut Print-Then-Cut alignment, apply labels to printed cassettes, and verify legibility and adhesive durability.
7. [ ] **Documentation & Archive:** Document the label generation toolchain in `Labels/README.md` and archive Plan 012 with a walkthrough upon physical validation.

## Acceptance criteria

- [ ] Python script generates valid 300+ DPI PDF/PNG print sheets and SVG cut sheets without external closed-source dependencies.
- [ ] Labels fit cleanly within the $34 \times 10\text{ mm}$ lid zone without overhang.
- [ ] Full-lid wrap option leaves the $23.0 \times 58.5\text{ mm}$ glass window completely clear.
- [ ] Vector head and drive icons are sharp and instantly recognizable at $9\text{ mm}$ physical label height.
- [ ] Cricut Print-Then-Cut successfully registers marks and cuts labels accurately.
- [ ] Fastener database includes standard coarse/fine Metric (M1.6–M12) and SAE (#0 through 1/2") fasteners, nuts, and washers.

## Validation record

Record physical print results, laser toner adhesion on vinyl stock, Cricut cut accuracy, and legibility observations here during execution.

## Archive handoff

The walkthrough will document the hardware taxonomy, SVG rendering pipeline, Cricut workflow instructions, and photos/scans of applied physical labels on loaded cassette trays.
