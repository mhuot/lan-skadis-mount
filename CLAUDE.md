# lan-pegboard-mount

3D-printed brackets that hook into the slotted DuraFrame uprights of an
Ergotron LAN Organizer 3000 and mount standard 1/4"-hole pegboard with
1/4-20 bolts. Mounted behind a lan-spool-shelf cradle level with 1/8"
board, the pegboard doubles as a backstop the resting spools just graze.

## Source of truth

- `scripts/build_pegboard_bracket.py` builds the one printed part. All
  dimensions live at the top of that file; no shared params module (see
  the module-caching trap in the fusion-360-mcp skill).
- Slot geometry (3/4" slots, 1" pitch, ~1/8" wide, single column per
  upright, hook throat = face metal 2.0 + 1.8 mm) was VERIFIED by printed
  gauges in ~/lan-spool-shelf — reuse changes from there deliberately.
- Builds land in the Fusion cloud project **"LAN Pegboard Mount"** as the
  document "Pegboard Mount Bracket"; each run saves a new version. The
  hook stack and widths are parameter-driven; body/slot geometry is
  script-driven with reference-only parameters.

## Which scripts run where

- **Fusion 360 only**: `scripts/build_pegboard_bracket.py`, via
  `python3 scripts/run_in_fusion.py scripts/build_pegboard_bracket.py`
  (MCP server at 127.0.0.1:27182; Fusion must be running).
- **Locally, in `.venv`**: `scripts/check_stl.py`.

## Printing

Flat on the side face, like the spool brackets: supports on build plate
only (under the hook blades). ASA or PETG, 4 perimeters, 25% infill —
loads are far below the spool cradle's.
