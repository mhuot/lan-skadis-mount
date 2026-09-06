"""Fusion 360 script: SKADIS nut-channel bracket for Ergotron DuraFrame.

Run inside Fusion via scripts/run_in_fusion.py. Same proven hook stack as
build_skadis_bracket.py, but the board is bolted on instead of hung on pegs.

Why this exists. The peg bracket works, and its photographs prove it, but it
has no adjustment anywhere: four rigid posts have to enter four slots at
once, so every error in the upright measurement, in print shrinkage, and in
the board's own tolerance lands on the person holding the board. Measured
3-5 mm out left to right, 2026-09-06, and there is nothing to turn.

The joint this builds instead:

  * A DIN 562 M4 square nut feeds edgewise through a SKADIS slot (2.2 mm
    thick passes the 5 mm slot), turns flat behind the board, and drops into
    a horizontal channel cut in this plate's face. The channel is 7.4 mm
    tall against a 7.0 mm nut, so the nut cannot rotate and can be tightened
    one-handed from the front.
  * The channel is mountTravel longer than the nut. That length IS the
    left-right adjustment: slide, then tighten.
  * The IKEA decorative M4 screw goes in from the front, through the board
    slot, into the nut. The nut stands nutProud of the plate face so
    tightening clamps it against the channel floor rather than leaving it
    free to slide.

Why the plate is 11 mm and not the peg bracket's 5.4 mm: the screw is 15 mm
long and the board is 6.0 mm thick (MEASURED 2026-09-06 -- the peg bracket
was built to a community-quoted 4.6 and its pegs were therefore 1.4 mm short
of reaching through the board, which is its own bug). That leaves 9.0 mm of
screw behind the board with nowhere to go: at 5.4 mm the tip would stand
proud of the plate's back face and foul the upright's face metal. So
plateThickness is DERIVED from the screw, not chosen. A happy side effect
answers the question the sketch asked -- whether the inboard extension needs
a support rib. Bending stiffness goes as thickness cubed, so 5.4 -> 11.0 is
already 8.5x stiffer out of plane; a rib on top of that is carrying nothing.

Attribution: the idea of hanging SKADIS on printed pegs rather than bolting
through it comes from "Skadis to Kallax mount adapter" by WegBier
(https://www.printables.com/model/137113-skadis-to-kallax-mount-adapter),
licensed CC BY-NC-SA, incompatible with this repository's MIT licence, so
none of that model's geometry is reproduced here. This part does not use a
peg at all. SKADIS interface dimensions are measurements of IKEA's product,
cross-checked against https://github.com/franpoli/OpenSCADutil and
https://github.com/TassSinclair/skadis, and then re-measured on the board.

Variants: --variant left, --variant right, --variant coupon. Print the
coupon FIRST. It is one channel in a stub of plate, about 25 minutes, and it
is the only cheap way to find out whether the nut and screw numbers below
match the hardware actually in your hand.
"""

# The whole part lives in one file on purpose: Fusion caches imported
# modules AND globals across MCP runs, so a shared params module would
# serve stale numbers. That trade costs a long module.
# pylint: disable=too-many-lines

import datetime
import math

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
# MEASURED 2026-09-05: 28 13/16" between the FACING edges of the two slot
# columns. Centre to centre is that plus one slot width.
SLOT_INSIDE_GAP = 731.84
UPRIGHT_SPACING = SLOT_INSIDE_GAP + SLOT_WIDTH

# --- SKADIS interface ------------------------------------------------------
# MEASURED 2026-09-06: the board is ~6 mm, not the 4.6 mm the community
# libraries quote. Everything downstream of a screw length depends on this.
BOARD_THICKNESS = 6.0
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

