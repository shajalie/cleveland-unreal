"""Compass 18–22: U-shaped work area, window sink and a furnished breakfast nook."""

import math
import bpy
from ..primitives import box, cylinder_between
from ..furnishings import group, import_asset, rounded_cushion
from ..materials import scanned
from .fixtures import basin, cabinet, faucet, sphere


def range_appliance(position, m):
    before = set(bpy.data.objects)
    box("Stainless range body", (0, 0, 0.43), (0.76, 0.66, 0.86), m["steel"], 0.022)
    box("Oven black glass", (0, -0.339, 0.41), (0.60, 0.009, 0.40), m["appliance_glass"], 0.03)
    box("Oven lower drawer", (0, -0.338, 0.115), (0.68, 0.015, 0.13), m["steel"], 0.01)
    cylinder_between("Oven handle", (-0.31, -0.39, 0.68), (0.31, -0.39, 0.68), 0.018, m["steel"])
    for x in [-0.29, -0.19, 0.19, 0.29]:
        cylinder_between(
            "Range control dial", (x, -0.344, 0.81), (x, -0.368, 0.81), 0.023, m["steel"]
        )
    for x in [-0.19, 0.19]:
        for y in [-0.17, 0.15]:
            cylinder_between("Gas burner", (x, y, 0.865), (x, y, 0.88), 0.075, m["iron"])
            for axis in [0, 1]:
                box(
                    "Cast iron stove grate",
                    (x, y, 0.91),
                    ((0.30 if axis == 0 else 0.018), (0.018 if axis == 0 else 0.27), 0.018),
                    m["iron"],
                    0.004,
                )
    return group("Kitchen gas range", set(bpy.data.objects) - before, position, math.pi)


