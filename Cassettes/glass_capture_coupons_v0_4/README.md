# Short compliant end-capture coupon v0.4 — Plan 009

Print `build/short_compliant_end_capture_coupon_v0_4.stl`. This implements the
requested direct 75% reduction of the successful v0.3 straight lever arm, from
27.0 mm to 6.75 mm. The 27.0 mm loading channel, 23.0/24.0 mm capture openings,
1.4 mm channel height, 0.6 mm tongue, and positive shoulder are unchanged.

Print top/visible-face down exactly as supplied **in PETG**, with no scaling or
internal support. PLA is excluded from this shortened latch test. Record the
PETG product and print settings.

## Staged test

1. Inspect the tongue root and channel before inserting glass.
2. Hold the coupon clear of the work surface. Depress the latch manually without
   using the glass as a cam. Stop immediately if the tongue whitens, creases,
   cracks, remains bent, or requires uncomfortable force.
3. If the first actuation returns fully, insert the undamaged pane and verify the
   positive shoulder blocks withdrawal.
4. Complete five release/re-engagement cycles, inspecting the root after each.
5. Only if the first five cycles remain unchanged, continue to 25 total cycles.
   Record permanent set, return height, force change, wear, and final retention.

The same-travel simple-beam estimate is approximately 11.1% outer-fiber strain,
versus 0.69% for v0.3. That calculation remains recorded as design metadata, but
the user's experience is that a 0.6 mm PETG feature will tolerate this motion;
the physical PETG print is authoritative. This result must not be generalized to
PLA. Eye protection and glass containment remain required.

Regenerate with `python3 generate_glass_capture_coupon.py`.
