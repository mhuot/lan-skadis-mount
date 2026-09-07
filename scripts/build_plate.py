"""Lay pre-rotated brackets out on one print plate.

Runs locally in .venv (trimesh, numpy):

    .venv/bin/python scripts/build_plate.py left right -o exports/pair.stl

The two hands are mirrored, so they do not share a print orientation: the
inboard edge goes on the bed, which is a -90 degree rotation about X for the
left bracket and +90 for the right. PrusaSlicer's --rotate-x is global, so a
plate holding both cannot be sliced from the part STLs -- every attempt puts
one hand cavity-end up, where the slicer packs the cavity with support that
can never be removed.

So the rotation is baked in here instead, each part is dropped onto Z=0, and
they are spread along X with a gap wide enough that their brims do not meet.
Slice the result with NO rotation.
"""

import argparse
import math
import pathlib

import trimesh

EXPORTS = pathlib.Path("exports")
# Inboard edge on the bed: see the module docstring.
ROTATION = {"left": -90.0, "right": 90.0}
GAP = 14.0  # brims collide below about 14 mm, and PrusaSlicer calls it a conflict


def oriented(hand):
    """One bracket, rotated into its print orientation and sat on Z=0."""
    mesh = trimesh.load(EXPORTS / f"skadis_nut_{hand}.stl", force="mesh")
    mesh.apply_transform(
        trimesh.transformations.rotation_matrix(
            math.radians(ROTATION[hand]), [1, 0, 0], mesh.centroid
        )
    )
    mesh.apply_translation([0, 0, -mesh.bounds[0][2]])
    return mesh


def main():
    """Build a plate from the named hands and write it as one STL."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hands", nargs="+", choices=sorted(ROTATION))
    parser.add_argument("-o", "--output", required=True)
    arguments = parser.parse_args()

    placed, cursor = [], 0.0
    for hand in arguments.hands:
        mesh = oriented(hand)
        mesh.apply_translation([cursor - mesh.bounds[0][0], 0, 0])
        cursor = mesh.bounds[1][0] + GAP
        placed.append(mesh)
        print(
            f"  {hand:5s} rotated {ROTATION[hand]:+.0f} deg about X, "
            f"footprint {mesh.extents[0]:.1f} x {mesh.extents[1]:.1f} mm, "
            f"{mesh.extents[2]:.1f} tall"
        )

    plate = trimesh.util.concatenate(placed)
    plate.apply_translation([-plate.centroid[0], -plate.centroid[1], 0])
    pathlib.Path(arguments.output).parent.mkdir(parents=True, exist_ok=True)
    plate.export(arguments.output)
    print(
        f"wrote {arguments.output}: {len(arguments.hands)} parts, "
        f"plate {plate.extents[0]:.0f} x {plate.extents[1]:.0f} mm, "
        f"volume {plate.volume:.0f} mm^3"
    )


if __name__ == "__main__":
    main()
