"""Author a separate, reproducible landscape layer and shared plant prototypes."""

import json
import math
import random
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from geometry.primitives import box, extrusion, finish, segment
from geometry.materials import plain, scanned
from landscape.layout import (
    HOUSE,
    AREAWAY,
    POOL,
    DRIVE,
    PATH,
    REAR_BEDS,
    grade,
    lawn,
    planting,
    bed_height,
    inside,
    WALK_ROUTES,
    excluded,
)

RNG = random.Random(301403)
INSTANCES = {}
PROTOTYPES = {}


def texture_material(name, asset, size, folder="landscape"):
    mat = plain(name, (0.3, 0.3, 0.3), 0.8)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    p = nodes.get("Principled BSDF")
    uv = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / size,) * 3
    links.new(uv.outputs["UV"], mapping.inputs["Vector"])
    for suffix, socket in [("diff", "Base Color"), ("nor_gl", "Normal"), ("rough", "Roughness")]:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(
            str(ROOT / "reference/materials" / folder / f"{asset}_{suffix}.jpg"),
            check_existing=True,
        )
        links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        if suffix != "diff":
            tex.image.colorspace_settings.name = "Non-Color"
        if socket == "Normal":
            normal = nodes.new("ShaderNodeNormalMap")
            normal.inputs["Strength"].default_value = 0.85
            links.new(tex.outputs["Color"], normal.inputs["Color"])
            links.new(normal.outputs["Normal"], p.inputs[socket])
        else:
            links.new(tex.outputs["Color"], p.inputs[socket])
    return mat


def mesh_object(name, vertices, faces, material, metric=True):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if metric:
        finish(obj, material)
    else:
        mesh.materials.append(material)
    return obj


def terrain(materials):
    # One closed manifold volume; explicit excavations preserve the basement and pool.
    xs = [-18 + i * 0.5 for i in range(73)]
    ys = [-22 + i * 0.5 for i in range(105)]
    nx, ny = len(xs), len(ys)
    vertices = [(x, y, grade(x, y)) for y in ys for x in xs]
    faces = [
        (j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i)
        for j in range(ny - 1)
        for i in range(nx - 1)
    ]
    boundary = list(range(nx)) + [j * nx + nx - 1 for j in range(1, ny)]
    boundary += list(range(nx * ny - 2, nx * (ny - 1) - 1, -1)) + [
        j * nx for j in range(ny - 2, 0, -1)
    ]
    bottom = len(vertices)
    vertices += [(vertices[i][0], vertices[i][1], -4.5) for i in boundary]
    faces += [
        (a, b, bottom + (k + 1) % len(boundary), bottom + k)
        for k, (a, b) in enumerate(zip(boundary, boundary[1:] + boundary[:1]))
    ]
    faces.append(tuple(reversed(range(bottom, len(vertices)))))
    obj = mesh_object("LV3_ContinuousGround", vertices, faces, materials["soil"])
    obj.data.materials.append(materials["lawn"])
    for polygon in obj.data.polygons:
        if polygon.normal.z > 0.8 and lawn(polygon.center.x, polygon.center.y):
            polygon.material_index = 1
    for index, ring in enumerate((HOUSE, AREAWAY, POOL)):
        cut = extrusion("Excavation", ring, -5, 12, None)
        cut.modifiers.clear()
        mod = obj.modifiers.new(f"Preserved excavation {index}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        mod.solver = "EXACT"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cut, do_unlink=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    open_edges = sum(not e.is_manifold for e in bm.edges)
    bm.free()
    if open_edges:
        raise RuntimeError(f"Ground has {open_edges} non-manifold edges")
    return obj


def landscaping_surfaces(m):
    terrain(m)
    drive = extrusion("LV3_CurvedConcreteDrive", DRIVE, -0.76, 0.18, m["concrete"])
    drive["reference_photos"] = "00,01,02,03"
    for y in [-14, -11, -8, -5, -2.6]:
        # Thin recessed-looking sealant joints, below a walking step threshold.
        left, right = (
            (5.37, 9.02)
            if y < -10
            else (5.15, 8.7)
            if y < -6
            else (5.0, 8.3)
            if y < -3
            else (4.79, 7.53)
        )
        segment(
            "LV3_DriveExpansionJoint", (left, y), (right, y), 0.009, 0.003, -0.578, m["joint"], 0
        )
    # A curved stone approach connects the driveway to the existing front steps.
    for index, (a, b) in enumerate(zip(PATH, PATH[1:])):
        segment("LV3_StoneApproach", a, b, 1.25, 0.12, -0.71, m["stone"], 0.006)
        if index:
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=40, radius=0.625, depth=0.12, location=(*a, -0.65)
            )
            obj = bpy.context.object
            obj.name = "LV3_ApproachCurve"
            finish(obj, m["stone"], 0.005)
    for bed in REAR_BEDS:
        ring = bed["poly"]
        obj = extrusion("LV3_RaisedBed_" + bed["id"], ring, -1.70, bed["z"] + 1.70, m["stucco"])
        obj["reference_photos"] = "45,47,51,52"
        # Soil inside the retaining perimeter; hard cap is narrow, not a blank slab.
        center = Vector((sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)))
        inner = [tuple(Vector(p) + (center - Vector(p)).normalized() * 0.09) for p in ring]
        extrusion("LV3_BedSoil_" + bed["id"], inner, bed["z"] - 0.04, 0.052, m["soil"])
        for a, b in zip(ring, ring[1:] + ring[:1]):
            segment("LV3_RetainingCap", a, b, 0.10, 0.045, bed["z"] - 0.022, m["stucco"], 0.01)


