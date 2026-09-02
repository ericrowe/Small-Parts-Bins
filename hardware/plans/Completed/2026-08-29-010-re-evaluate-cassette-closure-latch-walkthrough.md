# Walkthrough — Plan 010: Re-evaluate Cassette Closure Latch & Divider Retention

- Date: 2026-08-29
- Plans resolved: Plan 010 (Completed)
- Baseline Release: `Cassettes/glass_slide_cassette_40x80/`
- Git commits: `0643d9d` .. `a08792d`

## 1. Problem Definition & Root Cause

During physical validation of Plan 003 (Optional Cassette Dividers) and Plan 004, physical testing revealed that inserting divider cards created slight outward lateral deflection on the front (latch-side) body wall along the $80\text{ mm}$ unsupported span. This reduced the $0.65\text{ mm}$ clasp undercut overlap enough that the closure latch failed to hold closed. Additionally, removing thin PETG lids from high-adhesion PEI build plates caused occasional tearing at the compliant glass retention clip root.

---

## 2. Solutions Implemented & Physically Verified

1. **Internal Flanking Ridges ($+0.80\text{ mm}$ Inward Projection):**
   * Placed vertical reinforcing ridges along the front body wall flanking each divider station ($Y = \pm 12.87\text{ mm}$).
   * Creates deep $1.40\text{–}1.60\text{ mm}$ guide channels and braces the front wall span down from $80\text{ mm}$ to $22.6\text{ mm}$ around the center latch.
2. **Loose-Fit Gravity Drop-In Dividers ($33.00\text{ mm}$):**
   * Sized divider cards to $33.00\text{ mm}$ width across the $34.10\text{ mm}$ channel bottom span ($+1.10\text{ mm}$ lateral clearance), completely eliminating transverse wedging force against the walls.
3. **Reinforced Closure Clasp ($0.85\text{ mm}$ Undercut Catch):**
   * Thickened cantilever clasp beam to $1.25\text{ mm}$ with $0.85\text{ mm}$ undercut catch on the front body wall. Snaps crisply and holds firmly closed in both divided and undivided configurations.
4. **Reinforced Compliant Glass Clip ($1.20\text{ mm}$ / 6 Solid Layers):**
   * Strengthened compliant tongue and lid top plate to $1.20\text{ mm}$ / $3.60\text{ mm}$ with $2.5\text{ mm}$ 3D root gussets (+125% stronger), completely eliminating bed-peeling tear failures while preserving $+1.10\text{ mm}$ of clear air below upper carrier tray feet.

---

## 3. Physical Validation Results

* **Dividers:** $33.00\text{ mm}$ cards drop in cleanly by gravity with zero wall friction.
* **Latch Snap:** Crisp, tactile snap; holds firmly closed under full carrier rollover and vigorous agitation.
* **Bed Adhesion:** Lids release cleanly from textured PEI build plates without clip deformation or root tearing.
