# Gridfinity Glass-Window Cassette System

## Purpose

Design a durable, modular small-parts storage system for screws, nuts, bolts,
and similar hardware. Open Gridfinity bins spill when knocked over, so this
system uses individually closed and labeled cassettes held in stackable,
Gridfinity-compatible carrier trays. The contents and approximate stock level
must remain visible through a replaceable glass window.

Treat the physical-print feedback and measured parts recorded below as binding.
Do not substitute generic Gridfinity assumptions or visually plausible hinge
geometry for checked dimensions and exported-STL validation.

## System Architecture

- The system has two levels:
  1. A Gridfinity-compatible carrier tray that locates a set of cassettes.
  2. Independently closed, removable cassettes in several modular sizes.
- Carrier trays must be stackable while loaded.
- Cassette lids, glass, hinges, latches, labels, and pull features must remain
  below or clear of the carrier's stacking engagement plane.
- Cassettes must remain individually closed when removed or when a carrier is
  knocked over. The tray organizes them; the cassette closure prevents spills.
- Labels and windows must remain visible from above when the drawer is open.
- Prefer fewer than 10 cassettes per carrier when practical. Carriers holding
  20 or more are acceptable when packing or part size makes that useful.
- The current reference carrier holds six smallest-size cassettes.

## Drawer Constraint

- Measured inside drawer height: **4 3/8 in = 111.125 mm**.
- Treat 111.125 mm as an absolute measured ceiling, not a target part height.
- Reserve practical clearance for drawer variation, insertion, removal, tray
  stacking, labels, and print tolerances before choosing a maximum stack height.

## Gridfinity Carrier Constraints

- Base all carrier footprints on the standard **42 mm Gridfinity pitch**.
- The 42 mm pitch is not usable internal space. Account for carrier walls,
  clearances, dividers, corner geometry, and the stacking lip.
- Use **2.0 mm minimum printed walls** for carrier trays unless a tested design
  justifies something thicker. Do not reduce them to force a packing result.
- Calculate cassette packing against the narrowest stacking-lip throat, not
  against `42N` or the carrier's maximum outside dimensions.
- Preserve the standard Gridfinity base and stacking interface unless the user
  explicitly approves a deviation.
- Working Gridfinity envelopes used in this project:

  | Carrier | Approx. outside | Approx. narrowest lip throat |
  |---|---:|---:|
  | 2 × 3 | 83.5 × 125.5 mm | 78.3 × 120.3 mm |
  | 3 × 4 | 125.5 × 167.5 mm | 120.3 × 162.3 mm |

- Treat those throat values as current design envelopes. Recheck them against
  the selected authoritative Gridfinity profile before releasing a final tray.
- Current reference layout: a **3 × 4 Gridfinity carrier** containing six
  smallest cassettes in a 3-across × 2-deep arrangement.
- Six current cassette envelopes with 0.4 mm gaps occupy approximately
  **119.45 × 160.4 mm**, fitting the working 120.3 × 162.3 mm throat.
- Provide enough clearance for real prints to insert and remove without binding.
  Do not treat a zero-clearance CAD packing result as acceptable.
- Carrier design must allow fingertip access or another simple removal feature
  without loading or prying against the glass.

### Physically Verified 14U Carrier Architecture

- The vertical-layout architecture uses two identical **3 × 4 × 7U** carriers,
  stacked for a 14U engaged height.
- Total modeled stack height, including the exposed top lip: **102.4 mm**.
  Nominal clearance below the measured 111.125 mm drawer ceiling: **8.725 mm**.
- **Physically Verified (2026-08-28):** Both 7U carrier trays have been printed in PETG,
  installed into existing Gridfinity baseplates in the target drawer, and tested for
  stacking and clearance. The 14U stack fits with ample clearance and stable engagement
  ([Plan 001](Plans/Completed/2026-08-28-001-validate-14u-carrier-stack.md)).
- Each carrier holds six modular cassettes in the reference 3 × 2 layout.
- The cassette support floor is at Z = 6.75 mm and the stacking engagement shelf is at
  Z = 49.0 mm.
- **Upper Tray Foot Clearance Constraint:** The upper tray's $3 \times 4$ array of Gridfinity
  feet extends $4.75\text{ mm}$ downward below the Z = 49.0 mm lip shelf into the lower tray's
  internal cavity (lowest upper foot surface sits at $Z = 44.25\text{ mm}$).
