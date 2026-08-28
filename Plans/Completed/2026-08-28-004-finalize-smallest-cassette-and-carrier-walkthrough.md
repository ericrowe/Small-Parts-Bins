# Plan 004 Walkthrough — Finalize the Smallest Cassette and Six-Cassette Carrier

- Completed: 2026-08-28
- Archived plan: `2026-08-28-004-finalize-smallest-cassette-and-carrier.md`
- Git range: `main..main`

## 1. Objective and Scope

Plan 004 aimed to consolidate the verified carrier (Plan 001), height-optimized cassette body (Plan 002), removable divider system (Plan 003), and positive glass capture (Plan 009) into a production release candidate for the smallest $40 \times 80\text{ mm}$ cassette family member and its 6-cassette $3 \times 4$ carrier tray.

## 2. Boundary Condition & Physical Failure Mode

During physical testing of the integrated v0.8 divided body and divider cards:
1. **Front-Wall Deflection:** Inserting the baseline $1.20\text{ mm}$ divider cards into the $1.40\text{ mm}$ side-wall slots creates outward deflection on the front (latch-side) long wall of the cassette body.
2. **Latch Disengagement:** The v0.7/v0.8 closure clasp features a $1.20\text{ mm}$ thick cantilever beam on the lid that engages a central $0.65\text{ mm}$ undercut catch on the front body wall ($Y \in [-4.0, +4.0\text{ mm}]$). The outward deflection of the front wall under divider insertion reduces or eliminates this $0.65\text{ mm}$ engagement overlap, causing the latch to fail to remain positively closed.

## 3. Plan Closeout and Transition

Per the stop and rollback criteria defined in Plan 004, production candidate finalization cannot proceed while a critical containment interface (the closure latch) fails under valid operational conditions (divider installation).

Plan 004 is therefore closed, and a dedicated, focused engineering ticket—**Plan 010: Re-evaluate Cassette Closure Latch**—has been created and queued at **Priority 1** to redesign the latch and front-wall interface.

## 4. Reusable Parts & Stable Baseline

- **3 × 4 × 7U Carrier Trays:** Fully verified and physically stable (Plan 001).
- **v0.8 Envelope & Internal Cavity:** $39.55 \times 80.0 \times 36.0\text{ mm}$ closed envelope, $30.8\text{ mm}$ depth (Plan 002).
- **Thickened Hinge Wall & Divider Channels:** $4.30\text{ mm}$ left wall with $+0.65\text{ mm}$ knuckle clearance and $1.40\text{ mm}$ slot channels (Plan 003).
- **Glass Capture & Hinge:** $27.0 \times 1.4\text{ mm}$ end-loaded glass channel, $6.75\text{ mm}$ PETG slide tongue, and support-free 3-knuckle filament hinge (Plan 009).

## 5. Next Steps

Execution proceeds immediately to **Plan 010** to investigate and resolve the latch engagement failure across divided and undivided configurations via rapid tolerance and geometry coupons before resuming the production release freeze.