# --- Fastener, from the hardware in hand -----------------------------------
# VERIFY THESE ON THE COUPON BEFORE PRINTING BRACKETS. Nut figures are
# DIN 562 M4 nominal; the screw length is measured.
NUT_ACROSS_FLATS = 7.0
NUT_THICKNESS = 2.2
NUT_CHANNEL_CLEARANCE = 0.4  # across flats and along the channel
# The nut stands this far out of its pocket so the screw clamps it down onto
# the channel floor. Flush or recessed and the nut is free to slide along the
# channel after tightening, which throws away the adjustment you just made.
NUT_PROUD = 0.2
SCREW_LENGTH = 15.0  # MEASURED: IKEA SKADIS decorative M4
SCREW_DIAMETER = 4.0
SCREW_CLEARANCE = 0.8
SCREW_TIP_CLEARANCE = 2.2  # tip stops this far short of the plate's back face
assert NUT_THICKNESS < BOARD_SLOT_WIDTH, "nut will not feed through a board slot"
assert NUT_ACROSS_FLATS < BOARD_SLOT_HEIGHT, "nut will not feed through a board slot"

# --- Plate and mounts ------------------------------------------------------
BRACKET_WIDTH = 24.0  # still fits the 25.4 gap at the module centre
# DERIVED, not chosen: deep enough that a SCREW_LENGTH screw through a
# BOARD_THICKNESS board stops SCREW_TIP_CLEARANCE short of the back face.
PLATE_THICKNESS = SCREW_LENGTH - BOARD_THICKNESS - NUT_PROUD + SCREW_TIP_CLEARANCE
NUT_POCKET_DEPTH = NUT_THICKNESS - NUT_PROUD
NUT_CHANNEL_HEIGHT = NUT_ACROSS_FLATS + NUT_CHANNEL_CLEARANCE
SCREW_SLOT_WIDTH = SCREW_DIAMETER + SCREW_CLEARANCE
# +-6 mm. The reported error is 3-5 mm; this also swallows 12 mm of error in
# UPRIGHT_SPACING, which is the measurement that has been wrong twice.
MOUNT_TRAVEL = 12.0
NUT_CHANNEL_LENGTH = MOUNT_TRAVEL + NUT_ACROSS_FLATS + NUT_CHANNEL_CLEARANCE
SCREW_SLOT_LENGTH = MOUNT_TRAVEL + SCREW_SLOT_WIDTH
# ONE channel per bracket. A board hangs on four of these, two per upright,
# so one channel each is already four screws in a rectangle -- and a second
# channel would add a constraint rather than strength, because the two rows
# on one bracket are pinned 40 mm apart with no way to take up error between
# them. Spacing the brackets vertically instead puts that adjustment back in
# the assembly, where it belongs: see bracket_spacing_options().
MOUNT_ROWS = 1
MOUNT_EDGE_MARGIN = 2.5  # plate left beyond the end of a channel
# Plate height is DERIVED from whichever stack is taller, hooks or channels,
# so dropping to one channel actually shortens the part instead of leaving
# 12 mm of plate above a channel that is no longer there.
HOOK_STACK_HEIGHT = (
    2.0
    + (HOOK_ROWS - 1) * SLOT_PITCH_VERTICAL
    + HOOK_NECK_HEIGHT
    + HOOK_LIP_DROP
    + MOUNT_EDGE_MARGIN
)
MOUNT_STACK_HEIGHT = (
    (MOUNT_ROWS - 1) * BOARD_PITCH + NUT_CHANNEL_HEIGHT + 2 * MOUNT_EDGE_MARGIN
)
PLATE_HEIGHT = 2.0 * math.ceil(max(HOOK_STACK_HEIGHT, MOUNT_STACK_HEIGHT) / 2.0)
TOP_HOOK_NECK_TOP = PLATE_HEIGHT - 2.0
# Centre the channel stack on the plate, whatever the row count.
TOP_MOUNT_Z = (PLATE_HEIGHT + (MOUNT_ROWS - 1) * BOARD_PITCH) / 2.0
PLATE_INBOARD_EXTENSION = 9.0
SLOT_OVERSHOOT = 1.0  # cut profiles reach past the faces they cut
BOARD_SHIFT = 0.0

# The coupon is a stub of the real cross-section carrying one channel.
COUPON_HEIGHT = 20.0
COUPON_MOUNT_Z = 10.0