- Total usable height inside a loaded lower carrier: $44.25 - 6.75 = \mathbf{37.50\text{ mm}}$.
- Standard carrier release: `Carriers/carrier_3x4_14u_test/` version 0.1.

## Modular Cassette Family

- The smallest v0.7 cassette is the current **1 × 1 cassette module** for
  family planning; it is not one 42 mm Gridfinity cell.
- Develop multiple cassette sizes for different part volumes.
- Larger cassettes must occupy integer multiples of a consistent cassette
  sub-grid so different sizes can be mixed in one compatible carrier.
- Preserve the current smallest-cassette packing as the provisional sub-grid:
  39.55 × 80.0 mm closed envelope with nominal 0.4 mm inter-cassette gaps.
- Do not freeze larger external dimensions until carrier clearance and physical
  prints establish the final sub-grid pitch.
- Larger cassettes may use one or multiple standard microscope-slide window
  modules. Keep window replacement, labeling, hinge access, and stacking
  clearance consistent across the family.
- Optimize carrier footprint and cassette combinations together. Do not enlarge
  a cassette merely to align it with one 42 mm Gridfinity cell.

## Canonical Smallest Cassette: v0.7 Baseline & v0.8 Height Optimization

The physically verified baseline height is **v0.7** ($28.0\text{ mm}$ closed height).
The physically verified height-optimized standard (**Plan 002**) is **v0.8** ($36.0\text{ mm}$ closed height),
which expands usable cavity depth by +35.1% while maintaining $1.50\text{ mm}$ clearance below
the upper carrier tray's Gridfinity feet ($Z = 44.25\text{ mm}$, lowest foot surface).

| Feature | v0.7 Baseline | v0.8 Optimized Height |
|---|---:|---:|
| Nominal body | 38.6 × 80.0 × 24.8 mm | 38.6 × 80.0 × 32.8 mm |
| Maximum closed envelope, including hinge | 39.55 × 80.0 × 28.0 mm | 39.55 × 80.0 × 36.0 mm |
| Body wall and floor | 2.0 mm | 2.0 mm |
| Internal cavity before hinge/latch intrusion | 34.6 × 76.0 × 22.8 mm | 34.6 × 76.0 × 30.8 mm |
| Glass pocket / channel | 27.0 × 76.8 × 1.4 mm clear | 27.0 × 76.8 × 1.4 mm clear |
| Maximum intended measured slide | 26.3 × 76.3 × 1.2 mm | 26.3 × 76.3 × 1.2 mm |
| Visible window | 23.0 × 58.5 mm | 23.0 × 58.5 mm |
| Solid label zone | 34.0 × 10.0 mm | 34.0 × 10.0 mm |
| Stacking clearance below upper tray feet ($Z = 44.25$) | +9.50 mm | +1.50 mm |

- The hinge runs along one long side and the positive latch is on the opposite
  long side.
- The lid is 100% interchangeable between v0.7 and v0.8: the 3.20 mm lid top plate,
  27.0 × 1.4 mm end-loaded glass channel, 6.75 mm compliant PETG latch, and peaked
  3-knuckle filament hinge are identical.
- The lid has a centered fingernail opening relief at the latch edge:
  approximately 14.0 mm wide × 1.3 mm deep × 1.4 mm high.
- Preserve approximately 1.8 mm of roof above the fingernail relief and at
  least the current 0.95 mm relief-to-latch clearance.

## Glass Window and Label

- Baseline window material: low-cost, plain, clear, non-frosted microscope
  slide glass. Do not switch back to acrylic without explicit approval.
- Prefer standard slides near **75 × 25 mm and 1.1–1.2 mm thick**, ideally with
  ground or polished edges. Standard 76 × 26 mm or 3 × 1 in slides may vary;
  measure the delivered batch before relying on nominal dimensions.
- Never design the glass as a press fit and never instruct the user to force a
  slide. Enclose and support all edges. Reject chipped or oversize glass.
- Avoid 2 mm slides; the current lid is designed for no more than 1.2 mm glass.
- The pane is end-loaded into continuous rails and positively blocked by an
  integral PETG compliant shoulder. The shoulder returns behind the pane end; it
  does not remain pressed against the glass face. The pane is fixed in the lid;
  it is not the moving lid.
- Optional clear polyester safety film may be applied to the parts-facing side
  to retain fragments while leaving the exposed top surface as scratch-resistant
  glass. Trim film so it does not change the fit.
