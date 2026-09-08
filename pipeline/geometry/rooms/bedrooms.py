"""Bedrooms and sunroom directed by Compass photographs 27–40 and plan 55."""

import math
import bpy
from ..primitives import box, cylinder_between, annotate
from ..furnishings import group, import_asset, rounded_cushion
from .domestic import bed, chest, lamp, desk, bookcase, books, fan, framed_mirror, recolor
from .fixtures import sphere, cabinet
from .bathrooms import radiator


def primary(m):
    before = set(bpy.data.objects)
    blue = recolor(m["towel"], "Primary blue cotton duvet", (0.37, 0.48, 0.51))
    bed("Primary upholstered bed", (-4.12, 4.50, 3.12), 1.65, m, math.pi / 2, blue)
    for y in [3.24, 5.76]:
        chest(
            "Primary white bedside chest",
            (-5.00, y, 3.12),
            (0.60, 0.45, 0.62),
            m,
            math.pi / 2,
            True,
            2,
        )
        lamp("Primary pleated bedside lamp", (-5.01, y, 3.76), m)
        books("Primary bedside reading", (-4.95, y + 0.16, 3.76), 0.18, m, 27, math.pi / 2)
    # Bench is beyond the duvet; it leaves the eastern hall-to-bath route clear.
    rounded_cushion(
        "Primary upholstered foot bench", (-2.66, 4.50, 3.61), (0.45, 1.71, 0.17), m["towel"]
    )
    for y in [3.78, 5.22]:
        for x in [-2.8, -2.52]:
            cylinder_between("Primary bench leg", (x, y, 3.15), (x, y, 3.55), 0.023, m["wood"])
    chest(
        "Primary long timber dresser",
        (-1.86, 2.96, 3.12),
        (1.72, 0.50, 0.93),
        m,
        -math.pi / 2,
        columns=3,
    )
    television("Primary wall television", (-1.58, 2.96, 4.78), 1.12, m, -math.pi / 2)
    lamp("Primary dresser lamp", (-1.91, 3.49, 4.08), m, 0.50)
    chest("Primary rear chest", (-2.14, 7.19, 3.12), (0.78, 0.41, 0.92), m, rows=4)
    # Free-standing exposed masonry pier visible in 27–30; dimensions inferred.
    box("Primary exposed brick chimney", (-2.35, 6.15, 4.49), (0.53, 0.48, 2.74), m["brick"], 0.014)
    framed_mirror(
        "Primary leaning dressing mirror", (-2.65, 6.11, 4.07), (0.51, 1.69), m, math.pi / 2
    )
    desk("Primary dressing table", (-4.11, 0.53, 3.12), (1.18, 0.48), m, math.pi)
    import_asset("dining_chair_02", (-4.11, 1.22, 3.12), math.pi, 0.93)
    fan("Primary ceiling fan", (-3.50, 4.40, 5.76), m)
    radiator((-5.13, 1.2, 3.12), 0.92, math.pi / 2, m)
    root = group("Furnished primary bedroom", set(bpy.data.objects) - before, (0, 0, 0))
    annotate(root, "primary_bedroom", [27, 28, 29, 30, 55])


def television(name, position, width, m, angle=0):
    before = set(bpy.data.objects)
    box(name + " frame", (0, 0, 0), (width, 0.045, width * 0.5625), m["iron"], 0.009)
    box(
        name + " screen",
        (0, -0.024, 0),
        (width - 0.026, 0.004, width * 0.5625 - 0.025),
        m["appliance_glass"],
        0.003,
    )
    return group(name, set(bpy.data.objects) - before, position, angle)


