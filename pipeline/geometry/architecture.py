"""Openings, floor cuts, joinery and circulation built from spatial constraints."""

import math
import bpy
from mathutils import Vector, Matrix
from .primitives import (
    box,
    segment,
    extrusion,
    cylinder_between,
    wall_with_openings,
    stair_flight,
    annotate,
)


def difference(obj, name, center, size):
    cutter = box(name, center, size, None, 0)
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new(name, "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def curve_tube(name, points, radius, material):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 12
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    curve.materials.append(material)
    return obj


def portal(wall, hole, base, m):
    if not wall["ext"] and not hole.get("floorGlass"):
        return
    if hole["id"] == "front_door":
        front_door(hole, base, m)
        return
    a, b = Vector(hole["a"]), Vector(hole["b"])
    direction = (b - a).normalized()
    length = (b - a).length
    normal = Vector((-direction.y, direction.x))
    sill = hole.get("sill", 0 if hole.get("floorGlass") else 0.82)
    head = hole.get("head", 2.3)
    arch = hole.get("arch", False)
    radius = length / 2
    spring = head - radius
    frame = m["iron"] if hole.get("operable") else m["wood"]
    if hole.get("frame_finish") == "white":
        frame = m["ivory"]

    def pt(t, z, offset=0):
        p = a + direction * t + normal * offset
        return (p.x, p.y, base + z)

    for t in [0, length]:
        cylinder_between(
            hole["id"] + "_jamb", pt(t, sill), pt(t, spring if arch else head), 0.038, frame
        )
    if arch:
        points = [
            pt(
                length / 2 + radius * math.cos(math.pi * i / 96),
                spring + radius * math.sin(math.pi * i / 96),
            )
            for i in range(97)
        ]
        curve_tube(hole["id"] + "_curved_frame", points, 0.043, frame)
    else:
        cylinder_between(hole["id"] + "_head", pt(0, head), pt(length, head), 0.037, frame)
    cylinder_between(hole["id"] + "_threshold", pt(0, sill), pt(length, sill), 0.035, frame)
    # Separate hinged leaves, each with real glass thickness and metal mullions.
    leaves = hole.get("leaf_count", 2 if length > 1.3 else 1)
    for leaf in range(leaves):
        left = length * leaf / leaves + 0.045
        right = length * (leaf + 1) / leaves - 0.045
        before = set(bpy.data.objects)

        def top(t):
            return (
                spring + math.sqrt(max(0, radius * radius - (t - radius) ** 2)) - 0.045
                if arch
                else head - 0.045
            )

        bottom = sill + 0.04
        # Glazing subdivided at the curve, with a closed solid rather than a rectangle across the arch.
        verts = []
        count = 48
        for offset in [-0.002, 0.002]:
            verts.extend([pt(left, bottom, offset), pt(right, bottom, offset)])
            verts.extend(
                pt(
                    right - (right - left) * i / count,
                    top(right - (right - left) * i / count),
                    offset,
                )
                for i in range(count + 1)
            )
        n = count + 3
        faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
        mesh = bpy.data.meshes.new(hole["id"] + "_glass")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(hole["id"] + f"_glass_{leaf}", mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(m["glass"])
        for t in [left, right]:
            cylinder_between(hole["id"] + "_stile", pt(t, bottom), pt(t, top(t)), 0.026, frame)
        for z in [bottom] + [sill + (head - sill) * v for v in [0.25, 0.5, 0.75]]:
            if z < min(top(left), top(right)):
                cylinder_between(hole["id"] + "_mullion", pt(left, z), pt(right, z), 0.014, frame)
        if hole.get("operable"):
            p0, p1 = pt(left, 0), pt(right, 0)
            segment(hole["id"] + "_lower_panel", p0[:2], p1[:2], 0.042, 0.19, base + 0.035, frame)
        elif right - left > 0.40:
            t = (left + right) / 2
            cylinder_between(
                hole["id"] + "_vertical_muntin", pt(t, bottom), pt(t, top(t)), 0.011, frame
            )
        if hole.get("operable"):
            hinge = pt(left if leaf == 0 else right, 0)
            handle = pt(right - 0.09 if leaf == 0 else left + 0.09, 1.02, 0.05)
            cylinder_between(
                hole["id"] + "_handle",
                handle,
                (handle[0], handle[1], handle[2] + 0.12),
                0.012,
                m["brass"],
            )
            empty = bpy.data.objects.new(hole["id"] + f"_hinge_{leaf}", None)
            bpy.context.collection.objects.link(empty)
            empty.location = hinge
            children = list(set(bpy.data.objects) - before - {empty})
            for child in children:
                child.parent = empty
                child.matrix_parent_inverse = Matrix.Translation(-Vector(hinge))
            empty["interaction"] = "hinged_door"
            empty["closed_angle"] = 0
            empty["open_angle"] = (-1 if leaf == 0 else 1) * 95
            empty["portal_id"] = hole["id"]
            annotate(empty, "operable_door", hole.get("evidence", []))


def front_door(hole, base, m):
    x = (hole["a"][0] + hole["b"][0]) / 2
    y = hole["a"][1]
    width = abs(hole["b"][0] - hole["a"][0])
    for xx in [x - width / 2, x - 0.46, x + 0.46, x + width / 2]:
        box("Entry jamb", (xx, y, base + 1.12), (0.06, 0.15, 2.24), m["wood"], 0.008)
    for zz in [2.24, 2.54]:
        box("Entry transom frame", (x, y, base + zz), (width + 0.08, 0.15, 0.07), m["wood"], 0.008)
    box("Entry transom glass", (x, y, base + 2.39), (width - 0.06, 0.006, 0.22), m["glass"], 0)
    for xx in [x - 0.59, x + 0.59]:
        box("Entry fixed sidelight", (xx, y, base + 1.13), (0.18, 0.006, 2.10), m["glass"], 0)
    before = set(bpy.data.objects)
    box("Paneled front door leaf", (x, y, base + 1.10), (0.86, 0.05, 2.18), m["wood"], 0.007)
    for xx in [x - 0.215, x + 0.215]:
        for zz, height in [(0.38, 0.42), (0.93, 0.35), (1.40, 0.31), (1.84, 0.31)]:
            for side in [-1, 1]:
                box(
                    "Raised entry panel",
                    (xx, y + side * 0.033, base + zz),
                    (0.33, 0.025, height),
                    m["wood"],
                    0.012,
                )
    cylinder_between(
        "Entry brass lever",
        (x + 0.32, y - 0.072, base + 1.02),
        (x + 0.22, y - 0.072, base + 1.02),
        0.013,
        m["brass"],
    )
    children = set(bpy.data.objects) - before
    hinge = Vector((x - 0.43, y, base))
    root = bpy.data.objects.new("front_door_hinge", None)
    bpy.context.collection.objects.link(root)
    root.location = hinge
    for child in children:
        child.parent = root
        child.matrix_parent_inverse = Matrix.Translation(-hinge)
    root["interaction"] = "hinged_door"
    root["portal_id"] = "front_door"
    root["closed_angle"] = 0
    root["open_angle"] = 95
    annotate(root, "operable_door", [3, 4, 5])


def railing(name, a, b, z, m, height=0.95):
    a, b = Vector(a), Vector(b)
    length = (b - a).length
    cylinder_between(
        name + "_handrail", (a.x, a.y, z + height), (b.x, b.y, z + height), 0.021, m["iron"]
    )
    cylinder_between(name + "_lower", (a.x, a.y, z + 0.11), (b.x, b.y, z + 0.11), 0.012, m["iron"])
    for i in range(math.ceil(length / 0.115) + 1):
        p = a + (b - a) * i / math.ceil(length / 0.115)
        cylinder_between(
            name + "_baluster", (p.x, p.y, z + 0.08), (p.x, p.y, z + height), 0.007, m["iron"], 16
        )


def build_house(model, m):
    for floor in model["floors"]:
        z = floor["base"]
        ceiling = floor["ceiling"]
        fid = floor["id"]
        slab = extrusion(fid + "_floor", floor["outline"], z - 0.20, 0.20, m["floor"])
        slab.data.materials.append(m["stucco"])
        for face in slab.data.polygons:
            if face.normal.z < 0.5:
                face.material_index = 1
        cap = extrusion(fid + "_ceiling", floor["outline"], z + ceiling, 0.10, m["plaster"])
        if fid == "upper":
            difference(slab, "Stair opening", (0.13, 4.53, z), (1.24, 3.46, 0.8))
        if fid == "main":
            difference(cap, "Stair headroom opening", (0.13, 4.53, z + ceiling), (1.24, 3.46, 0.8))
        if fid == "main":
            for room in floor["rooms"]:
                if room["name"] in ["Foyer", "Stairs / hall"]:
                    extrusion(
                        room["name"] + " limestone floor", room["poly"], 0.001, 0.009, m["concrete"]
                    )
        for wall in floor["walls"]:
            before = set(bpy.data.objects)
            wall_with_openings(wall, z, ceiling, m["stucco"] if wall["ext"] else m["plaster"])
            for obj in set(bpy.data.objects) - before:
                annotate(obj, "structural_wall", [55])
                if wall["ext"] and obj.type == "MESH":
                    obj.data.materials.append(m["plaster"])
                    direction = (Vector(wall["b"]) - Vector(wall["a"])).normalized()
                    inward = Vector((-direction.y, direction.x, 0))
                    for face in obj.data.polygons:
                        normal = obj.rotation_euler.to_matrix() @ face.normal
                        if normal.dot(inward) > 0.5:
                            face.material_index = len(obj.data.materials) - 1
            for hole in wall["holes"]:
                portal(wall, hole, z, m)
        # Continuous perimeter trim has corresponding cuts at floor-reaching doors.
        for wall in floor["walls"]:
            a, b = Vector(wall["a"]), Vector(wall["b"])
            d = (b - a).normalized()
            length = (b - a).length
            cuts = []
            for h in wall["holes"]:
                if h.get("sill", 0 if not h.get("window") or h.get("floorGlass") else 0.82) < 0.12:
                    cuts.append(sorted(((Vector(h["a"]) - a).dot(d), (Vector(h["b"]) - a).dot(d))))
            cursor = 0
            for lo, hi in sorted(cuts) + [[length, length]]:
                offset = Vector((-d.y, d.x)) * 0.146 if wall["ext"] else Vector((0, 0))
                if lo > cursor + 0.02:
                    segment(
                        fid + "_baseboard",
                        a + d * cursor + offset,
                        a + d * lo + offset,
                        0.036 if wall["ext"] else 0.19,
                        0.14,
                        z,
                        m["wood"],
                        0.008,
                    )
                cursor = max(cursor, hi)
    # Foundations close the exposed void below the main floor without filling the basement rooms.
    for wall in model["floors"][0]["walls"]:
        if not wall["ext"]:
            continue
        spec = {**wall, "id": wall["id"] + "_foundation", "holes": []}
        if wall["id"] == "main_wall_06":
            spec["holes"] = [
                {
                    "id": "foundation_lower_exit",
                    "a": [-4.95, 11.2776],
                    "b": [-3.9, 11.2776],
                    "sill": 0,
                    "head": 2.1,
                    "window": False,
                }
            ]
        wall_with_openings(spec, -2.72, 2.72, m["stucco"])
    # Living room exposed ceiling timbers, visible grain and softened edges.
    for i in range(13):
        box(
            "Living oak ceiling beam",
            (2.80, 0.25 + i * 0.58, 2.82),
            (3.98, 0.12, 0.15),
            m["wood"],
            0.008,
        )
    for i in range(6):
        box(
            "Study oak ceiling beam",
            (2.94, 7.89 + i * 0.58, 2.82),
            (3.70, 0.12, 0.15),
            m["wood"],
            0.008,
        )
    main = next(s for s in model["stairs"] if s["id"] == "main_stair")
    stair_flight(main, m["wood"])
    rise = main["high"] / main["risers"]
    for i in range(main["risers"]):
        y = main["start"][1] + (i + 0.5) * main["tread"]
        z = (i + 1) * rise
        box(
            "Rounded oak stair nosing",
            (0.13, y - main["tread"] / 2 - 0.012, z - 0.014),
            (1.13, 0.048, 0.03),
            m["wood"],
            0.014,
        )
        cylinder_between(
            "Stair iron baluster", (-0.44, y, z), (-0.44, y, z + 0.91), 0.009, m["iron"], 24
        )
    cylinder_between(
        "Continuous stair rail", (-0.44, 1.40, 0.96), (-0.44, 6.26, 4.01), 0.032, m["wood"]
    )
    railing("Landing guard", (-0.47, 2.80), (-0.47, 6.26), 3.12, m)
    # Porch columns and overhead slab preserve the carport lane to the right.
    box("Porch roof", (1.0, -1.6, 2.98), (13.7, 3.55, 0.23), m["stucco"])
    for x in [-5.62, -1.42, 1.07, 7.56]:
        box("Stucco porch pier", (x, -3.02, 1.40), (0.42, 0.42, 2.98), m["stucco"], 0.013)
        box("Pier capital", (x, -3.02, 2.81), (0.53, 0.53, 0.15), m["stucco"])


def build_terraces(model, m):
    for s in model["surfaces"]:
        if s["id"] == "front_grade":
            continue
        material = m["concrete"] if s["id"] in ["pool_deck", "basement_areaway"] else m["tile"]
        slab = extrusion(s["id"], s["poly"], s["z"] - 0.16, 0.16, material)
        if s["id"] == "pool_deck":
            difference(slab, "Pool excavation", (-4.8, 18.5, -1.7), (6.096, 3.048, 1))
    for s in model["stairs"]:
        if s["id"] == "main_stair":
            continue
        stair_flight(
            s,
            m["brick"]
            if s["id"] == "study_steps"
            else m["tile"]
            if s["id"] != "front_steps"
            else m["concrete"],
        )
    # Support walls stop at actual stair openings, rather than blocking circulation.
    for name, a, b, low, high in [
        ("Dining deck face", (-1.04, 14.1), (0.3, 14.1), -1.62, -1.11),
        ("Dining deck left", (-2.75, 14.1), (-2.28, 14.1), -1.62, -1.11),
        ("Sitting retaining", (0.3, 13.13), (0.3, 15.1), -1.62, -0.45),
        ("Sitting lower return", (0.3, 15.1), (5.5, 15.1), -1.62, -0.45),
        ("Areaway east", (-2.75, 11.28), (-2.75, 14.1), -2.72, -1.11),
    ]:
        segment(name, a, b, 0.22, high - low, low, m["stucco"])
    railing("Dining rear guard", (-1.02, 14.1), (0.3, 14.1), -1.11, m)
    railing("Dining areaway guard", (-2.75, 11.4), (-2.75, 13.98), -1.11, m)
    railing("Sitting side guard", (0.30, 13.16), (0.30, 15.1), -0.45, m)
    railing("Sitting garden guard", (0.30, 15.1), (5.5, 15.1), -0.45, m)
    # Vehicle approach remains below the carport platform; the carport roof spans it.
    box("Vehicle lane", (6.15, -8.5, -0.68), (2.7, 17, 0.12), m["concrete"])
    # Cut the porch floor out of the lane: roof and piers remain above a drive-through opening.
    difference(bpy.data.objects["porch"], "Carport clear lane", (6.16, -1.6, -0.09), (2.80, 3.4, 1))
    box("Pedestrian approach", (-0.20, -8.0, -0.65), (1.90, 8.0, 0.10), m["concrete"])


def roof(m):
    from . import roof_tiles
    from .primitives import finish

    outer = [(-5.74, -0.24, 6.04), (5.01, -0.24, 6.04), (5.01, 7.85, 6.04), (-5.74, 7.85, 6.04)]
    inner = [(-2.68, 2.10, 7.30), (1.94, 2.10, 7.30), (1.94, 5.43, 7.30), (-2.68, 5.43, 7.30)]
    vertices = outer + inner
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]

    def mesh(name, vertices, faces, material):
        data = bpy.data.meshes.new(name)
        data.from_pydata(vertices, [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        return finish(obj, material)

    top = mesh("Hip roof", vertices, faces, m["tile"])
    top["height_status"] = "Roof pitch inferred from aerial and front photograph"
    box("Flat central roof", (-0.37, 3.765, 7.25), (4.62, 3.33, 0.10), m["ivory"])
    for a, b in zip(outer, outer[1:] + outer[:1]):
        segment("White eaves fascia", a[:2], b[:2], 0.22, 0.20, 5.91, m["stucco"])
    for x0, x1 in [(-5.5, -2.75), (0.8, 4.7624)]:
        box(
            "Flat rear wing roof",
            ((x0 + x1) / 2, 9.45, 5.97),
            (x1 - x0 + 0.30, 3.92, 0.16),
            m["ivory"],
        )
    roof_tiles.build(mesh)
    box("Chimney", (4.37, 4.65, 6.70), (0.72, 0.82, 1.44), m["stucco"], 0.015)
    box("Chimney cap", (4.37, 4.65, 7.46), (0.84, 0.94, 0.12), m["concrete"])
