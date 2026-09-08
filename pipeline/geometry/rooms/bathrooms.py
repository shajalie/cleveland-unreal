"""Distinct fixtures and finishes from Compass 23/24, 32/33, 37/41 and 42."""

import math
import bpy
from ..primitives import box, cylinder_between
from ..materials import plain, scanned
from ..furnishings import group, rounded_cushion
from ..architecture import curve_tube
from .fixtures import basin, faucet, panel, sphere, toilet, lathe


def vanity(position, width, angle, m, timber=True):
    before = set(bpy.data.objects)
    finish = m["wood"] if timber else m["ivory"]
    box("Vanity cabinet", (0, 0, 0.395), (width, 0.44, 0.59), finish, 0.012)
    for x in [-width / 2 + 0.035, width / 2 - 0.035]:
        for y in [-0.18, 0.18]:
            box("Vanity foot", (x, y, 0.09), (0.055, 0.055, 0.18), finish, 0.006)
    for x in [-width / 4, width / 4]:
        panel("Vanity paneled door", x, -0.23, 0.38, width / 2 - 0.009, 0.43, finish, m["iron"])
    panel("Vanity top drawer", 0, -0.23, 0.62, width - 0.01, 0.12, finish, m["iron"])
    basin("Open ceramic washbasin", (0, 0, 0.87), width + 0.02, 0.48, m["ceramic"])
    faucet("Bathroom mixer faucet", (0, 0.18, 0.89), m["steel"], 0.18)
    cylinder_between("Basin drain", (0, 0, 0.704), (0, 0, 0.71), 0.021, m["steel"])
    box("Mirror glass", (0, 0.232, 1.48), (width * 0.74, 0.007, 0.72), m["mirror"], 0.003)
    for x in [-width * 0.39, width * 0.39]:
        box("Mirror vertical frame", (x, 0.24, 1.48), (0.032, 0.035, 0.79), finish, 0.004)
    for z in [1.08, 1.88]:
        box("Mirror horizontal frame", (0, 0.24, z), (width * 0.82, 0.035, 0.032), finish, 0.004)
    for x in [-width * 0.27, 0, width * 0.27]:
        cylinder_between("Vanity light mount", (x, 0.22, 2.03), (x, 0.08, 2.03), 0.013, m["steel"])
        lathe(
            "Vanity glass shade",
            [(1, -0.06), (1, 0.06), (0.94, 0.06), (0.94, -0.06), (1, -0.06)],
            (x, 0.07, 2),
            (0.042, 0.042),
            m["glass"],
        )
        sphere("Vanity lamp bulb", (x, 0.07, 2), (0.017, 0.017, 0.033), m["lamp"])
        data = bpy.data.lights.new("Bathroom practical light", "POINT")
        data.energy, data.shadow_soft_size = 6, 0.035
        data.color = (1, 0.82, 0.64)
        light = bpy.data.objects.new("Bathroom practical light", data)
        bpy.context.collection.objects.link(light)
        light.location = (x, 0.045, 1.98)
    cylinder_between(
        "Soap dispenser bottle",
        (width * 0.35, 0.13, 0.88),
        (width * 0.35, 0.13, 1.01),
        0.026,
        m["ceramic"],
    )
    cylinder_between(
        "Soap pump", (width * 0.35, 0.13, 1.01), (width * 0.35, 0.10, 1.025), 0.007, m["steel"]
    )
    return group("Complete bathroom vanity", set(bpy.data.objects) - before, position, angle)


