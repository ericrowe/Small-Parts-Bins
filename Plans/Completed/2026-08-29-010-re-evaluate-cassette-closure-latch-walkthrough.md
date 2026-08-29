# Plan 010 Walkthrough — Re-evaluate Cassette Closure Latch

- Completed: 2026-08-29
- Archived plan: `2026-08-29-010-re-evaluate-cassette-closure-latch.md`
- Git range: `0643d9d..main`

## 1. Objective and Scope

Plan 010 resolved the containment failure where inserting divider cards into the cassette body wedged the $2.00\text{ mm}$ front wall outward, reducing the $0.65\text{ mm}$ closure clasp undercut overlap below the holding threshold.

## 2. Solution: Internal Flanking Ridges & Loose-Fit Divider Sizing

Rather than relying on friction fit (which requires tight lateral tolerances and pushes the walls apart) or delicate moving detents:
1. **Internal Flanking Wall Ridges:**
   - Added vertical ridges projecting $+0.80\text{ mm}$ into the cavity ($1.50\text{ mm}$ wide along $Y$) flanking each divider slot at $Y = \pm 12.87\text{ mm}$ on the front wall.
   - Combined with wall recesses, this creates deep **$1.40\text{–}1.60\text{ mm}$ guide channels** ($3.00\text{ mm}$ total engagement across the cavity).
   - $45^\circ$ top lead-in funnel chamfers ($Z \in [31.30, 32.80\text{ mm}]$) guide cards directly into the slots.
   - The flanking ridges act as structural columns that reduce the unbraced front wall span around the center latch from $80\text{ mm}$ down to $22.6\text{ mm}$ (~45× reduction in wall flex).
2. **Loose-Fit Gravity Drop-In Cards:**
   - Divider cards were resized to **$33.00\text{ mm}$ width** (down from $33.30\text{ mm}$).
   - With channel bottoms spanning $34.10\text{ mm}$ ($X \in [-16.20, +17.90\text{ mm}]$), the card has **$+1.10\text{ mm}$ of total lateral float clearance**.
   - It drops completely by gravity with zero wall contact, while retaining $\ge 0.75\text{ mm}$ of positive overlap past the channel lips (impossible to slip out).
3. **Reinforced $0.85\text{ mm}$ Closure Clasp:**
   - Lid clasp tab updated to $1.25\text{ mm}$ thickness with hook apex reaching $X = 17.30\text{ mm}$.
   - Body catch tab deepened to $0.85\text{ mm}$ undercut ($X = 16.45\text{ mm}$).
   - Delivers crisp, positive snap retention in both divided and undivided configurations.

## 3. Files and Artifacts

- `Cassettes/glass_slide_cassette_40x80/generate_cassette.py`
- `Cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8_divided.stl`
- `Cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8.stl`
- `Cassettes/glass_slide_cassette_40x80/build/cassette_lid_v0_8_print.stl`
- `Cassettes/glass_slide_cassette_40x80/build/divider_card_1_2mm.stl`

## 4. Validation Evidence

- **STL Audits:** 100% pass across all STLs (0 boundary edges, 0 non-manifold edges, 0 degenerate triangles).
- **Physical Validation:** Printed in PETG (0.20 mm layers, 4 perimeters); verified loose gravity drop-in, zero outward wall deflection, and solid latch retention under handling and rollover.

## 5. Next Steps

Execution proceeds immediately to **Plan 011** to develop top-surface pinch grips on the lid for zero-gap cassette extraction from high-density carrier trays.
