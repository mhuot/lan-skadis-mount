"""Fusion 360 script: SKADIS bracket for Ergotron DuraFrame uprights.

Run inside Fusion via scripts/run_in_fusion.py. Hooks into the slotted
uprights of a LAN Organizer 3000 and carries two upward-opening pegs that an
IKEA SKADIS board hangs on. No bolts, no nuts: lower the board so each slot's
top edge rests on a peg root, and the prong in front of the board stops it
tipping out. Lift 12 mm and pull forward to remove.

Attribution: the idea of hanging SKADIS on printed pegs rather than bolting
through it comes from "Skadis to Kallax mount adapter" by WegBier
(https://www.printables.com/model/137113-skadis-to-kallax-mount-adapter),
licensed CC BY-NC-SA. That licence is incompatible with this repository's MIT
licence, so NONE of that model's geometry is reproduced here. The peg is
implemented from the published SKADIS interface dimensions, which are
measurements of IKEA's product rather than anyone's authorship, cross-checked
against two independent OpenSCAD libraries:
  https://github.com/franpoli/OpenSCADutil  (distance_between_pegs = 40,
      peg_default_width = 5, peg_default_thickness = 4.6)
  https://github.com/TassSinclair/skadis    (distance_between_hooks = 40)

The horizontal grid problem, and why pegOffsetY exists: the board's slot
columns repeat every 40 mm, and the uprights are uprightSpacing apart. 711.2
is not a multiple of 40, so the second bracket misses a column by
40 - (711.2 mod 40) = 8.8 mm. A peg is a fixed post with no adjustment, so
the offset is built in instead: print the left brackets with pegOffsetY = 0
and the right brackets with pegOffsetY = the printed offset below. MEASURE
your uprights first and set uprightSpacing; the script computes the rest.

Every dimension is parameter driven with real units, and the build fails if
any declared parameter drives no geometry or carries the wrong unit.
"""

import datetime

import adsk.core
import adsk.fusion

MM = 0.1  # Fusion API lengths are centimetres

# Appended by run_in_fusion.py --variant; see the note in build_rod_bracket.py.
BUILD_VARIANT = "left"

# Set True only to deliberately discard a hand edit in the document.
ALLOW_OVERWRITE = False

PROJECT_DIR = "/Users/mhuot/lan-pegboard-mount"
FUSION_PROJECT_NAME = "LAN Pegboard Mount"

# --- Upright, measured and confirmed by the spool shelf gauge prints --------
SLOT_WIDTH = 3.2
SLOT_HEIGHT = 19.05
SLOT_PITCH_VERTICAL = 25.4
FACE_METAL_THICKNESS = 2.0
# MEASURED 2026-09-05: 28 13/16" (731.84 mm) between the FACING edges of the
# two slot columns — right edge of the left slot to left edge of the right
# slot. Centre-to-centre is that plus one slot width, because each centre
# sits half a slot in from the edge that was measured. The old 711.2 was a
# nominal 28" and was 23.8 mm wrong, which is most of a slot column.
SLOT_INSIDE_GAP = 731.84
UPRIGHT_SPACING = SLOT_INSIDE_GAP + SLOT_WIDTH

# --- SKADIS interface (community-measured; confirm on your own board) ------
BOARD_THICKNESS = 4.6
BOARD_SLOT_WIDTH = 5.0
BOARD_SLOT_HEIGHT = 15.0
BOARD_PITCH = 40.0

# --- Hook stack, proven on the real desk -----------------------------------
HOOK_TAB_WIDTH = SLOT_WIDTH - 0.8
HOOK_THROAT = FACE_METAL_THICKNESS + 1.8
HOOK_NECK_HEIGHT = 5.0
HOOK_LIP_THICKNESS = 4.5
HOOK_LIP_DROP = 12.0
HOOK_LIP_CHAMFER = 1.5
HOOK_ROWS = 2
assert HOOK_NECK_HEIGHT + HOOK_LIP_DROP < SLOT_HEIGHT - 1.0, "hook will not enter"

