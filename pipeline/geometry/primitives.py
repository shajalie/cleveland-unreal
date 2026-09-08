"""Metric mesh primitives with useful UVs, continuous normals and real bevels."""

import math
import bpy
import bmesh
from mathutils import Vector


def annotate(obj, semantic, evidence=()):
    obj["semantic"] = semantic
    obj["reference_photos"] = ",".join(str(p) for p in evidence)
    return obj


def finish(obj, material, bevel=0):
    if obj.type == "MESH":
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
        metric_uvs(obj)
    if material:
        obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Physical edge radius", "BEVEL")
        modifier.width = bevel
        modifier.segments = 6
        modifier.limit_method = "ANGLE"
        modifier.harden_normals = True
        for face in obj.data.polygons:
            face.use_smooth = True
        normal = obj.modifiers.new("Area weighted normals", "WEIGHTED_NORMAL")
        normal.keep_sharp = True
    return obj


def metric_uvs(obj):
    """Face-aligned metric UVs; one repeat per meter before material scale."""
    uv = obj.data.uv_layers.get("MetricUV") or obj.data.uv_layers.new(name="MetricUV")
    for poly in obj.data.polygons:
        axis = max(range(3), key=lambda i: abs(poly.normal[i]))
        axes = [i for i in range(3) if i != axis]
        for li in poly.loop_indices:
            v = obj.data.vertices[obj.data.loops[li].vertex_index].co
            uv.data[li].uv = (v[axes[0]], v[axes[1]])


def box(name, center, size, material=None, bevel=0.003):
    vertices = [
        (x * size[0] / 2, y * size[1] / 2, z * size[2] / 2)
        for z in [-1, 1]
        for y in [-1, 1]
        for x in [-1, 1]
    ]
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = center
    return finish(obj, material, min(bevel, min(size) * 0.15))


def segment(name, a, b, width, height, z, material, bevel=0.003):
    start, end = Vector(a), Vector(b)
    center = (start + end) * 0.5
    obj = box(
        name,
        (center.x, center.y, z + height * 0.5),
        ((end - start).length, width, height),
        material,
        bevel,
    )
    obj.rotation_euler.z = math.atan2(end.y - start.y, end.x - start.x)
    return obj


def extrusion(name, outline, base, height, material):
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(outline, outline[1:] + outline[:1]))
    if area < 0:
        outline = list(reversed(outline))
    count = len(outline)
    vertices = [(x, y, z) for z in [base, base + height] for x, y in outline]
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(obj, material, 0.003)


def cylinder_between(name, a, b, radius, material, vertices=32):
    a, b = Vector(a), Vector(b)
    depth = (b - a).length
    points = [
        (
            radius * math.cos(i * 2 * math.pi / vertices),
            radius * math.sin(i * 2 * math.pi / vertices),
            z,
        )
        for z in [-depth / 2, depth / 2]
        for i in range(vertices)
    ]
    faces = [tuple(reversed(range(vertices))), tuple(range(vertices, 2 * vertices))]
    faces += [
        (i, (i + 1) % vertices, (i + 1) % vertices + vertices, i + vertices)
        for i in range(vertices)
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (a + b) * 0.5
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    for polygon in obj.data.polygons:
        polygon.use_smooth = len(polygon.vertices) == 4
    return finish(obj, material, 0.001)


def wall_with_openings(wall, base, height, material):
    a, b = Vector(wall["a"]), Vector(wall["b"])
    delta = b - a
    length = delta.length
    direction = delta.normalized()
    thickness = wall.get("thickness", 0.25 if wall["ext"] else 0.15)

    def point(t):
        return a + direction * t

    openings = []
    for hole in wall["holes"]:
        first = (Vector(hole["a"]) - a).dot(direction)
        last = (Vector(hole["b"]) - a).dot(direction)
        left, right = sorted((first, last))
        assert -0.02 <= left < right <= length + 0.02, (wall["id"], hole["id"], left, right, length)
        sill = hole.get("sill", 0 if hole.get("floorGlass") or not hole.get("window") else 0.82)
        head = hole.get("head", 2.3)
        openings.append((max(0, left), min(length, right), sill, head, hole))
    cursor = 0
    for left, right, sill, head, hole in sorted(openings, key=lambda h: h[0]):
        if left > cursor + 0.001:
            segment(
                wall["id"] + "_pier", point(cursor), point(left), thickness, height, base, material
            )
        if sill > 0:
            segment(
                wall["id"] + "_sill", point(left), point(right), thickness, sill, base, material
            )
        if not hole.get("arch"):
            segment(
                wall["id"] + "_lintel",
                point(left),
                point(right),
                thickness,
                height - head,
                base + head,
                material,
            )
        else:
            radius = (right - left) / 2
            spring = head - radius
            # 96 segments in the arch: no visible straight-sided arch silhouette.
            normal = Vector((-direction.y, direction.x))
            vertices = []
            steps = 96
            for side in [-1, 1]:
                for index in range(steps + 1):
                    t = left + (right - left) * index / steps
                    z = spring + math.sqrt(max(0, radius * radius - (t - (left + right) / 2) ** 2))
                    p = point(t) + normal * thickness * 0.5 * side
                    vertices += [(p.x, p.y, base + z), (p.x, p.y, base + height)]
            offset = (steps + 1) * 2
            faces = []
            for i in range(steps):
                j = i * 2
                faces += [
                    (j, j + 2, j + 3, j + 1),
                    (offset + j + 1, offset + j + 3, offset + j + 2, offset + j),
                    (j, offset + j, offset + j + 2, j + 2),
                    (j + 1, j + 3, offset + j + 3, offset + j + 1),
                ]
            faces += [
                (0, 1, offset + 1, offset),
                (2 * steps, offset + 2 * steps, offset + 2 * steps + 1, 2 * steps + 1),
            ]
            mesh = bpy.data.meshes.new(hole["id"] + "_arch")
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            obj = bpy.data.objects.new(hole["id"] + "_arch", mesh)
            bpy.context.collection.objects.link(obj)
            finish(obj, material, 0.004)
        cursor = max(cursor, right)
    if cursor < length:
        segment(
            wall["id"] + "_pier", point(cursor), point(length), thickness, height, base, material
        )
    return openings


def stair_flight(spec, material):
    direction = Vector(spec["direction"]).normalized()
    start = Vector(spec["start"])
    rise = (spec["high"] - spec["low"]) / spec["risers"]
    assert 0.12 <= rise <= 0.20, spec["id"]
    meshes = []
    for index in range(spec["risers"]):
        center = start + direction * (index + 0.5) * spec["tread"]
        top = spec["low"] + (index + 1) * rise
        obj = box(
            spec["id"] + f"_tread_{index + 1:02d}",
            (center.x, center.y, (top + spec["low"]) / 2),
            (spec["tread"], spec["width"], top - spec["low"]),
            material,
            0.008,
        )
        obj.rotation_euler.z = math.atan2(direction.y, direction.x)
        annotate(obj, "stair_tread", spec["evidence"])
        obj["step_top_m"] = top
        meshes.append(obj)
    return meshes