def _is_coupon():
    """True when this run builds the fit coupon rather than a bracket."""
    return BUILD_VARIANT == "coupon"


def plate_height():
    """Plate height for this variant, mm."""
    return COUPON_HEIGHT if _is_coupon() else PLATE_HEIGHT


def top_mount_z():
    """Z of the top channel's centre for this variant, mm."""
    return COUPON_MOUNT_Z if _is_coupon() else TOP_MOUNT_Z


def mount_rows():
    """Channel rows for this variant."""
    return 1 if _is_coupon() else MOUNT_ROWS


def bracket_spacing_options(limit=9):
    """Vertical spacings, in hook pitches, that two brackets can share.

    With one channel per bracket the vertical alignment moves out of the
    part and into the assembly, and the two grids do not agree: the upright
    puts brackets on a 25.4 mm pitch and the board puts slots on 40 mm. A
    screw has boardSlotHeight - screwDiameter of freedom inside its slot, so
    a spacing works only if some whole number of board pitches lands inside
    that. 2 x 25.4 = 50.8 against 40 misses by 10.8 of an available 11.0 and
    is not a spacing to trust; 3 x 25.4 = 76.2 against 80 misses by 3.8.
    """
    play = BOARD_SLOT_HEIGHT - SCREW_DIAMETER
    options = []
    for pitches in range(1, limit + 1):
        rise = pitches * SLOT_PITCH_VERTICAL
        rows = max(1, round(rise / BOARD_PITCH))
        miss = abs(rise - rows * BOARD_PITCH)
        if miss <= play * 0.6:
            options.append((pitches, rise, rows, miss))
    return options


def grid_correction():
    """How far the right bracket's channel sits from the left one's, mm.

    Unchanged from the peg bracket: the nut still lands in a board slot, so
    the two brackets' mount centres still have to be a whole number of
    boardPitch apart while the brackets themselves are uprightSpacing apart.
    The difference now is that being wrong is recoverable -- the channel has
    mountTravel of slide in it -- instead of fatal.
    """
    remainder = UPRIGHT_SPACING % BOARD_PITCH
    if not remainder:
        return 0.0
    apart = round(BOARD_PITCH - remainder, 2)
    together = round(-remainder, 2)
    return apart if abs(apart) <= abs(together) else together


def mount_offset():
    """This bracket's channel centre, mm. Negative is left.

    Half the grid correction each way, so the pair mirrors. Hard-coding one
    side at zero and loading the whole correction onto the other is what
    walked the right bracket's peg off its plate.

    The coupon takes the left bracket's offset rather than sitting on the
    centreline, so it is a real slice of a real part: centring it would test
    a channel that no bracket actually has, and would fail the plate-edge
    check for a reason the bracket does not have.
    """
    half = grid_correction() / 2.0
    # Keyed off "right", not "left", so the coupon lands on the same side
    # as plate_span() puts its inboard extension. Keying both off "left"
    # independently is how the coupon got a left plate and a right channel.
    sign = 1.0 if BUILD_VARIANT == "right" else -1.0
    return round(BOARD_SHIFT + sign * half, 2)


def plate_span():
    """(outboard edge, inboard edge) of the plate in Y, mm."""
    half = BRACKET_WIDTH / 2.0
    if BUILD_VARIANT == "right":
        return half, -half - PLATE_INBOARD_EXTENSION
    return -half, half + PLATE_INBOARD_EXTENSION


