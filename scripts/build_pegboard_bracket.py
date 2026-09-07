"""Fusion 360 script: pegboard mount bracket for Ergotron DuraFrame uprights.

Run inside Fusion via scripts/run_in_fusion.py. Hooks into the slotted
uprights of a LAN Organizer 3000 (geometry verified on the real desk by the
lan-spool-shelf project) and presents a flat face that standard pegboard
bolts to with 1/4-20 hardware through its own 1/4" holes. Both the board's
hole grid and the upright slots run on 1" pitch, so the grids align by
construction; the bolt slots run horizontally (+/-7 mm) to absorb
upright-spacing tolerance, and an open-ended nut track in the rear face
holds each nut captive and flush, so nothing protrudes toward the upright.

Mounted behind a lan-spool-shelf cradle level with 1/8" board, the board's
front face lands ~10 mm off the upright — exactly at a resting spool's
rearmost point — so the board doubles as a backstop the spools just graze.

Two hook rows by default (hookRows drives a pattern; use 3-4 for heavy tool
loads). The hook stack is copied from the proven lan-spool-shelf design:
fully constrained profile sketch dimensioned against user parameters, with
hookThroat defined as faceMetalThickness + 1.8 mm. Scaffolding is repeated
rather than shared on purpose — Fusion's persistent interpreter caches
imported modules across MCP runs (see the fusion-360-mcp skill).
"""

import datetime

import adsk.core
import adsk.fusion

MM = 0.1  # Fusion API lengths are centimetres

# Set True only to deliberately discard a hand edit in the document.
ALLOW_OVERWRITE = False

PROJECT_DIR = "/Users/mhuot/lan-skadis-mount"
FUSION_PROJECT_NAME = "LAN Pegboard Mount"
DOC_NAME = "Pegboard Mount Bracket"
EXPORT_NAME = "pegboard_mount_bracket"

# --- Upright slot geometry (verified by lan-spool-shelf gauge prints) -------
SLOT_PITCH_VERTICAL = 25.4
SLOT_WIDTH = 3.2  # measured, confirmed by the spool shelf gauge print
FACE_METAL_THICKNESS = 2.0

# --- Hook stack (proven dimensions from lan-spool-shelf) --------------------
HOOK_TAB_WIDTH = SLOT_WIDTH - 0.8
HOOK_THROAT = FACE_METAL_THICKNESS + 1.8
HOOK_NECK_HEIGHT = 5.0
HOOK_LIP_THICKNESS = 4.5
HOOK_LIP_DROP = 12.0
HOOK_LIP_CHAMFER = 1.5
HOOK_ROWS = 2

# --- Plate and pegboard attachment ------------------------------------------
BRACKET_WIDTH = 24.0
PLATE_THICKNESS = 7.0  # board bolts to the front face
PLATE_HEIGHT = HOOK_ROWS * SLOT_PITCH_VERTICAL + 23.2  # margin around rows
TOP_HOOK_NECK_TOP = PLATE_HEIGHT - 2.0
BOLT_COUNT = 2  # one per pegboard row, 1" apart, interleaved between hooks
BOLT_SLOT_HEIGHT = 7.0  # clearance for 1/4-20 (1/4" = 6.35)
BOLT_SLOT_LENGTH = 14.0  # horizontal: +/-7 mm of upright-spacing slop
NUT_ACROSS_FLATS = 11.11  # 1/4-20 hex nut (7/16")
NUT_TRACK_HEIGHT = NUT_ACROSS_FLATS + 0.4  # nut slides in from the side
NUT_TRACK_DEPTH = 6.0  # from the rear face; leaves a 1 mm floor up front
# Bolt centres sit midway between hook neck bands, still on the 1" grid.
TOP_BOLT_CENTER_Z = TOP_HOOK_NECK_TOP - HOOK_NECK_HEIGHT - 7.7