- Provide a flat solid area for **9 mm Brother TZe label tape**. The current
  smallest lid provides a 34 × 10 mm label zone.

## Hinge: Required v0.6 Geometry Retained in v0.7

- The hinge is an original three-knuckle removable-pin design, not a copied or
  published tested hinge. Say so when provenance matters.
- Use a straight piece of nominal **1.75 mm printer filament**, approximately
  75 mm long, as the removable pin.
- The body uses the long center knuckle; the lid uses the two end knuckles.
- Use the support-free peaked outside profile and teardrop/45-degree bore roof.
  Do not return to a long horizontal circular tube.
- Print the body upright and the lid top/label-face down in the supplied STL
  orientations.
- Current nominal bore cores:
  - Body knuckle: **2.25 mm diameter**.
  - Lid knuckles: **2.10 mm diameter**.
- Current modeled minimum radial clearance around 1.75 mm filament:
  - Body: approximately 0.242 mm.
  - Lid: approximately 0.168 mm.
- Preserve 0.15 mm attachment-to-bore clearance at the body support and lid
  rail, 0.8 mm axial gap between alternating knuckles, and the current 0.25 mm
  radial clearance to mating reliefs.
- Use the current 2.45 mm rotational keep-out and validate opening through at
  least 120 degrees.
- Each v0.7 lid knuckle requires the v0.6 continuous, bed-supported root:
  - Root begins at print Z = 0 and remains solid for the first 1.8 mm.
  - First knuckle material begins at approximately print Z = 0.55 mm.
  - Root extends 0.20 mm past the hinge axis.
  - Root overlaps each knuckle end by 0.10 mm along the pin axis.
  - Root remains 0.15 mm clear of the lid bore and full-height body end wall.
  - Root remains approximately 0.70 mm clear of the body center knuckle axially.
  - Validate root/body collision clearance over a 0–120 degree sweep.
- Do not use internal hinge support. Correct printability in the model.
- If a lid bore alone prints slightly tight, a 2.0 mm drill may be turned gently
  by hand. Do not power-drill printed knuckles.

## Pane Capture

- Current v0.7 integration geometry:
  - 27.0 mm loading channel and 1.4 mm clear height.
  - 23.0 mm top/visible opening and 24.0 mm opposite opening.
  - 0.95/0.45 mm overlap per side on the measured 24.9 mm glass.
  - 0.70 mm axial clearance for a 76.3 mm pane.
  - Integral PETG tongue: 8.0 mm wide × 0.8 mm thick (4 layers) × 6.75 mm free length with 45° root gussets and 1.05 mm root embed.
  - Entry opening cutout: 0.50 mm tight perimeter outline matching the finger pad, tongue, and gussets.
  - Reinforced clasp: 1.20 mm thick cantilever beam on lid with 0.65 mm undercut catch on body wall.
  - Split-line alignment: body rim at standard Z = 24.80 mm; lid outer perimeter skirts extend to local Z = 0.00 mm with concentric hinge knuckle alignment along X = -18.20 mm, Z = 25.00 mm.
  - Relaxed tongue face sits flush at channel ceiling (0.2–0.3 mm clearance over 1.1–1.2 mm glass).
- Print the lid top/label-face down without internal support. Manually depress
  the tongue during pane insertion/removal; never use the glass to cam it aside.
- **Physical validation:** The complete v0.7 lid was printed in PETG and physically
  verified: glass retention, hinge operation, and closure clasp meet all design parameters.
  Plan 009 is complete.

Legacy v0.6 snap-retainer evidence:

- Use a replaceable underside retainer with four chamfered lugs engaging a
  positive 0.35 mm-deep groove in the lid pocket wall.
- The installed glass is the retainer's upper stop. Judge final retention with
  the correct glass installed, not with an empty lid.
- Preserve the retainer fit ladder:

  | Variant | Lug projection per side | Nominal seated state |
  |---|---:|---:|
  | Existing firm | 0.30 mm | 0.05 mm groove clearance |
  | Firm+ | 0.35 mm | Fills groove, no preload |
  | Firmer | 0.40 mm | 0.05 mm preload |
  | Firmest | 0.45 mm | 0.10 mm preload; **best physical fit** |

- **Best v0.6 ladder fit: Firmest 0.45.** It worked best in the initial physical
  fit comparison, but subsequent handling shows that the glass can still be
  knocked out easily. Treat it as experimental and inadequate for production
  containment, not as a verified final capture method.
