---
name: hardware-prototyper
description: >-
  Design rapid physical test coupons, tolerance fit ladders, and document Human-in-the-Loop (HITL)
  physical measurements. Use this skill when calibrating 3D printer tolerances, snap-fits,
  sliding channels, or hinge clearances before committing to large production prints.
---

# Hardware Prototyper Skill

This skill standardizes rapid iterative physical prototyping and caliper measurement logging.

## Core Rules for Physical Validation

1. **Always Print Fit Coupons First:**
   - Never print a large 5-hour multi-feature part to test a 0.2 mm fit tolerance.
   - Design isolated, 15-minute test coupons (e.g. 4-step fit ladder) to physically calibrate clearances under actual slicer and material conditions.
2. **Preserve Tested Ladders in Git History:**
   - Record exact measured dimensions (e.g. caliper readings to 2 decimal places), material (PETG/ASA/PLA), nozzle size, and slicer layer height.
3. **The Physical Print Governs CAD:**
   - If a physical print contradicts CAD model assumptions (e.g. bore sag, thermal shrinkage, bed adhesion warping), update the model to match physical reality rather than scaling in the slicer.