def shower(position, size, angle, m, green=False):
    before = set(bpy.data.objects)
    width, depth = size
    tile = m["green_tile"] if green else m["ceramic"]
    grout = m["grout"]
    box("Shower raised tray", (0, 0, 0.065), (width, depth, 0.13), m["ceramic"], 0.012)
    # Individual tile joints remain visible at grazing light.
    for row in range(9):
        for col in range(4):
            x = -width / 2 + (col + 0.5) * width / 4
            box(
                "Shower back wall tile",
                (x, depth / 2 - 0.017, 0.14 + (row + 0.5) * 0.25),
                (width / 4 - 0.004, 0.028, 0.246),
                tile,
                0.002,
            )
        for col in range(5):
            y = -depth / 2 + (col + 0.5) * depth / 5
            box(
                "Shower side wall tile",
                (-width / 2 + 0.017, y, 0.14 + (row + 0.5) * 0.25),
                (0.028, depth / 5 - 0.004, 0.246),
                tile,
                0.002,
            )
    for i in range(8):
        for j in range(10):
            box(
                "Shower mosaic floor",
                (-width / 2 + (i + 0.5) * width / 8, -depth / 2 + (j + 0.5) * depth / 10, 0.139),
                (width / 8 - 0.003, depth / 10 - 0.003, 0.012),
                tile,
                0.002,
            )
    box("Shower linear drain", (0, 0.12, 0.148), (0.14, 0.09, 0.007), grout, 0.003)
    box("Shower glass front", (0, -depth / 2, 1.13), (width, 0.008, 2.02), m["glass"], 0.002)
    box("Shower glass return", (width / 2, 0, 1.13), (0.008, depth, 2.02), m["glass"], 0.002)
    cylinder_between(
        "Shower overhead rail",
        (-width / 2, -depth / 2, 2.18),
        (width / 2, -depth / 2, 2.18),
        0.013,
        m["steel"],
    )
    cylinder_between(
        "Shower door handle",
        (width * 0.18, -depth / 2 - 0.035, 0.94),
        (width * 0.18, -depth / 2 - 0.035, 1.23),
        0.012,
        m["steel"],
    )
    for z in [0.30, 1.93]:
        box(
            "Shower glass hinge",
            (-width / 2 + 0.025, -depth / 2, z),
            (0.058, 0.035, 0.069),
            m["steel"],
            0.006,
        )
    cylinder_between(
        "Shower riser pipe",
        (-width * 0.20, depth / 2 - 0.08, 1.10),
        (-width * 0.20, depth / 2 - 0.08, 2.10),
        0.009,
        m["steel"],
    )
    cylinder_between(
        "Rain shower arm",
        (-width * 0.20, depth / 2 - 0.08, 2.10),
        (-width * 0.20, depth / 2 - 0.32, 2.10),
        0.010,
        m["steel"],
    )
    cylinder_between(
        "Rain shower head",
        (-width * 0.20, depth / 2 - 0.32, 2.065),
        (-width * 0.20, depth / 2 - 0.32, 2.09),
        0.11,
        m["steel"],
    )
    sphere(
        "Shower mixer valve",
        (-width * 0.20, depth / 2 - 0.035, 1.12),
        (0.07, 0.025, 0.07),
        m["steel"],
    )
    curve_tube(
        "Hand shower flexible hose",
        [
            (-width * 0.1, depth / 2 - 0.08, 1.14),
            (0.07, depth / 2 - 0.1, 0.62),
            (0.19, depth / 2 - 0.12, 0.83),
            (0.15, depth / 2 - 0.11, 1.45),
        ],
        0.007,
        m["steel"],
    )
    box(
        "Shower toiletry shelf",
        (-width * 0.28, depth / 2 - 0.14, 0.78),
        (0.28, 0.24, 0.028),
        tile,
        0.005,
    )
    for i in range(3):
        cylinder_between(
            "Shower shampoo bottle",
            (-width * 0.28 - 0.08 + i * 0.07, depth / 2 - 0.16, 0.80),
            (-width * 0.28 - 0.08 + i * 0.07, depth / 2 - 0.16, 0.95 + i % 2 * 0.035),
            0.023,
            m["ceramic"],
        )
    return group("Complete shower enclosure", set(bpy.data.objects) - before, position, angle)


def radiator(position, length, angle, m):
    before = set(bpy.data.objects)
    for i in range(max(3, int(length / 0.065))):
        x = -length / 2 + i * 0.065
        for y in [-0.035, 0.035]:
            cylinder_between("Radiator cast column", (x, y, 0.10), (x, y, 0.68), 0.026, m["ivory"])
        for z in [0.12, 0.65]:
            sphere("Radiator rounded joint", (x, 0, z), (0.03, 0.065, 0.036), m["ivory"])
    return group("Cast iron radiator", set(bpy.data.objects) - before, position, angle)