def register(obj, kind, cull=3500):
    source_name = obj.name
    # Unreal interprets a trailing _number as its internal FName suffix.
    # End with letters so names survive the Blender/USD/Unreal round trip.
    obj.name = f"LV3_PROTO_{len(PROTOTYPES):03d}_{kind}Mesh"
    obj.data.name = obj.name
    obj["landscape_prototype"] = True
    PROTOTYPES[obj.name] = {"kind": kind, "cullCm": cull, "sourceName": source_name}
    INSTANCES[obj.name] = []
    return obj.name


def instance(key, x, y, z, scale=1, yaw=None):
    record = {
        "position": [x, y, z],
        "scale": [scale] * 3 if isinstance(scale, (int, float)) else list(scale),
        "yaw": RNG.random() * 360 if yaw is None else yaw,
    }
    if PROTOTYPES[key]["kind"] == "grass":
        dx = (grade(x + 0.02, y) - grade(x - 0.02, y)) / 0.04
        dy = (grade(x, y + 0.02) - grade(x, y - 0.02)) / 0.04
        record["normal"] = list(Vector((-dx, -dy, 1)).normalized())
    INSTANCES[key].append(record)


def grass_prototype(index, material):
    verts, faces, colors = [], [], []
    # 256 individual tapered, bent blades per half-metre patch. No alpha cards.
    for _ in range(256):
        x, y = RNG.uniform(-0.25, 0.25), RNG.uniform(-0.25, 0.25)
        angle = RNG.random() * math.tau
        h, w, bend = (
            RNG.uniform(0.035, 0.085),
            RNG.uniform(0.0018, 0.0038),
            RNG.uniform(0.006, 0.028),
        )
        side = Vector((math.cos(angle), math.sin(angle), 0))
        forward = Vector((-side.y, side.x, 0))
        start = len(verts)
        for t, width in [(0, w), (0.52, w * 0.73), (1, 0)]:
            center = Vector((x, y, h * t)) + forward * (bend * t * t)
            for s in (-1, 1):
                verts.append(tuple(center + side * width * s * 0.5))
                colors.append((0.7 + RNG.random() * 0.3, t, t, 1))
        faces.extend([(start, start + 1, start + 3, start + 2), (start + 2, start + 3, start + 4)])
    obj = mesh_object(f"MownGrass{index}", verts, faces, material, False)
    attribute = obj.data.color_attributes.new(
        name="BladeHeight", type="FLOAT_COLOR", domain="POINT"
    )
    for item, value in zip(attribute.data, colors):
        item.color = value
    for p in obj.data.polygons:
        p.use_smooth = True
    return register(obj, "grass", 2000)