# name: (value or expression, unit, comment). Order is creation order, so an
# expression may only reference names declared above it. Every parameter must
# drive geometry — _audit_parameters fails the build otherwise.
PARAMETERS = {
    "bracketWidth": (BRACKET_WIDTH, "mm", "bracket width across the upright"),
    "plateThickness": (PLATE_THICKNESS, "mm", "the board bolts to this face"),
    "plateHeight": (PLATE_HEIGHT, "mm", "plate height, spans the hook rows"),
    "slotWidth": (SLOT_WIDTH, "mm", "measured slot width in the upright"),
    "slotPitchVertical": (SLOT_PITCH_VERTICAL, "mm", "1 inch, measured"),
    "faceMetalThickness": (FACE_METAL_THICKNESS, "mm", "upright face metal"),
    "hookTabWidth": ("slotWidth - 0.8 mm", "mm", "blade width through the slot"),
    "hookThroat": ("faceMetalThickness + 1.8 mm", "mm", "gap behind the plate"),
    "hookNeckHeight": (HOOK_NECK_HEIGHT, "mm", "bears on the slot bottom edge"),
    "hookLipThickness": (HOOK_LIP_THICKNESS, "mm", "lip thickness behind the face"),
    "hookLipDrop": (HOOK_LIP_DROP, "mm", "engagement below the neck"),
    "hookLipChamfer": (HOOK_LIP_CHAMFER, "mm", "lead-in past slot burrs"),
    "topHookNeckTop": (TOP_HOOK_NECK_TOP, "mm", "top row, below the plate top"),
    "hookRows": (str(HOOK_ROWS), "", "number of hook rows (pattern count)"),
    "topBoltCentre": (TOP_BOLT_CENTER_Z, "mm", "top bolt, above the plate foot"),
    "boltSlotHeight": (BOLT_SLOT_HEIGHT, "mm", "1/4-20 clearance, vertical"),
    "boltSlotLength": (BOLT_SLOT_LENGTH, "mm", "horizontal adjustment range"),
    "nutTrackHeight": (NUT_TRACK_HEIGHT, "mm", "across flats of a 1/4-20 nut"),
    "nutTrackDepth": (NUT_TRACK_DEPTH, "mm", "track depth from the rear face"),
}


def _value(millimetres):
    return adsk.core.ValueInput.createByReal(millimetres * MM)


def _point(x_mm, z_mm):
    """Sketch point on the XZ plane (sketch +y is model MINUS Z)."""
    return adsk.core.Point3D.create(x_mm * MM, -z_mm * MM, 0)


def _add_polygon(sketch, points_mm):
    lines = sketch.sketchCurves.sketchLines
    count = len(points_mm)
    for index in range(count):
        start = _point(*points_mm[index])
        end = _point(*points_mm[(index + 1) % count])
        lines.addByTwoPoints(start, end)


def _polyline(sketch, points_mm):
    """Closed polygon whose consecutive lines share sketch points."""
    lines = sketch.sketchCurves.sketchLines
    made = [lines.addByTwoPoints(_point(*points_mm[0]), _point(*points_mm[1]))]
    for target in points_mm[2:]:
        made.append(lines.addByTwoPoints(made[-1].endSketchPoint, _point(*target)))
    made.append(lines.addByTwoPoints(made[-1].endSketchPoint, made[0].startSketchPoint))
    return made


def _polyline(sketch, points_mm):
    """Closed polygon whose consecutive lines share sketch points."""
    lines = sketch.sketchCurves.sketchLines
    made = [lines.addByTwoPoints(_point(*points_mm[0]), _point(*points_mm[1]))]
    for target in points_mm[2:]:
        made.append(lines.addByTwoPoints(made[-1].endSketchPoint, _point(*target)))
    made.append(lines.addByTwoPoints(made[-1].endSketchPoint, made[0].startSketchPoint))
    return made


