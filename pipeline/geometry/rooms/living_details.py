"""Distinct missing living/study objects observed in Compass 7–14."""

import math
import bpy
from ..primitives import box, cylinder_between
from ..furnishings import group, rounded_cushion
from .domestic import chest, lamp, framed_mirror
from .bedrooms import television


def build(m):
    before = set(bpy.data.objects)
    box("Upright piano cabinet", (0, 0, 0.59), (1.36, 0.46, 1.15), m["iron"], 0.013)
    box("Piano keyboard bed", (0, -0.32, 0.73), (1.30, 0.24, 0.085), m["iron"], 0.008)
    box("Piano music rest", (0, -0.25, 1.0), (0.90, 0.025, 0.25), m["iron"])
    box("Piano top lid", (0, 0, 1.185), (1.40, 0.49, 0.035), m["iron"], 0.009)
    for i in range(52):
        x = -0.616 + i * 0.024
        box("Piano ivory key", (x, -0.33, 0.785), (0.023, 0.18, 0.018), m["ivory"], 0.001)
        if i % 7 not in [2, 6] and i < 51:
            box(
                "Piano black key",
                (x + 0.012, -0.292, 0.804),
                (0.013, 0.107, 0.019),
                m["iron"],
                0.001,
            )
    for x in [-0.085, 0, 0.085]:
        cylinder_between("Piano brass pedal", (x, -0.20, 0.11), (x, -0.34, 0.08), 0.014, m["brass"])
    rounded_cushion("Piano bench seat", (0, -0.78, 0.47), (0.84, 0.35, 0.08), m["leather"])
    for x in [-0.35, 0.35]:
        for y in [-0.89, -0.67]:
            box("Piano bench leg", (x, y, 0.23), (0.033, 0.033, 0.46), m["iron"])
    group(
        "Living upright piano and bench",
        set(bpy.data.objects) - before,
        (1.18, 6.80, 0),
        math.pi / 2,
    )
    framed_mirror("Living mantel mirror", (4.48, 4.60, 1.87), (1.06, 0.83), m, -math.pi / 2)
    for y in [2.95, 6.08]:
        chest("Living sofa side table", (1.44, y, 0), (0.44, 0.43, 0.55), m, math.pi / 2, rows=1)
        lamp("Living shaded table lamp", (1.43, y, 0.58), m, 0.48)
    television("Study television", (1.24, 10.55, 1.36), 0.78, m, math.pi / 2)
    rounded_cushion(
        "Study patterned sofa pillow", (1.56, 8.40, 0.89), (0.20, 0.45, 0.43), m["fabric"]
    )
    rounded_cushion(
        "Study sofa accent pillow", (1.56, 9.75, 0.89), (0.20, 0.42, 0.42), m["leather"]
    )
    lamp("Study cabinet lamp", (1.43, 10.94, 0.78), m, 0.43)
