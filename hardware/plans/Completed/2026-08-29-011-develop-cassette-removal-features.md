# Plan 011 — Develop cassette features to aid removal from carrier

- Status: Completed
- Depends on: Plans 001–003, 009, and 010 completed
- Created: 2026-08-29
- Started: 2026-08-29
- Completed: 2026-08-29
- Git start: `d3ba095`
- Git completion: `3e2091f`

## Outcome

Develop and evaluate cassette and carrier features to solve the problem of extracting individual
cassettes from closely packed Gridfinity carrier trays (3 × 4 layout with 0.4 mm inter-cassette gaps),
enabling human fingers to easily and reliably grasp and remove any loaded cassette directly from above
while the carrier remains inside an open drawer.

## Problem Statement & Exploratory Scope

In tightly packed $3 \times 4$ carrier arrays with minimal ($0.4\text{ mm}$) inter-cassette spacing:
* Smooth-sided cassettes leave insufficient purchase room for fingers to lift them vertically.
* Shallow tilt/rocker mechanisms do not elevate the cassette enough above adjacent bins.
* Outer tray scallops weaken carrier wall integrity under heavy hardware loads and require removing the tray from the drawer.

This plan encompasses designing, testing, and selecting effective extraction solutions—such as body-anchored vertical pull tabs, finger purchase contours, push-assist aids, or lid clearance features—to provide effortless tool-free removal from above.

## Requirements

- Enable effortless two-finger vertical extraction directly from above without tools and without prying against the glass.
- Provide a robust anchor mechanism:
  - Utilize a $15.0\text{ mm}$ vertical dovetail keyway integrated into the front/right body wall ($X \in [14.80, 17.80\text{ mm}]$, $Y \in [15.00, 28.00\text{ mm}]$).
  - Add a clean clearance notch in the lid's front perimeter skirt ($Y \in [14.00, 29.00\text{ mm}]$) leaving $\ge 0.5\text{ mm}$ solid plastic between the glass channel and the cutout.
  - Sized pull tab (`pull_tab_v0_8.stl`) with $15.0\text{ mm}$ vertical dovetail shank and $+4.0\text{ mm}$ raised contoured grip fin with concave finger purchase scoops.
- Maintain support-free FDM 3D printing for all parts (lid prints top-face down directly on bed; pull tab prints flat on its back face in PETG in ~1 minute).
- Stacking clearance: Ensure all removal features remain strictly below the upper carrier tray's central inter-foot clearance valley ($Z \le 40.50\text{ mm}$, providing $\ge +1.80\text{ mm}$ of clear vertical air below upper carrier trays).
- Preserve backwards compatibility and modularity: pull tab is modular and optional per box.

## Non-goals

- Do not alter the 14U carrier tray external walls, base feet, or stacking interface.
- Do not reduce carrier wall thickness or add cutouts that weaken carrier load capacity.
- Do not alter the glass microscope slide dimensions ($75 \times 25 \times 1.1\text{–}1.2\text{ mm}$) or positive slide retention mechanism.

## Implementation steps

1. [x] **Problem Exploration & Mechanism Prototyping:** Evaluated top pinch flutes, push-to-tilt rocker inserts, and lid-mounted tabs; established requirement for robust body-anchored vertical extraction feature.
2. [x] **Body Dovetail Keyway Integration:** Added monolithic reinforced $13.0\text{ mm}$ boss column with $2.5\text{ mm}$ solid sidewalls, $1.5\text{ mm}$ outer back wall, and $45^\circ$ under-shelf lead-in taper into `build_divided_body()` and `build_body()`.
3. [x] **Lid Clearance Cutaway & Solid Roof Restoration:** Added $15.0\text{ mm}$ wide full-depth through-notch ($Y \in [14.00, 29.00\text{ mm}]$) in `build_lid_local()` allowing generous sloppy clearance around the pull tab while preserving the solid flat rear label roof.
4. [x] **Pull Tab Generator (`pull_tab_v0_8.stl`):** Modeled vertical shank male dovetail and ergonomic grip head in `build_pull_tab()`, printable flat on back face.
5. [x] **Tolerance Fit Ladder Calibration:** Generated progressive fit variants (`_fit_0_20`, `_fit_0_15`, `_fit_0_10`, `_fit_0_05`).
6. [x] **Physical Validation:** Sliced and printed in PETG. The $+0.10\text{ mm}$ fit variant (`pull_tab_v0_8_fit_0_10.stl`) seated firmly against the bottom stop, eliminated wobble, and the lid closed and latched cleanly without interference. Set $+0.10\text{ mm}$ as production baseline standard.
7. [x] **Export & Mesh Audit:** Verified all STLs for 0 boundary edges and 0 non-manifold edges.
8. [x] **CAD Multi-Views & Documentation:** Rendered multi-view sheets and updated `README.md` and `AGENTS.md`.
9. [x] **Plan Archive:** Archived Plan 011 with comprehensive walkthrough narrative.

## Acceptance criteria

- [x] Pull tab slides firmly down into the body wall dovetail keyway and seats against the bottom stop.
- [x] Lid closes completely and latches without binding against the pull tab.
- [x] Pull tab allows effortless vertical finger extraction from a fully packed carrier tray.
- [x] Closed assembly with pull tab fits under stacked upper carrier trays with $\ge +1.50\text{ mm}$ clearance.
- [x] All exported binary STLs pass mesh audit (0 boundary edges, 0 non-manifold edges).

## Validation record

- **Physical Finding (2026-08-29):** The $+0.10\text{ mm}$ fit clearance variant (`pull_tab_v0_8_fit_0_10.stl`, $7.80\text{ mm}$ base, $5.80\text{ mm}$ neck, $2.80\text{ mm}$ thickness) was physically printed and tested by the user. Confirmed: "10 worked, and the cover closes now."
- **Lid Cutout Finding (2026-08-29):** The enlarged $15.00\text{ mm}$ through-notch allows the lid to swing freely through 120° and positively latch without touching or deflecting against the installed pull tab.
