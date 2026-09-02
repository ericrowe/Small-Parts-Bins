# Plan 003 Walkthrough — Develop Optional Cassette Dividers

## 1. Objective and Scope

Plan 003 developed a removable divider system for the height-optimized **v0.8** cassette ($36.0\text{ mm}$ closed height). The goal was to provide optional multi-compartment storage (dividing the cassette into 3 equal compartments) with positive floor and side-wall retention to prevent part transfer during rollover, while keeping the cavity smooth and unobstructed when dividers are omitted.

## 2. Locating Concept & Fit Coupon Validation

1. **Locating Architecture:**
   - Rather than protruding internal ribs that consume volume when undivided, Plan 003 uses **$0.60\text{ mm}$ recessed side-wall channels** and a continuous **$0.60\text{ mm}$ floor groove**.
   - A dedicated 4-station tolerance coupon (`Cassettes/divider_fit_coupon_v0_1/`) evaluated slot widths from $1.30\text{ mm}$ to $1.60\text{ mm}$ against a baseline $1.20\text{ mm}$ divider card.
2. **Coupon Physical Result:**
   - **Station 2 ($1.40\text{ mm}$ slot width, $+0.20\text{ mm}$ clearance)** was physically selected for its smooth tactile slide, secure seating, and absence of binding.

## 3. Full-Size Body Engineering & Hinge/Clasp Clearance

When translating the coupon interface to the full $80.0\text{ mm}$ body span, two physical geometric interferences were resolved:

1. **Straight-Line Vertical Drop-In (Hinge Knuckle Clearance):**
   - The body's peaked hinge knuckle on the left rim extends inward to $X = -16.15\text{ mm}$.
   - To provide a 100% straight vertical drop-in path without requiring the user to angle or tilt the card, the inner left wall was thickened to **$4.30\text{ mm}$** (inner face at $X = -15.00\text{ mm}$, slot recess to $X = -15.60\text{ mm}$).
   - The divider card's left edge ($X = -15.50\text{ mm}$) has **$+0.65\text{ mm}$ of clear vertical air** past the hinge knuckle, while the increased wall thickness eliminates long-wall flex.
2. **Closure Clasp Integrity & Station Layout:**
   - The central closure catch on the right wall spans $Y \in [-4.00, +4.00\text{ mm}]$.
   - Testing showed that a center slot crowded the clasp and was redundant with the two thirds stations.
   - The center slot was omitted, leaving the closure catch 100% solid and continuous. Two stations at **$Y = \pm 12.87\text{ mm}$** create three equal **$24.53\text{ mm}$** compartments.

## 4. Final Standard Specifications

- **Cassette Body Envelope:** $38.60 \times 80.00 \times 32.80\text{ mm}$ ($36.0\text{ mm}$ closed height).
- **Usable Cavity:** $32.30\text{ mm}$ width $\times 76.00\text{ mm}$ length $\times 30.80\text{ mm}$ depth.
- **Divider Stations:** $Y = \pm 12.87\text{ mm}$ (3 equal $24.53\text{ mm}$ compartments).
- **Slot Geometry:** $1.40\text{ mm}$ slot width, $0.60\text{ mm}$ wall recess, $0.60\text{ mm}$ floor groove.
- **Divider Card:** $33.30 \times 31.20 \times 1.20\text{ mm}$ with top finger notch ($10 \times 1.5\text{ mm}$) and $0.6\text{ mm}$ bottom corner lead-ins ($0.20\text{ mm}$ lid clearance).
- **STL Audits:**
  - `cassette_body_v0_8_divided.stl`: 476 triangles, **0 boundary / 0 non-manifold edges**.
  - `divider_card_full_1_2mm.stl`: 48 triangles, **0 boundary / 0 non-manifold edges**.

## 5. Physical Validation & Status

The full-size divided body and divider cards were 3D printed in PETG and physically verified: straight drop-in insertion, positive retention, and smooth lid closure were confirmed. Plan 003 is complete and ready for integration into the production candidate release in **Plan 004**.