# --- Plate and pegs --------------------------------------------------------
BRACKET_WIDTH = 24.0  # still fits the 25.4 gap at the module centre
PLATE_THICKNESS = 5.4  # board face then lands 10.0 mm off the upright
PLATE_HEIGHT = 60.0
TOP_HOOK_NECK_TOP = PLATE_HEIGHT - 2.0
# Two small numbers that look alike and are not. pegClearance is a sliding
# fit: how easily the peg enters the slot. pegRootProud is a standoff: how
# far the root pokes past the board's front face so the prong does not pinch
# it. Sharing one parameter means loosening a tight peg also lets the board
# rattle front-to-back, so they stay separate even at equal values.
# Both of these came from a printed part in a real board, 2026-09-05:
# the peg was too tight left-to-right in the slot, so the width clearance
# went from 0.2 to 0.3 (peg 4.70 in a 5.00 slot, 0.15 a side).
PEG_CLEARANCE = 0.3  # total across the slot width
PEG_ROOT_PROUD = 0.2  # root beyond the board's front face
PEG_WIDTH = BOARD_SLOT_WIDTH - PEG_CLEARANCE
PEG_ROOT_LENGTH = BOARD_THICKNESS + PEG_ROOT_PROUD
PEG_ROOT_HEIGHT = 4.0  # the slot's top edge bears on this
# 2.0, not 1.0: the prong is what stops the board tipping out, so it is
# loaded in bending over its 7 mm rise. At 1.0 it bent under a hand push —
# section modulus 0.78 mm^3, about 90 MPa at only 10 N, past what ASA takes.
# 2.0 is four times stiffer. A millimetre asked off the peg should come off
# the root or the rise, never off this.
PEG_PRONG_THICKNESS = 2.0  # sits in front of the board
PEG_TOTAL_HEIGHT = BOARD_SLOT_HEIGHT - 4.0  # 11: prong rises 7 mm above the root
PEG_PRONG_CHAMFER = 0.6  # lead-in; must stay under the prong thickness
PEG_BEARING_FILLET = 1.5  # the top edges the board actually lands on
PEG_PRONG_FRONT_FILLET = 1.0  # the prong's two front corners, thumb-facing
TOP_PEG_ROOT_Z = 45.0
PEG_ROWS = 2
PEG_EDGE_MARGIN = 1.6  # plate left either side of a peg
# The pegs sit inboard, toward the middle of the desk, so that is the edge
# they crowd. The plate grows on that side only: the hooks stay centred on
# the upright's slot column (they have to), the outboard edge stays where it
# was, and the extra material goes into the gap between the uprights where
# nothing else lives.
PLATE_INBOARD_EXTENSION = 4.0
# The grid correction is split evenly between the two brackets, so they are
# a mirrored pair: equal gap from each peg to its outer plate edge. Only the
# DIFFERENCE between the two offsets is fixed by the board's column grid;
# how it is split is free, and splitting it in half is the symmetric choice.
# Set BOARD_SHIFT to slide the whole board along the desk without breaking
# that symmetry: it moves both brackets' pegs together.
BOARD_SHIFT = 0.0


# These three depend on BUILD_VARIANT, so they MUST be computed when run()
# is called, not at module level: run_in_fusion.py appends the --variant
# assignment AFTER this script text, so any module-level constant derived
# from BUILD_VARIANT is baked in at the default before the override lands.
# Getting this wrong built the right-hand bracket as a left one and saved it
# over the left document, reporting success the whole way.
def grid_correction():
    """How far the right bracket's peg must sit from the left one's, mm.

    Only the DIFFERENCE between the two offsets matters: the pegs have to
    land on board columns a whole number of boardPitch apart, and the
    brackets are pinned to uprights uprightSpacing apart. So

        uprightSpacing + rightOffset - leftOffset = k * boardPitch

    With 711.2 mm uprights and a 40 mm pitch the two candidates are 720
    (+8.8, pegs move apart) and 680 (-31.2, pegs move together). The
    smaller correction wins; the other needs 15.6 mm on each bracket, well
    past what the plate allows.
    """
    remainder = UPRIGHT_SPACING % BOARD_PITCH
    if not remainder:
        return 0.0
    apart = round(BOARD_PITCH - remainder, 2)
    together = round(-remainder, 2)
    return apart if abs(apart) <= abs(together) else together


def peg_offset():
    """This bracket's peg offset, mm. Negative is left.

    Half the grid correction goes each way, which makes the two brackets a
    mirrored pair with equal peg-to-edge gaps. Hard-coding the left at zero
    and loading the whole correction onto the right is what made the right
    bracket unbuildable — +8.8 mm walked its peg off a 24 mm plate — and
    even after relating the two, an uneven split left one peg crowding an
    edge while the other sat near the middle.
    """
    half = grid_correction() / 2.0
    sign = -1.0 if BUILD_VARIANT == "left" else 1.0
    return round(BOARD_SHIFT + sign * half, 2)


def _check_peg_geometry():
    """The chamfer cannot be deeper than the prong it is cut into.

    Shortening the prong to 1 mm while the lead-in chamfer stayed at 1.2 mm
    would have eaten the whole prong and then some — the sketch would still
    have solved into something, silently.
    """
    if PEG_PRONG_CHAMFER >= PEG_PRONG_THICKNESS:
        raise RuntimeError(
            f"pegProngChamfer {PEG_PRONG_CHAMFER} mm must be less than "
            f"pegProngThickness {PEG_PRONG_THICKNESS} mm"
        )
    if PEG_ROOT_LENGTH < BOARD_THICKNESS:
        raise RuntimeError(
            f"pegRootLength {PEG_ROOT_LENGTH} mm is shorter than the board's "
            f"{BOARD_THICKNESS} mm: the root would not reach through it"
        )


def plate_span():
    """(outboard edge, inboard edge) of the plate in Y, mm.

    Inboard is +Y on the left bracket and -Y on the right, so the pair
    mirrors: each grows toward the middle of the desk.
    """
    half = BRACKET_WIDTH / 2.0
    if BUILD_VARIANT == "left":
        return -half, half + PLATE_INBOARD_EXTENSION
    return half, -half - PLATE_INBOARD_EXTENSION


