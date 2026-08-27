# Glass-capture mechanics coupon v0.2 — physical-test notes

## Pane and print record

- Pane material/source:
- Pane width × length × thickness: 24.9 mm wide; length and thickness not reported
- Edge condition before test:
- Printer:
- Filament:
- Nozzle / layer height / perimeters:
- Slicer and version:
- Other relevant settings:

## Assembly result

- Pane slides to far stop without force:
- Gate inserts/removes without loading pane: Nominal clearance is acceptable,
  but print sag required minor cleanup before the gate would fit. Insertion then
  broke one side of the frame because the surrounding material was too thin.
- 1.75 mm pin inserts through both 2.05 mm bores:
- Pin remains contained:
- Pane rattle or bowing:
- Rail, gate, pin, or pane damage: One side of the frame fractured during gate
  insertion; no other damage was reported with this observation.
- Escape path observed: The actual glass is narrower than the current frame's
  capture geometry and tends to fall through/out because lateral roof overlap is
  insufficient.

## Ten-cycle result

- Gate/pin cycles completed:
- Fit change or wear:
- Final retention result:
- Final pane edge condition:
- Specimen disposition:

Do not perform impact or rollover testing until all assembly checks pass. Wear
eye protection, contain the specimen, and document the exact test protocol before
performing it. Stop immediately for glass damage, unsafe ejection, rail fracture,
or any need to force or pry against the pane.

## Physical result — 2026-08-27

- Gate fit: passed.
- Gate clearance as modeled: acceptable; as-printed sag required minor cleanup
  before assembly, so support-free printability has not passed.
- Frame strength at gate end: failed; one thin side fractured during insertion.
- Lateral pane capture: failed; the glass is narrower than the modeled frame
  assumption and the current rail overlap does not reliably retain it.
- Stop further testing with the damaged frame. The next revision must reinforce
  the gate-end frame, preserve the verified 1.4 mm vertical channel and gate
  clearance, improve the sag-prone unsupported geometry, and expand lateral roof
  overlap based on the measured glass width. A larger continuous frame may add
  support, but that must be demonstrated by a new coupon rather than assumed.
- Measured glass width: 24.9 mm. Preserve a wide loading channel for alternate
  panes while increasing roof overlap; do not narrow the whole channel around
  this one specimen.
- Print material, settings, pane length/thickness, exact fracture location, and
  remaining assembly observations have not yet been reported.
- User-proposed follow-up: replace the separate gate and filament pin with an
  integral compliant retaining feature to reduce loose/moving parts. Evaluate a
  manually actuated positive latch; do not accept friction-only retention or a
  design that requires the glass to flex the latch during insertion.