def sunroom(m):
    before = set(bpy.data.objects)
    desk("Sunroom writing desk", (-4.28, 9.82, 3.12), (1.63, 0.67), m)
    # Swiveling office chair silhouette with five feet and casters.
    chair = set(bpy.data.objects)
    cylinder_between("Office chair lift", (0, 0, 0.09), (0, 0, 0.49), 0.029, m["steel"])
    rounded_cushion("Office leather seat", (0, 0, 0.50), (0.54, 0.52, 0.16), m["leather"])
    rounded_cushion("Office leather back", (0, 0.24, 0.83), (0.54, 0.14, 0.66), m["leather"])
    rounded_cushion("Office leather headrest", (0, 0.26, 1.10), (0.53, 0.16, 0.18), m["leather"])
    for i in range(5):
        a = i * math.tau / 5
        x, y = 0.34 * math.cos(a), 0.34 * math.sin(a)
        cylinder_between("Office chair radial foot", (0, 0, 0.15), (x, y, 0.08), 0.021, m["iron"])
        sphere("Office chair caster", (x, y, 0.05), (0.033, 0.026, 0.036), m["iron"])
    group("Sunroom office chair", set(bpy.data.objects) - chair, (-4.28, 10.48, 3.12))
    for x in [-5.02, -3.35]:
        lamp("Sunroom table lamp", (x, 10.86, 3.88), m, 0.52)
    chest(
        "Sunroom rear window cabinets",
        (-4.10, 10.93, 3.12),
        (2.18, 0.38, 0.71),
        m,
        white=True,
        rows=2,
        columns=3,
    )
    chest(
        "Sunroom filing cabinet", (-3.13, 9.37, 3.12), (0.63, 0.43, 0.74), m, -math.pi / 2, True, 2
    )
    box("Sunroom printer", (-3.14, 9.40, 3.96), (0.36, 0.40, 0.20), m["ivory"], 0.024)
    box("Printer output slot", (-3.36, 9.40, 3.96), (0.007, 0.29, 0.05), m["iron"])
    box("Printer paper tray", (-3.31, 9.40, 3.87), (0.18, 0.27, 0.014), m["ivory"])
    bookcase("Sunroom open shelves", (-3.13, 8.23, 3.12), 0.71, 1.75, m, -math.pi / 2, 31)
    books("Sunroom desktop books", (-4.89, 9.91, 3.90), 0.29, m, 31)
    cylinder_between(
        "Sunroom pencil cup", (-4.85, 9.64, 3.90), (-4.85, 9.64, 4.0), 0.036, m["brass"]
    )
    for i in range(7):
        cylinder_between(
            "Sunroom colored pencil",
            (-4.87 + i * 0.006, 9.64, 3.94),
            (-4.885 + i * 0.008, 9.645, 4.08),
            0.0028,
            m["wood"],
        )
    fan("Sunroom ceiling fan", (-4.12, 9.30, 5.76), m)
    root = group("Furnished sunroom office", set(bpy.data.objects) - before, (0, 0, 0))
    annotate(root, "sunroom", [31, 55])


def secondary(m):
    before = set(bpy.data.objects)
    # Rear bedroom (35–36): head on the southern partition, side window to the east.
    blue = recolor(m["towel"], "Blue bedroom woven bed linen", (0.43, 0.61, 0.63))
    bed("Blue bedroom bed", (3.52, 8.86, 3.12), 1.32, m, math.pi, blue)
    chest("Blue bedside cabinet", (2.50, 8.05, 3.12), (0.45, 0.42, 0.62), m, math.pi, rows=2)
    lamp("Blue bedroom bedside lamp", (2.50, 8.05, 3.78), m, 0.44)
    chest("Blue dark dresser", (1.22, 9.23, 3.12), (1.10, 0.47, 0.89), m, math.pi / 2)
    framed_mirror("Blue bedroom dresser mirror", (1.02, 9.23, 4.57), (0.68, 0.82), m, math.pi / 2)
    desk("Blue bedroom study desk", (4.33, 10.36, 3.12), (0.88, 0.50), m, -math.pi / 2)
    import_asset("dining_chair_02", (3.65, 10.36, 3.12), -math.pi / 2, 0.94)
    cabinet("Blue bedroom wardrobe", (1.54, 10.78, 3.12), 1.03, 0.46, 2.35, m)
    fan("Blue bedroom fan", (2.98, 9.38, 5.76), m)
    sphere("Blue bed basketball cushion", (3.52, 8.19, 4.05), (0.13, 0.13, 0.13), m["leather"])
    root = group("Furnished blue bedroom", set(bpy.data.objects) - before, (0, 0, 0))
    annotate(root, "bedroom_3", [35, 36, 55])
    before = set(bpy.data.objects)
    # Front bedroom (38–40): storage bed and overhead library, clear western doorway.
    pink = recolor(m["fabric"], "Yellow bedroom quilt", (0.62, 0.47, 0.40))
    bed("Yellow bedroom storage bed", (3.43, 3.23, 3.12), 1.40, m, linen=pink, storage=True)
    for x in [2.45, 4.41]:
        bookcase("Yellow bed side library", (x, 4.32, 3.12), 0.40, 2.08, m, seed=38)
    box("Yellow overhead library top", (3.43, 4.32, 5.28), (2.38, 0.29, 0.05), m["ivory"])
    box("Yellow overhead library shelf", (3.43, 4.32, 4.87), (1.55, 0.29, 0.035), m["ivory"])
    for x in [2.90, 3.43, 3.96]:
        box("Yellow library divider", (x, 4.32, 5.075), (0.025, 0.29, 0.38), m["ivory"])
        books("Yellow overhead books", (x - 0.21, 4.30, 4.90), 0.30, m, 40 + int(x * 10))
    desk("Yellow bedroom desk", (1.19, 1.45, 3.12), (1.12, 0.49), m, math.pi / 2)
    import_asset("dining_chair_02", (1.83, 1.45, 3.12), math.pi / 2, 0.94)
    import_asset("modern_arm_chair_01", (3.80, 0.76, 3.12), math.pi, 0.96, m["towel"])
    lamp("Yellow bedroom reading lamp", (4.38, 1.36, 3.78), m)
    chest("Yellow lamp side table", (4.38, 1.36, 3.12), (0.40, 0.38, 0.62), m, white=True, rows=2)
    root = group("Furnished yellow bedroom", set(bpy.data.objects) - before, (0, 0, 0))
    annotate(root, "bedroom_2", [38, 39, 40, 55])


def build(m):
    primary(m)
    sunroom(m)
    secondary(m)