- Plan 009 has priority immediately after the active carrier test. It must
  investigate positive pane capture, including an end-loaded slide with a
  removable mechanical end stop, and test both glass and transparent plastic
  pane options of different measured thicknesses.
- Plan 009 v0.1 fit coupons physically selected the smallest tested variants:
  a 2.05 mm transverse bore works with the intended 1.75 mm filament pin, and a
  1.4 mm clear pane channel works and meets the reported requirements. Carry
  those exact fits into the next mechanics coupon. The print material/settings
  and measured pane dimensions were not reported, and the end gate, knockout
  retention, alternate panes, and final lid remain unverified.
- The glass used in the Plan 009 v0.2 frame is 24.9 mm wide. It fell through the
  25.1 mm capture opening, confirming inadequate lateral overlap. Preserve the
  27.0 mm loading channel for wider alternate slides while testing a provisional
  23.0 mm capture opening: 0.95 mm overlap per side on the measured pane and
  1.65 mm per side at the current 26.3 mm maximum pane width. Validate the
  resulting 2.0 mm ledges for sag and support-free printing.
- Plan 009 v0.3 is a short, top-face-down,
  pass-through coupon with a 27.0 mm loading channel, 23.0 mm top opening,
  24.0 mm opposite opening, 1.4 mm channel height, and integral manually
  depressed positive end latch. It has no loose gate or pin. Treat all v0.3
  latch, sag, overlap, retention, and cycle behavior as unverified until printed.
- Plan 009 v0.3 was subsequently reported to work in all tested respects. The
  user recommends a roughly 75% shorter latch footprint. Do not directly shorten
  the 27.0 × 0.6 mm straight tongue to 6.75 mm at the same 1.4 mm travel: the
  simple beam estimate rises from about 0.69% to 11.1% strain. Compact it with a
  longer folded flexure path or another tested geometry. Material/settings and
  detailed cycle/wear results remain unreported.
- The user explicitly chose to physically try the direct 75% reduction because
  v0.3 actuation pressure was far below anything expected to damage the glass.
  Plan 009 v0.4 therefore preserves every successful v0.3 capture dimension and
  changes only the straight free length from 27.0 to 6.75 mm. It remains a
  PETG-specific staged coupon; the user's experience indicates this 0.6 mm PETG
  feature will tolerate the motion despite the conservative beam calculation.
  PLA is excluded. Actuation, full return, root condition, positive retention,
  and cycle behavior remain required before production selection.
- The v0.4 PETG print was subsequently reported to work. Its short coupon is too
  flexible for a meaningful supported-stiffness evaluation, so the 6.75 mm latch
  is approved for the next complete-lid test article. Reuse the verified
  v0.5/v0.6 body and hinge pin. Preserve the v0.6 hinge, latch, label, envelope,
  and top-face-down support-free print orientation while evaluating the new pane
  capture within the full lid perimeter.
- The existing firm retainer remains the lightest reference in the stronger
  ladder. Keep all variants for recalibration after a material, printer, nozzle,
  extrusion, or slicer-setting change; when recalibrating, test upward in order.
- Do not force a retainer that requires levering against the glass.
- The legacy retainer ladder remains available through Git history for failure
## Removable Dividers: Physically Verified Standard (Plan 003)

- The divider interface uses vertical wall channels and a continuous bottom floor groove to locate removable divider cards without reducing usable cavity volume when omitted.
- **Physical Coupon Validation (2026-08-28):** The 1.20 mm test card in Station 2 (1.40 mm slot width, +0.20 mm total clearance, 0.60 mm wall recess, 0.60 mm floor groove) provides the preferred tactile slide fit without binding or excessive wobble.
- **Physical Full-Size Body Validation (2026-08-28):** Full-size v0.8 divided body and 1.20 mm cards were printed in PETG and verified for tactile slide fit, retention, and non-interference with the closed lid/glass ([Plan 003](Plans/Completed/2026-08-28-003-develop-optional-cassette-dividers.md)).
- **Thickened Left Hinge Wall ($4.30\text{ mm}$):** Inner left face sits at $X = -15.00\text{ mm}$, providing **$+0.65\text{ mm}$ of clear vertical drop-in clearance** past the inward-sloping hinge knuckle peak ($X = -16.15\text{ mm}$) and eliminating long-wall flex along the 80 mm body span.
- **Divider Station Layout:**
  - Two stations at thirds ($Y = \pm 12.87\text{ mm}$) divide the cavity into three equal **$24.53\text{ mm}$** compartments.
  - The center slot is omitted from the smallest cassette to avoid crowding the central closure clasp ($Y \in [-4.0, +4.0\text{ mm}]$) and because it is redundant with the thirds stations. Larger cassette dividers will be addressed in Plan 005.
