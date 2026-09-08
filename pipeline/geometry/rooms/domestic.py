"""Reusable household objects, with dimensions and layered surface detail.

These are reference-directed approximations, not scans of the photographed items.
Objects face local -Y; group transforms place complete assemblies in each room.
"""

import math
import random
import bpy
from ..primitives import box, cylinder_between, finish, annotate
from ..furnishings import group, rounded_cushion
from ..materials import plain
from .fixtures import lathe


def recolor(source, name, color):
    material = source.copy()
    material.name = name
    shader = material.node_tree.nodes.get("Principled BSDF")
    # Keep the measured normal/roughness maps, replace only the base pigment.
    for link in list(shader.inputs["Base Color"].links):
        material.node_tree.links.remove(link)
    shader.inputs["Base Color"].default_value = (*color, 1)
    return material


def chest(name, position, size, m, angle=0, white=False, rows=3, columns=1):
    before = set(bpy.data.objects)
    w, d, h = size
    material = m["ivory"] if white else m["wood"]
    box(name + " carcass", (0, 0, h / 2), (w, d, h - 0.08), material, 0.012)
    box(name + " top", (0, -0.01, h), (w + 0.04, d + 0.03, 0.03), material, 0.009)
    for row in range(rows):
        z = 0.10 + (row + 0.5) * (h - 0.15) / rows
        for column in range(columns):
            x = -w / 2 + (column + 0.5) * w / columns
            box(
                name + " inset drawer",
                (x, -d / 2 - 0.012, z),
                (w / columns - 0.025, 0.026, (h - 0.15) / rows - 0.018),
                material,
                0.005,
            )
            for side in [-1, 1] if w / columns > 0.65 else [0]:
                hx = x + side * w / columns * 0.26
                cylinder_between(
                    name + " drawer pull",
                    (hx - 0.045, -d / 2 - 0.047, z),
                    (hx + 0.045, -d / 2 - 0.047, z),
                    0.006,
                    m["iron"],
                )
    for x in [-w / 2 + 0.04, w / 2 - 0.04]:
        for y in [-d / 2 + 0.04, d / 2 - 0.04]:
            box(name + " foot", (x, y, 0.05), (0.06, 0.06, 0.10), material)
    return group(name, set(bpy.data.objects) - before, position, angle)


def lamp(name, position, m, height=0.52):
    before = set(bpy.data.objects)
    lathe(
        name + " turned base",
        [
            (0, 0),
            (1, 0),
            (1, 0.025),
            (0.48, 0.04),
            (0.23, 0.12),
            (0.20, height * 0.58),
            (0.4, height * 0.61),
        ],
        (0, 0, 0),
        (0.075, 0.075),
        m["brass"],
    )
    # Pleats have real changing normals and an open shade, rather than a solid cone.
    verts, faces = [], []
    for z, radius in [(height * 0.60, 0.18), (height, 0.095)]:
        for i in range(128):
            a = i * math.tau / 128
            r = radius + (0.003 if i % 2 else -0.003)
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(128):
        j = (i + 1) % 128
        faces.append((i, j, j + 128, i + 128))
    mesh = bpy.data.meshes.new(name + " pleated shade")
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.collection.objects.link(obj)
    finish(obj, m["towel"])
    data = bpy.data.lights.new(name + " practical bulb", "POINT")
    data.energy, data.shadow_soft_size = 12, 0.035
    data.color = (1, 0.78, 0.51)
    light = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(light)
    light.location = (0, 0, height * 0.78)
    return group(name, set(bpy.data.objects) - before, position)


def desk(name, position, size, m, angle=0):
    before = set(bpy.data.objects)
    w, d = size
    box(name + " wooden desktop", (0, 0, 0.755), (w, d, 0.045), m["wood"], 0.025)
    for x in [-w / 2 + 0.10, w / 2 - 0.10]:
        for y in [-d / 2 + 0.07, d / 2 - 0.07]:
            cylinder_between(name + " leg", (x, y, 0.025), (x, y, 0.745), 0.025, m["ivory"])
    box(name + " apron", (0, d / 2 - 0.05, 0.66), (w - 0.1, 0.025, 0.15), m["wood"])
    return group(name, set(bpy.data.objects) - before, position, angle)


def books(name, position, length, m, seed=3014, angle=0):
    before = set(bpy.data.objects)
    rng = random.Random(seed)
    colors = [
        (0.28, 0.065, 0.04),
        (0.09, 0.16, 0.19),
        (0.50, 0.39, 0.23),
        (0.7, 0.65, 0.49),
        (0.11, 0.09, 0.065),
    ]
    materials = [
        bpy.data.materials.get(f"Book binding {i}") or plain(f"Book binding {i}", c, 0.66)
        for i, c in enumerate(colors)
    ]
    x = -length / 2
    while x < length / 2 - 0.035:
        width = min(rng.uniform(0.018, 0.052), length / 2 - x)
        height, depth = rng.uniform(0.19, 0.29), rng.uniform(0.14, 0.19)
        material = rng.choice(materials)
        box(
            name + " paper block",
            (x + width / 2, 0, height / 2),
            (width - 0.004, depth - 0.004, height - 0.005),
            m["ivory"],
            0.001,
        )
        box(
            name + " bound spine",
            (x + width / 2, -depth / 2, height / 2),
            (width, 0.007, height),
            material,
            0.002,
        )
        for side in [x, x + width]:
            box(name + " cover", (side, 0, height / 2), (0.002, depth, height), material, 0.0004)
        for z in [height * 0.15, height * 0.82]:
            box(
                name + " spine band",
                (x + width / 2, -depth / 2 - 0.004, z),
                (width * 0.7, 0.001, 0.002),
                m["brass"],
                0,
            )
        x += width + rng.uniform(0.001, 0.003)
    return group(name, set(bpy.data.objects) - before, position, angle)


