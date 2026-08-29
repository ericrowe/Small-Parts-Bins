# Walkthrough — Plan 011: Develop Cassette Features to Aid Removal from Carrier

## Executive Summary

Plan 011 resolved the challenge of extracting individual cassettes from tightly packed Gridfinity carrier trays ($3 \times 4$ array with minimal $0.4\text{ mm}$ inter-cassette spacing) directly from above inside open drawers.
Through rapid prototyping and Human-in-the-Loop (HITL) physical validation, a modular, body-anchored vertical dovetail pull tab (`pull_tab_v0_8.stl`), reinforced boss keyway on the body wall, and matching enlarged lid through-notch were designed, printed in PETG, and physically verified.

---

## 1. Problem Exploration & Mechanism Selection

In densely packed $3 \times 4$ carrier arrays:
* **Friction & Finger Purchase:** Smooth-sided cassettes with $0.4\text{ mm}$ gaps leave no purchase room for fingers to lift them vertically.
* **Evaluated Alternatives:**
  * *Top Pinch Flutes:* Tested on earlier lids; lacked sufficient tactile purchase for heavy hardware bins.
  * *Push-to-Tilt Tray Rockers:* Evaluated with physical rocker prints; pivoting the cassette elevated the corner by only ~4 mm, which was inadequate for comfortable finger grasp without disturbing neighboring bins.
  * *Tray Side Scallops:* Rejected to prevent reducing carrier wall strength under heavy loads and to avoid requiring tray removal from drawers.
  * *Lid-Mounted Pull Tabs:* Investigated; determined there was insufficient structural room on the front lid rail without compromising the internal glass channel or label area.
* **Selected Standard:** A rigid, standalone pull tab (`pull_tab_v0_8.stl`) that anchors into a vertical dovetail keyway integrated directly into the front body wall, passing through a generous clearance notch in the lid.

---

## 2. Geometry Architecture & Design

```
+-------------------------------------------------------------+
|                     Closed Cassette v0.8                    |
|                                                             |
|  [ Hinge ] ===== [ Glass Window ] ===== [ Lid Clearance ]   |
|     |                                           |           |
|     +-----------------------------------+       |           |
|     |  Body Cavity & Dividers           |   [ Pull Tab ]    |
|     |                                   |  (Grip + Shank)   |
|     |                                   |       |           |
|     +-----------------------------------+   [ Dovetail ]    |
|                                             [ Boss Keyway ] |
+-------------------------------------------------------------+
```

### Key Dimensions & Features:
1. **Monolithic Reinforced Body Boss Keyway:**
   * **Span:** $Y \in [15.00, 28.00\text{ mm}]$ ($13.00\text{ mm}$ wide solid boss column) on the inside front/right body wall.
   * **Sidewalls:** Solid **$2.50\text{ mm}$ thick sidewalls** ($X \in [14.80, 17.80\text{ mm}]$) flanking the dovetail slot with $45^\circ$ lead-in chamfers into the cavity wall.
   * **Outer Wall:** **$1.50\text{ mm}$ solid wall** behind the keyway ($X \in [17.80, 19.30\text{ mm}]$).
   * **Floor Stop:** Solid bottom stop at $Z = 17.80\text{ mm}$ supported by a **$45^\circ$ support-free lead-in taper** sloping down to $Z = 15.30\text{ mm}$ where it meets the inner vertical cavity wall.
   * **Slot Envelope:** $8.00\text{ mm}$ base width, $6.00\text{ mm}$ throat neck width, $3.00\text{ mm}$ depth ($X \in [14.80, 17.80\text{ mm}]$).

2. **Physically Verified Pull Tab (`pull_tab_v0_8.stl`):**
   * Sized at the physically verified **$+0.10\text{ mm}$ fit clearance standard**:
     * **Base Width:** $7.80\text{ mm}$ ($Y \in [-3.90, +3.90\text{ mm}]$).
     * **Throat Neck Width:** $5.80\text{ mm}$ ($Y \in [-2.90, +2.90\text{ mm}]$).
     * **Shank Thickness:** $2.80\text{ mm}$ ($X \in [14.90, 17.70\text{ mm}]$).
   * **Ergonomic Grip Head:** $+4.00\text{ mm}$ raised fin above the lid with deep concave thumb/finger hollow scoops and tactile horizontal grip ribs on the face-up side.
   * **Print Orientation:** Prints 100% flat on its back face directly on the print bed with zero supports in **~60 seconds** in PETG.