def _extrude_all_profiles(component, sketch, width, operation, name):
    """Symmetric full-length extrude; width is mm or a parameter expression."""
    profiles = adsk.core.ObjectCollection.create()
    for index in range(sketch.profiles.count):
        profiles.add(sketch.profiles.item(index))
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(profiles, operation)
    if isinstance(width, str):
        width_input = adsk.core.ValueInput.createByString(width)
    else:
        width_input = _value(width)
    extrude_input.setSymmetricExtent(width_input, True)
    feature = extrudes.add(extrude_input)
    feature.name = name
    return feature


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def _dimension(sketch, point_a, point_b, orientation, expression, text_x, text_z):
    dimension = sketch.sketchDimensions.addDistanceDimension(
        point_a, point_b, orientation, _point(text_x, text_z)
    )
    dimension.parameter.expression = expression


def _ensure_parameters(design):
    """Create or update user parameters, each with its declared unit."""
    user_parameters = design.userParameters
    for name, (value, unit, comment) in PARAMETERS.items():
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
        expected = PARAMETERS.get(parameter.name)
        if expected is None or parameter.unit != expected[1]:
            print(f"  dropping stale parameter {parameter.name}")
            parameter.deleteMe()


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
        if parameter.unit != PARAMETERS[parameter.name][1]:
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


# pylint: disable-next=too-many-locals
def _pin_corners(sketch, lines, corners):
    """Dimension each corner's X and Z off the origin, by expression."""
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


def _build_hooks(component, plane):  # pylint: disable=too-many-locals
    """Proven lan-spool-shelf hook stack: constrained profile + row pattern."""
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
    mid_neck = (neck_top + neck_bottom) / 2.0
    _dimension(
        sketch,
        sketch.originPoint,
        top.startSketchPoint,
        vertical,
        "topHookNeckTop",
        6.0,
        neck_top / 2.0,
    )
    _dimension(
        sketch,
        top.startSketchPoint,
        top.endSketchPoint,
        horizontal,
        "hookThroat + hookLipThickness",
        -4.0,
        neck_top + 5.0,
    )
    _dimension(
        sketch,
        neck.endSketchPoint,
        neck.startSketchPoint,
        horizontal,
        "hookThroat",
        -2.0,
        neck_bottom - 3.0,
    )
    _dimension(
        sketch,
        top.startSketchPoint,
        neck.endSketchPoint,
        vertical,
        "hookNeckHeight",
        3.0,
        mid_neck,
    )
    _dimension(
        sketch,
        inner.endSketchPoint,
        inner.startSketchPoint,
        vertical,
        "hookLipDrop - hookLipChamfer",
        -10.0,
        (neck_bottom + lip_bottom) / 2.0,
    )
    _dimension(
        sketch,
        chamfer.startSketchPoint,
        chamfer.endSketchPoint,
        horizontal,
        "hookLipChamfer",
        -4.0,
        lip_bottom - 3.0,
    )
    _dimension(
        sketch,
        chamfer.startSketchPoint,
        chamfer.endSketchPoint,
        vertical,
        "hookLipChamfer",
        -9.0,
        lip_bottom + 3.0,
    )
    extrude = _extrude_all_profiles(
        component,
        sketch,
        "hookTabWidth",
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "Hook profile",
    )
    pattern_entities = adsk.core.ObjectCollection.create()
    pattern_entities.add(extrude)
    patterns = component.features.rectangularPatternFeatures
    pattern_input = patterns.createInput(
        pattern_entities,
        component.zConstructionAxis,
        adsk.core.ValueInput.createByString("hookRows"),
        adsk.core.ValueInput.createByString("-slotPitchVertical"),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )
    patterns.add(pattern_input).name = "Hook rows"


def _bolt_center_zs():
    return [TOP_BOLT_CENTER_Z - row * SLOT_PITCH_VERTICAL for row in range(BOLT_COUNT)]