def _check_mount_fits():
    """The channel, plus its travel, has to stay on the plate."""
    outboard_edge, inboard_edge = plate_span()
    low, high = sorted((outboard_edge, inboard_edge))
    channel_low = mount_offset() - NUT_CHANNEL_LENGTH / 2.0
    channel_high = mount_offset() + NUT_CHANNEL_LENGTH / 2.0
    gaps = (channel_low - low, high - channel_high)
    if min(gaps) < MOUNT_EDGE_MARGIN:
        raise RuntimeError(
            f"channel at {mount_offset():+.2f} mm spanning "
            f"{NUT_CHANNEL_LENGTH:.1f} mm leaves {min(gaps):.2f} mm of plate "
            f"beside it, under the {MOUNT_EDGE_MARGIN} mm margin. Raise "
            f"PLATE_INBOARD_EXTENSION (now {PLATE_INBOARD_EXTENSION} mm) or "
            f"cut MOUNT_TRAVEL (now {MOUNT_TRAVEL} mm)."
        )
    if plate_height() < top_mount_z() + NUT_CHANNEL_HEIGHT / 2.0 + MOUNT_EDGE_MARGIN:
        raise RuntimeError("top channel runs off the top of the plate")
    lowest = top_mount_z() - (mount_rows() - 1) * BOARD_PITCH
    if lowest - NUT_CHANNEL_HEIGHT / 2.0 < MOUNT_EDGE_MARGIN:
        raise RuntimeError("bottom channel runs off the bottom of the plate")
    tip = PLATE_THICKNESS + BOARD_THICKNESS + NUT_PROUD - SCREW_LENGTH
    if tip < 0.5:
        raise RuntimeError(
            f"a {SCREW_LENGTH} mm screw through a {BOARD_THICKNESS} mm board "
            f"ends {tip:.2f} mm from the plate's back face -- it would foul "
            "the upright's face metal"
        )
    if not _is_coupon():
        for pitches, rise, rows, miss in bracket_spacing_options():
            print(
                f"  stack two brackets {pitches} hook pitches apart "
                f"({rise:.1f} mm) for {rows} board rows ({rows * BOARD_PITCH:.0f} mm), "
                f"off by {miss:.1f} mm of {BOARD_SLOT_HEIGHT - SCREW_DIAMETER:.1f} mm"
            )
    print(
        f"  plate {min(low, high):+.1f}..{max(low, high):+.1f} mm, "
        f"channel gaps {gaps[0]:.2f} / {gaps[1]:.2f} mm, "
        f"screw tip stops {tip:.2f} mm short of the back face"
    )


def export_name():
    """Stem for the exported STL/STEP/F3D."""
    return f"skadis_nut_{BUILD_VARIANT}"


def doc_name():
    """Name of the saved Fusion document."""
    return f"SKADIS Nut Bracket {BUILD_VARIANT.capitalize()}"


def _hook_parameters():
    """Parameters that only the hook stack uses; the coupon has no hooks."""
    return {
        "slotWidth": (SLOT_WIDTH, "mm", "measured upright slot width"),
        "slotPitchVertical": (SLOT_PITCH_VERTICAL, "mm", "1 inch, measured"),
        "faceMetalThickness": (FACE_METAL_THICKNESS, "mm", "upright face metal"),
        "hookTabWidth": ("slotWidth - 0.8 mm", "mm", "blade width through the slot"),
        "hookThroat": ("faceMetalThickness + 1.8 mm", "mm", "gap behind the plate"),
        "hookNeckHeight": (HOOK_NECK_HEIGHT, "mm", "bears on the slot bottom edge"),
        "hookLipThickness": (HOOK_LIP_THICKNESS, "mm", "lip behind the upright face"),
        "hookLipDrop": (HOOK_LIP_DROP, "mm", "engagement below the neck"),
        "hookLipChamfer": (HOOK_LIP_CHAMFER, "mm", "lead-in past slot burrs"),
        "topHookNeckTop": ("plateHeight - 2 mm", "mm", "top hook row"),
        "hookRows": (str(HOOK_ROWS), "", "hook rows (pattern count)"),
    }