def _check_peg_offset():
    """A peg has to stay on the plate, with material left either side."""
    outboard_edge, inboard_edge = plate_span()
    low, high = sorted((outboard_edge, inboard_edge))
    peg_low = peg_offset() - PEG_WIDTH / 2.0
    peg_high = peg_offset() + PEG_WIDTH / 2.0
    gaps = (peg_low - low, high - peg_high)
    if min(gaps) < PEG_EDGE_MARGIN:
        raise RuntimeError(
            f"peg at {peg_offset():+.2f} mm leaves {min(gaps):.2f} mm of plate "
            f"beside it, under the {PEG_EDGE_MARGIN} mm margin. Raise "
            f"PLATE_INBOARD_EXTENSION (now {PLATE_INBOARD_EXTENSION} mm) or "
            "widen BRACKET_WIDTH — but over 25.4 mm the outboard half stops "
            "fitting between the two slot columns at the module centre."
        )
    print(
        f"  plate {min(low, high):+.1f}..{max(low, high):+.1f} mm, "
        f"peg gaps {gaps[0]:.2f} / {gaps[1]:.2f} mm"
    )


def export_name():
    """Stem for the exported STL/STEP/F3D."""
    return f"skadis_bracket_{BUILD_VARIANT}"


def doc_name():
    """Name of the saved Fusion document."""
    return f"SKADIS Bracket {BUILD_VARIANT.capitalize()}"


def parameters():
    """The parameter table, including the variant's peg offset."""
    return {
        "bracketWidth": (BRACKET_WIDTH, "mm", "bracket width across the upright"),
        "plateThickness": (PLATE_THICKNESS, "mm", "board rear face sits on this"),
        "plateHeight": (PLATE_HEIGHT, "mm", "plate height"),
        "slotWidth": (SLOT_WIDTH, "mm", "measured upright slot width"),
        "slotPitchVertical": (SLOT_PITCH_VERTICAL, "mm", "1 inch, measured"),
        "faceMetalThickness": (FACE_METAL_THICKNESS, "mm", "upright face metal"),
        "hookTabWidth": ("slotWidth - 0.8 mm", "mm", "blade width through the slot"),
        "hookThroat": ("faceMetalThickness + 1.8 mm", "mm", "gap behind the plate"),
        "hookNeckHeight": (HOOK_NECK_HEIGHT, "mm", "bears on the slot bottom edge"),
        "hookLipThickness": (HOOK_LIP_THICKNESS, "mm", "lip behind the upright face"),
        "hookLipDrop": (HOOK_LIP_DROP, "mm", "engagement below the neck"),
        "hookLipChamfer": (HOOK_LIP_CHAMFER, "mm", "lead-in past slot burrs"),
        "topHookNeckTop": (TOP_HOOK_NECK_TOP, "mm", "top hook row"),
        "hookRows": (str(HOOK_ROWS), "", "hook rows (pattern count)"),
        "boardThickness": (BOARD_THICKNESS, "mm", "SKADIS panel thickness"),
        "boardSlotWidth": (BOARD_SLOT_WIDTH, "mm", "SKADIS slot width"),
        "boardSlotHeight": (BOARD_SLOT_HEIGHT, "mm", "SKADIS slot height"),
        "boardPitch": (BOARD_PITCH, "mm", "SKADIS grid pitch"),
        "pegClearance": (PEG_CLEARANCE, "mm", "sliding fit across the slot"),
        "pegRootProud": (PEG_ROOT_PROUD, "mm", "root past the board's front face"),
        "pegWidth": ("boardSlotWidth - pegClearance", "mm", "peg width in the slot"),
        "pegRootLength": (
            "boardThickness + pegRootProud",
            "mm",
            "root through the board",
        ),
        "pegRootHeight": (PEG_ROOT_HEIGHT, "mm", "slot top edge bears on this"),
        "pegProngThickness": (PEG_PRONG_THICKNESS, "mm", "prong in front of board"),
        "pegTotalHeight": (
            "boardSlotHeight - 4 mm",
            "mm",
            "prong rise above the root, and the lift needed to release",
        ),
        "pegProngChamfer": (PEG_PRONG_CHAMFER, "mm", "lead-in on the prong top"),
        "pegBearingFillet": (
            PEG_BEARING_FILLET,
            "mm",
            "round on the root top edges the board bears on",
        ),
        "pegProngFrontFillet": (
            PEG_PRONG_FRONT_FILLET,
            "mm",
            "round on the prong's front corners, where fingers meet it",
        ),
        "topPegRootZ": (TOP_PEG_ROOT_Z, "mm", "top peg root, above the plate foot"),
        "pegRows": (str(PEG_ROWS), "", "pegs per bracket (pattern count)"),
        "pegOffsetY": (peg_offset(), "mm", "offset onto the board's 40 mm grid"),
        "plateInboardExtension": (
            PLATE_INBOARD_EXTENSION,
            "mm",
            "extra plate toward the desk centre, where the peg crowds",
        ),
    }


