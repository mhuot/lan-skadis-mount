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


## SKÅDIS variant

`scripts/build_skadis_bracket.py` builds a bracket that hooks the upright
and carries two upward-opening pegs. Lower a SKÅDIS onto them — each slot's
top edge rests on a peg root, and the prong in front of the board stops it
tipping out. Lift 12 mm and pull forward to take it off. No bolts, no nuts.

```sh
python3 scripts/run_in_fusion.py scripts/build_skadis_bracket.py --variant left
python3 scripts/run_in_fusion.py scripts/build_skadis_bracket.py --variant right
```

**Measure your uprights first.** The board's slot columns repeat every
40 mm and your uprights are whatever they are — 711.2 mm nominal on a 30"
frame. Since 711.2 is not a multiple of 40, the second bracket misses a
column by 8.8 mm, and a peg is a fixed post with no adjustment. So the
offset is built in: set `UPRIGHT_SPACING` at the top of the script, and it
computes `pegOffsetY` for the right-hand brackets (0 for the left ones).
Print two of each per board.

| | |
|---|---|
| Bracket | 60 × 24 × 20.5 mm, ~8.6 cm³, ~9 g |
| Board | SKÅDIS 4.6 mm thick, 5 × 15 mm slots, 40 mm grid |
| Board face | lands 10 mm off the upright — same plane as the pegboard version, so it still works as a spool backstop |
| Print | plate flat on the bed, hooks and pegs up; supports on build plate only |

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