# pylint: disable-next=too-many-locals
def _build_body(component, plane):
    """Plate, hooks, nut tracks and bolt slots — every edge dimensioned."""
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    new_body = adsk.fusion.FeatureOperations.NewBodyFeatureOperation

    plate = component.sketches.add(plane)
    plate.name = "Plate"
    corners = [
        (0.0, 0.0, None, None),
        (PLATE_THICKNESS, 0.0, None, None),
        (PLATE_THICKNESS, PLATE_HEIGHT, "plateThickness", "plateHeight"),
        (0.0, PLATE_HEIGHT, None, None),
    ]
    lines = _polyline(plate, [(x, z) for x, z, _, _ in corners])
    constraints = plate.geometricConstraints
    constraints.addCoincident(lines[0].startSketchPoint, plate.originPoint)
    for line in (lines[0], lines[2]):
        constraints.addHorizontal(line)
    for line in (lines[1], lines[3]):
        constraints.addVertical(line)
    _pin_corners(plate, lines, corners)
    _extrude_all_profiles(component, plate, "bracketWidth", new_body, "Plate")
    _build_hooks(component, plane)

    # Nut tracks: open-ended channels milled from the rear face (x = 0,
    # against the upright), leaving a floor at the board face. The nut
    # slides in from the side and cannot rotate.
    for index, bolt_z in enumerate(_bolt_center_zs()):
        centre_expression = _bolt_centre_expression(index)
        half = NUT_TRACK_HEIGHT / 2.0
        track = component.sketches.add(plane)
        track.name = f"Nut track {index}"
        corners = [
            (
                0.0,
                bolt_z - half,
                None,
                f"{centre_expression} - nutTrackHeight / 2",
            ),
            (NUT_TRACK_DEPTH, bolt_z - half, None, None),
            (
                NUT_TRACK_DEPTH,
                bolt_z + half,
                "nutTrackDepth",
                f"{centre_expression} + nutTrackHeight / 2",
            ),
            (0.0, bolt_z + half, None, None),
        ]
        lines = _polyline(track, [(x, z) for x, z, _, _ in corners])
        constraints = track.geometricConstraints
        for line in (lines[0], lines[2]):
            constraints.addHorizontal(line)
        for line in (lines[1], lines[3]):
            constraints.addVertical(line)
        constraints.addCollinear(lines[3], plate_rear_axis(component, track))
        _pin_corners(track, lines, corners)
        _extrude_all_profiles(component, track, "bracketWidth + 10 mm", cut, track.name)

        slot = component.sketches.add(plane)
        slot.name = f"Bolt slot {index}"
        half_slot = BOLT_SLOT_HEIGHT / 2.0
        corners = [
            (
                0.0,
                bolt_z - half_slot,
                None,
                f"{centre_expression} - boltSlotHeight / 2",
            ),
            (PLATE_THICKNESS + 1.0, bolt_z - half_slot, None, None),
            (
                PLATE_THICKNESS + 1.0,
                bolt_z + half_slot,
                "plateThickness + 1 mm",
                f"{centre_expression} + boltSlotHeight / 2",
            ),
            (0.0, bolt_z + half_slot, None, None),
        ]
        lines = _polyline(slot, [(x, z) for x, z, _, _ in corners])
        constraints = slot.geometricConstraints
        for line in (lines[0], lines[2]):
            constraints.addHorizontal(line)
        for line in (lines[1], lines[3]):
            constraints.addVertical(line)
        constraints.addCollinear(lines[3], plate_rear_axis(component, slot))
        _pin_corners(slot, lines, corners)
        _extrude_all_profiles(component, slot, "boltSlotLength", cut, slot.name)


def plate_rear_axis(component, sketch):
    """The sketch's own vertical axis, projected so edges can sit on x = 0."""
    projected = sketch.project(component.zConstructionAxis)
    return projected.item(0)


def _bolt_centre_expression(index):
    """Z of bolt row `index`, on the same 1 inch grid as the hooks."""
    if index == 0:
        return "topBoltCentre"
    return f"topBoltCentre - {index} * slotPitchVertical"


def _probe(body, x_mm, y_mm, z_mm):
    point = adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)
    return body.pointContainment(point)