def _point(x_mm, z_mm):
    """Sketch point on the XZ plane (sketch +y is model MINUS Z)."""
    return adsk.core.Point3D.create(x_mm * MM, -z_mm * MM, 0)


def _polyline(sketch, points_mm):
    """Closed polygon whose consecutive lines share sketch points."""
    lines = sketch.sketchCurves.sketchLines
    made = [lines.addByTwoPoints(_point(*points_mm[0]), _point(*points_mm[1]))]
    for target in points_mm[2:]:
        made.append(lines.addByTwoPoints(made[-1].endSketchPoint, _point(*target)))
    made.append(lines.addByTwoPoints(made[-1].endSketchPoint, made[0].startSketchPoint))
    return made


# pylint: disable-next=too-many-locals
def _pin_corners(sketch, lines, corners):
    """Dimension a corner's X and Z off the origin, by expression."""
    horizontal = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    vertical = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
    dimensions = sketch.sketchDimensions
    for index, (x_mm, z_mm, x_expression, z_expression) in enumerate(corners):
        point = lines[index].startSketchPoint
        for orientation, expression, text in (
            (horizontal, x_expression, (x_mm * 0.5, z_mm - 5.0 - index * 3.0)),
            (vertical, z_expression, (x_mm + 6.0 + index * 3.0, z_mm * 0.5)),
        ):
            if expression is None:
                continue
            dimension = dimensions.addDistanceDimension(
                sketch.originPoint, point, orientation, _point(*text)
            )
            dimension.parameter.expression = expression


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def _extrude(
    component, sketch, width_expression, operation, name, offset_expression=None
):
    """Symmetric extrude of every profile, optionally offset along Y."""
    profiles = adsk.core.ObjectCollection.create()
    for index in range(sketch.profiles.count):
        profiles.add(sketch.profiles.item(index))
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(profiles, operation)
    if offset_expression is not None:
        extrude_input.startExtent = adsk.fusion.OffsetStartDefinition.create(
            adsk.core.ValueInput.createByString(offset_expression)
        )
    extrude_input.setSymmetricExtent(
        adsk.core.ValueInput.createByString(width_expression), True
    )
    feature = extrudes.add(extrude_input)
    feature.name = name
    return feature


def _ensure_parameters(design):
    """Create or update user parameters, each with its declared unit."""
    user_parameters = design.userParameters
    for name, (value, unit, comment) in parameters().items():
        expression = value if isinstance(value, str) else f"{value} {unit}".strip()
        existing = user_parameters.itemByName(name)
        if existing:
            existing.expression = expression
            existing.comment = comment
        else:
            user_parameters.add(
                name,
                adsk.core.ValueInput.createByString(expression),
                unit,
                comment,
            )


def _drop_stale_parameters(design):
    """Delete parameters this script no longer declares, or that changed unit."""
    user_parameters = design.userParameters
    for index in range(user_parameters.count - 1, -1, -1):
        parameter = user_parameters.item(index)
        expected = parameters().get(parameter.name)
        if expected is None or parameter.unit != expected[1]:
            print(f"  dropping stale parameter {parameter.name}")
            parameter.deleteMe()


def _build_plate(component, plane):
    """The plate the hooks hang off and the board rests against."""
    sketch = component.sketches.add(plane)
    sketch.name = "Plate"
    corners = [
        (0.0, 0.0, None, None),
        (PLATE_THICKNESS, 0.0, None, None),
        (PLATE_THICKNESS, PLATE_HEIGHT, "plateThickness", "plateHeight"),
        (0.0, PLATE_HEIGHT, None, None),
    ]
    lines = _polyline(sketch, [(x, z) for x, z, _, _ in corners])
    constraints = sketch.geometricConstraints
    constraints.addCoincident(lines[0].startSketchPoint, sketch.originPoint)
    for line in (lines[0], lines[2]):
        constraints.addHorizontal(line)
    for line in (lines[1], lines[3]):
        constraints.addVertical(line)
    _pin_corners(sketch, lines, corners)
    # Asymmetric: bracketWidth centred on the hooks, plus the inboard
    # extension. A symmetric extrude offset by half the extension gives
    # exactly that, and inboard is +Y on the left bracket, -Y on the right.
    inboard = 1.0 if BUILD_VARIANT == "left" else -1.0
    _extrude(
        component,
        sketch,
        "bracketWidth + plateInboardExtension",
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "Plate",
        offset_expression=(
            "plateInboardExtension / 2" if inboard > 0 else "-plateInboardExtension / 2"
        ),
    )


