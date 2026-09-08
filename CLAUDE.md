# skadis-bench-frame-mount

3D-printed brackets that hang a board on the slotted DuraFrame uprights of
an Ergotron LAN Organizer 3000. Two designs: the **SKÅDIS captured-nut
bracket (current)** and hardware-store pegboard bolted on with 1/4-20.

An M4 square nut, MEASURED 7 x 7 x 3 mm (a DIN 557 pattern, not the thin
DIN 562 at 2.2 that this was first built around -- the open channel hid the
error because a pocket facing the board does not care how thick the nut is),
lives in a cavity INSIDE the plate, closed on the board
side by a 4 mm wall and closed at both ends. It drops in through a short
vertical entry from the plate's TOP EDGE at the outboard end of its travel,
then slides inboard; to get out it must be back at that spot AND rise 20 mm,
which gravity never does with the bracket hanging. Captured by geometry, no
tooth, nothing to tune. The outboard end carries a 45 deg roof (a triangular
CUT beyond the nut's stop, NOT a chamfer -- chamfering the concave end edges
fills the corners and narrows the entry below the nut) so it prints with no
support inside the cavity. 12 mm of slide = the left-right adjustment, so the board
is positioned at assembly rather than at slicing. Tightening pulls the nut
forward onto the wall and clamps the board between the screw head and a flat
plate face.

Three designs preceded it and were deleted, not kept as variants: printed
pegs (worked, but zero adjustment, 3-5 mm out left to right); an open channel
milled in the face (adjustable, but the board covered the pocket, so the nut
had to be posted through a board slot with the board already hanging); and a
cavity with a mouth in the outboard edge (captured, but the nut slid straight
back out in the hand). Do not reintroduce any; git history has all three.

## Source of truth

- `scripts/build_skadis_nut_bracket.py` builds the current bracket
  (`--variant left|right|coupon`); `build_pegboard_bracket.py` builds the
  bolt-through pegboard bracket. All dimensions live at the top of each file;
  no shared params module (see the module-caching trap in the fusion-360-mcp
  skill).
- Parameter housekeeping runs ensure -> drop -> ensure, in that order.
  Fusion refuses to delete a parameter another expression still mentions, so
  dropping nutProud failed while plateThickness was still written as
  "... - nutProud", and the build then died in its own audit on a parameter
  it had just reported as removed.
- Two numbers in the nut bracket are MEASURED and everything hangs off them:
  the board is **6.0 mm** (not the 4.6 the community libraries quote — the
  peg bracket's roots were 1.4 mm short of reaching through because of it)
  and the decorative screw is **15 mm**. `plateThickness` is DERIVED from
  those, not chosen: 15 - 6 + 2.0 = 11.0 mm, deep enough that the tip
  stops short of the back face instead of fouling the upright's face metal.
  Never hand-set it; change the screw or board and let it follow.
- With one channel per bracket, vertical alignment lives in the ASSEMBLY:
  the upright is on 25.4 mm and the board on 40 mm. WIDER IS BETTER -- the
  two brackets on an upright are what stop the board rotating and the
  spacing is the moment arm -- so 19 pitches (482.6 vs 480, off 2.6) on a
  56 cm board, which lands them ~15 mm inside each corner. 3 pitches (76.2)
  is equally valid and bunches all four across the middle of the board. Two
  pitches misses by 10.8 of the 11.0 mm a screw has inside its slot. The
  build prints the whole list, searched out to 20 pitches.
- Upright spacing is MEASURED, not nominal: `SLOT_INSIDE_GAP` = 731.84 mm
  between the facing edges of the two slot columns, + one slot width =
  735.04 mm centres, giving peg offsets of ±7.52 mm inboard. The nominal
  28" would have been wrong in both size and direction.
- Slot geometry (3/4" slots, 1" pitch, ~1/8" wide, single column per
  upright, hook throat = face metal 2.0 + 1.8 mm) was VERIFIED by printed
  gauges in ~/lan-spool-shelf — reuse changes from there deliberately.
- Builds land in the Fusion cloud project **"LAN Pegboard Mount"** (named
  before the repo was renamed to skadis-bench-frame-mount; FUSION_PROJECT_NAME in
  each script must keep matching the cloud project, so do not rename one
  without the other) as the documents "Pegboard Mount Bracket", "SKADIS Nut
  Bracket Left/Right/Coupon" (the peg design's documents are stale, and are
  left alone rather than deleted from the cloud without asking); each run
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
  loads), `scripts/render_part.py` (the stills), `scripts/build_joint_diagram.py`
  (the section drawing on the page, generated from the build script's own
  constants so it cannot drift) and `scripts/stamp_assets.py`.
  Run stamp_assets after ANY of the other two: Pages caches models and images
  hard, so a corrected GLB kept rendering the old geometry on a phone that had
  loaded the page before, with current HTML beside it and nothing visibly
  wrong. It rewrites each local asset URL as ?v=<content hash>, so the URL
  changes exactly when the bytes do. It is idempotent.
- **Fusion, any time**: `scripts/audit_parameters.py` — every parameter must
  drive geometry, carry the right unit, and every sketch should be fully
  constrained. The build script audits itself too.

## Printing

On a side face, like the spool brackets, so the hook profile is drawn inside
every layer rather than stacked across them. In that orientation the cavity,
the entry and the screw slot need NO support -- they run along the build
direction -- and organic supports grow only under the two hooks.

Put the INBOARD edge on the bed, so the cavity's ROOFED outboard end is
uppermost: `--rotate-x -90` for the LEFT bracket and `--rotate-x 90` for the
RIGHT. The hands are mirrored and do not share a rotation. The other way up
leaves the flat inboard end as a 3.4 mm ceiling and the slicer grows organic
support up inside the cavity to hold it -- where the nut has to slide and
where nothing can reach. `--support-material-buildplate-only` does NOT stop
that; the tree routes out through the screw slot. Supports reach z 29.0 the
wrong way up and z 21.6 the right way up, and the 21.6 is the hooks.

PETG is sufficient and arguably better than ASA here: stresses run 2-5% of
yield and the 2.4 mm hook tab is tougher in PETG. 4 perimeters, 40% infill,
5 mm brim, organic supports at 0.25 mm contact distance (PETG welds to them
at the stock 0.2). About 16 g and an hour per bracket. ASA is for the spool
cradle, whose hooks carry ~10x more.

The supports touch the side face of the hook tabs, which is the face that
enters the slot: caliper a tab after cleanup, nominal 2.4 mm, must stay
under ~2.6 mm for a 3.2 mm slot.

## Third-party models

WegBier's "Skadis to Kallax mount adapter" (Printables 137113) is where this
project started and is CC BY-NC-SA — incompatible with this repo's MIT
licence. Its geometry is deliberately NOT reproduced; the peg is built from
published SKÅDIS interface dimensions, which are measurements of IKEA's
product. Keep it that way: cite inspiration, implement independently, and
never paste a CC-BY-NC or -SA part into an MIT repo.
