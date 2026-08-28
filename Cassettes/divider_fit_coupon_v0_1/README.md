# Cassette Divider Fit Coupon v0.1 — Plan 003

This low-material test coupon evaluates the slot and floor groove tolerances
for removable cassette dividers before updating the full-size cassette body.

## Features

- **Body Width & Wall Geometry:** Matches the standard cassette cross section ($38.60\text{ mm}$ outer width, $34.60\text{ mm}$ cavity width, $2.00\text{ mm}$ outer walls).
- **Floor Containment Groove:** $0.60\text{ mm}$ deep transverse groove across the $2.00\text{ mm}$ solid floor (leaves $1.40\text{ mm}$ base plate) to prevent tiny parts (M2 washers/nuts) from slipping under divider.
- **Wall Slot Recesses:** $0.60\text{ mm}$ deep recesses into the left and right walls to positively locate dividers without loose rattling.
- **Tolerance Ladder (4 Stations spaced 8.0 mm along Y):**
  - **Station 1 ($Y = -12.0\text{ mm}$):** $1.30\text{ mm}$ slot width ($+0.10\text{ mm}$ nominal clearance on $1.20\text{ mm}$ card)
  - **Station 2 ($Y = -4.0\text{ mm}$):** $1.40\text{ mm}$ slot width ($+0.20\text{ mm}$ nominal clearance)
  - **Station 3 ($Y = +4.0\text{ mm}$):** $1.50\text{ mm}$ slot width ($+0.30\text{ mm}$ nominal clearance)
  - **Station 4 ($Y = +12.0\text{ mm}$):** $1.60\text{ mm}$ slot width ($+0.40\text{ mm}$ nominal clearance)

![Divider coupon preview](build/divider_coupon_multiview.png)

## Print these files

- `build/divider_slot_coupon.stl` (print upright without support; ~15-20 min print)
- `build/divider_card_1_2mm.stl` (primary $1.20\text{ mm}$ test card with top finger pull tab; print flat; ~3 min print)
- `build/divider_card_1_0mm.stl` (optional $1.00\text{ mm}$ thinner card for comparison)
- `build/divider_card_1_4mm.stl` (optional $1.40\text{ mm}$ thicker card for comparison)

## Physical Evaluation Procedure

1. Print the coupon and the $1.20\text{ mm}$ test divider card in PETG or PLA with 0.20 mm layers.
2. Test inserting the $1.20\text{ mm}$ divider card into each of the 4 slot stations (Station 1 through Station 4):
   - **Station 1 (1.30 mm):** Check if insertion binds or if print layer lines cause resistance.
   - **Station 2 (1.40 mm):** Check for smooth slide-in with light positive guidance.
   - **Station 3 (1.50 mm):** Check slide ease and lateral play/rattle.
   - **Station 4 (1.60 mm):** Check if the gap is too loose for small washers/screws.
3. Check the bottom floor engagement: Confirm the divider tongue drops cleanly into the floor groove with zero gap underneath.
4. Test finger extraction: Use the top tab to pull the divider out without needing tools.
5. Report which slot width (1.3, 1.4, 1.5, or 1.6 mm) provides the ideal balance of smooth insertion and secure containment.
