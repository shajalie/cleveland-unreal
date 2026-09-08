"""Woven rugs with modeled fringe and ornament, not photographs baked with lighting.

Motifs and colors approximate the visible rugs. They are not exact reproductions.
"""

import math
import bpy
from ..primitives import box, cylinder_between, finish, annotate
from ..furnishings import group
from .domestic import recolor


def rug(name, position, width, length, m, blue=False, angle=0):
    before = set(bpy.data.objects)
    colors = [(0.29, 0.035, 0.027), (0.027, 0.065, 0.11), (0.64, 0.45, 0.22), (0.70, 0.64, 0.47)]
    materials = [recolor(m["towel"], name + f" yarn {i}", color) for i, color in enumerate(colors)]
    box(
        name + " woven backing",
        (0, 0, 0.008),
        (width, length, 0.016),
        materials[1 if blue else 0],
        0.009,
    )
    vertices, faces, indices = [], [], []

    def polygon(points, color):
        start = len(vertices)
        vertices.extend((x, y, 0.018 + len(faces) * 0.000002) for x, y in points)
        faces.append(tuple(range(start, len(vertices))))
        indices.append(color)

    def diamond(x, y, rx, ry, color):
        polygon([(x - rx, y), (x, y - ry), (x + rx, y), (x, y + ry)], color)

    def border(inset, thickness, color):
        x, y = width / 2 - inset, length / 2 - inset
        for sign in [-1, 1]:
            xx = sign * x
            polygon(
                [(xx, -y), (xx, y), (xx - sign * thickness, y), (xx - sign * thickness, -y)], color
            )
            yy = sign * y
            polygon(
                [(-x, yy), (x, yy), (x, yy - sign * thickness), (-x, yy - sign * thickness)], color
            )

    border(0.015, 0.016, 3)
    border(0.045, 0.13, 1 if not blue else 0)
    border(0.19, 0.014, 3)
    border(0.22, 0.012, 2)
    # Small rosettes and leaves in the continuous border.
    for i in range(max(4, int(length / 0.14))):
        y = -length / 2 + 0.13 + i * (length - 0.26) / max(1, int(length / 0.14) - 1)
        for sign in [-1, 1]:
            x = sign * (width / 2 - 0.11)
            diamond(x, y, 0.042, 0.05, 2)
            diamond(x, y, 0.020, 0.022, 3)
    for i in range(max(4, int(width / 0.14))):
        x = -width / 2 + 0.14 + i * (width - 0.28) / max(1, int(width / 0.14) - 1)
        for sign in [-1, 1]:
            y = sign * (length / 2 - 0.11)
            diamond(x, y, 0.05, 0.04, 2)
            diamond(x, y, 0.022, 0.018, 3)
    for j in range(max(1, int((length - 0.6) / 0.27))):
        y = -length / 2 + 0.36 + j * 0.27
        for i in range(max(1, int((width - 0.6) / 0.23))):
            x = -width / 2 + 0.35 + i * 0.23
            if abs(x) / (width * 0.28) + abs(y) / (length * 0.32) < 1:
                continue
            diamond(x, y, 0.034, 0.061, 2)
            for dx, dy in [(0.04, 0.04), (-0.04, -0.04), (0.04, -0.04), (-0.04, 0.04)]:
                diamond(x + dx, y + dy, 0.018, 0.027, 3)
    for scale, color in [(1, 3), (0.92, 1), (0.80, 2), (0.73, 0), (0.47, 3), (0.39, 1), (0.18, 2)]:
        diamond(0, 0, width * 0.26 * scale, length * 0.29 * scale, color)
    mesh = bpy.data.meshes.new(name + " woven ornament")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.collection.objects.link(obj)
    finish(obj, None)
    for material in materials:
        mesh.materials.append(material)
    for face, index in zip(mesh.polygons, indices):
        face.material_index = index
    for i in range(int(width / 0.018)):
        x = -width / 2 + 0.009 + i * 0.018
        for sign in [-1, 1]:
            cylinder_between(
                name + " cotton fringe",
                (x, sign * length / 2, 0.012),
                (x + 0.004 * math.sin(i * 2), sign * (length / 2 + 0.035), 0.006),
                0.0013,
                materials[3],
                6,
            )
    root = group(name, set(bpy.data.objects) - before, position, angle)
    annotate(root, "patterned_rug", [15, 27, 31, 35, 38])
    root["fidelity"] = (
        "Approximate woven motifs and color families, not the exact photographed rug."
    )


def build(m):
    for name, position, width, length, blue in [
        ("Primary Persian-style rug", (-3.56, 4.45, 3.125), 3.10, 4.55, False),
        ("Sunroom Persian-style rug", (-4.13, 9.59, 3.125), 1.79, 2.43, True),
        ("Blue room red runner", (2.24, 9.10, 3.125), 0.72, 2.28, False),
        ("Yellow bedroom blue rug", (2.17, 2.17, 3.125), 1.44, 1.64, True),
        ("Yellow bedroom red rug", (3.60, 0.97, 3.125), 1.60, 1.12, False),
        ("Dining Persian-style rug", (-3.55, 2.10, 0.026), 2.75, 3.15, False),
        ("Study Persian-style rug", (2.94, 9.36, 0.034), 2.60, 2.5, False),
    ]:
        rug(name, position, width, length, m, blue)
