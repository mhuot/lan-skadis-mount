"""Render an exported STL to a PNG for the docs page.

Runs locally in .venv (trimesh, numpy, pillow):

    .venv/bin/python scripts/render_part.py exports/skadis_nut_left.stl \
        docs/images/nut_bracket_front.png --azimuth 35

A painter's-algorithm rasteriser rather than a real renderer: no GPU, no
headless GL, nothing to install beyond what check_stl.py already needs. It
is enough to prove a part looks like what the build script says it is, and
to put an honest picture on the page.
"""

import argparse

import numpy as np
import trimesh
from PIL import Image

WIDTH, HEIGHT = 1100, 900
BACKGROUND = np.array([0.965, 0.969, 0.976])  # matches the page's --bg
PART_COLOUR = np.array([0.776, 0.165, 0.133])  # the red ASA, sRGB
LIGHT = np.array([0.35, 0.5, 0.79])


def oriented(mesh, azimuth_deg, elevation_deg):
    """A copy of the mesh turned to the requested view."""
    working = mesh.copy()
    for angle, axis in ((-elevation_deg, [1, 0, 0]), (azimuth_deg, [0, 0, 1])):
        working.apply_transform(
            trimesh.transformations.rotation_matrix(
                np.radians(angle), axis, working.centroid
            )
        )
    return working


def shaded(mesh):
    """Per-face brightness from a single key light plus ambient."""
    triangles = mesh.vertices[:, [0, 2, 1]][mesh.faces]
    normals = np.cross(
        triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    )
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = normals / np.where(lengths == 0, 1, lengths)
    key = LIGHT / np.linalg.norm(LIGHT)
    return np.clip(np.abs(normals @ key), 0, 1) * 0.62 + 0.38, triangles


# pylint: disable-next=too-many-locals
def render(mesh, azimuth_deg, elevation_deg):
    """Rasterise the mesh to an RGB array."""
    brightness, triangles = shaded(oriented(mesh, azimuth_deg, elevation_deg))
    flat = triangles.reshape(-1, 3)
    low, high = flat.min(0), flat.max(0)
    span = max(high[0] - low[0], high[1] - low[1]) or 1.0
    scale = min(WIDTH, HEIGHT) * 0.80 / span
    centre = (low + high) / 2.0
    screen = triangles.copy()
    screen[:, :, 0] = (triangles[:, :, 0] - centre[0]) * scale + WIDTH / 2.0
    screen[:, :, 1] = HEIGHT / 2.0 - (triangles[:, :, 1] - centre[1]) * scale

    image = np.tile(BACKGROUND.astype(np.float32), (HEIGHT, WIDTH, 1))
    depth = np.full((HEIGHT, WIDTH), -np.inf)
    grid_x, grid_y = np.meshgrid(np.arange(WIDTH), np.arange(HEIGHT))
    for index in np.argsort(triangles[:, :, 2].mean(axis=1)):
        tri = screen[index]
        min_x, max_x = max(int(tri[:, 0].min()), 0), min(
            int(tri[:, 0].max()) + 2, WIDTH
        )
        min_y, max_y = max(int(tri[:, 1].min()), 0), min(
            int(tri[:, 1].max()) + 2, HEIGHT
        )
        if min_x >= max_x or min_y >= max_y:
            continue
        px, py = grid_x[min_y:max_y, min_x:max_x], grid_y[min_y:max_y, min_x:max_x]
        (x0, y0), (x1, y1), (x2, y2) = tri[:, :2]
        denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denominator) < 1e-9:
            continue
        weight_a = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / denominator
        weight_b = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / denominator
        weight_c = 1.0 - weight_a - weight_b
        inside = (weight_a >= 0) & (weight_b >= 0) & (weight_c >= 0)
        if not inside.any():
            continue
        z = weight_a * tri[0, 2] + weight_b * tri[1, 2] + weight_c * tri[2, 2]
        closer = inside & (z > depth[min_y:max_y, min_x:max_x])
        if not closer.any():
            continue
        depth[min_y:max_y, min_x:max_x][closer] = z[closer]
        image[min_y:max_y, min_x:max_x][closer] = PART_COLOUR * brightness[index]
    return (np.clip(image, 0, 1) * 255).astype(np.uint8)


def main():
    """Render one STL from one viewpoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stl")
    parser.add_argument("png")
    parser.add_argument("--azimuth", type=float, default=35.0)
    parser.add_argument("--elevation", type=float, default=20.0)
    arguments = parser.parse_args()
    mesh = trimesh.load(arguments.stl, force="mesh")
    Image.fromarray(render(mesh, arguments.azimuth, arguments.elevation)).save(
        arguments.png
    )
    print(f"wrote {arguments.png}  extents mm {mesh.extents.round(2)}")


if __name__ == "__main__":
    main()