3. **Enlarged Sloppy Lid Clearance Cutaway:**
   * **Notch Span:** Full-depth through-notch spanning **$15.00\text{ mm}$** ($Y \in [14.00, 29.00\text{ mm}]$) from $X = 14.50$ to $19.30\text{ mm}$ across all $3.60\text{ mm}$ of lid thickness.
   * **Clearance:** Provides **$+2.00\text{ mm}$ clear sloppy air** on each side around the $11.0\text{ mm}$ pull tab grip fin, allowing the lid to swing freely through 120° and latch securely with zero binding.
   * **Protection:** Preserves a solid plastic barrier enclosing the internal glass microscope slide loading channel.

4. **Stacking Clearance Budget:**
   * Pull tab apex sits at $Z = 40.40\text{ mm}$ (carrier $Z = 47.15\text{ mm}$).
   * Located inside the upper carrier tray's central inter-foot clearance valley (ceiling $Z = 49.00\text{ mm}$), preserving **$+1.85\text{ mm}$ of clear vertical air** below loaded upper carrier trays.

---

## 3. Physical Validation Record

* **2026-08-29 (HITL Physical Validation):**
  * **Test Articles:** Body with reinforced boss keyway, lid with $15.00\text{ mm}$ through-notch, and progressive pull tab tolerance ladder (`_fit_0_20`, `_fit_0_15`, `_fit_0_10`, `_fit_0_05`) printed in PETG on PEI textured sheet.
  * **Results:**
    * The $+0.10\text{ mm}$ clearance variant (`pull_tab_v0_8_fit_0_10.stl`) seated firmly into the keyway, locked positively against the bottom stop, and eliminated lateral wobble while remaining removable by hand when desired.
    * The lid closed, swung through its full arc, and latched securely with zero interference against the installed tab: *"10 worked, and the cover closes now."*
  * **Outcome:** $+0.10\text{ mm}$ adopted as the standard default for `pull_tab_v0_8.stl`.

---

## 4. Verification and Artifact Deliverables

| Artifact | Description | Audit Status |
|---|---|---|
| [`cassette_body_v0_8_divided.stl`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/Cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8_divided.stl) | Divided body with monolithic reinforced boss keyway & $45^\circ$ lead-in | Passed (0 boundary / 0 non-manifold) |
| [`cassette_body_v0_8.stl`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/Cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8.stl) | Undivided body with monolithic reinforced boss keyway & $45^\circ$ lead-in | Passed (0 boundary / 0 non-manifold) |
| [`cassette_lid_v0_8_print.stl`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/Cassettes/glass_slide_cassette_40x80/build/cassette_lid_v0_8_print.stl) | Lid with $15.0\text{ mm}$ sloppy through-cutout & $1.20\text{ mm}$ glass clip | Passed (0 boundary / 0 non-manifold) |
| [`pull_tab_v0_8.stl`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/Cassettes/glass_slide_cassette_40x80/build/pull_tab_v0_8.stl) | Production pull tab (+0.10 mm verified fit standard) | Passed (0 boundary / 0 non-manifold) |
| [`pull_tab_v0_8_multiview.png`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/docs/images/pull_tab_v0_8_multiview.png) | 3D multi-view engineering drawing of pull tab | Complete |
| [`cassette_lid_v0_8_multiview.png`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/docs/images/cassette_lid_v0_8_multiview.png) | 3D multi-view engineering drawing of lid with pull tab cutout | Complete |
| [`cassette_body_v0_8_divided_multiview.png`](file:///Volumes/T9/Sync/Working/Shop/Projects/_Gridfinity/_Small%20Parts%20Bins/docs/images/cassette_body_v0_8_divided_multiview.png) | 3D multi-view engineering drawing of divided body | Complete |

Plan 011 is complete and archived.
