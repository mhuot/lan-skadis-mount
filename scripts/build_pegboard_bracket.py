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

PROJECT_DIR = "/Users/mhuot/lan-pegboard-mount"
FUSION_PROJECT_NAME = "LAN Pegboard Mount"
DOC_NAME = "Pegboard Mount Bracket"
EXPORT_NAME = "pegboard_mount_bracket"

# --- Upright slot geometry (verified by lan-spool-shelf gauge prints) -------
SLOT_PITCH_VERTICAL = 25.4
FACE_METAL_THICKNESS = 2.0

# --- Hook stack (proven dimensions from lan-spool-shelf) --------------------
HOOK_TAB_WIDTH = 2.4
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

_DRIVING = "drives the model; safe to edit live in Fusion"
_REFERENCE = "reference only — edit scripts/build_pegboard_bracket.py and rebuild"
PARAMETERS = {
    "bracketWidth": (BRACKET_WIDTH, _DRIVING),
    "hookTabWidth": (HOOK_TAB_WIDTH, _DRIVING),
    "slotPitchVertical": (SLOT_PITCH_VERTICAL, _DRIVING),
    "faceMetalThickness": (FACE_METAL_THICKNESS, _DRIVING),
    "hookThroat": ("faceMetalThickness + 1.8 mm", _DRIVING),
    "hookNeckHeight": (HOOK_NECK_HEIGHT, _DRIVING),
    "hookLipThickness": (HOOK_LIP_THICKNESS, _DRIVING),
    "hookLipDrop": (HOOK_LIP_DROP, _DRIVING),
    "hookLipChamfer": (HOOK_LIP_CHAMFER, _DRIVING),
    "topHookNeckTop": (TOP_HOOK_NECK_TOP, _DRIVING),
    "hookRows": (str(HOOK_ROWS), _DRIVING),
    "plateThickness": (PLATE_THICKNESS, _REFERENCE),
    "plateHeight": (PLATE_HEIGHT, _REFERENCE),
    "boltSlotHeight": (BOLT_SLOT_HEIGHT, _REFERENCE),
    "boltSlotLength": (BOLT_SLOT_LENGTH, _REFERENCE),
    "nutTrackHeight": (NUT_TRACK_HEIGHT, _REFERENCE),
    "nutTrackDepth": (NUT_TRACK_DEPTH, _REFERENCE),
}
UNITLESS_PARAMETERS = {"hookRows"}


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
    user_parameters = design.userParameters
    for name, (value, comment) in PARAMETERS.items():
        expression = value if isinstance(value, str) else f"{value} mm"
        units = "" if name in UNITLESS_PARAMETERS else "mm"
        existing = user_parameters.itemByName(name)
        if existing:
            existing.expression = expression
            existing.comment = comment
        else:
            user_parameters.add(
                name,
                adsk.core.ValueInput.createByString(expression),
                units,
                comment,
            )


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


def _build_body(component, plane):
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    new_body = adsk.fusion.FeatureOperations.NewBodyFeatureOperation

    plate = component.sketches.add(plane)
    plate.name = "Plate"
    _add_polygon(
        plate,
        [
            (0.0, 0.0),
            (PLATE_THICKNESS, 0.0),
            (PLATE_THICKNESS, PLATE_HEIGHT),
            (0.0, PLATE_HEIGHT),
        ],
    )
    _extrude_all_profiles(component, plate, "bracketWidth", new_body, "Plate")
    _build_hooks(component, plane)

    # Nut tracks: open-ended horizontal channels milled from the rear face
    # (x = 0, against the upright) leaving a 1 mm floor at the board face.
    # The nut slides in from the side and cannot rotate.
    tracks = component.sketches.add(plane)
    tracks.name = "Nut tracks"
    for bolt_z in _bolt_center_zs():
        half = NUT_TRACK_HEIGHT / 2.0
        _add_polygon(
            tracks,
            [
                (0.0, bolt_z - half),
                (NUT_TRACK_DEPTH, bolt_z - half),
                (NUT_TRACK_DEPTH, bolt_z + half),
                (0.0, bolt_z + half),
            ],
        )
    _extrude_all_profiles(component, tracks, "bracketWidth + 10 mm", cut, "Nut tracks")

    slots = component.sketches.add(plane)
    slots.name = "Bolt slots"
    for bolt_z in _bolt_center_zs():
        half = BOLT_SLOT_HEIGHT / 2.0
        _add_polygon(
            slots,
            [
                (-1.0, bolt_z - half),
                (PLATE_THICKNESS + 1.0, bolt_z - half),
                (PLATE_THICKNESS + 1.0, bolt_z + half),
                (-1.0, bolt_z + half),
            ],
        )
    _extrude_all_profiles(component, slots, BOLT_SLOT_LENGTH, cut, "Bolt slots")


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
        _clear_timeline(design)
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
    _export(design)
    description = (
        f"scripted build {datetime.date.today().isoformat()}: "
        f"{HOOK_ROWS} hook rows, 1/4-20 bolt slots, "
        f"plate {PLATE_THICKNESS} mm"
    )
    if data_file is None:
        document.saveAs(DOC_NAME, folder, description, "")
    else:
        document.save(description)
    print(f"saved '{DOC_NAME}' in project '{FUSION_PROJECT_NAME}': {description}")
    print("build complete")
