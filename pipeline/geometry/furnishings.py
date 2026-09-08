"""Reference-directed furniture, soft goods and lived-in details."""

import math
import random
from pathlib import Path
import bpy
from mathutils import Vector
from .primitives import box, cylinder_between, annotate
from .architecture import curve_tube

ROOT = Path(__file__).resolve().parents[2]
RNG = random.Random(3014)


def group(name, objects, position, angle=0):
    parent = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(parent)
    for obj in objects:
        if obj.parent not in objects:
            world = obj.matrix_world.copy()
            obj.parent = parent
            obj.matrix_world = world
    parent.location = position
    parent.rotation_euler.z = angle
    return parent


def rounded_cushion(name, center, size, material):
    obj = box(name, center, size, material, 0)
    bevel = obj.modifiers.new("Upholstery rounding", "BEVEL")
    bevel.width = min(size) * 0.32
    bevel.segments = 5
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    subdiv = obj.modifiers.new("Continuous upholstery surface", "SUBSURF")
    subdiv.levels = 2
    subdiv.render_levels = 2
    texture = bpy.data.textures.get("Leather soft wrinkles") or bpy.data.textures.new(
        "Leather soft wrinkles", type="CLOUDS"
    )
    texture.noise_scale = 0.085
    texture.noise_depth = 2
    displace = obj.modifiers.new("Subtle cushion settling", "DISPLACE")
    displace.texture = texture
    displace.strength = 0.006
    displace.mid_level = 0.5
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def sofa(m):
    before = set(bpy.data.objects)
    box("Sofa shadow plinth", (0, 0, 0.20), (2.45, 0.81, 0.18), m["wood"], 0.025)
    rounded_cushion(
        "Leather upholstered lower frame", (0, 0, 0.35), (2.55, 0.94, 0.24), m["leather"]
    )
    for x in [-1.20, 1.20]:
        rounded_cushion("Padded leather arm", (x, 0, 0.61), (0.23, 0.98, 0.43), m["leather"])
        for y in [-0.32, 0.32]:
            cylinder_between("Sofa timber foot", (x, y, 0.02), (x, y, 0.24), 0.036, m["wood"])
    for i in range(3):
        x = (i - 1) * 0.738
        rounded_cushion(
            "Individual leather seat", (x, -0.08, 0.49), (0.73, 0.75, 0.18), m["leather"]
        )
        back = rounded_cushion(
            "Individual softly padded back", (x, 0.36, 0.78), (0.75, 0.21, 0.67), m["leather"]
        )
        back.rotation_euler.x = math.radians(-9)
        # Piped seam around each seat, with a continuous rounded path.
        points = []
        for cx, cy, start in [
            (0.30, 0.23, 0),
            (-0.30, 0.23, 90),
            (-0.30, -0.32, 180),
            (0.30, -0.32, 270),
        ]:
            for j in range(13):
                theta = math.radians(start + j * 90 / 12)
                points.append(
                    (x + cx + 0.035 * math.cos(theta), cy + 0.035 * math.sin(theta), 0.547)
                )
        curve_tube("Leather seat piping", points + [points[0]], 0.0025, m["leather"])
        # Shallow channel seam across the back follows the photographed recliner form.
        curve_tube(
            "Back channel seam",
            [
                (x - 0.30, 0.234, 0.77),
                (x - 0.15, 0.227, 0.755),
                (x, 0.223, 0.75),
                (x + 0.15, 0.227, 0.755),
                (x + 0.30, 0.234, 0.77),
            ],
            0.003,
            m["leather"],
        )
    parent = group(
        "Living three-seat leather sofa",
        set(bpy.data.objects) - before,
        (1.40, 4.6, 0),
        math.pi / 2,
    )
    annotate(parent, "sofa", [7, 8, 9])
    parent["fidelity"] = (
        "Custom approximate silhouette; upholstery model is not a scan of the actual sofa."
    )