# pylint: disable-next=too-many-locals
def _build_hooks(component, plane):
    """The proven hook profile, extruded and patterned down the plate."""
    sketch = component.sketches.add(plane)
    sketch.name = "Hook profile"
    neck_top = TOP_HOOK_NECK_TOP
    neck_bottom = neck_top - HOOK_NECK_HEIGHT
    lip_bottom = neck_bottom - HOOK_LIP_DROP
    back = -HOOK_THROAT
    lip_back = -(HOOK_THROAT + HOOK_LIP_THICKNESS)
    lines = _polyline(
        sketch,
        [
            (0.0, neck_top),
            (lip_back, neck_top),
            (lip_back, lip_bottom),
            (back - HOOK_LIP_CHAMFER, lip_bottom),
            (back, lip_bottom + HOOK_LIP_CHAMFER),
            (back, neck_bottom),
            (0.0, neck_bottom),
        ],
    )
    # pylint: disable-next=unbalanced-tuple-unpacking
    top, rear, bottom, chamfer, inner, neck, face = lines
    constraints = sketch.geometricConstraints
    for line in (top, bottom, neck):
        constraints.addHorizontal(line)
    for line in (rear, inner, face):
        constraints.addVertical(line)
    constraints.addCoincident(sketch.originPoint, face)
    horizontal = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    vertical = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
    dimensions = sketch.sketchDimensions

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def dimension(point_a, point_b, orientation, expression, text_x, text_z):
        item = dimensions.addDistanceDimension(
            point_a, point_b, orientation, _point(text_x, text_z)
        )
        item.parameter.expression = expression

    dimension(
        sketch.originPoint,
        top.startSketchPoint,
        vertical,
        "topHookNeckTop",
        6.0,
        neck_top / 2.0,
    )
    dimension(
        top.startSketchPoint,
        top.endSketchPoint,
        horizontal,
        "hookThroat + hookLipThickness",
        -4.0,
        neck_top + 5.0,
    )
    dimension(
        neck.endSketchPoint,
        neck.startSketchPoint,
        horizontal,
        "hookThroat",
        -2.0,
        neck_bottom - 3.0,
    )
    dimension(
        top.startSketchPoint,
        neck.endSketchPoint,
        vertical,
        "hookNeckHeight",
        3.0,
        (neck_top + neck_bottom) / 2.0,
    )
    dimension(
        inner.endSketchPoint,
        inner.startSketchPoint,
        vertical,
        "hookLipDrop - hookLipChamfer",
        -10.0,
        (neck_bottom + lip_bottom) / 2.0,
    )
    dimension(
        chamfer.startSketchPoint,
        chamfer.endSketchPoint,
        horizontal,
        "hookLipChamfer",
        -4.0,
        lip_bottom - 3.0,
    )
    dimension(
        chamfer.startSketchPoint,
        chamfer.endSketchPoint,
        vertical,
        "hookLipChamfer",
        -9.0,
        lip_bottom + 3.0,
    )
    extrude = _extrude(
        component,
        sketch,
        "hookTabWidth",
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Hook profile",
    )
    entities = adsk.core.ObjectCollection.create()
    entities.add(extrude)
    patterns = component.features.rectangularPatternFeatures
    pattern_input = patterns.createInput(
        entities,
        component.zConstructionAxis,
        adsk.core.ValueInput.createByString("hookRows"),
        adsk.core.ValueInput.createByString("-slotPitchVertical"),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )
    patterns.add(pattern_input).name = "Hook rows"


# pylint: disable-next=too-many-locals
def _build_pegs(component, plane):
    """Upward-opening pegs: root through the board, prong in front of it.

    The board is lowered on: each slot's top edge comes to rest on a root,
    and the prong ahead of the board stops it tipping out. The whole peg
    silhouette is shorter than the slot, so lifting it clear releases it.
    """
    sketch = component.sketches.add(plane)
    sketch.name = "Peg profile"
    face = PLATE_THICKNESS
    root_end = face + PEG_ROOT_LENGTH
    prong_end = root_end + PEG_PRONG_THICKNESS
    base = TOP_PEG_ROOT_Z
    root_top = base + PEG_ROOT_HEIGHT
    prong_top = base + PEG_TOTAL_HEIGHT
    face_expression = "plateThickness"
    root_end_expression = "plateThickness + pegRootLength"
    prong_end_expression = "plateThickness + pegRootLength + pegProngThickness"
    base_expression = "topPegRootZ"
    root_top_expression = "topPegRootZ + pegRootHeight"
    prong_top_expression = "topPegRootZ + pegTotalHeight"
    chamfer = PEG_PRONG_CHAMFER
    # The prong's top outer corner is chamfered: the board is lowered onto
    # these pegs blind, with the prong hidden behind it, so a slot that
    # arrives slightly off needs somewhere to slide rather than something to
    # catch on. Exactly the failure the first slot gauge had on the upright.
    corners = [
        (face, base, face_expression, base_expression),
        (prong_end, base, prong_end_expression, None),
        (
            prong_end,
            prong_top - chamfer,
            None,
            f"{prong_top_expression} - pegProngChamfer",
        ),
        (
            prong_end - chamfer,
            prong_top,
            f"{prong_end_expression} - pegProngChamfer",
            prong_top_expression,
        ),
        (root_end, prong_top, root_end_expression, None),
        (root_end, root_top, None, root_top_expression),
        (face, root_top, None, None),
    ]
    lines = _polyline(sketch, [(x, z) for x, z, _, _ in corners])
    constraints = sketch.geometricConstraints
    # Alternating edges are horizontal and vertical, except line 2 which is
    # the chamfer and stays free. Getting these groups the wrong way round
    # deforms the profile silently: the sketch still solves, the extrude
    # still succeeds, and only a probe catches it.
    for line in (lines[0], lines[3], lines[5]):
        constraints.addHorizontal(line)
    for line in (lines[1], lines[4], lines[6]):
        constraints.addVertical(line)
    _pin_corners(sketch, lines, corners)
    extrude = _extrude(
        component,
        sketch,
        "pegWidth",
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Peg profile",
        offset_expression="pegOffsetY",
    )
    entities = adsk.core.ObjectCollection.create()
    entities.add(extrude)
    patterns = component.features.rectangularPatternFeatures
    pattern_input = patterns.createInput(
        entities,
        component.zConstructionAxis,
        adsk.core.ValueInput.createByString("pegRows"),
        adsk.core.ValueInput.createByString("-boardPitch"),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )
    patterns.add(pattern_input).name = "Peg rows"


