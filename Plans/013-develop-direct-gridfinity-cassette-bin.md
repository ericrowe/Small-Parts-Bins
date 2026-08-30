# Plan 013 — Develop direct 1x2 7U Gridfinity cassette bin

- Status: In Work
- Depends on: Baseline glass slide capture, hinge, and closure latch mechanics
- Created: 2026-08-29
- Started: 2026-08-29
- Completed: Not completed
- Git start: `7e03e71`
- Git completion: Not completed

## Outcome

Develop a standalone $1 \times 2$ Gridfinity-compatible cassette bin (7U height) that sits directly on standard Gridfinity baseplates and accepts standard Gridfinity bins stacked directly on top of its lid, while retaining the replaceable glass microscope slide window, positive slide capture, peaked filament hinge, and positive closure latch.

## Requirements

### 1. Gridfinity Dimensional Architecture
- **Footprint:** Standard $1 \times 2$ Gridfinity envelope ($42.0 \times 84.0\text{ mm}$ nominal pitch, $41.5 \times 83.5\text{ mm}$ outside perimeter, $3.75\text{--}4.0\text{ mm}$ corner radius).
- **Base Interface:** Standard $1 \times 2$ Gridfinity base with two $42\text{ mm}$ base cells centered at $(0, \pm 21.0\text{ mm})$ ($35.6 \to 37.2 \to 41.5\text{ mm}$ profile, $4.75\text{ mm}$ base height, solid floor at $Z = 6.00\text{--}6.75\text{ mm}$).
- **Height Standard (7U):**
  - Engaged stacking shelf plane at $7\text{U} = \mathbf{49.00\text{ mm}}$.
  - Standard Gridfinity stacking lip ($+4.40\text{ mm}$ above shelf plane) integrated directly into the lid top.
  - Total overall height: $\mathbf{53.40\text{ mm}}$.
  - 2-high bin stack = $49.00 + 53.40 = \mathbf{102.40\text{ mm}}$, fitting the measured $111.125\text{ mm}$ drawer with $+8.725\text{ mm}$ clearance.

### 2. Lid with Gridfinity Stacking Rim
- Integrate standard $1 \times 2$ Gridfinity stacking lip ($+4.40\text{ mm}$ height, $41.5 \times 83.5\text{ mm}$ outer, $37.2 \times 79.2\text{ mm}$ throat) into the lid.
- Retain the positive glass slide loading channel ($27.0 \times 1.4\text{ mm}$) and $1.20\text{ mm}$ reinforced compliant PETG capture clip.
- Symmetrical solid $34.0 \times 10.0\text{ mm}$ flat label zones on both ends for 9 mm Brother TZe tape.
- Centered $23.0 \times 55.0\text{ mm}$ clear microscope slide glass viewing aperture.

### 3. Body Architecture
- $1 \times 2$ Gridfinity base with continuous walls.
- Internal usable cavity: $36.5 \times 78.5 \times 42.0\text{ mm}$ deep (massive hardware capacity!).
- Integrated removable divider card channels at thirds stations.
- No pull tab or dovetail boss (bin sits directly in baseplates and stacks bin-on-bin).
- Peaked 3-knuckle filament hinge on one long side and reinforced $0.85\text{ mm}$ closure catch on opposite long side.

### 4. 3D Printability
- Body prints upright in PETG or ASA with zero internal supports.
- Lid prints top/stacking-rim down directly on build plate in PETG without supports.
- All exported STLs must pass mesh audit with 0 boundary edges and 0 non-manifold edges.

## Non-goals

- Do not alter the standard Gridfinity base or stacking lip profiles.
- Do not require carrier trays (this is a direct standalone Gridfinity bin).
- Do not change standard glass microscope slide dimensions ($75 \times 25 \times 1.1\text{--}1.2\text{ mm}$).

## Implementation steps

1. [ ] **Parametric CAD Generator:** Write `Cassettes/gridfinity_cassette_1x2_7u/generate_gridfinity_cassette.py`.
2. [ ] **Base & Body Modeling:** Implement $1 \times 2$ Gridfinity base feet, cavity walls, divider slots, hinge knuckle, and inward closure catch.
3. [ ] **Stacking Lid Modeling:** Implement $1 \times 2$ Gridfinity stacking lip, glass channel, compliant clip, and symmetrical label zones.
4. [ ] **Mesh Audit & STL Export:** Audit all exported meshes for 0 boundary edges and 0 non-manifold edges.
5. [ ] **CAD Multi-Views & Documentation:** Render 3D multi-views and write `Cassettes/gridfinity_cassette_1x2_7u/README.md`.
6. [ ] **Physical Validation:** Print test body, lid, and divider cards in PETG; verify baseplate fit, lid closure, glass retention, and 2-high bin stacking in drawer.
7. [ ] **Plan Archive:** Archive Plan 013 upon physical validation.

## Acceptance criteria

- [ ] Body base fits cleanly into standard Gridfinity baseplates.
- [ ] Another standard $1 \times 2$ (or two $1 \times 1$) Gridfinity bin stacks securely onto the closed lid.
- [ ] Lid swings through $\ge 120^\circ$ and latches securely.
- [ ] Standard $75 \times 25\text{ mm}$ glass slide slides into channel and is positively retained.
- [ ] 2-high stack measures $\le 102.5\text{ mm}$ and fits in $111.125\text{ mm}$ drawer.
- [ ] All STLs pass mesh audit (0 boundary / 0 non-manifold).