def import_asset(asset, position, angle=0, target_height=None, material_override=None):
    path = ROOT / ".local/model-assets" / asset / (asset + "_1k.gltf")
    if not path.exists():
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = set(bpy.data.objects) - before
    meshes = [o for o in objects if o.type == "MESH"]
    bpy.context.view_layer.update()
    corners = [o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
    low = Vector([min(v[i] for v in corners) for i in range(3)])
    high = Vector([max(v[i] for v in corners) for i in range(3)])
    root = group(asset, objects, (0, 0, 0))
    # Imported roots may contain glTF coordinate-system transforms; preserve them.
    scale = target_height / (high.z - low.z) if target_height else 1
    root.scale = (scale,) * 3
    root.rotation_euler.z = angle
    center = Vector(((low.x + high.x) * 0.5, (low.y + high.y) * 0.5, low.z)) * scale
    center.rotate(root.rotation_euler)
    root.location = Vector(position) - center
    for obj in meshes:
        if material_override:
            for slot in obj.material_slots:
                if any(w in slot.name.lower() for w in ["fabric", "leather", "cushion", "pillow"]):
                    slot.material = material_override
    root["source"] = "https://polyhaven.com/a/" + asset
    root["license"] = "CC0"
    return root


def curtain(name, x, y, z, width, height, m, angle=0):
    verts = []
    faces = []
    nx = 80
    ny = 24
    for j in range(ny + 1):
        t = j / ny
        for i in range(nx + 1):
            u = i / nx
            # Fine and broad folds, gathered more tightly at the rod.
            xx = (u - 0.5) * width * (0.67 + 0.33 * t)
            yy = 0.055 * math.sin(u * math.pi * 16) + 0.012 * math.sin(u * math.pi * 32)
            zz = -t * height + 0.012 * math.sin(u * math.pi * 16) * t * t
            verts.append((xx, yy, zz))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, y, z)
    obj.rotation_euler.z = angle
    obj.data.materials.append(m["ivory"])
    for f in mesh.polygons:
        f.use_smooth = True
    solid = obj.modifiers.new("Linen thickness", "SOLIDIFY")
    solid.thickness = 0.001
    annotate(obj, "linen_curtain", [7, 8, 9])


def living_room(m):
    sofa(m)
    # Chairs are placed facing the conversation area, not facing the walls.
    for x, y, angle in [(3.65, 2.53, math.radians(150)), (3.66, 6.25, math.radians(25))]:
        import_asset("modern_arm_chair_01", (x, y, 0), angle, 0.98, m["fabric"])
    box("Sisal area rug", (2.78, 4.47, 0.014), (2.70, 4.35, 0.022), m["rug"], 0.008)
    for i in range(105):
        y = 2.33 + i * 0.041
        for x in [1.39, 4.17]:
            cylinder_between(
                "Rug fringe",
                (x, y, 0.026),
                (x + (0.035 if x > 3 else -0.035), y, 0.027),
                0.0013,
                m["rug"],
                8,
            )
    box("Oak coffee table", (2.78, 4.51, 0.45), (0.62, 1.22, 0.045), m["wood"], 0.026)
    box("Coffee table lower shelf", (2.78, 4.51, 0.17), (0.51, 1.06, 0.026), m["wood"], 0.012)
    for x in [2.57, 2.99]:
        for y in [4.08, 4.94]:
            cylinder_between("Coffee table leg", (x, y, 0.035), (x, y, 0.44), 0.018, m["wood"])
    for i in range(5):
        box(
            "Coffee table book",
            (2.79, 4.55, 0.20 + i * 0.026),
            (0.32, 0.23, 0.024),
            m["ivory" if i % 2 else "leather"],
            0.002,
        )
    # Fireplace occupies the solid pier between the two side-window groups.
    box("Limestone hearth", (4.40, 4.60, 0.055), (0.70, 1.19, 0.11), m["concrete"], 0.009)
    box("Firebox dark recess", (4.60, 4.60, 0.55), (0.08, 0.83, 0.89), m["iron"])
    for y in [3.96, 5.24]:
        box("Timber mantel leg", (4.54, y, 0.61), (0.29, 0.14, 1.18), m["wood"], 0.012)
    box("Timber mantel shelf", (4.48, 4.60, 1.26), (0.46, 1.56, 0.12), m["wood"], 0.013)
    box("Mantel frieze", (4.50, 4.60, 1.11), (0.26, 1.30, 0.17), m["wood"], 0.01)
    for y0, y1 in [(2.18, 3.60), (5.68, 6.73)]:
        cylinder_between(
            "Curtain rod", (4.48, y0 - 0.2, 2.49), (4.48, y1 + 0.2, 2.49), 0.012, m["iron"]
        )
        for y in [y0 - 0.08, y1 + 0.08]:
            curtain("Living linen curtain", 4.44, y, 2.46, 0.43, 2.42, m, math.pi / 2)
    import_asset("potted_plant_04", (4.13, 3.88, 0.11), target_height=0.76)
    import_asset("potted_plant_04", (4.12, 6.86, 0), target_height=0.74)