def imported_prototypes(asset, target_height, kind):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(
        filepath=str(ROOT / ".local/model-assets" / asset / f"{asset}_1k.gltf")
    )
    objects = set(bpy.data.objects) - before
    alpha = list((ROOT / ".local/model-assets" / asset / "textures").glob(f"{asset}_*alpha.png"))
    result = []
    for obj in sorted((o for o in objects if o.type == "MESH"), key=lambda o: o.name):
        # Source assets may contain a row of variants in one mesh. Keep each
        # separated row group as its own compact, normalized prototype.
        obj.data.transform(obj.matrix_world)
        obj.matrix_world.identity()
        xx = sorted(set(round(v.co.x, 5) for v in obj.data.vertices))
        span = xx[-1] - xx[0]
        gaps = sorted(
            [(b - a, (a + b) / 2) for a, b in zip(xx, xx[1:]) if b - a > max(0.035, span * 0.018)],
            reverse=True,
        )
        splits = (
            sorted(v for _, v in gaps[:3])
            if asset in ("shrub_04", "flower_gazania", "fern_02")
            else []
        )
        ranges = [-math.inf] + splits + [math.inf]
        for j, (lo, hi) in enumerate(zip(ranges, ranges[1:])):
            part = obj.copy()
            part.data = obj.data.copy()
            bpy.context.collection.objects.link(part)
            bm = bmesh.new()
            bm.from_mesh(part.data)
            doomed = [v for v in bm.verts if not lo <= v.co.x < hi]
            bmesh.ops.delete(bm, geom=doomed, context="VERTS")
            bm.to_mesh(part.data)
            bm.free()
            if not part.data.polygons:
                bpy.data.objects.remove(part, do_unlink=True)
                continue
            vs = part.data.vertices
            low = Vector([min(v.co[i] for v in vs) for i in range(3)])
            high = Vector([max(v.co[i] for v in vs) for i in range(3)])
            anchor = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
            factor = target_height / max(0.01, high.z - low.z)
            for v in vs:
                v.co = (v.co - anchor) * factor
            part.name = f"{asset}_{j}"
            for mat in part.data.materials:
                if not mat or not mat.use_nodes:
                    continue
                p = mat.node_tree.nodes.get("Principled BSDF")
                if alpha and p:
                    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
                    tex.image = bpy.data.images.load(str(alpha[0]), check_existing=True)
                    tex.image.colorspace_settings.name = "Non-Color"
                    mat.node_tree.links.new(tex.outputs["Color"], p.inputs["Alpha"])
                    mat["landscape_alpha"] = str(alpha[0].relative_to(ROOT)).replace("\\", "/")
                mat["landscape_kind"] = kind
            result.append(register(part, kind, 4500 if kind == "shrub" else 2800))
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    if not result:
        raise RuntimeError("No plant prototype imported: " + asset)
    return result


def flower_cloud(name, color):
    material = plain("LV3_Flower_" + name, color, 0.65)
    verts, faces = [], []
    # Individual five-petal azalea-like corollas, concentrated on an irregular crown.
    for _ in range(380):
        theta = RNG.random() * math.tau
        r = math.sqrt(RNG.random()) * 0.61
        x, y = math.cos(theta) * r, math.sin(theta) * r
        z = 0.57 + 0.22 * math.sqrt(max(0, 1 - (r / 0.62) ** 2)) + RNG.uniform(-0.055, 0.055)
        for petal in range(5):
            angle = theta + petal * math.tau / 5
            middle = Vector((x + math.cos(angle) * 0.016, y + math.sin(angle) * 0.016, z + 0.01))
            base = len(verts)
            verts.append((x, y, z))
            for k in range(5):
                a = angle + (k - 2) * 0.4
                verts.append(
                    tuple(
                        middle
                        + Vector(
                            (math.cos(a) * 0.018, math.sin(a) * 0.018, 0.005 * math.sin(k * 0.8))
                        )
                    )
                )
            faces.extend([(base, base + k + 1, base + k + 2) for k in range(4)])
    return register(
        mesh_object("AzaleaFlowers_" + name, verts, faces, material, False), "flowers", 2800
    )


