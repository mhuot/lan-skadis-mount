# lan-skadis-mount

3D-printed brackets that hang a board on the slotted DuraFrame uprights of
an Ergotron LAN Organizer 3000. Three designs: the **SKÅDIS nut-channel
bracket (current)**, the SKÅDIS peg bracket it replaced, and hardware-store
pegboard bolted on with 1/4-20.

The peg bracket works — a board hung on four of them — but has no adjustment
anywhere, and came out 3-5 mm off left to right with nothing to turn. The
nut-channel bracket carries an M4 square nut in a horizontal channel with
12 mm of slide, so the board is positioned at assembly rather than at
slicing. Keep the peg script; it is a working design, not a mistake.

## Source of truth

- `scripts/build_skadis_nut_bracket.py` builds the current bracket
  (`--variant left|right|coupon`); `scripts/build_skadis_bracket.py` builds
  the older peg bracket (`--variant left|right`); `build_pegboard_bracket.py`
  builds the bolt-through pegboard bracket. All dimensions live at the top of
  each file; no shared params module (see the module-caching trap in the
  fusion-360-mcp skill).
- Two numbers in the nut bracket are MEASURED and everything hangs off them:
  the board is **6.0 mm** (not the 4.6 the community libraries quote — the
  peg bracket's roots were 1.4 mm short of reaching through because of it)
  and the decorative screw is **15 mm**. `plateThickness` is DERIVED from
  those, not chosen: 15 - 6 - 0.2 + 2.2 = 11.0 mm, deep enough that the tip
  stops short of the back face instead of fouling the upright's face metal.
  Never hand-set it; change the screw or board and let it follow.
- With one channel per bracket, vertical alignment lives in the ASSEMBLY:
  the upright is on 25.4 mm and the board on 40 mm. Stack two brackets
  3 pitches apart (76.2 vs 80 mm) or 8 (203.2 vs 200). Two pitches misses by
  10.8 of the 11.0 mm a screw has inside its slot. The build prints the list.
- Upright spacing is MEASURED, not nominal: `SLOT_INSIDE_GAP` = 731.84 mm
  between the facing edges of the two slot columns, + one slot width =
  735.04 mm centres, giving peg offsets of ±7.52 mm inboard. The nominal
  28" would have been wrong in both size and direction.
- Slot geometry (3/4" slots, 1" pitch, ~1/8" wide, single column per
  upright, hook throat = face metal 2.0 + 1.8 mm) was VERIFIED by printed
  gauges in ~/lan-spool-shelf — reuse changes from there deliberately.
- Builds land in the Fusion cloud project **"LAN Pegboard Mount"** (named
  before the repo was renamed to lan-skadis-mount; FUSION_PROJECT_NAME in
  each script must keep matching the cloud project, so do not rename one
  without the other) as the documents "Pegboard Mount Bracket", "SKADIS
  Bracket Left/Right" and "SKADIS Nut Bracket Left/Right/Coupon"; each run
  saves a new version recording its body volume. EVERY
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

- **Fusion 360 only**: every `build_*.py`, via
  `python3 scripts/run_in_fusion.py scripts/build_skadis_nut_bracket.py
  --variant left` (MCP server at 127.0.0.1:27182; Fusion must be running).
- **Locally, in `.venv`**: `scripts/check_stl.py` (mesh vs the volume the
  build printed), `scripts/build_web_assets.py` (the two GLBs the Pages site
  loads) and `scripts/render_part.py` (the stills).
- **Fusion, any time**: `scripts/audit_parameters.py` — every parameter must
  drive geometry, carry the right unit, and every sketch should be fully
  constrained. The build script audits itself too.

## Printing

On a side face (`--rotate-x 90`), like the spool brackets, so the hook
profile is drawn inside every layer rather than stacked across them. In that
orientation the nut channel and screw relief need NO support — they run
along the build direction — and organic supports grow only under the two
hooks. ASA for the real set (it creeps less than PETG under the hooks'
permanent tension), 4 perimeters, 40% infill.

The supports touch the side face of the hook tabs, which is the face that
enters the slot: caliper a tab after cleanup, nominal 2.4 mm, must stay
under ~2.6 mm for a 3.2 mm slot. PETG welds to organic supports; use a
0.25 mm contact distance.

## Third-party models

WegBier's "Skadis to Kallax mount adapter" (Printables 137113) inspired the
SKÅDIS peg approach and is CC BY-NC-SA — incompatible with this repo's MIT
licence. Its geometry is deliberately NOT reproduced; the peg is built from
published SKÅDIS interface dimensions, which are measurements of IKEA's
product. Keep it that way: cite inspiration, implement independently, and
never paste a CC-BY-NC or -SA part into an MIT repo.