def dining_room(m):
    center = (-3.55, 2.10)
    box("Dining rug", (*center, 0.013), (2.75, 3.15, 0.025), m["rug"])
    box("Dining table", (*center, 0.755), (1.05, 1.90, 0.065), m["wood"], 0.025)
    for x in [-3.97, -3.13]:
        for y in [1.40, 2.80]:
            cylinder_between("Dining table leg", (x, y, 0.02), (x, y, 0.74), 0.041, m["wood"])
    for x, y, angle in [
        (-4.42, 1.65, math.pi / 2),
        (-4.42, 2.55, math.pi / 2),
        (-2.68, 1.65, -math.pi / 2),
        (-2.68, 2.55, -math.pi / 2),
        (-3.55, 0.76, math.pi),
        (-3.55, 3.45, 0),
    ]:
        import_asset("dining_chair_02", (x, y, 0), angle, 0.97)
    box("Dining sideboard", (-5.02, 3.0, 0.48), (0.60, 1.6, 0.96), m["wood"], 0.015)
    for y in [2.44, 2.97, 3.50]:
        box("Raised sideboard door", (-4.702, y, 0.47), (0.035, 0.49, 0.79), m["wood"], 0.008)


def kitchen(m):
    for x in [-5.05, -2.04]:
        for i in range(4):
            y = 4.70 + i * 0.58
            box("Kitchen base cabinet", (x, y, 0.44), (0.62, 0.56, 0.86), m["ivory"], 0.009)
            box("Stone countertop", (x, y, 0.91), (0.66, 0.59, 0.045), m["concrete"], 0.007)
            box("Upper cabinet", (x, y, 1.97), (0.36, 0.55, 0.73), m["ivory"], 0.008)
            front = x + (0.32 if x < -3 else -0.32)
            box("Recessed cabinet panel", (front, y, 0.48), (0.025, 0.44, 0.62), m["ivory"], 0.006)
            cylinder_between(
                "Cabinet handle",
                (front + 0.015, y - 0.12, 0.72),
                (front + 0.015, y + 0.12, 0.72),
                0.008,
                m["iron"],
                16,
            )
    box("Breakfast table", (-4.12, 9.16, 0.75), (1.0, 1.0, 0.05), m["wood"], 0.024)
    for y, angle in [(8.36, math.pi), (9.96, 0)]:
        import_asset("dining_chair_02", (-4.12, y, 0), angle, 0.95)


def study(m):
    box("Study rug", (2.94, 9.36, 0.018), (2.60, 2.5, 0.025), m["rug"], 0.01)
    import_asset("mid_century_lounge_chair", (3.93, 9.60, 0), math.radians(45), 1.08, m["sage"])
    box("Study sofa lower", (1.63, 9.01, 0.31), (0.76, 1.82, 0.32), m["wood"], 0.07)
    for y in [8.55, 9.47]:
        rounded_cushion("Study sage seat", (1.67, y, 0.50), (0.79, 0.88, 0.20), m["sage"])
        rounded_cushion("Study sage back", (1.35, y, 0.79), (0.19, 0.92, 0.67), m["sage"])
    for y in [8.02, 10.02]:
        rounded_cushion("Study sofa arm", (1.63, y, 0.63), (0.79, 0.18, 0.46), m["sage"])
    import_asset("book_encyclopedia_set_01", (1.42, 10.61, 0.74), target_height=0.30)
    box("Study low book cabinet", (1.42, 10.61, 0.36), (0.48, 0.93, 0.72), m["ivory"], 0.008)
    box("Study cabinet shelf", (1.42, 10.61, 0.73), (0.52, 0.98, 0.035), m["ivory"], 0.006)


