# Walkthrough: Plan S12 — Fix Multi-Screw Cluster Patch Mask Shape Mismatch in `classify_bolt_head_type` (`IMG_6399.jpeg`)

## 1. Summary of Changes
1. **Root Cause Fixed ([`server/app/services/part_ingestor_service.py`](../../../server/app/services/part_ingestor_service.py))**:
   - In `_extract_pieces_from_mask()`, paired `local_mask = comp_mask` with `crop_bgr = work[by : by + bh, bx : bx + bw]` whenever a secondary peak's `2*patch_r` local slice contains no foreground pixels.
   - Added a defensive shape guard in `classify_bolt_head_type()` verifying `gray.shape == component_mask.shape` before evaluating `gray[component_mask > 0]`.
2. **Red-Green Regression Test ([`server/tests/test_part_ingestor.py`](../../../server/tests/test_part_ingestor.py))**:
   - Added `test_img_6399_multi_screw_cluster_patch_mask_shape_regression` verifying both direct mismatched-shape handling in `classify_bolt_head_type()` and full `analyze_cartridge_photo()` execution on `Temp/IMG_6399.jpeg` (`M2.5 × 16` Black Oxide SHCS).

## 2. Verification & Coverage Scorecard
- **Automated Tests**: `42/42 passed` (`100%` pass rate in `./Parts-Database/run_tests.sh`).
- **Live Verification**: Deployed to `tasker-pi.local:8090` and verified `Temp/IMG_6399.jpeg` returns `HTTP 200` (`cartridge_label: "M2.5 × 16"`, `pitch: "0.45 mm"`).
