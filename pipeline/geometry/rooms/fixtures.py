"""Smooth sanitary ware, framed cabinetry and curved plumbing in meters."""

import math
import bpy
from ..primitives import box, cylinder_between, finish
from ..architecture import curve_tube
from ..furnishings import group


def sphere(name, position, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def lathe(name, profile, center, scale, material, square=False):
    vertices, faces = [], []
    count = 64
    for radius, height in profile:
        for j in range(count):
            angle = j * math.tau / count
            x, y = math.cos(angle), math.sin(angle)
            if square:
                x, y = math.copysign(abs(x) ** 0.5, x), math.copysign(abs(y) ** 0.5, y)
            vertices.append(
                (
                    center[0] + x * radius * scale[0],
                    center[1] + y * radius * scale[1],
                    center[2] + height,
                )
            )
    for row in range(len(profile) - 1):
        for j in range(count):
            a, b = row * count + j, row * count + (j + 1) % count
            faces.append((a, b, b + count, a + count))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    finish(obj, material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def basin(name, center, width, depth, material):
    return lathe(
        name,
        [
            (0, -0.22),
            (0.87, -0.22),
            (1, -0.035),
            (1, 0),
            (0.84, 0),
            (0.80, -0.055),
            (0.55, -0.16),
            (0, -0.17),
        ],
        center,
        (width / 2, depth / 2),
        material,
        True,
    )


def faucet(name, position, material, height=0.30):
    x, y, z = position
    points = [(x, y, z), (x, y, z + height * 0.64)]
    for i in range(25):
        theta = math.pi * i / 24
        points.append(
            (x, y - 0.095 + 0.095 * math.cos(theta), z + height * 0.64 + 0.095 * math.sin(theta))
        )
    curve_tube(name, points, 0.011, material)
    cylinder_between(name + " foot", (x, y, z - 0.008), (x, y, z + 0.022), 0.024, material)
    for dx in [-0.10, 0.10]:
        cylinder_between(name + " tap", (x + dx, y, z), (x + dx, y, z + 0.045), 0.018, material)
        cylinder_between(
            name + " lever", (x + dx, y, z + 0.045), (x + dx + 0.04, y, z + 0.045), 0.006, material
        )


def panel(name, x, y, z, width, height, material, handle_material, glass=None):
    for px in [x - width / 2 + 0.023, x + width / 2 - 0.023]:
        box(name + " stile", (px, y, z), (0.046, 0.028, height), material, 0.003)
    for pz in [z - height / 2 + 0.025, z + height / 2 - 0.025]:
        box(name + " rail", (x, y, pz), (width - 0.08, 0.028, 0.05), material, 0.003)
    box(
        name + " inset",
        (x, y + 0.012, z),
        (width - 0.07, 0.008, height - 0.08),
        glass or material,
        0.003,
    )
    sphere(
        name + " knob",
        (x + width * 0.32, y - 0.025, z + height * 0.25),
        (0.013, 0.013, 0.013),
        handle_material,
    )


def cabinet(name, position, width, depth, height, m, angle=0, glazed=False):
    before = set(bpy.data.objects)
    material = m["ivory"]
    for x in [-width / 2 + 0.01, width / 2 - 0.01]:
        box(name + " side", (x, 0, height / 2), (0.02, depth, height), material)
    box(name + " back", (0, depth / 2 - 0.01, height / 2), (width, 0.02, height), material)
    shelf_count = 5 if glazed else 2
    for index in range(shelf_count):
        z = 0.02 + index * (height - 0.04) / max(1, shelf_count - 1)
        box(name + " shelf", (0, 0, z), (width, depth, 0.022), material)
        if glazed and index < shelf_count - 1:
            for side in [-1, 1]:
                for plate in range(4):
                    lathe(
                        name + " stacked plate",
                        [(0, 0), (0.8, 0.002), (1, 0.01), (1, 0.014), (0, 0.011)],
                        (side * width * 0.24, 0, z + 0.02 + plate * 0.014),
                        (0.10, 0.10),
                        m["ceramic"],
                    )
    door_count = 2 if width > 0.65 else 1
    for index in range(door_count):
        w = width / door_count - 0.006
        x = -width / 2 + (index + 0.5) * width / door_count
        rows = 1 if glazed else (3 if height > 2 else 2 if height > 1.05 else 1)
        for row in range(rows):
            panel(
                name + " door",
                x,
                -depth / 2 - 0.012,
                (row + 0.5) * height / rows,
                w,
                height / rows - 0.014,
                material,
                m["steel"],
                m["glass"] if glazed else None,
            )
    if height > 1.0:
        for step in range(3):
            box(
                name + " crown molding",
                (0, -0.015 - step * 0.009, height + step * 0.021),
                (width + 0.03 + step * 0.016, depth + 0.03 + step * 0.015, 0.027),
                material,
                0.006,
            )
    obj = group(name, set(bpy.data.objects) - before, position, angle)
    return obj


def toilet(position, angle, m):
    before = set(bpy.data.objects)
    lathe(
        "Toilet pedestal",
        [(0, 0), (0.82, 0), (0.68, 0.05), (0.50, 0.22), (0.86, 0.32)],
        (0, 0, 0.025),
        (0.19, 0.27),
        m["ceramic"],
    )
    lathe(
        "Porcelain toilet bowl",
        [
            (0.65, 0.22),
            (0.94, 0.30),
            (1, 0.39),
            (0.84, 0.40),
            (0.75, 0.34),
            (0.35, 0.27),
            (0, 0.25),
        ],
        (0, -0.04, 0),
        (0.205, 0.29),
        m["ceramic"],
    )
    lathe(
        "Toilet seat ring",
        [(1, 0.40), (1, 0.425), (0.75, 0.425), (0.75, 0.40), (1, 0.40)],
        (0, -0.04, 0),
        (0.21, 0.29),
        m["ceramic"],
    )
    box("Toilet cistern", (0, 0.24, 0.56), (0.39, 0.19, 0.40), m["ceramic"], 0.055)
    box("Cistern lid", (0, 0.24, 0.775), (0.405, 0.205, 0.03), m["ceramic"], 0.012)
    cylinder_between(
        "Toilet flush control", (-0.14, 0.131, 0.70), (-0.09, 0.131, 0.70), 0.014, m["steel"]
    )
    return group("Toilet fixture", set(bpy.data.objects) - before, position, angle)