def wicker_chair(m, position, angle):
    before = set(bpy.data.objects)
    # Curved mesh of interlaced strands: real silhouette and transmitted daylight.
    for i in range(38):
        x = -0.27 + i * 0.54 / 37
        pts = [
            (x, -0.30 + j * 0.59 / 35, 0.47 + 0.014 * math.sin(j * math.pi + i * math.pi))
            for j in range(36)
        ]
        curve_tube("Wicker seat longitudinal", pts, 0.0032, m["wood"])
        pts = [(x, 0.29 + 0.10 * (j / 40) ** 1.7, 0.47 + j * 0.67 / 40) for j in range(41)]
        curve_tube("Wicker back longitudinal", pts, 0.003, m["wood"])
    for i in range(46):
        t = i / 45
        curve_tube(
            "Wicker back cross",
            [
                (
                    x,
                    0.29 + 0.10 * t**1.7 + 0.006 * math.sin(k * math.pi + i * math.pi),
                    0.47 + t * 0.67,
                )
                for k, x in enumerate([-0.27 + j * 0.54 / 45 for j in range(46)])
            ],
            0.0031,
            m["wood"],
        )
    for i in range(40):
        y = -0.30 + i * 0.59 / 39
        curve_tube(
            "Wicker seat cross",
            [
                (-0.27 + j * 0.54 / 36, y, 0.47 + 0.006 * math.sin(j * math.pi + i * math.pi))
                for j in range(37)
            ],
            0.003,
            m["wood"],
        )
    for x in [-0.31, 0.31]:
        curve_tube(
            "Iron rocking base",
            [(x, -0.48 + j * 0.96 / 48, 0.04 + 0.16 * ((j - 24) / 24) ** 2) for j in range(49)],
            0.018,
            m["iron"],
        )
        for y in [-0.23, 0.22]:
            cylinder_between("Chair leg", (x, y, 0.07), (x, y, 0.49), 0.017, m["iron"])
        curve_tube(
            "Curved iron chair arm",
            [
                (x, -0.28, 0.48),
                (x, -0.34, 0.62),
                (x, -0.30, 0.71),
                (x, 0.12, 0.70),
                (x, 0.30, 0.63),
            ],
            0.019,
            m["iron"],
        )
        curve_tube(
            "Iron chair back edge",
            [(x, 0.28, 0.45), (x, 0.31, 0.84), (x, 0.40, 1.16)],
            0.020,
            m["iron"],
        )
    parent = group("Woven patio rocking chair", set(bpy.data.objects) - before, position, angle)
    annotate(parent, "patio_chair", [10, 47])
    parent["fidelity"] = "Photo-informed approximate hand-built wicker chair."


def patio(m):
    # Door approach at x=2.94 remains clear; chairs surround the table farther out.
    for p, a in [
        ((1.36, 13.0, -0.45), math.pi / 2),
        ((4.51, 13.0, -0.45), -math.pi / 2),
        ((2.95, 14.42, -0.45), 0),
    ]:
        wicker_chair(m, p, a)
    cylinder_between(
        "Patio round table", (2.95, 13.30, -0.08), (2.95, 13.30, -0.03), 0.53, m["iron"], 96
    )
    for x, y in [(2.6, 13.0), (3.3, 13.0), (2.6, 13.6), (3.3, 13.6)]:
        cylinder_between("Patio table leg", (x, y, -0.44), (x, y, -0.06), 0.018, m["iron"])
    import_asset("potted_plant_04", (2.95, 13.3, -0.01), target_height=0.30)
    box("Outdoor dining table", (-1.30, 12.0, -0.36), (1.40, 0.82, 0.05), m["wood"])
    for x in [-1.87, -0.73]:
        for y in [11.69, 12.31]:
            cylinder_between("Outdoor table leg", (x, y, -1.11), (x, y, -0.37), 0.025, m["iron"])
    for y, a in [(11.33, math.pi), (12.69, 0)]:
        import_asset("dining_chair_02", (-1.3, y, -1.11), a, 0.96)
    for p, h in [
        ((0.59, 11.7, -0.45), 0.5),
        ((4.97, 14.7, -0.45), 0.68),
        ((0.08, 13.9, -1.11), 0.6),
    ]:
        import_asset("potted_plant_04", p, target_height=h)
