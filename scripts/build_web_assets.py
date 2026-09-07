"""Assemble the Pages viewer GLB from the exported part STLs.

Runs locally in .venv (trimesh, numpy):

    .venv/bin/python scripts/build_web_assets.py

Places four nut-channel brackets on two DuraFrame uprights, hangs a SKADIS
board on them, and drops an M4 screw into each channel, then writes
docs/models/skadis-mount.glb for model-viewer.

The board is built rather than subtracted. A 760 x 560 panel carries about
530 slots, and a boolean difference of that many pockets is both slow and
fragile; the same panel is trivially exact if you build the material that
IS there -- a solid strip between every pair of slot rows, and a rib between
every pair of slots within a row. No booleans, no near-misses.

Colour note: the palette is authored in sRGB to match the printed parts, but
glTF baseColorFactor is linear, so every colour goes through the sRGB EOTF
before export. Skipping that step washes the whole scene out.

The assembly maths lives here rather than in the Fusion scripts on purpose:
this is a picture, not a part, and nothing printable should depend on it.
"""

import math
from pathlib import Path

import trimesh

EXPORTS = Path("exports")
GLB_PATH = Path("docs/models/skadis-mount.glb")
PART_GLB_PATH = Path("docs/models/nut-bracket.glb")

# --- Mirrors build_skadis_nut_bracket.py; see README -----------------------
UPRIGHT_SPACING = 735.04
PLATE_THICKNESS = 11.0
PLATE_HEIGHT = 48.0
CHANNEL_Z = PLATE_HEIGHT / 2.0
MOUNT_OFFSET = 7.52
NUT_PROUD = 0.2
# 19 hook pitches against 12 board rows: 482.6 vs 480, off by 2.6 mm of the
# 11 mm a screw has inside its slot. On a 560 mm board that puts the four
# brackets about 39 mm inside each corner, which is where they belong -- a
# tighter valid spacing like 3 pitches (76.2 mm) bunches all four into a
# band across the middle and gives the board almost no leverage arm.
BRACKET_RISE = 482.6

BOARD_WIDTH = 760.0
BOARD_HEIGHT = 560.0
BOARD_THICKNESS = 6.0
BOARD_PITCH = 40.0
SLOT_WIDTH = 5.0
SLOT_HEIGHT = 15.0
BOARD_FACE_X = PLATE_THICKNESS + NUT_PROUD

UPRIGHT_WIDTH = 50.0
UPRIGHT_DEPTH = 25.0
UPRIGHT_HEIGHT = 720.0

SCREW_HEAD_RADIUS = 4.0
SCREW_HEAD_HEIGHT = 2.4

# sRGB, roughly the real materials
PALETTE = {
    "printed": (198, 42, 34, 255),  # the red ASA the brackets print in
    "board": (221, 221, 215, 255),  # white SKADIS, a shade off the page
    "upright": (74, 78, 84, 255),  # painted steel
    "screw": (188, 190, 194, 255),
}
METALLIC = {"screw": 0.85, "upright": 0.35}
ROUGHNESS = {"printed": 0.75, "board": 0.7, "upright": 0.55, "screw": 0.3}


def srgb_to_linear(channel):
    """glTF baseColorFactor is linear; the palette above is sRGB."""
    ratio = channel / 255.0
    if ratio <= 0.04045:
        return ratio / 12.92
    return ((ratio + 0.055) / 1.055) ** 2.4


def material(group):
    """PBR material for a palette group, converted to linear."""
    red, green, blue, alpha = PALETTE[group]
    return trimesh.visual.material.PBRMaterial(
        baseColorFactor=[
            srgb_to_linear(red),
            srgb_to_linear(green),
            srgb_to_linear(blue),
            alpha / 255.0,
        ],
        metallicFactor=METALLIC.get(group, 0.0),
        roughnessFactor=ROUGHNESS.get(group, 0.6),
    )