def build(m):
    backsplash = scanned(
        "Kitchen beige stone backsplash", "marble_01", 0.55, True, tint=(0.75, 0.64, 0.43)
    )
    for row in range(5):
        for col in range(11):
            x = -5.22 + col * 0.15 + (row % 2) * 0.075
            if x < -3.68:
                box(
                    "Range backsplash tile",
                    (x, 4.266, 0.99 + row * 0.09),
                    (0.146, 0.022, 0.086),
                    backsplash,
                    0.001,
                )
        for col in range(35):
            y = 4.46 + col * 0.10 + (row % 2) * 0.05
            z = 0.99 + row * 0.09
            if 5.50 <= y <= 6.86 and z > 1.0:
                continue
            box(
                "Sink wall backsplash tile",
                (-5.348, y, z),
                (0.022, 0.096, 0.086),
                backsplash,
                0.001,
            )
    for y in [5.0, 6.3, 7.5, 9.65]:
        cylinder_between(
            "Recessed light trim", (-4.08, y, 2.866), (-4.08, y, 2.888), 0.075, m["ivory"]
        )
        cylinder_between(
            "Recessed light diffuser", (-4.08, y, 2.862), (-4.08, y, 2.866), 0.06, m["lamp"]
        )
        data = bpy.data.lights.new("Kitchen recessed practical", "AREA")
        data.energy, data.shape, data.size = 7, "DISK", 0.12
        data.color = (1, 0.9, 0.78)
        light = bpy.data.objects.new("Kitchen recessed practical", data)
        bpy.context.collection.objects.link(light)
        light.location = (-4.08, y, 2.858)
    # West wall: countertops are genuinely cut around the bowl, not laid across it.
    for y, length in [(5.10, 1.31), (7.25, 1.31)]:
        cabinet("Kitchen west base", (-5.13, y, 0.09), length, 0.62, 0.79, m, math.pi / 2)
        box(
            "West stone worktop",
            (-5.12, y, 0.905),
            (0.68, length + 0.02, 0.04),
            m["worktop"],
            0.007,
        )
    cabinet("Farmhouse sink cabinet", (-5.14, 6.17, 0.09), 0.84, 0.61, 0.58, m, math.pi / 2)
    before = set(bpy.data.objects)
    basin("Open farmhouse sink", (0, 0, 0.91), 0.84, 0.57, m["ceramic"])
    faucet("Pull-down kitchen faucet", (0, 0.22, 0.93), m["steel"], 0.34)
    group("Sink beneath west window", set(bpy.data.objects) - before, (-5.11, 6.17, 0), math.pi / 2)
    box("Stone behind sink", (-5.43, 6.17, 0.905), (0.10, 0.86, 0.04), m["worktop"], 0.004)
    # The dishwasher sits to the right of the sink when facing the window.
    box("Dishwasher stainless front", (-4.786, 6.99, 0.45), (0.035, 0.59, 0.80), m["steel"], 0.014)
    cylinder_between(
        "Dishwasher handle", (-4.745, 6.76, 0.80), (-4.745, 7.22, 0.80), 0.017, m["steel"]
    )
    # Range under microwave on the short wall; the dining entrance stays clear.
    range_appliance((-4.22, 4.58, 0.03), m)
    cabinet("Range left base", (-4.94, 4.58, 0.09), 0.64, 0.61, 0.79, m, math.pi)
    cabinet("Range right drawers", (-3.77, 4.58, 0.09), 0.20, 0.61, 0.79, m, math.pi)
    for x, width in [(-4.98, 0.62), (-3.77, 0.20)]:
        cabinet("Range wall upper", (x, 4.40, 1.47), width, 0.35, 1.26, m, math.pi)
    cabinet("Cupboard above microwave", (-4.22, 4.40, 2.12), 0.78, 0.35, 0.61, m, math.pi)
    box("Microwave stainless case", (-4.22, 4.43, 1.88), (0.76, 0.40, 0.40), m["steel"], 0.015)
    box(
        "Microwave glass door",
        (-4.28, 4.638, 1.87),
        (0.55, 0.012, 0.27),
        m["appliance_glass"],
        0.012,
    )
    box("Microwave controls", (-3.92, 4.64, 1.88), (0.09, 0.015, 0.28), m["iron"], 0.004)
    # Short east run stops before the hall opening.
    cabinet("East pantry cupboard", (-1.90, 7.15, 0.09), 0.74, 0.58, 2.65, m, -math.pi / 2)
    cabinet("East counter base", (-1.90, 6.49, 0.09), 0.62, 0.58, 0.79, m, -math.pi / 2)
    box("East stone counter", (-1.90, 6.49, 0.905), (0.66, 0.64, 0.04), m["worktop"], 0.006)
    cabinet(
        "East glass crockery cupboard", (-1.73, 6.52, 1.47), 0.62, 0.35, 1.25, m, -math.pi / 2, True
    )
    cabinet(
        "West glass crockery cupboard", (-5.29, 7.43, 1.46), 0.78, 0.35, 1.26, m, math.pi / 2, True
    )
    # Refrigerator, separated freezer drawer and dispenser.
    box("French door refrigerator", (-5.05, 8.28, 1.05), (0.79, 0.92, 2.10), m["steel"], 0.028)
    for y in [8.05, 8.51]:
        box("Refrigerator upper door", (-4.636, y, 1.36), (0.028, 0.445, 1.40), m["steel"], 0.015)
        cylinder_between(
            "Refrigerator vertical handle",
            (-4.59, y + (0.17 if y < 8.28 else -0.17), 0.87),
            (-4.59, y + (0.17 if y < 8.28 else -0.17), 1.73),
            0.018,
            m["steel"],
        )
    box("Refrigerator freezer drawer", (-4.63, 8.28, 0.37), (0.03, 0.90, 0.56), m["steel"], 0.016)
    box(
        "Refrigerator dispenser recess", (-4.604, 8.01, 1.36), (0.016, 0.22, 0.32), m["iron"], 0.008
    )
    # Furnished breakfast area leaves a route from the kitchen to the terrace door.
    box("Breakfast bench storage", (-4.08, 10.92, 0.25), (2.18, 0.49, 0.48), m["ivory"], 0.01)
    rounded_cushion(
        "Breakfast bench cushion", (-4.08, 10.90, 0.53), (2.14, 0.51, 0.12), m["fabric"]
    )
    for x in [-4.65, -3.60]:
        cushion = rounded_cushion(
            "Breakfast bench back cushion", (x, 11.05, 0.79), (0.56, 0.15, 0.48), m["fabric"]
        )
        cushion.rotation_euler.x = -0.12
    top = box("Breakfast oak table", (-4.17, 10.06, 0.765), (1.28, 0.85, 0.055), m["wood"], 0.05)
    top["reference_photos"] = "20,21"
    for x in [-4.67, -3.67]:
        for y in [9.77, 10.35]:
            cylinder_between("Breakfast table leg", (x, y, 0.02), (x, y, 0.74), 0.028, m["wood"])
    import_asset("dining_chair_02", (-4.17, 9.38, 0), math.pi, 0.94)
    # Counter objects visible in the listing, with separate silhouettes and contact shadows.
    box("Coffee machine", (-5.11, 5.22, 1.10), (0.29, 0.28, 0.37), m["iron"], 0.025)
    box("Coffee machine chrome face", (-4.952, 5.22, 1.12), (0.018, 0.22, 0.28), m["steel"], 0.009)
    box("Four slot toaster", (-5.10, 7.60, 1.025), (0.26, 0.34, 0.24), m["steel"], 0.04)
    for offset in [-0.06, 0.06]:
        box("Toaster slot", (-5.10 + offset, 7.60, 1.150), (0.015, 0.25, 0.009), m["iron"], 0.003)
    for i in range(5):
        x, y = -5.14 + i * 0.043, 4.93
        cylinder_between(
            "Cooking oil bottle", (x, y, 0.93), (x, y, 1.12 + i % 2 * 0.07), 0.018, m["glass"]
        )
        sphere("Bottle cap", (x, y, 1.14 + i % 2 * 0.07), (0.015, 0.015, 0.02), m["iron"])
    for position in [(-5.37, 5.83, 1.05), (-5.37, 6.53, 1.05)]:
        import_asset("potted_plant_04", position, target_height=0.36)
    box("Kitchen runner", (-4.12, 6.52, 0.015), (0.74, 3.18, 0.022), m["fabric"], 0.005)
