# Plan S05: Standardized Batch Label Sheet Generator & Cricut Print-Then-Cut Exporter

## 1. Goal Description
Labeling hundreds of hardware bins and storage shelves requires batch multi-up sheet generation. Regardless of the physical output medium (pre-cut adhesive sheets, continuous thermal tape, or uncut sticker paper), the visual format must strictly adhere to a **Unified Standard Label Specification**.
This plan implements:
1. **Canonical Label Specification**: Standardized high-contrast layout containing QR code, human-readable part description, thread size/pitch, drive/head icon, and bin coordinate ID.
2. **Multi-Source Export Engine**:
   - **Pre-cut Label Sheets**: Standard Avery templates (e.g. Avery 5160 30-up, Avery 5167 80-up).
   - **Continuous Thermal Rolls**: Brother QL / Dymo continuous streams.
   - **Cricut "Print Then Cut"**: Multi-up full-sheet SVG/PDF with standardized sensor registration marks and precision cut-boundary vector paths for automated kiss-cutting on uncut vinyl/sticker paper.
3. **Batch Export Web UI**: Select drawers, categories, or bin ranges and export print-ready files with 1 click.

---

## 2. Architecture & Workflow Diagram

```mermaid
flowchart TD
    subgraph Selection["Catalog Selection (:8090)"]
        Select["Select Category / Drawer / Range (e.g. 60 Bins)"]
        Format["Choose Export Format"]
    end

    subgraph CoreEngine["Unified Label Layout Generator"]
        Spec["Canonical Label Specification (QR, Text, Drive Icon, Bin ID)"]
        Renderer["Vector SVG / PDF Sheet Engine"]
    end

    subgraph Exporters["Multi-Medium Exporters"]
        Avery["Avery Pre-Cut Sheets (5160 / 5167 PDF)"]
        Thermal["Continuous Thermal Roll (Brother / Dymo SVG)"]
        Cricut["Cricut 'Print Then Cut' (SVG + Registration Marks & Cut Paths)"]
    end

    Select --> Format
    Format --> Spec
    Spec --> Renderer
    Renderer --> Avery
    Renderer --> Thermal
    Renderer --> Cricut
```

---

## 3. Code Modifications

### Label Generators & Templates
- `[MODIFY]` [`hardware/labels/generate_labels.py`](../../hardware/labels/generate_labels.py): Refactor to enforce canonical label layout across all format exporters.
- `[NEW]` `hardware/labels/cricut_exporter.py`: Cricut Print-Then-Cut generator creating SVG/PDF with exact boundary cut paths and corner optical registration sensor marks.
- `[NEW]` `hardware/labels/avery_templates.py`: Grid layout definitions for Avery 5160, 5167, and custom multi-up letter sheets.
- `[MODIFY]` [`server/app/main.py`](../../server/app/main.py): Add `/api/labels/export-batch` accepting part IDs and target format (`avery_5160`, `avery_5167`, `thermal_roll`, `cricut_print_cut`).
- `[NEW]` `server/app/templates/label_batch_export.html`: Web interface for selecting parts and downloading print-ready vector sheets.

### Tests
- `[NEW]` `server/tests/test_batch_label_generator.py`: Automated tests verifying SVG/PDF dimensions, QR code data encoding, and Cricut cut-path geometry.

---

## 4. Test Updates & Specifications

### Test Harness (`server/tests/test_batch_label_generator.py`)
1. **`test_canonical_label_layout_content()`**:
   - Asserts generated label contains part title, thread spec, drive icon, bin ID, and valid scannable QR payload `PARTS:<id>`.
2. **`test_cricut_print_then_cut_svg_structure()`**:
   - Generates a 24-bin Cricut sheet. Asserts SVG contains `<g id="cut-lines">` with rect/rounded-rect cut paths and registration marks in the four corners.
3. **`test_avery_5160_grid_alignment()`**:
   - Verifies 30 labels fit within 3 columns $\times$ 10 rows on an 8.5" $\times$ 11" page with standard margins (0.5" top/bottom, 0.1875" left/right).

---

## 5. Documentation Updates
- `[MODIFY]` [`hardware/labels/README.md`](../../hardware/labels/README.md): Document Cricut Print-Then-Cut workflow, Avery alignment calibration, and canonical layout standards.
- `[MODIFY]` [`Parts-Database/docs/plans/AGENTS.md`](AGENTS.md): Register Plan S05.

---

## 6. Verification Plan

### Automated Tests:
```bash
./run_tests.sh
```

### Manual Verification:
1. Open `:8090/labels` in the web catalog.
2. Select "M3 Socket Head Assortment (15 items)".
3. Export as Cricut Print-Then-Cut SVG; import into Cricut Design Space and verify printable artwork and cut lines separate onto appropriate layers.