def _fillet_peg_roots(component, body):
    """Round the two top edges of each peg root — where the board lands.

    These are the long edges bounding the root's top face, running out from
    the plate to the prong. The board's slot descends over the root and its
    top edge comes to rest on that face, so these are the corners it slides
    past on the way down and bears against once seated.

    An earlier version filleted the root/plate junction instead, reasoning
    that it was the tension side of a cantilever. It is — but at ~4 MPa of
    ~40 that never mattered, and those edges sit inside the slot's void
    where the board never touches them. Corrected after the user moved the
    fillet in the document; the geometry here reproduces theirs.
    """
    root_end = PLATE_THICKNESS + PEG_ROOT_LENGTH
    wanted_z = [
        TOP_PEG_ROOT_Z - row * BOARD_PITCH + PEG_ROOT_HEIGHT for row in range(PEG_ROWS)
    ]
    wanted_y = [peg_offset() - PEG_WIDTH / 2.0, peg_offset() + PEG_WIDTH / 2.0]
    edges = adsk.core.ObjectCollection.create()
    for index in range(body.edges.count):
        edge = body.edges.item(index)
        start = edge.startVertex.geometry
        end = edge.endVertex.geometry
        if abs(start.y - end.y) > 1e-6 or abs(start.z - end.z) > 1e-6:
            continue  # must run along X, out from the plate
        if abs(start.x - end.x) < 1e-6:
            continue
        low_x, high_x = sorted((start.x / MM, end.x / MM))
        if low_x < PLATE_THICKNESS - 0.01 or high_x > root_end + 0.01:
            continue
        if not any(abs(start.z / MM - z) < 0.01 for z in wanted_z):
            continue
        if not any(abs(start.y / MM - y) < 0.01 for y in wanted_y):
            continue
        edges.add(edge)
    expected = 2 * PEG_ROWS
    if edges.count != expected:
        raise RuntimeError(
            f"expected {expected} peg bearing edges to fillet, found {edges.count}"
        )
    fillets = component.features.filletFeatures
    fillet_input = fillets.createInput()
    fillet_input.addConstantRadiusEdgeSet(
        edges, adsk.core.ValueInput.createByString("pegBearingFillet"), True
    )
    fillets.add(fillet_input).name = "Peg bearing fillets"


def _fillet_prong_front(component, body):
    """Round the two vertical corners of each prong's front face.

    The outermost surface of the whole bracket, and the one a hand lands on
    when pressing the board home — sharp printed corners there are the ones
    you feel. Added by hand in the document (v9) and folded back here.
    """
    prong_end = PLATE_THICKNESS + PEG_ROOT_LENGTH + PEG_PRONG_THICKNESS
    wanted_y = [peg_offset() - PEG_WIDTH / 2.0, peg_offset() + PEG_WIDTH / 2.0]
    edges = adsk.core.ObjectCollection.create()
    for index in range(body.edges.count):
        edge = body.edges.item(index)
        start = edge.startVertex.geometry
        end = edge.endVertex.geometry
        if abs(start.x - end.x) > 1e-6 or abs(start.y - end.y) > 1e-6:
            continue  # must run along Z
        if abs(start.z - end.z) < 1e-6:
            continue
        if abs(start.x / MM - prong_end) > 0.01:
            continue  # must lie in the prong's front face
        if not any(abs(start.y / MM - y) < 0.01 for y in wanted_y):
            continue
        edges.add(edge)
    expected = 2 * PEG_ROWS
    if edges.count != expected:
        raise RuntimeError(
            f"expected {expected} prong front edges to fillet, found {edges.count}"
        )
    fillets = component.features.filletFeatures
    fillet_input = fillets.createInput()
    fillet_input.addConstantRadiusEdgeSet(
        edges, adsk.core.ValueInput.createByString("pegProngFrontFillet"), True
    )
    fillets.add(fillet_input).name = "Prong front fillets"


def _probe(body, x_mm, y_mm, z_mm):
    point = adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)
    return body.pointContainment(point)