def parameters():
    """The parameter table for this variant. Every entry drives geometry."""
    table = {
        "bracketWidth": (BRACKET_WIDTH, "mm", "bracket width across the upright"),
        "plateHeight": (plate_height(), "mm", "plate height"),
        "plateInboardExtension": (
            PLATE_INBOARD_EXTENSION,
            "mm",
            "extra plate toward the desk centre, where the channel reaches",
        ),
        "boardThickness": (BOARD_THICKNESS, "mm", "measured SKADIS panel thickness"),
        "screwLength": (SCREW_LENGTH, "mm", "measured decorative M4 screw"),
        "screwDiameter": (SCREW_DIAMETER, "mm", "M4 shank"),
        "screwClearance": (SCREW_CLEARANCE, "mm", "slack around the shank"),
        "screwTipClearance": (
            SCREW_TIP_CLEARANCE,
            "mm",
            "tip stops this short of the plate's back face",
        ),
        "screwSlotWidth": (
            "screwDiameter + screwClearance",
            "mm",
            "screw relief slot height",
        ),
        "nutAcrossFlats": (NUT_ACROSS_FLATS, "mm", "M4 square nut across flats"),
        "nutThickness": (NUT_THICKNESS, "mm", "M4 square nut thickness"),
        "nutChannelClearance": (
            NUT_CHANNEL_CLEARANCE,
            "mm",
            "slack around the nut in its channel",
        ),
        "nutProud": (NUT_PROUD, "mm", "nut stands out of the pocket to be clamped"),
        "nutPocketDepth": ("nutThickness - nutProud", "mm", "channel depth"),
        "nutChannelHeight": (
            "nutAcrossFlats + nutChannelClearance",
            "mm",
            "channel height; under the nut's diagonal so it cannot turn",
        ),
        "plateThickness": (
            "screwLength - boardThickness - nutProud + screwTipClearance",
            "mm",
            "derived: deep enough to swallow the screw",
        ),
        "mountTravel": (MOUNT_TRAVEL, "mm", "left-right adjustment"),
        "nutChannelLength": (
            "mountTravel + nutAcrossFlats + nutChannelClearance",
            "mm",
            "channel length along the plate",
        ),
        "screwSlotLength": (
            "mountTravel + screwSlotWidth",
            "mm",
            "relief slot length along the plate",
        ),
        "topMountZ": (top_mount_z(), "mm", "top channel centre"),
        "mountOffsetY": (mount_offset(), "mm", "channel centre on the board's grid"),
        "slotOvershoot": (SLOT_OVERSHOOT, "mm", "cuts reach past the faces they cut"),
    }
    if not _is_coupon():
        table.update(_hook_parameters())
    # boardPitch and mountRows exist only to drive the row pattern, and the
    # coupon has a single row and therefore no pattern. Declaring them anyway
    # would leave two parameters driving nothing, which this build treats as
    # a failure rather than a wart.
    if mount_rows() > 1:
        table.update(
            {
                "boardPitch": (BOARD_PITCH, "mm", "SKADIS grid pitch"),
                "mountRows": (
                    str(mount_rows()),
                    "",
                    "channels per bracket (pattern count)",
                ),
            }
        )
    return table


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
        (PLATE_THICKNESS, plate_height(), "plateThickness", "plateHeight"),
        (0.0, plate_height(), None, None),
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
    inboard = -1.0 if BUILD_VARIANT == "right" else 1.0
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


# pylint: disable-next=too-many-arguments,too-many-positional-arguments,too-many-locals
def _cut_rectangle(
    component, plane, name, geometry, expressions, width_expression, offset_expression
):
    """Cut one rectangle in the XZ plane, extruded symmetrically along Y.

    geometry is (x_low, x_high, z_low, z_high) in mm for the initial sketch;
    expressions is (x_high, z_low, x_span, z_span) as parameter expressions.
    x_low is left to fall out of x_high minus the span, because it is often
    negative and a distance dimension carries no sign: dimensioning it off
    the origin lets the solver mirror the rectangle to the wrong side of the
    plate, which is exactly how the peg strip flipped.
    """
    x_low, x_high, z_low, z_high = geometry
    x_high_expression, z_low_expression, x_span, z_span = expressions
    sketch = component.sketches.add(plane)
    sketch.name = name
    lines = _polyline(
        sketch,
        [(x_low, z_low), (x_high, z_low), (x_high, z_high), (x_low, z_high)],
    )
    constraints = sketch.geometricConstraints
    for line in (lines[0], lines[2]):
        constraints.addHorizontal(line)
    for line in (lines[1], lines[3]):
        constraints.addVertical(line)
    horizontal = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    vertical = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
    dimensions = sketch.sketchDimensions
    corner = lines[1].startSketchPoint  # (x_high, z_low)
    for point_a, point_b, orientation, expression, text in (
        (sketch.originPoint, corner, horizontal, x_high_expression, (x_high / 2, -6.0)),
        (sketch.originPoint, corner, vertical, z_low_expression, (-6.0, z_low / 2)),
        (lines[0].startSketchPoint, corner, horizontal, x_span, (x_low, z_low - 4.0)),
        (corner, lines[1].endSketchPoint, vertical, z_span, (x_high + 4.0, z_low)),
    ):
        dimension = dimensions.addDistanceDimension(
            point_a, point_b, orientation, _point(*text)
        )
        dimension.parameter.expression = expression
    return _extrude(
        component,
        sketch,
        width_expression,
        adsk.fusion.FeatureOperations.CutFeatureOperation,
        name,
        offset_expression=offset_expression,
    )