def plant_layout(m):
    grasses = [grass_prototype(i, m["blade"]) for i in range(4)]
    shrubs = imported_prototypes("shrub_04", 0.75, "shrub")
    ferns = imported_prototypes("fern_02", 0.55, "groundcover")
    cover = imported_prototypes("periwinkle_plant", 0.17, "groundcover")
    bermuda = imported_prototypes("grass_bermuda_01", 0.16, "groundcover")
    flowers = imported_prototypes("flower_gazania", 0.32, "flowers")
    pots = imported_prototypes("planter_pot_clay", 0.4, "pot")
    crowns = [
        flower_cloud("Pink", (0.6, 0.028, 0.17)),
        flower_cloud("White", (0.78, 0.76, 0.68)),
        flower_cloud("Coral", (0.50, 0.025, 0.012)),
    ]
    # Half-metre tiles are randomly rotated, scaled and dithered inside the lawn.
    for ix in range(43):
        for iy in range(74):
            x = -10 + ix * 0.46 + RNG.uniform(-0.025, 0.025)
            y = -14 + iy * 0.49 + RNG.uniform(-0.025, 0.025)
            if lawn(x, y, 0.21):
                instance(
                    RNG.choice(grasses), x, y, grade(x, y) + 0.015, (1, 1, RNG.uniform(0.75, 1.2))
                )
    # Dense, layered side/rear planting; real stem/leaf scans replace polygon blobs.
    for _ in range(1250):
        x, y = RNG.uniform(-10.2, 10.1), RNG.uniform(-10, 22)
        if planting(x, y):
            instance(RNG.choice(shrubs), x, y, bed_height(x, y) + 0.02, RNG.uniform(0.8, 1.6))
    for _ in range(2600):
        x, y = RNG.uniform(-10.2, 10.1), RNG.uniform(-10, 22)
        if planting(x, y):
            instance(
                RNG.choice(cover if RNG.random() < 0.72 else ferns),
                x,
                y,
                bed_height(x, y) + 0.015,
                RNG.uniform(0.75, 1.45),
            )
    # Front flowering masses frame, and never close, the entry path.
    for index, (x, y) in enumerate(
        [
            (-5.25, -4.4),
            (-4.2, -4.55),
            (-3.1, -4.65),
            (-1.95, -4.5),
            (1.25, -4.3),
            (2.25, -4.55),
            (3.2, -4.85),
        ]
    ):
        for j in range(8):
            a = j * math.tau / 8
            instance(
                RNG.choice(shrubs),
                x + math.cos(a) * 0.30,
                y + math.sin(a) * 0.30,
                -0.6,
                RNG.uniform(0.8, 1.0),
            )
        instance(crowns[index % 3], x, y, -0.6, 1, yaw=RNG.random() * 360)
    # Photo 49: pots and flowers along the fence. Keep a clear pool circulation lane.
    for x, y in [(x, 21.85) for x in [-7.3, -5.6, -3.6, -1.6, 0.8, 3.1, 5.2]] + [
        (4.9, 12.0),
        (0.65, 14.55),
        (-2.45, 13.55),
    ]:
        z = grade(x, y) if y > 21 else -0.45 if x > 1 else -1.11
        if y > 21:
            z = -1.62
        instance(pots[0], x, y, z, RNG.uniform(0.8, 1.2))
        for _ in range(5):
            instance(
                RNG.choice(flowers),
                x + RNG.uniform(-0.1, 0.1),
                y + RNG.uniform(-0.1, 0.1),
                z + 0.32,
                RNG.uniform(0.8, 1.2),
            )
    for _ in range(180):
        x, y = RNG.uniform(5.8, 9.3), RNG.uniform(11, 21.7)
        if lawn(x, y) and not lawn(x, y, 0.45):
            instance(bermuda[0], x, y, grade(x, y), 0.65)
    # The photo shows a planted rear fence line beyond the deck, not bare ground.
    for _ in range(100):
        x, y = RNG.uniform(-8.8, 8.8), RNG.uniform(22.35, 23.35)
        instance(RNG.choice(shrubs), x, y, grade(x, y), RNG.uniform(1.0, 1.5))
        instance(RNG.choice(cover), x + 0.15, y - 0.15, grade(x, y), RNG.uniform(0.9, 1.3))