def bookcase(name, position, width, height, m, angle=0, seed=1):
    before = set(bpy.data.objects)
    depth = 0.28
    for x in [-width / 2, width / 2]:
        box(name + " upright", (x, 0, height / 2), (0.028, depth, height), m["ivory"])
    box(name + " backing", (0, depth / 2, height / 2), (width, 0.018, height), m["ivory"])
    count = int(height / 0.34)
    for i in range(count + 1):
        z = 0.06 + i * (height - 0.10) / count
        box(name + " shelf", (0, 0, z), (width, depth, 0.024), m["ivory"])
        if i < count:
            books(name + " shelf books", (0, -0.015, z + 0.013), width - 0.06, m, seed + i)
    return group(name, set(bpy.data.objects) - before, position, angle)


def bed(name, position, width, m, angle=0, linen=None, storage=False):
    before = set(bpy.data.objects)
    material = m["ivory"] if storage else m["towel"]
    box(name + " upholstered platform", (0, 0, 0.25), (width + 0.07, 2.05, 0.32), material, 0.05)
    rounded_cushion(name + " mattress", (0, -0.02, 0.50), (width, 1.97, 0.25), m["towel"])
    rounded_cushion(name + " headboard", (0, 1.03, 0.82), (width + 0.14, 0.12, 1.21), material)
    for x in [-width / 2 + 0.08, width / 2 - 0.08]:
        for y in [-0.9, 0.9]:
            cylinder_between(name + " foot", (x, y, 0.02), (x, y, 0.18), 0.03, m["wood"])
    # Draped duvet with gravity-like edge drops and continuous wrinkle geometry.
    verts, faces = [], []
    nx, ny = 96, 112
    for j in range(ny + 1):
        y = -1.25 + j * 2.05 / ny
        for i in range(nx + 1):
            x = -width / 2 - 0.23 + i * (width + 0.46) / nx
            overhang = max(abs(x) - width / 2 + 0.035, 0)
            foot_drop = max(-y - 0.93, 0)
            z = 0.695 - 1.05 * max(overhang, foot_drop)
            z += 0.012 * math.sin(16 * x + 3 * y) * math.sin(11 * y)
            z += 0.006 * math.sin(37 * x + 7 * y) + 0.004 * math.cos(41 * y - 2 * x)
            verts.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    mesh = bpy.data.meshes.new(name + " draped duvet")
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.collection.objects.link(obj)
    finish(obj, linen or m["fabric"])
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    solid = obj.modifiers.new("Quilt thickness", "SOLIDIFY")
    solid.thickness = 0.018
    for x in [-width * 0.24, width * 0.24]:
        pillow = rounded_cushion(
            name + " sleeping pillow", (x, 0.69, 0.75), (width * 0.43, 0.48, 0.17), m["towel"]
        )
        pillow.rotation_euler.x = -0.17
        accent = rounded_cushion(
            name + " upright pillow", (x, 0.53, 0.91), (width * 0.36, 0.14, 0.47), m["towel"]
        )
        accent.rotation_euler.x = -0.19
    if storage:
        for x in [-width * 0.25, width * 0.25]:
            box(name + " storage drawer", (x, -1.04, 0.28), (width * 0.48, 0.025, 0.24), m["ivory"])
            cylinder_between(
                name + " storage handle",
                (x - 0.04, -1.066, 0.3),
                (x + 0.04, -1.066, 0.3),
                0.006,
                m["iron"],
            )
    root = group(name, set(bpy.data.objects) - before, position, angle)
    annotate(root, "bed", [27, 28] if "Primary" in name else [35, 38])
    return root


def fan(name, position, m):
    before = set(bpy.data.objects)
    cylinder_between(name + " downrod", (0, 0, -0.17), (0, 0, 0), 0.018, m["iron"])
    lathe(
        name + " motor",
        [(0, -0.25), (1, -0.25), (1, -0.17), (0, -0.14)],
        (0, 0, 0),
        (0.11, 0.11),
        m["steel"],
    )
    for i in range(3):
        a = i * math.tau / 3
        blade = box(
            name + " curved blade",
            (0.32 * math.cos(a), 0.32 * math.sin(a), -0.22),
            (0.55, 0.105, 0.013),
            m["wood"],
            0.025,
        )
        blade.rotation_euler = (0.07, 0.08, a + 0.14)
    root = group(name, set(bpy.data.objects) - before, position)
    root["runtime_motion"] = "ceiling_fan"
    return root


def framed_mirror(name, position, size, m, angle=0):
    before = set(bpy.data.objects)
    w, h = size
    box(name + " silver", (0, 0, 0), (w, 0.008, h), m["mirror"])
    for x in [-w / 2, w / 2]:
        box(name + " side", (x, -0.01, 0), (0.035, 0.035, h + 0.035), m["wood"])
    for z in [-h / 2, h / 2]:
        box(name + " rail", (0, -0.01, z), (w, 0.035, 0.035), m["wood"])
    return group(name, set(bpy.data.objects) - before, position, angle)