def _verify(body):  # pylint: disable=too-many-locals
    """Numeric probes; raise on any surprise so the failure is loud."""
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    outside = adsk.fusion.PointContainment.PointOutsidePointContainment
    lip_mid_x = -(HOOK_THROAT + HOOK_LIP_THICKNESS / 2.0)
    checks = []
    for row in range(HOOK_ROWS):
        neck_top = TOP_HOOK_NECK_TOP - row * SLOT_PITCH_VERTICAL
        lip_mid_z = neck_top - HOOK_NECK_HEIGHT - HOOK_LIP_DROP / 2.0
        checks.append((f"row {row} lip", lip_mid_x, 0.0, lip_mid_z, inside))
    top_lip_z = TOP_HOOK_NECK_TOP - HOOK_NECK_HEIGHT - HOOK_LIP_DROP / 2.0
    checks += [
        ("throat gap is open", -HOOK_THROAT / 2.0, 0.0, top_lip_z, outside),
        ("no hook beside blade", lip_mid_x, HOOK_TAB_WIDTH, top_lip_z, outside),
    ]
    floor_x = (NUT_TRACK_DEPTH + PLATE_THICKNESS) / 2.0
    for label, bolt_z in zip(("top", "bottom"), _bolt_center_zs()):
        checks += [
            (f"{label} bolt slot open", 3.5, 0.0, bolt_z, outside),
            (
                f"{label} bolt slot open at end",
                3.5,
                BOLT_SLOT_LENGTH / 2.0 - 1.0,
                bolt_z,
                outside,
            ),
            (
                f"{label} nut track open at edge",
                NUT_TRACK_DEPTH / 2.0,
                BRACKET_WIDTH / 2.0 - 1.0,
                bolt_z,
                outside,
            ),
            (
                f"{label} track floor",
                floor_x,
                BRACKET_WIDTH / 2.0 - 1.0,
                bolt_z,
                inside,
            ),
            (
                f"plate above {label} bolt",
                3.5,
                0.0,
                bolt_z + NUT_TRACK_HEIGHT / 2.0 + 2.0,
                inside,
            ),
        ]
    checks.append(("plate near bottom", 3.5, 0.0, 6.0, inside))
    failures = []
    for label, x_mm, y_mm, z_mm, expected in checks:
        actual = _probe(body, x_mm, y_mm, z_mm)
        state = "ok" if actual == expected else f"FAIL (got {actual})"
        print(f"  probe {label:30s} ({x_mm:6.1f},{y_mm:6.1f},{z_mm:6.1f}) {state}")
        if actual != expected:
            failures.append(label)
    if failures:
        raise RuntimeError(f"geometry probes failed: {failures}")


def _export(design):
    root = design.rootComponent
    export_manager = design.exportManager
    step_path = f"{PROJECT_DIR}/cad/{EXPORT_NAME}.step"
    archive_path = f"{PROJECT_DIR}/cad/{EXPORT_NAME}.f3d"
    stl_path = f"{PROJECT_DIR}/exports/{EXPORT_NAME}.stl"
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


def run(_context: str):
    """Build the bracket into its saved document, verify, export, version."""
    app = adsk.core.Application.get()
    folder = _fusion_project(app).rootFolder
    data_file = _existing_data_file(folder, DOC_NAME)
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
    _build_body(component, component.xZConstructionPlane)

    if component.bRepBodies.count != 1:
        raise RuntimeError(f"expected one body, got {component.bRepBodies.count}")
    body = component.bRepBodies.item(0)
    body.name = EXPORT_NAME

    bounding = body.boundingBox
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
        f"scripted build {datetime.date.today().isoformat()}: "
        f"{HOOK_ROWS} hook rows, 1/4-20 bolt slots, "
        f"plate {PLATE_THICKNESS} mm"
    )
    description += f" vol {body.volume / (MM ** 3):.0f} mm3"
    if data_file is None:
        document.saveAs(DOC_NAME, folder, description, "")
    else:
        document.save(description)
    print(f"saved '{DOC_NAME}' in project '{FUSION_PROJECT_NAME}': {description}")
    print("build complete")