def _pattern_down(component, feature, name):
    """Repeat a mount feature down the plate on the board's 40 mm pitch."""
    if mount_rows() < 2:
        return
    entities = adsk.core.ObjectCollection.create()
    entities.add(feature)
    patterns = component.features.rectangularPatternFeatures
    pattern_input = patterns.createInput(
        entities,
        component.zConstructionAxis,
        adsk.core.ValueInput.createByString("mountRows"),
        adsk.core.ValueInput.createByString("-boardPitch"),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )
    patterns.add(pattern_input).name = name


def _build_mounts(component, plane):
    """The nut channel and the screw relief behind it, one row per mount.

    Two cuts, both open to the front face where the board lands:

      * the channel, nutPocketDepth deep, nutChannelHeight tall. The nut
        lives here and slides along it. It is deliberately shallower than
        the nut is thick so the screw clamps the nut to the channel floor.
      * the screw relief, straight through to the plate's back face. It has
        to be through rather than blind: 15 mm of screw minus a 6 mm board
        is 9 mm behind the board, and a blind floor is one more thing to
        bottom out on if the screw or the board is not what we measured.

    The relief is shorter and narrower than the channel, so the channel
    always has a floor for the nut to be clamped against, whatever position
    along the travel it ends up in.
    """
    face = PLATE_THICKNESS
    channel_z = top_mount_z()
    channel = _cut_rectangle(
        component,
        plane,
        "Nut channel",
        (
            face - NUT_POCKET_DEPTH,
            face + SLOT_OVERSHOOT,
            channel_z - NUT_CHANNEL_HEIGHT / 2.0,
            channel_z + NUT_CHANNEL_HEIGHT / 2.0,
        ),
        (
            "plateThickness + slotOvershoot",
            "topMountZ - nutChannelHeight / 2",
            "nutPocketDepth + slotOvershoot",
            "nutChannelHeight",
        ),
        "nutChannelLength",
        "mountOffsetY",
    )
    _pattern_down(component, channel, "Nut channel rows")
    relief = _cut_rectangle(
        component,
        plane,
        "Screw relief",
        (
            -SLOT_OVERSHOOT,
            face + SLOT_OVERSHOOT,
            channel_z - SCREW_SLOT_WIDTH / 2.0,
            channel_z + SCREW_SLOT_WIDTH / 2.0,
        ),
        (
            "plateThickness + slotOvershoot",
            "topMountZ - screwSlotWidth / 2",
            "plateThickness + 2 * slotOvershoot",
            "screwSlotWidth",
        ),
        "screwSlotLength",
        "mountOffsetY",
    )
    _pattern_down(component, relief, "Screw relief rows")


def _probe(body, x_mm, y_mm, z_mm):
    point = adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)
    return body.pointContainment(point)


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