- **Divider Card Standard:** $33.30\text{ mm}$ width $\times 31.20\text{ mm}$ height $\times 1.20\text{ mm}$ thickness with $10 \times 1.5\text{ mm}$ top extraction notch and $0.6\text{ mm}$ bottom corner lead-in chamfers ($0.20\text{ mm}$ lid clearance).

## Materials and Print Assumptions

- Support both ASA and PETG for the unchanged body. Use PETG for the v0.7 lid
  because its integral pane latch is a physically tested PETG-specific feature.
- Reasonable starting settings: 0.4 mm nozzle, 0.20 mm layers, four perimeters.
- Retainers may use 0.16 or 0.20 mm layers so the 0.8 mm bezel divides evenly.
- Keep seams away from hinge bores where possible.
- Do not scale parts in the slicer to fix tolerances. Change named parametric
  dimensions and release a new version.
- Do not generate support inside the pane channel or inside/beneath the retained
  v0.6 hinge geometry.

## Compatibility and Failure History

Do not regress to earlier geometries:

- **v0.1:** hinge parts lacked mating wall/rail relief and could not assemble;
  the glass retainer had no meaningful positive capture.
- **v0.2:** added mating relief, fingernail access, and a retainer groove, but
  the long circular horizontal hinge bore sagged badly in PETG.
- **v0.3:** introduced the peaked hinge and stronger retainers, but separate
  rectangular attachment solids intruded into the bores when slicer-unioned.
- **v0.4:** fixed attachment intrusion, but the long body bore printed slightly
  deformed and required manual opening.
- **v0.5:** enlarged only the body bore to 2.25 mm; the lid still had a tapered
  root that left much of each knuckle beginning as a floating cantilever.
- **v0.6:** retained hinge baseline. Keeps the v0.5 body bore and adds continuous,
  bed-supported roots beneath both lid knuckles. The v0.6 lid paired with a
  printed v0.5 body has been physically verified as a functioning hinge.
- **v0.7:** current canonical smallest cassette baseline. Keeps the v0.6 hinge
  and label zone; replaces the failed snap retainer with the physically verified
  end-loaded channel and integral 6.75 mm PETG compliant latch. Features a tight
  0.50 mm perimeter cutout, reinforced 1.20 mm / 0.65 mm undercut closure clasp,
  and concentric Z = 24.80 mm split-line alignment.

Compatibility rules:

- **Physically verified cassette baseline:** v0.7 lid + v0.5/v0.6/v0.7 body.
- A successful v0.5 or v0.6 body should be reused with the v0.7 lid; it does not need
  to be reprinted merely to change its version label because the rim remains at Z = 24.80 mm.
- The v0.7 body adds an aligned catch profile for the reinforced clasp and is backwards compatible with earlier lids.
- Grooved-lid retainers and glass remain historical calibration evidence; the positive-capture v0.7 lid is the active production baseline.

## Human and AI Roles in Development

This project uses an iterative Human-in-the-Loop (HITL) rapid prototyping and physical validation workflow. Responsibilities are clearly divided:

### Role of the Human Collaborator
1. **Strategic Direction & Requirements:** Defines product vision, physical boundaries (e.g. measured drawer heights, hardware capacity, slide dimensions), and sets/approves plan priorities.
2. **Fabrication & Machine Operation:** Manages slicing (e.g. Bambu Studio), chooses materials (PETG, ASA, PLA), configures print settings (temperatures, perimeters, layer heights), and operates the 3D printer.
3. **Physical Assembly & Caliper Measurement:** Performs all physical assembly (hinge pin insertion, glass loading, tray stacking) and measures actual physical prints and hardware batches with calipers.
4. **Tactile & Ergonomic Evaluation:** Tests real-world usability, finger purchase/pinch room, latch actuation stiffness, snap holding force, and cassette extraction ease from packed carrier trays.
5. **Authoritative Ground-Truth Adjudication:** Acts as the binding authority on physical reality. When physical print observations or hardware interactions contradict modeled assumptions (e.g. upper tray foot protrusion, slide dropout, or bed adhesion peeling), the Human's physical findings govern all subsequent geometry revisions.

