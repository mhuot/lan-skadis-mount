# LAN Pegboard Mount

Two ways to hang a board on the slotted DuraFrame uprights of an Ergotron
LAN Organizer 3000: hardware-store pegboard bolted on, or an IKEA SKÅDIS
hung on printed pegs. Both reuse the hook design already fit-verified on
the real desk.

Hangs standard 1/4"-hole pegboard on the slotted DuraFrame uprights of an
Ergotron LAN Organizer 3000 — no drilling into the frame. Grown out of
[lan-spool-shelf](../lan-spool-shelf); the hook design is the one already
fit-verified on the real desk.

## How it works

- Each printed bracket hooks a slot column with two rows of the proven
  blade hooks (`hookRows` parameter goes to 3-4 for heavy tool walls).
- The pegboard bolts to the bracket's flat front face with **1/4-20 x
  5/8" bolts + washers** through the board's own holes. Slots and board
  holes both sit on a 1" grid, so everything lines up; the bracket's bolt
  slots run horizontally (+/-7 mm) to absorb upright-spacing tolerance.
- Nuts slide into open-ended tracks in the bracket's rear face — captive,
  can't spin, and flush so nothing touches the upright.
- Use 4 brackets per board (two per upright). **1/8" board recommended**:
  behind a spool cradle level its face lands ~10 mm off the upright,
  exactly at a resting spool's rearmost point, so it doubles as a spool
  backstop. (1/4" board works but nudges spools ~3 mm forward.)
- Peg hooks insert anywhere except directly over the uprights (the steel
  is behind the board there).

## Printing

`exports/pegboard_mount_bracket.stl` — flat on its side, supports on
build plate only, ASA or PETG, 4 perimeters, 25% infill. ~10 g and ~30
minutes each.

## Rebuilding

Fusion 360 running with its MCP server on `127.0.0.1:27182`, then:

```sh
python3 scripts/run_in_fusion.py scripts/build_pegboard_bracket.py
```

Rebuilds into the "Pegboard Mount Bracket" document ("LAN Pegboard
Mount" Fusion project), probes the geometry numerically, exports
STL/STEP/F3D together, and saves a new document version.


## SKÅDIS variant  — the one in use

`scripts/build_skadis_bracket.py` builds a bracket that hooks the upright
and carries two upward-opening pegs. Lower a SKÅDIS onto them — each slot's
top edge rests on a peg root, and the prong in front of the board stops it
tipping out. Lift ~11 mm and pull forward to take it off. No bolts, no nuts.

**Validated 2026-09-05:** a board hangs on four of these, two pegs a side,
both ends engaged.

```sh
python3 scripts/run_in_fusion.py scripts/build_skadis_bracket.py --variant left
python3 scripts/run_in_fusion.py scripts/build_skadis_bracket.py --variant right
```

### Measure your uprights — this is what sizes the pegs

The board's slot columns repeat every 40 mm; your uprights are whatever they
are. Only the *difference* between the two brackets' peg offsets is fixed:

> uprightSpacing + rightOffset − leftOffset = a whole number of 40 mm columns

Splitting that difference in half makes the pair mirror images with equal
plate gaps, which is what `peg_offset()` does. Measure between the **facing
edges of the two slot columns** (right edge of a left slot → left edge of a
right slot) and set `SLOT_INSIDE_GAP`; the script adds one slot width to get
centres, and derives everything else.

On this desk: 28 13/16" = 731.84 mm between facing edges → **735.04 mm**
centres → 15.04 mm past an 18-column span → each bracket's pegs sit
**7.52 mm toward the middle** of the desk, and the engaged columns land
720.00 mm apart. Nominal 28" would have given ±4.4 mm *outward* — the wrong
size and the wrong direction, which is why this is measured, not assumed.

Print **two of each** per board.

| | |
|---|---|
| Bracket | 60 × 28 × 20.5 mm, 9.89 cm³, ~9.5 g in ASA |
| Plate | 24 mm centred on the hooks plus 4 mm **inboard only**. The outboard half stays at 12 mm so two brackets still fit side by side on the two slot columns at the module centre, with 1.4 mm between them — a symmetric 28 mm plate would overlap by 2.6 mm. |
| Peg | 4.70 mm wide in a 5.00 mm slot (`pegClearance` 0.3, set after a print that was too tight), root 4.80 mm through a 4.6 mm board, prong 2.0 mm |
| Prong | 2.0 mm, not 1.0: it carries the board's tipping load over a 7 mm rise and bent under a hand push at 1.0 mm. A millimetre asked off the peg should come off the root or the rise, never off this. |
| Rounding | 0.6 mm lead-in chamfer on the prong top (the board is lowered on blind); 1.5 mm fillet on the root's top side edges, where the board's slot edge actually bears; 1.0 mm fillet on the prong's front corners, the surface a hand meets |
| Board | SKÅDIS 4.6 mm thick, 5 × 15 mm slots, 40 mm grid |
| Board face | lands 10 mm off the upright — same plane as the pegboard version, so it still works as a spool backstop |
| Print | **on its side**, the 28 mm face on the bed — same rule as the spool brackets. That puts the peg's bending stress along the layers instead of across them. Organic supports, build plate only: the hooks and pegs start ~10 mm up with nothing under them. Plate-flat stands each peg on a layer bond and a knock snaps one off. |

### Credit

The idea of hanging a SKÅDIS on printed pegs rather than bolting through it
comes from **[Skadis to Kallax mount adapter](https://www.printables.com/model/137113-skadis-to-kallax-mount-adapter)
by WegBier**, licensed CC BY-NC-SA.

That licence is incompatible with this repository's MIT licence — the
NonCommercial term contradicts it outright, and ShareAlike would pull the
whole repo off MIT — so **none of that model's geometry is reproduced
here.** The peg is implemented independently from the published SKÅDIS
interface dimensions, which describe IKEA's product rather than anyone's
authorship, cross-checked against two unrelated OpenSCAD libraries:
[franpoli/OpenSCADutil](https://github.com/franpoli/OpenSCADutil) and
[TassSinclair/skadis](https://github.com/TassSinclair/skadis), which agree
on 40 mm pitch, 5 mm slot width and 4.6 mm board thickness.

If you want WegBier's adapter itself, print it from the link above — it
mounts a SKÅDIS to a KALLAX, and personal use is squarely within its
licence.
