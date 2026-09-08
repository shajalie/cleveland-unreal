"""Lower-level furnished library from Compass 43–44, within inferred partitions."""

import math
from ..primitives import box, cylinder_between
from ..furnishings import rounded_cushion, import_asset
from .domestic import bookcase, desk, chest, lamp
from .bedrooms import television


def build(m):
    for i in range(4):
        bookcase(
            "Lower library book wall",
            (-1.72, 1.0 + i * 1.23, -2.72),
            1.16,
            2.18,
            m,
            -math.pi / 2,
            43 + i * 10,
        )
    desk("Lower library writing table", (-4.94, 2.34, -2.72), (1.69, 0.58), m, math.pi / 2)
    import_asset("dining_chair_02", (-4.19, 2.34, -2.72), math.pi / 2, 0.95)
    import_asset("potted_plant_04", (-4.99, 1.84, -1.93), target_height=0.38)
    chest("Lower media cabinet", (-5.05, 4.65, -2.72), (1.05, 0.43, 0.84), m, math.pi / 2)
    television("Lower wall television", (-5.31, 4.65, -1.22), 1.07, m, math.pi / 2)
    lamp("Lower library desk lamp", (-4.95, 2.91, -1.93), m)
    for y in [9.12, 9.85]:
        rounded_cushion("Lower white sofa seat", (-1.98, y, -2.23), (0.75, 0.69, 0.17), m["towel"])
        rounded_cushion("Lower white sofa back", (-1.70, y, -1.99), (0.15, 0.70, 0.60), m["towel"])
        for x in [-2.22, -1.77]:
            cylinder_between("Lower sofa leg", (x, y, -2.69), (x, y, -2.3), 0.018, m["iron"])
    for y in [1.3, 4.6, 9.3]:
        box(
            "Lower flush ceiling diffuser", (-3.40, y, -0.41), (0.34, 0.34, 0.055), m["lamp"], 0.025
        )