### Role of the AI Agent
1. **Parametric Modeling & Code Generation:** Writes and maintains clean, editable Python scripts that generate watertight, support-free printable STL meshes anchored to component directories.
2. **Mesh Auditing & Mathematical Rigor:** Verifies binary integrity, manifoldness (0 boundary edges, 0 non-manifold edges), coordinate finiteness, shell connectivity, and computes vertical/lateral tolerance budgets.
3. **Task Pipeline & Plan Management:** Maintains the structured plan queue, priorities table, checklists, and dependency gates under `Plans/`.
4. **Continuous Documentation Synchronization:** Ensures that all repository documentation (top-level `README.md`, component READMEs, manifests, physical-test notes, and active plan files) is reviewed and kept 100% current with every commit.

## Design and Validation Workflow

- Preserve the editable parametric Python generator, README, binary STLs,
  manifest, assembly reference, and preview images in each release.
- Build outputs belong strictly inside each component's folder (e.g.
  `Cassettes/<name>/build/` or `Carriers/<name>/build/`), never at the top-level
  repository root. Every parametric generator script must anchor its default
  output directory to `Path(__file__).resolve().parent / "build"` so executing it
  from any current working directory writes to the component's folder.
- When rebuilding or iterating on a component in an active release directory
  (such as `Cassettes/glass_slide_cassette_40x80/`), the generator must overwrite
  the `build/` directory inside that folder. Clean up superseded generated
  files in that folder and rely on Git history to preserve prior revisions.
- Version every geometry change. The working release directory may replace old
  generated artifacts after a Git checkpoint when the user explicitly chooses
  Git as the revision history; never rewrite the Git history that preserves the
  physically tested revision.
- Record the user's material, slicer settings, measured dimensions, and physical
  outcome beside the revision that was tested.
- Before printing a full body or lid, provide small hinge coupons reproducing
  the exact full-part attachment geometry and print orientation.
- Before printing a full pane-capture lid, provide representative channel and
  latch coupons unless the exact geometry has already passed physical coupons.
- Validate the **exported STL**, not only source equations or an assembly render:
  - Binary STL triangle count and file integrity.
  - Zero boundary and zero non-manifold edges for each printable STL.
  - No degenerate triangles or non-finite coordinates.
  - Actual sectional checks through hinge roots and bores.
  - No floating islands, unsupported cantilevers, or slicer-dependent coplanar
    contacts at functional joints.
  - Bore/attachment clearances and pin containment.
  - Hinge sweep and root/body collision clearance.
  - Closed envelope and carrier-throat packing.
- A manifold audit alone is insufficient: earlier failures were closed shells
  whose overlapping solids produced blocked bores or unsupported printed starts.
- Treat physical prints as authoritative. If a print contradicts the model,
  diagnose the actual STL and layer orientation before claiming the design works.

## Repository Working Agreements

- This is an AI-assisted project. Do not present AI-generated source, dimensions,
  geometry, analysis, or documentation as certified, professionally reviewed,
  or physically verified without direct evidence. Preserve the AI-use warning
  in the top-level `README.md` and carry applicable safety limitations into
  release instructions and walkthroughs.
- Preserve the active-development warning in the top-level `README.md`. Every
  printable release must use explicit versions and document compatibility;
  never imply that current geometry, filenames, or cross-version fit will remain
  unchanged or compatible without notice and physical evidence.
- Use the repository task pipeline in `IDEAS.md` and `Plans/` for project work.
  Ideas are limited to three sentences. Fully developed future plans may wait
  in `Plans/Queued/`; multiple numbered plans may be in work directly in
  `Plans/` when their current steps can proceed independently. Implementation
  must follow each plan's ordered checklist and dependency gates.
- Maintain the documented queued-plan order in `Plans/PRIORITIES.md`. Plan
  numbers are permanent identifiers, not priority ranks, and priority values
  must appear only in `Plans/PRIORITIES.md`. Reassess priorities when physical
  failures, dependencies, or user goals change. Higher-priority eligible work
  normally starts first, but independent plans may overlap while another plan
  waits on printing, measurement, material, or other external results.
- Use focused plan-numbered Git commits for concurrent work. Do not combine
  unrelated implementation changes from different plans in one checkpoint, and
  do not finalize a dependency-gated dimension before its prerequisite physical
  evidence exists.