def _verify(body):  # pylint: disable=too-many-locals
    """Numeric probes; raise on any surprise so the failure is loud."""
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    outside = adsk.fusion.PointContainment.PointOutsidePointContainment
    face = PLATE_THICKNESS
    pocket_mid_x = face - NUT_POCKET_DEPTH / 2.0
    behind_floor_x = face - NUT_POCKET_DEPTH - 1.0
    offset = mount_offset()
    above_channel_z = top_mount_z() + NUT_CHANNEL_HEIGHT / 2.0 + 2.0
    checks = [("plate interior", face / 2.0, 0.0, above_channel_z, inside)]
    if not _is_coupon():
        lip_mid_x = -(HOOK_THROAT + HOOK_LIP_THICKNESS / 2.0)
        for row in range(HOOK_ROWS):
            neck_top = TOP_HOOK_NECK_TOP - row * SLOT_PITCH_VERTICAL
            lip_z = neck_top - HOOK_NECK_HEIGHT - HOOK_LIP_DROP / 2.0
            checks.append((f"hook row {row} lip", lip_mid_x, 0.0, lip_z, inside))
    for row in range(mount_rows()):
        mount_z = top_mount_z() - row * BOARD_PITCH
        beyond = NUT_CHANNEL_LENGTH / 2.0 + 1.0
        checks += [
            (f"row {row} channel open", pocket_mid_x, offset, mount_z, outside),
            (f"row {row} relief through", 0.5, offset, mount_z, outside),
            (
                f"row {row} channel floor",
                behind_floor_x,
                offset,
                mount_z + SCREW_SLOT_WIDTH / 2.0 + 1.0,
                inside,
            ),
            (
                f"row {row} nut cannot turn",
                pocket_mid_x,
                offset,
                mount_z + NUT_CHANNEL_HEIGHT / 2.0 + 1.0,
                inside,
            ),
            (
                f"row {row} travel inboard",
                pocket_mid_x,
                offset + MOUNT_TRAVEL / 2.0,
                mount_z,
                outside,
            ),
            (
                f"row {row} travel outboard",
                pocket_mid_x,
                offset - MOUNT_TRAVEL / 2.0,
                mount_z,
                outside,
            ),
            (
                f"row {row} plate past channel",
                pocket_mid_x,
                offset + beyond,
                mount_z,
                inside,
            ),
            (
                f"row {row} plate before channel",
                pocket_mid_x,
                offset - beyond,
                mount_z,
                inside,
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


# pylint: disable-next=too-many-statements
def run(_context: str):
    """Build the bracket into its saved document, verify, export, version."""
    if BUILD_VARIANT not in ("left", "right", "coupon"):
        raise ValueError(
            f"BUILD_VARIANT must be left, right or coupon, got {BUILD_VARIANT!r}"
        )
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
    _check_mount_fits()
    _build_plate(component, plane)
    if not _is_coupon():
        _build_hooks(component, plane)
    _build_mounts(component, plane)
    if component.bRepBodies.count != 1:
        raise RuntimeError(f"expected one body, got {component.bRepBodies.count}")
    body = component.bRepBodies.item(0)
    body.name = export_name()

    bounding = body.boundingBox
    print(f"variant: {BUILD_VARIANT}, channel centre {mount_offset():+.2f} mm")
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
        f"channel {mount_offset():+.2f} mm, travel {MOUNT_TRAVEL} mm, "
        f"board {BOARD_THICKNESS} mm, screw {SCREW_LENGTH} mm"
    )
    # saveAs and save return a BOOLEAN, and saveAs can return True without
    # saving: the document stays open, named, and unsaved. isSaved is the
    # only answer worth believing.
    description += f" vol {body.volume / (MM ** 3):.0f} mm3"
    if data_file is None:
        saved = document.saveAs(doc_name(), folder, description, "")
    else:
        saved = document.save(description)
    if not saved or not document.isSaved:
        raise RuntimeError(
            f"{doc_name()!r} NOT saved (saveAs returned {saved}, "
            f"isSaved={document.isSaved}). The CAD exports above are still good."
        )
    print(f"saved '{doc_name()}' in project '{FUSION_PROJECT_NAME}': {description}")
    print("build complete")