def _verify(body):  # pylint: disable=too-many-locals,too-many-statements
    """Numeric probes; raise on any surprise so the failure is loud."""
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    outside = adsk.fusion.PointContainment.PointOutsidePointContainment
    lip_mid_x = -(HOOK_THROAT + HOOK_LIP_THICKNESS / 2.0)
    face = PLATE_THICKNESS
    root_mid_x = face + PEG_ROOT_LENGTH / 2.0
    prong_mid_x = face + PEG_ROOT_LENGTH + PEG_PRONG_THICKNESS / 2.0
    checks = [("plate interior", 2.7, 0.0, 30.0, inside)]
    for row in range(HOOK_ROWS):
        neck_top = TOP_HOOK_NECK_TOP - row * SLOT_PITCH_VERTICAL
        lip_z = neck_top - HOOK_NECK_HEIGHT - HOOK_LIP_DROP / 2.0
        checks.append((f"hook row {row} lip", lip_mid_x, 0.0, lip_z, inside))
    for row in range(PEG_ROWS):
        base = TOP_PEG_ROOT_Z - row * BOARD_PITCH
        offset = peg_offset()
        checks += [
            (
                f"peg {row} root",
                root_mid_x,
                offset,
                base + PEG_ROOT_HEIGHT / 2.0,
                inside,
            ),
            (
                f"peg {row} prong",
                prong_mid_x,
                offset,
                base + PEG_TOTAL_HEIGHT - 2.0,
                inside,
            ),
            (
                f"peg {row} board space clear",
                root_mid_x,
                offset,
                base + PEG_TOTAL_HEIGHT - 2.0,
                outside,
            ),
            (
                f"peg {row} clear beside",
                root_mid_x,
                offset + PEG_WIDTH,
                base + PEG_ROOT_HEIGHT / 2.0,
                outside,
            ),
            (
                f"peg {row} nothing above prong",
                prong_mid_x,
                offset,
                base + PEG_TOTAL_HEIGHT + 2.0,
                outside,
            ),
        ]
    failures = []
    for label, x_mm, y_mm, z_mm, expected in checks:
        actual = _probe(body, x_mm, y_mm, z_mm)
        state = "ok" if actual == expected else f"FAIL (got {actual})"
        print(f"  probe {label:28s} ({x_mm:6.1f},{y_mm:6.1f},{z_mm:6.1f}) {state}")
        if actual != expected:
            failures.append(label)
    if failures:
        raise RuntimeError(f"geometry probes failed: {failures}")


def _references(expression, name):
    """True if a parameter expression references the given name."""
    index = expression.find(name)
    while index != -1:
        before = expression[index - 1] if index else " "
        after_index = index + len(name)
        after = expression[after_index] if after_index < len(expression) else " "
        if not (before.isalnum() or before == "_") and not (
            after.isalnum() or after == "_"
        ):
            return True
        index = expression.find(name, index + 1)
    return False


def _audit_parameters(design):
    """Fail the build if a parameter drives nothing or has the wrong unit."""
    user_parameters = design.userParameters
    all_parameters = design.allParameters
    expressions = {}
    for index in range(all_parameters.count):
        parameter = all_parameters.item(index)
        expressions[parameter.name] = parameter.expression or ""
    idle, wrong_unit = [], []
    for index in range(user_parameters.count):
        parameter = user_parameters.item(index)
        if parameter.unit != parameters()[parameter.name][1]:
            wrong_unit.append(f"{parameter.name}={parameter.unit!r}")
        used = any(
            other != parameter.name and _references(expression, parameter.name)
            for other, expression in expressions.items()
        )
        if not used:
            idle.append(parameter.name)
    print(f"  parameters: {user_parameters.count} declared, all driving geometry")
    if wrong_unit or idle:
        raise RuntimeError(f"audit failed: idle={idle} wrong_unit={wrong_unit}")


def _export(design):
    root = design.rootComponent
    export_manager = design.exportManager
    step_path = f"{PROJECT_DIR}/cad/{export_name()}.step"
    archive_path = f"{PROJECT_DIR}/cad/{export_name()}.f3d"
    stl_path = f"{PROJECT_DIR}/exports/{export_name()}.stl"
    export_manager.execute(export_manager.createSTEPExportOptions(step_path, root))
    export_manager.execute(
        export_manager.createFusionArchiveExportOptions(archive_path, root)
    )
    stl_options = export_manager.createSTLExportOptions(root, stl_path)
    stl_options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    export_manager.execute(stl_options)
    print(f"exported {step_path}")
    print(f"exported {archive_path}")
    print(f"exported {stl_path}")


def _fusion_project(app):
    projects = app.data.dataProjects
    for index in range(projects.count):
        if projects.item(index).name == FUSION_PROJECT_NAME:
            return projects.item(index)
    return projects.add(FUSION_PROJECT_NAME)


def _existing_data_file(folder, name):
    files = folder.dataFiles
    hits = [files.item(i) for i in range(files.count) if files.item(i).name == name]
    if len(hits) > 1:
        raise RuntimeError(f"{len(hits)} documents named {name!r} in the project")
    return hits[0] if hits else None


def _recorded_volume(data_file):
    """Body volume in mm^3 recorded by the most recent scripted save."""
    versions = data_file.versions
    for index in range(versions.count):  # newest first
        text = versions.item(index).description or ""
        if text.startswith("scripted") and " vol " in text:
            try:
                return float(text.split(" vol ")[1].split()[0])
            except (IndexError, ValueError):
                return None
    return None


