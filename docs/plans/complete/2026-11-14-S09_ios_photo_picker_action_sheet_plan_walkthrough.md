# Walkthrough: Plan S09 — Enable Native iOS Action Sheet ("Take Photo or Choose Image") on `/ingest`

## 1. Summary of Changes
- **Removed `capture="environment"` ([`server/templates/ingest.html`](../../../server/templates/ingest.html))**:
  - Updated `#photo-file-input` to `<input id="photo-file-input" type="file" accept="image/*" class="hidden" onchange="onPhotoSelected(event)" />` so iOS Safari opens the native action sheet (**Photo Library**, **Take Photo**, **Choose File**).
- **Red-Green Regression Test ([`server/tests/test_part_ingestor.py`](../../../server/tests/test_part_ingestor.py))**:
  - Verified `'capture=' not in res_empty.text` in `test_ingest_view_renders_html()`.

## 2. Test & Coverage Scorecard
- `Parts-Database`: **40 passed**, **88% statement coverage**, **100% behavioral invariants verified**.