def load_part(name):
    """Load one exported part STL as a single mesh."""
    mesh = trimesh.load(EXPORTS / f"{name}.stl")
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(list(mesh.geometry.values()))
    return mesh


def translation(x_mm, y_mm, z_mm):
    """Translation matrix in millimetres."""
    return trimesh.transformations.translation_matrix([x_mm, y_mm, z_mm])


def rotation(angle_degrees, axis):
    """Rotation matrix, degrees about an axis through the origin."""
    return trimesh.transformations.rotation_matrix(math.radians(angle_degrees), axis)


def placed(mesh, transform, group):
    """A transformed, coloured copy of a part."""
    part = mesh.copy()
    part.apply_transform(transform)
    part.visual = trimesh.visual.TextureVisuals(material=material(group))
    return part


def box(size, centre, group):
    """An axis-aligned box, coloured."""
    solid = trimesh.creation.box(extents=size)
    solid.apply_transform(translation(*centre))
    solid.visual = trimesh.visual.TextureVisuals(material=material(group))
    return solid


def slot_grid():
    """(y, z) centres of every SKADIS slot, board-local, origin at centre.

    The pattern is a 40 mm grid plus a second 40 mm grid shifted 20 mm in
    both directions, which is the same thing as slot rows every 20 mm whose
    columns alternate by 20 mm.
    """
    half_pitch = BOARD_PITCH / 2.0
    rows = int(BOARD_HEIGHT // half_pitch)
    columns = int(BOARD_WIDTH // BOARD_PITCH)
    centres = []
    for row in range(rows):
        z = -BOARD_HEIGHT / 2.0 + half_pitch * (row + 0.5)
        shift = 0.0 if row % 2 else half_pitch
        for column in range(columns):
            y = -BOARD_WIDTH / 2.0 + BOARD_PITCH * column + shift
            if abs(y) + SLOT_WIDTH / 2.0 <= BOARD_WIDTH / 2.0:
                centres.append((y, z))
    return centres


# pylint: disable-next=too-many-locals
def board(centre_z):
    """The perforated panel, built from the material between the slots."""
    half_pitch = BOARD_PITCH / 2.0
    rows = int(BOARD_HEIGHT // half_pitch)
    pieces = []
    thickness = BOARD_THICKNESS
    x_centre = BOARD_FACE_X + thickness / 2.0
    band = SLOT_HEIGHT
    gap = half_pitch - band  # solid strip between two slot rows

    # A strip is centred ON the boundary between two slot rows, not offset
    # from it: slot centres sit half_pitch apart, each slot is SLOT_HEIGHT
    # tall, so the solid left between them is one strip of `gap` straddling
    # the midpoint. Offsetting by gap/2 instead overlaps the slot band by
    # 2.5 mm at one end and leaves a full-width void at the other.
    for row in range(rows + 1):
        z = -BOARD_HEIGHT / 2.0 + half_pitch * row
        strip = trimesh.creation.box(extents=[thickness, BOARD_WIDTH, gap])
        strip.apply_transform(translation(x_centre, 0.0, centre_z + z))
        pieces.append(strip)
    # Ribs: within each slot row, the material either side of every slot.
    by_row = {}
    for y, z in slot_grid():
        by_row.setdefault(round(z, 3), []).append(y)
    for z, columns in by_row.items():
        edges = [-BOARD_WIDTH / 2.0]
        for y in sorted(columns):
            edges += [y - SLOT_WIDTH / 2.0, y + SLOT_WIDTH / 2.0]
        edges.append(BOARD_WIDTH / 2.0)
        for start, end in zip(edges[0::2], edges[1::2]):
            width = end - start
            if width <= 0.01:
                continue
            rib = trimesh.creation.box(extents=[thickness, width, band])
            rib.apply_transform(
                translation(x_centre, (start + end) / 2.0, centre_z + z)
            )
            pieces.append(rib)

    panel = trimesh.util.concatenate(pieces)
    panel.visual = trimesh.visual.TextureVisuals(material=material("board"))
    return panel


def screw(y_mm, z_mm):
    """An M4 head sitting on the board's front face."""
    head = trimesh.creation.cylinder(
        radius=SCREW_HEAD_RADIUS, height=SCREW_HEAD_HEIGHT, sections=32
    )
    head.apply_transform(
        translation(
            BOARD_FACE_X + BOARD_THICKNESS + SCREW_HEAD_HEIGHT / 2.0, y_mm, z_mm
        )
        @ rotation(90, [0, 1, 0])
    )
    head.visual = trimesh.visual.TextureVisuals(material=material("screw"))
    return head


def build_scene():
    """Four brackets on two uprights, a board on the brackets, four screws."""
    left = load_part("skadis_nut_left")
    right = load_part("skadis_nut_right")
    parts = []
    channel_zs = [CHANNEL_Z, CHANNEL_Z + BRACKET_RISE]

    board_centre_z = sum(channel_zs) / 2.0
    for sign, part in ((-1.0, left), (1.0, right)):
        column_y = sign * UPRIGHT_SPACING / 2.0
        parts.append(
            box(
                [UPRIGHT_DEPTH, UPRIGHT_WIDTH, UPRIGHT_HEIGHT],
                (-UPRIGHT_DEPTH / 2.0, column_y, board_centre_z),
                "upright",
            )
        )
        for rise in (0.0, BRACKET_RISE):
            parts.append(placed(part, translation(0.0, column_y, rise), "printed"))
        for channel_z in channel_zs:
            parts.append(screw(column_y + sign * -MOUNT_OFFSET, channel_z))

    parts.append(board(board_centre_z))
    return parts


def write_glb(parts, path):
    """Centre a part list, convert to Y-up, and write it as a GLB."""
    scene = trimesh.Scene()
    for index, part in enumerate(parts):
        scene.add_geometry(part, node_name=f"part_{index:02d}")
    bounds = scene.bounds
    centre = (bounds[0] + bounds[1]) / 2.0
    scene.apply_transform(trimesh.transformations.translation_matrix(-centre))
    # glTF is Y-up; the CAD scene is Z-up and trimesh does NOT convert. Without
    # this the board renders lying on its back and it still looks plausible --
    # just of the wrong thing.
    scene.apply_transform(rotation(-90, [1, 0, 0]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(trimesh.exchange.gltf.export_glb(scene))
    size_kb = path.stat().st_size / 1024.0
    extents = [round(float(value), 1) for value in (bounds[1] - bounds[0])]
    print(f"wrote {path} ({size_kb:.0f} kB), {len(parts)} parts, extents mm {extents}")


def main():
    """Write both GLBs the docs page loads: one bracket, and the assembly."""
    write_glb(
        [placed(load_part("skadis_nut_left"), rotation(0, [0, 0, 1]), "printed")],
        PART_GLB_PATH,
    )
    parts = build_scene()
    scene = trimesh.Scene()
    for index, part in enumerate(parts):
        scene.add_geometry(part, node_name=f"part_{index:02d}")
    bounds = scene.bounds
    centre = (bounds[0] + bounds[1]) / 2.0
    scene.apply_transform(trimesh.transformations.translation_matrix(-centre))
    # glTF is Y-up; the CAD scene is Z-up and trimesh does NOT convert. Without
    # this the board renders lying on its back and it still looks plausible --
    # just of the wrong thing.
    scene.apply_transform(rotation(-90, [1, 0, 0]))
    GLB_PATH.parent.mkdir(parents=True, exist_ok=True)
    GLB_PATH.write_bytes(trimesh.exchange.gltf.export_glb(scene))
    size_kb = GLB_PATH.stat().st_size / 1024.0
    extents = [round(float(value), 1) for value in (bounds[1] - bounds[0])]
    print(f"wrote {GLB_PATH} ({size_kb:.0f} kB), {len(parts)} parts")
    print(f"assembly extents mm: {extents}")


if __name__ == "__main__":
    main()
