# Plan 011 — Develop cassette extraction pull tabs

- Status: In Work
- Depends on: Plans 001–003, 009, and 010 completed
- Created: 2026-08-29
- Started: 2026-08-29
- Completed: Not completed
- Git start: `d3ba095`
- Git completion: Not completed

## Outcome

Develop an ergonomic, reliable extraction feature for individual cassettes in closely packed
Gridfinity carrier trays (3 × 4 layout with 0.4 mm inter-cassette gaps), enabling human fingers
to easily grasp and extract any loaded cassette directly from above while the carrier remains
inside an open drawer.

## Requirements

- Enable effortless two-finger vertical extraction directly from above without tools and without prying against the glass.
- Provide a robust anchor mechanism:
  - Utilize a $15.0\text{ mm}$ vertical dovetail keyway integrated into the front/right body wall ($X \in [16.00, 19.30\text{ mm}]$, $Y \in [17.50, 25.50\text{ mm}]$).
  - Add a clean clearance notch in the lid's front perimeter skirt ($Y \in [17.00, 26.00\text{ mm}]$) leaving $\ge 2.0\text{ mm}$ solid plastic between the glass channel and the cutout.
  - Sized pull tab (`pull_tab_v0_8.stl`) with $15.0\text{ mm}$ vertical dovetail shank and $+4.0\text{ mm}$ raised contoured grip fin with concave finger purchase scoops.
- Maintain support-free FDM 3D printing for all parts (lid prints top-face down directly on bed; pull tab prints flat on its side in PETG in ~2 minutes).
- Stacking clearance: Ensure the pull tab apex remains strictly below the upper carrier tray's central inter-foot clearance valley ($Z \le 40.50\text{ mm}$, providing $\ge +1.80\text{ mm}$ of clear vertical air below upper carrier trays).
- Preserve backwards compatibility and modularity: pull tab is modular and optional per box.

## Non-goals

- Do not alter the 14U carrier tray external walls, base feet, or stacking interface.
- Do not reduce carrier wall thickness or add cutouts that weaken carrier load capacity.
- Do not alter the glass microscope slide dimensions ($75 \times 25 \times 1.1\text{–}1.2\text{ mm}$) or positive slide retention mechanism.

## Implementation steps

1. [x] **Ergonomic Concept Prototyping:** Evaluated top pinch flutes and push-to-tilt rocker inserts; established requirement for direct vertical pull tab with body dovetail anchor.
2. [ ] **Body Dovetail Keyway Update:** Add $15.0\text{ mm}$ vertical dovetail keyway into the front wall of `build_divided_body()` and `build_body()`.
3. [ ] **Lid Clearance Cutaway & Solid Roof Restoration:** Add matching clearance notch to front skirt in `build_lid_local()` and restore solid flat rear roof for label.
4. [ ] **Pull Tab Generator (`pull_tab_v0_8.stl`):** Model vertical shank male dovetail and ergonomic grip head in `build_pull_tab()`.
5. [ ] **Export & Mesh Audit:** Generate and audit all STLs for 0 boundary edges and 0 non-manifold edges.
6. [ ] **CAD Multi-Views & Documentation:** Render updated multi-views and update README.
7. [ ] **Physical Validation:** Print test body, lid, and pull tab in PETG; verify slide fit, lock, lid clearance, and vertical extraction from carrier.
8. [ ] **Plan Archive:** Archive Plan 011 upon physical validation.

## Acceptance criteria

- [ ] Pull tab slides firmly down into the body wall dovetail keyway and seats against the bottom stop.
- [ ] Lid closes completely and latches without binding against the pull tab.
- [ ] Pull tab allows effortless vertical finger extraction from a fully packed carrier tray.
- [ ] Closed assembly with pull tab fits under stacked upper carrier trays with $\ge +1.50\text{ mm}$ clearance.
- [ ] All exported binary STLs pass mesh audit (0 boundary edges, 0 non-manifold edges).