def material_manifest():
    result = []
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        result.append(
            {
                "name": mat.name,
                "kind": mat.get("landscape_kind", ""),
                "alpha": mat.get("landscape_alpha"),
                "images": [
                    {
                        "path": str(
                            Path(bpy.path.abspath(n.image.filepath)).resolve().relative_to(ROOT)
                        ).replace("\\", "/"),
                        "name": n.image.name,
                    }
                    for n in mat.node_tree.nodes
                    if n.type == "TEX_IMAGE" and n.image
                ],
            }
        )
    return result


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m = {
        "soil": scanned("LV3_MulchAndSoil", "rocky_terrain_02", 2),
        "lawn": texture_material("LV3_LivingLawn", "Grass004", 1.4),
        "concrete": scanned("LV3_WornConcrete", "concrete_floor_worn_001", 2, True),
        "aggregate": texture_material("LV3_ExposedAggregate", "pebble_embedded_pavement", 1.4),
        "stone": texture_material("LV3_SlateApproach", "slate_floor_02", 1.2),
        "stucco": scanned("LV3_GardenStucco", "white_stucco", 2, True),
        "joint": plain("LV3_RecessedJoint", (0.06, 0.055, 0.045), 0.94),
        "blade": plain("LV3_GrassBlade", (0.045, 0.115, 0.016), 0.75),
    }
    landscaping_surfaces(m)
    # This material-only swatch supplies the pool-deck override during native import.
    swatch = box("LV3_AggregateSwatch", (0, 0, -20), (0.01, 0.01, 0.01), m["aggregate"], 0)
    swatch["material_swatch"] = True
    plant_layout(m)
    transfer = ROOT / "SourceAssets/Landscape-v3"
    transfer.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": 3,
        "seed": 301403,
        "prototypes": PROTOTYPES,
        "instances": INSTANCES,
        "materials": material_manifest(),
        "walkRoutes": WALK_ROUTES,
        "referencePhotos": [0, 1, 2, 3, 45, 47, 49, 51, 52],
        "aerial": "DC OCTO March 27, 2025 orthophoto",
        "limits": [
            "Plant types and unmeasured grades are representative, not a survey.",
            "Flowers/foliage retain the listing-photo appearance across study dates.",
        ],
    }
    (transfer / "landscape.json").write_text(json.dumps(manifest, indent=2))
    samples = []
    for ix in range(37):
        for iy in range(69):
            x, y = -9 + ix * 0.5, -13 + iy * 0.5
            if not excluded(x, y, 0.5) and (lawn(x, y, 0.1) or inside(x, y, DRIVE)):
                samples.append([x, y, -0.58 if inside(x, y, DRIVE) else grade(x, y)])
    (ROOT / "Config/landscape-probes.json").write_text(
        json.dumps({"routes": WALK_ROUTES, "floorSamples": samples}, indent=2)
    )
    # Save an editable layer including the actual instance layout (hidden for USD export).
    collection = bpy.data.collections.new("Garden instances - editable preview")
    bpy.context.scene.collection.children.link(collection)
    for name, records in INSTANCES.items():
        source = bpy.data.objects[name]
        for record in records:
            obj = bpy.data.objects.new(name.replace("PROTO_", "Instance_"), source.data)
            collection.objects.link(obj)
            obj.location = record["position"]
            obj.scale = record["scale"]
            obj.rotation_euler.z = math.radians(record["yaw"])
            if "normal" in record:
                obj.rotation_euler = (
                    Vector(record["normal"]).to_track_quat("Z", "Y")
                    @ Quaternion(Vector((0, 0, 1)), math.radians(record["yaw"]))
                ).to_euler()
    for name in PROTOTYPES:
        bpy.data.objects[name].hide_render = True
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "SourceAssets/Cleveland-Landscape-v3.blend"))
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "SourceAssets/Cleveland-Landscape-v3.blend"))
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for name in PROTOTYPES:
        bpy.data.objects[name].hide_render = False
    # Convert the legacy metric scale nodes to USD-supported Mapping nodes.
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        for node in list(mat.node_tree.nodes):
            if node.type == "VECT_MATH" and node.operation == "SCALE":
                mapping = mat.node_tree.nodes.new("ShaderNodeMapping")
                mapping.inputs["Scale"].default_value = (node.inputs[3].default_value,) * 3
                for link in list(node.inputs[0].links):
                    mat.node_tree.links.new(link.from_socket, mapping.inputs["Vector"])
                for link in list(node.outputs[0].links):
                    mat.node_tree.links.new(mapping.outputs["Vector"], link.to_socket)
                mat.node_tree.nodes.remove(node)
    bpy.ops.wm.usd_export(
        filepath=str(transfer / "Landscape.usdc"),
        check_existing=False,
        export_animation=False,
        export_materials=True,
        export_textures=True,
        overwrite_textures=True,
        relative_paths=True,
        export_custom_properties=True,
        author_blender_name=True,
        export_lights=False,
        export_cameras=False,
        convert_world_material=False,
        triangulate_meshes=True,
        root_prim_path="/LandscapeV3",
        convert_scene_units="METERS",
    )
    report = {
        "version": 3,
        "prototypes": len(PROTOTYPES),
        "instances": sum(map(len, INSTANCES.values())),
        "grassPatches": sum(
            len(v) for k, v in INSTANCES.items() if PROTOTYPES[k]["kind"] == "grass"
        ),
        "continuousGroundManifold": True,
        "source": "SourceAssets/Cleveland-Landscape-v3.blend",
    }
    (ROOT / "reports/landscape-build.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
