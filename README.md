# LAN Pegboard Mount

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