def build(m):
    m = dict(m)
    m["green_tile"] = scanned(
        "Green stone bathroom tile", "marble_01", 0.8, True, tint=(0.26, 0.46, 0.36)
    )
    m["grout"] = plain("Tile grout", (0.41, 0.43, 0.40), 0.85)
    ochre = m["plaster"].copy()
    ochre.name = "Powder room warm ochre"
    ochre.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (
        0.46,
        0.29,
        0.16,
        1,
    )
    for name, center, size in [
        ("Powder stone floor", (-0.784, 6.88, 0.012), (1.30, 1.28, 0.024)),
        ("Primary bath stone floor", (-0.33, 1.40, 3.132), (2.04, 2.55, 0.024)),
        ("Hall bath stone floor", (2.78, 6.17, 3.132), (3.75, 2.68, 0.024)),
    ]:
        box(name, center, size, m["ceramic"], 0.002)
    box("Powder painted window apron", (-0.784, 7.472, 0.46), (1.30, 0.016, 0.92), ochre)
    # Main powder room. Keep the south entry and north window unobstructed.
    box("Powder west painted wall", (-1.432, 6.88, 1.38), (0.016, 1.42, 2.76), ochre)
    box("Powder east painted wall", (-0.137, 6.88, 1.38), (0.016, 1.42, 2.76), ochre)
    vanity((-1.17, 6.92, 0), 0.72, math.pi / 2, m)
    toilet((-0.43, 7.20, 0), 0, m)
    cylinder_between(
        "Powder towel rail", (-1.43, 7.37, 1.24), (-1.12, 7.37, 1.24), 0.008, m["iron"]
    )
    rounded_cushion("Powder hand towel", (-1.26, 7.36, 1.04), (0.25, 0.024, 0.39), m["towel"])
    # Primary bathroom: the photo's shower / vanity / toilet row faces the bedroom.
    before = set(bpy.data.objects)
    for row in range(11):
        for col in range(10):
            box(
                "Primary green stone wall tile",
                (-1.25 + (col + 0.5) * 0.25, 2.05, (row + 0.5) * 0.244),
                (0.247, 0.016, 0.241),
                m["green_tile"],
                0.0015,
            )
    shower((-0.85, 1.18, 0), (0.86, 1.50), 0, m, True)
    vanity((0, 1.77, 0), 0.68, 0, m, False)
    toilet((0.77, 1.55, 0), 0, m)
    radiator((0.98, 0.70, 0), 1.0, math.pi / 2, m)
    group(
        "Primary bathroom fixtures",
        set(bpy.data.objects) - before,
        (-1.35, 1.40, 3.12),
        -math.pi / 2,
    )
    # Shared bathroom: oak vanity, glazed white-tile shower, toilet and radiator.
    vanity((2.02, 5.05, 3.12), 0.91, math.pi, m)
    shower((3.69, 5.52, 3.12), (1.25, 1.25), math.pi, m)
    toilet((4.28, 6.96, 3.12), -math.pi / 2, m)
    radiator((4.59, 6.38, 3.12), 0.83, math.pi / 2, m)
    # Lower-level laundry bath from photo 42. Partition geometry remains separately tracked.
    vanity((-3.09, 8.25, -2.72), 0.57, 0, m)
    toilet((-1.78, 8.17, -2.72), 0, m)
    shower((-3.80, 7.83, -2.72), (1.04, 1.32), 0, m)
    for z, label in [(-2.27, "Washer"), (-1.34, "Dryer")]:
        box(label + " body", (-2.39, 8.13, z), (0.69, 0.65, 0.87), m["ivory"], 0.025)
        cylinder_between(
            label + " silver door ring", (-2.39, 7.792, z), (-2.39, 7.762, z), 0.25, m["steel"]
        )
        cylinder_between(
            label + " dark window",
            (-2.39, 7.751, z),
            (-2.39, 7.743, z),
            0.212,
            m["appliance_glass"],
        )
        cylinder_between(
            label + " control dial",
            (-2.43, 7.79, z + 0.32),
            (-2.43, 7.76, z + 0.32),
            0.028,
            m["steel"],
        )