def _refuse_if_hand_edited(data_file, design):
    """Never clear a timeline carrying geometry this script did not build.

    Fusion labels a human's save "User Saved". That alone is not proof of an
    edit — opening a document and pressing save is common and harmless — so
    compare the geometry against the volume recorded by the last scripted
    save. Same volume, benign save, carry on. Different, stop: an edit is
    sitting there and rebuilding would discard it. That has already cost the
    label clip's mouth construction and the SKADIS peg fillet, both of which
    had to be reverse-engineered out of version history.
    """
    description = data_file.description or ""
    if ALLOW_OVERWRITE or description.startswith("scripted"):
        return
    recorded = _recorded_volume(data_file)
    bodies = design.rootComponent.bRepBodies
    current = bodies.item(0).volume / (MM**3) if bodies.count else None
    if recorded is not None and current is not None and abs(current - recorded) < 1.0:
        print(
            f"  note: last save was {description!r}, but the geometry still "
            f"matches the last scripted build ({current:.0f} mm^3) — proceeding"
        )
        return
    difference = (
        f"{current:.0f} vs {recorded:.0f} mm^3"
        if recorded is not None and current is not None
        else "no recorded volume to compare"
    )
    raise RuntimeError(
        f"{data_file.name!r} v{data_file.versionNumber} was last saved by hand "
        f"({description!r}) and its geometry differs: {difference}. Rebuilding "
        "would discard that edit. Inspect the document, fold the change into "
        "this script, then rebuild — or set ALLOW_OVERWRITE = True if the edit "
        "is genuinely disposable."
    )


def _clear_timeline(design):
    timeline = design.timeline
    while timeline.count:
        before = timeline.count
        timeline.item(timeline.count - 1).entity.deleteMe()
        if timeline.count >= before:
            raise RuntimeError("timeline item refused to delete")


# pylint: disable-next=too-many-statements
def run(_context: str):
    """Build the bracket into its saved document, verify, export, version."""
    if BUILD_VARIANT not in ("left", "right"):
        raise ValueError(f"BUILD_VARIANT must be left or right, got {BUILD_VARIANT!r}")
    app = adsk.core.Application.get()
    folder = _fusion_project(app).rootFolder
    data_file = _existing_data_file(folder, doc_name())
    if data_file is None:
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    else:
        document = app.documents.open(data_file, True)
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError("active document is not a design")
    if data_file is not None:
        _refuse_if_hand_edited(data_file, design)
        _clear_timeline(design)
        _drop_stale_parameters(design)
    _ensure_parameters(design)
    component = design.rootComponent
    plane = component.xZConstructionPlane
    _check_peg_offset()
    _check_peg_geometry()
    _build_plate(component, plane)
    _build_hooks(component, plane)
    _build_pegs(component, plane)
    if component.bRepBodies.count != 1:
        raise RuntimeError(f"expected one body, got {component.bRepBodies.count}")
    _fillet_peg_roots(component, component.bRepBodies.item(0))
    _fillet_prong_front(component, component.bRepBodies.item(0))

    if component.bRepBodies.count != 1:
        raise RuntimeError(f"expected one body, got {component.bRepBodies.count}")
    body = component.bRepBodies.item(0)
    body.name = export_name()

    bounding = body.boundingBox
    print(f"variant: {BUILD_VARIANT}, peg offset {peg_offset():.1f} mm")
    print(f"document: {document.name}")
    print(f"volume: {body.volume / (MM ** 3):.0f} mm^3")
    print(
        "bbox mm: "
        f"x [{bounding.minPoint.x / MM:.1f}, {bounding.maxPoint.x / MM:.1f}] "
        f"y [{bounding.minPoint.y / MM:.1f}, {bounding.maxPoint.y / MM:.1f}] "
        f"z [{bounding.minPoint.z / MM:.1f}, {bounding.maxPoint.z / MM:.1f}]"
    )
    _verify(body)
    _audit_parameters(design)
    _export(design)
    description = (
        f"scripted {BUILD_VARIANT} build {datetime.date.today().isoformat()}: "
        f"peg offset {peg_offset():.1f} mm, board {BOARD_THICKNESS} mm"
    )
    # saveAs and save return a BOOLEAN. Ignoring it prints "saved" over six
    # documents that were never written: they stay open, unsaved, and named,
    # which looks exactly like success from the script's side.
    description += f" vol {body.volume / (MM ** 3):.0f} mm3"
    if data_file is None:
        saved = document.saveAs(doc_name(), folder, description, "")
    else:
        saved = document.save(description)
    # saveAs can return True and still not save: the document stays open,
    # named, and unsaved. isSaved is the only answer worth believing.
    if not saved or not document.isSaved:
        raise RuntimeError(
            f"{doc_name()!r} NOT saved (saveAs returned {saved}, "
            f"isSaved={document.isSaved}). The CAD exports above are still good."
        )
    print(f"saved '{doc_name()}' in project '{FUSION_PROJECT_NAME}': {description}")
    print("build complete")