- Preserve continuity with plan-numbered Git checkpoints. When complete, move
  the plan to `Plans/Completed/` with its ISO completion date prefixed and add
  the matching `-walkthrough.md` file before treating that plan as archived.
- Read the top-level `README.md`, this file, the active plan, the current release
  README, manifest, and latest physical-test notes before changing geometry.
- Keep all dimensions in millimeters in source; include inch conversions only
  for user-supplied measurements such as the drawer height.
- Preserve unrelated user changes and existing revision directories.
- Never place or generate build directories at the top-level repository root;
  all generated builds belong strictly in their component subdirectories.
- Use Git checkpoints before and after substantive geometry changes.
- Never delete or rewrite a tested release to make a new revision look clean.
- Lead handoff notes with what changed, which old parts remain reusable, what
  must be reprinted, and what still lacks physical validation.
- Do not silently change the Gridfinity interface, 2.0 mm minimum carrier wall,
  glass standard, cassette sub-grid, drawer ceiling, hinge pin, or label format.
- Mark untested future cassette sizes and carrier features as provisional.

### Continuous Documentation Review and Updates With Every Commit

All repository documentation—including top-level `README.md`, component READMEs, manifests, physical-test notes, and active plan files—must be reviewed with every commit and updated whenever relevant changes occur. Do not force unnecessary edits, but ensure that no out-of-date or contradictory information resides in the repository:
- **Top-level `README.md`:** Must accurately reflect the active prototype revision in "Current status", active/in-work plans, component reference configuration tables, and file links (e.g. updating from v0.7 to v0.8 when a component envelope or height optimization changes).
- **Component READMEs and manifests:** Must accurately describe the current working dimensions, part versions, STL triangle counts, and compatibility notes.
- **Active plan documents:** Check off completed steps, record physical measurements, and maintain validation logs as work progresses.
- **Remote Synchronization:** Push commits to the remote tracking branch (`git push origin main`) with each milestone to keep offsite GitHub storage in sync. The user's GitHub Personal Access Token (PAT) has a limited lifespan; if a push fails due to token expiry or authentication failure, notify the user promptly so they can refresh it.
- **Never leave superseded version numbers, stale filenames, or outdated dimensions unrefreshed when committing changes.**

### Required Documentation Updates Before Every Plan Completion

Before setting any plan to `Complete` or moving it into `Plans/Completed/`,
review and update every applicable item below. An item may be recorded as
“reviewed—no change required,” but it must not be silently skipped:

1. **Top-level `README.md`:** current project status, verified baseline,
   provisional work, active/next plan, and relevant repository links.
2. **`AGENTS.md`:** binding dimensions, physical findings, compatibility and
   failure history, workflow rules, and any new non-regression constraint.
3. **`IDEAS.md`:** remove promoted work and add only genuinely deferred or
   follow-up ideas, each in no more than three sentences.
4. **`Plans/PRIORITIES.md`:** confirm the completed/in-work plan is absent from
   the queued order, reassess remaining work using the documented criteria,
   renumber priority ranks contiguously, date the decision, and identify the next
   eligible queued plan.
5. **The numbered plan:** completed checklist, validation evidence, decisions,
   deviations, completion date, and start/completion Git references.
6. **Relevant release README files:** what changed, what remains reusable, what
   must be reprinted, assembly/print instructions, and unverified limitations.
7. **Release manifests:** version, dimensions, file inventory, triangle counts,
   mesh audits, modeled checks, and validation state matching the exported files.
8. **Physical-test notes:** material, printer/nozzle, slicer settings, measured
   dimensions, test procedure, observed results, failures, and disposition.
9. **Source comments and generated previews/references:** named parameters,
   orientations, diagrams, and assembly references consistent with the release.
10. **Compatibility tables or notes:** reusable earlier parts, incompatible or
    superseded parts, and every required reprint.
11. **Completed archive pair:** the dated completed-plan file and matching dated
    `-walkthrough.md` containing the detailed implementation and validation
    narrative.
12. **Remote Synchronization (`git push`):** Push all completed commits to the remote
    repository (`git push origin main`) so GitHub offsite storage remains 100% current.

Run `python3 Plans/check_pipeline.py`, verify the exported artifacts required by
the plan, and make the final plan-numbered Git checkpoint only after this
documentation reconciliation is complete.
