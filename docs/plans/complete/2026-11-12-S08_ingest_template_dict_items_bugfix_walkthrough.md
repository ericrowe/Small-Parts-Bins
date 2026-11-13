# Walkthrough: Plan S08 — Fix Jinja2 `dict.items` Collision on `/ingest` When Homebox Bins Are Populated

**Completed**: 2026-11-12
**Status**: `ARCHIVED`

---

## 1. Summary of Changes

1. **Template Dictionary Subscript Fix ([`server/templates/ingest.html`](../../../server/templates/ingest.html))**:
   - Replaced `{% for item in b.items %}` with `{% for item in b['items'] %}` at line 247 so Jinja2 iterates over the `"items"` list inside each bin dictionary rather than resolving `dict.items`.
2. **Red-Green Regression Test ([`server/tests/test_part_ingestor.py`](../../../server/tests/test_part_ingestor.py))**:
   - Updated `test_ingest_view_renders_html()` to commit a populated bin (`BIN-001`, `25 pcs`) via `POST /api/ingest/commit` and then fetch `GET /ingest`, confirming `RED` before the fix and `GREEN` (`HTTP 200`, `"25 pcs"`, `"BIN-002"`) after.

---

## 2. Automated Test & Coverage Scorecard

- **Parts-Database Hermetic Suite**: `37/37 passed (100%)` in `5.83s`.
- **Statement Coverage**: `82%` (`4/4` domain invariants verified — `100%`).
- **Live Production Verification**: Deployed to Node 02 (`http://tasker-pi.local:8090/ingest`) and verified `HTTP 200 OK`.
