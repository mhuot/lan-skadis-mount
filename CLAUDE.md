# lan-pegboard-mount

3D-printed brackets that hang a board on the slotted DuraFrame uprights of
an Ergotron LAN Organizer 3000. Two variants: an IKEA SKÅDIS on printed
pegs (**the one in use, validated 2026-09-05**) and hardware-store pegboard
bolted on with 1/4-20. Behind a lan-spool-shelf cradle level the board face
lands 10 mm off the upright, so it doubles as a spool backstop.

## Source of truth

- `scripts/build_pegboard_bracket.py` builds the bolt-through pegboard
  bracket; `scripts/build_skadis_bracket.py` builds the SKÅDIS peg bracket
  (`--variant left|right`, a mirrored pair each carrying half the grid
  correction). All dimensions live at the top of each file; no shared
  params module (see the module-caching trap in the fusion-360-mcp skill).
- Upright spacing is MEASURED, not nominal: `SLOT_INSIDE_GAP` = 731.84 mm
  between the facing edges of the two slot columns, + one slot width =
  735.04 mm centres, giving peg offsets of ±7.52 mm inboard. The nominal
  28" would have been wrong in both size and direction.
- Slot geometry (3/4" slots, 1" pitch, ~1/8" wide, single column per
  upright, hook throat = face metal 2.0 + 1.8 mm) was VERIFIED by printed
  gauges in ~/lan-spool-shelf — reuse changes from there deliberately.
- Builds land in the Fusion cloud project **"LAN Pegboard Mount"** as the
  documents "Pegboard Mount Bracket", "SKADIS Bracket Left" and "SKADIS
  Bracket Right"; each run saves a new version recording its body volume. EVERY
  user parameter drives geometry — hooks, plate, bolt slots and nut tracks
  alike — and the build fails if one goes inert or carries a wrong unit.

## Working with the Fusion documents

Fusion is the surface Mike interacts with. The scripts still regenerate a
document from scratch, so a hand edit is something a rebuild would destroy:

1. **Never rebuild over an edit.** Each build script checks the latest
   version before clearing the timeline. A human's save is labelled
   `User Saved`; a scripted save starts with `scripted` and records the body
   volume. The build refuses only when a human save AND divergent geometry
   coincide, so an ordinary save is not a nuisance.
2. **An edit is a proposal.** Read the document, work out what changed, fold
   it into the script, rebuild, and confirm by matching volumes. The SKADIS
   peg fillet came from exactly this — the user moved it to the bearing
   edges, and later a prong front fillet; the script reproduces the current
   document exactly at 9892 mm^3.
3. **Overwritten edits survive** as the prior version in `dataFile.versions`.
4. `ALLOW_OVERWRITE = True` bypasses the guard; use it only deliberately.

## Which scripts run where

- **Fusion 360 only**: `scripts/build_pegboard_bracket.py`, via
  `python3 scripts/run_in_fusion.py scripts/build_pegboard_bracket.py`
  (MCP server at 127.0.0.1:27182; Fusion must be running).
- **Locally, in `.venv`**: `scripts/check_stl.py`.
- **Fusion, any time**: `scripts/audit_parameters.py` — every parameter must
  drive geometry, carry the right unit, and every sketch should be fully
  constrained. The build script audits itself too.

## Printing

Flat on the side face, like the spool brackets: supports on build plate
only (under the hook blades). ASA or PETG, 4 perimeters, 25% infill —
loads are far below the spool cradle's.

## Third-party models

WegBier's "Skadis to Kallax mount adapter" (Printables 137113) inspired the
SKÅDIS peg approach and is CC BY-NC-SA — incompatible with this repo's MIT
licence. Its geometry is deliberately NOT reproduced; the peg is built from
published SKÅDIS interface dimensions, which are measurements of IKEA's
product. Keep it that way: cite inspiration, implement independently, and
never paste a CC-BY-NC or -SA part into an MIT repo.
