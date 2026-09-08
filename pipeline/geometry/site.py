"""Unwarped GIS surroundings. Building heights and tree species remain estimates."""

import json
import math
from pathlib import Path
import bpy
from mathutils import Vector
from .primitives import box, extrusion, annotate

ROOT = Path(__file__).resolve().parents[2]
FEET = 1200 / 3937


def repair_foliage_opacity():
    """The glTF JPG base color has no alpha; use the upstream cutout map."""
    for material in bpy.data.materials:
        name = material.name.lower()
        key = (
            "tree_small_02_leaves_alpha"
            if "tree_small_02" in name and "leaves" in name
            else "fir_tree_01_twig_alpha"
            if "fir_tree_01" in name and "twig" in name
            else None
        )
        if not key or not material.use_nodes:
            continue
        shader = material.node_tree.nodes.get("Principled BSDF")
        if not shader:
            continue
        for old in list(material.node_tree.nodes):
            if old.name.startswith("Verified foliage opacity"):
                material.node_tree.nodes.remove(old)
        original = shader.inputs["Base Color"].links[0].from_node
        texture = material.node_tree.nodes.new("ShaderNodeTexImage")
        texture.name = "Verified foliage opacity"
        texture.image = bpy.data.images.load(
            str(ROOT / "reference/materials/foliage" / (key + ".png")), check_existing=True
        )
        texture.image.colorspace_settings.name = "Non-Color"
        if original.inputs.get("Vector") and original.inputs["Vector"].links:
            material.node_tree.links.new(
                original.inputs["Vector"].links[0].from_socket, texture.inputs["Vector"]
            )
        material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Alpha"])
        material["opacity_source"] = (
            "Poly Haven original 2k grayscale opacity, connected as color rather than JPG alpha"
        )


def place_tree(obj, source, spec, index, model):
    obj.scale = source.scale.copy()
    obj.rotation_euler = source.rotation_euler.copy()
    obj.rotation_euler.z += index * 2.39996
    local_z = [v[2] * obj.scale.z for v in source.bound_box]
    obj.scale.z *= spec["heightEstimate"] / max(0.01, max(local_z) - min(local_z))
    rotated = [
        obj.rotation_euler.to_matrix()
        @ Vector((v[0] * obj.scale.x, v[1] * obj.scale.y, v[2] * obj.scale.z))
        for v in source.bound_box
    ]
    radius = (
        max(
            max(v.x for v in rotated) - min(v.x for v in rotated),
            max(v.y for v in rotated) - min(v.y for v in rotated),
        )
        / 2
    )
    # Crown estimates constrain horizontal growth independently of tree height.
    # Keep a small building clearance; this is an explicit reconstruction assumption.
    center = Vector(spec["center"])
    distances = []
    for floor in model["floors"][:2]:
        outline = floor["outline"]
        for aa, bb in zip(outline, outline[1:] + outline[:1]):
            a, b = Vector(aa), Vector(bb)
            t = min(1, max(0, (center - a).dot(b - a) / (b - a).length_squared))
            distances.append((center - (a + t * (b - a))).length)
    target = min(spec["crownRadiusEstimate"], max(0.5, min(distances) - 0.25))
    factor = target / max(0.01, radius)
    obj.scale.x *= factor
    obj.scale.y *= factor
    rotated = [
        obj.rotation_euler.to_matrix()
        @ Vector((v[0] * obj.scale.x, v[1] * obj.scale.y, v[2] * obj.scale.z))
        for v in source.bound_box
    ]
    anchor = Vector(
        (
            (min(v.x for v in rotated) + max(v.x for v in rotated)) / 2,
            (min(v.y for v in rotated) + max(v.y for v in rotated)) / 2,
            min(v.z for v in rotated),
        )
    )
    obj.location = Vector((*spec["center"], -1.65)) - anchor
    obj["crown_radius_m"] = target
    obj["crown_status"] = "Aerial estimate, limited to preserve building clearance; not surveyed"


def site_data(model):
    data = json.loads((ROOT / "reference/model-data.json").read_text())
    old = data["indoor"]["floors"][0]["walls"][0]["holes"][-1]
    new = next(h for h in model["floors"][0]["walls"][0]["holes"] if h["id"] == "front_door")
    offset = [(new["a"][i] + new["b"][i] - old["a"][i] - old["b"][i]) / 2 for i in range(2)]

    def point(p):
        return [p[i] * FEET + offset[i] for i in range(2)]

    out = data["outdoor"]
    pool = next(z for z in out["zones"] if z["name"] == "Pool")
    pp = [point(p) for p in pool["poly"]]
    bounds = [[min(p[i] for p in pp), max(p[i] for p in pp)] for i in range(2)]
    result = {
        "translationMeters": offset,
        "sourceUnits": "US survey feet",
        "scaleToMeters": FEET,
        "registration": "Translation anchored to the entry; GIS coordinates are not stretched with the floor plan.",
        "parcel": [point(p) for p in out["parcel"]],
        "neighbors": [
            {
                "id": n["id"],
                "outline": [point(p) for p in n["ring"][:-1]],
                "eaveHeightEstimate": 6.5,
            }
            for n in out["neighbors"]
        ],
        "trees": [
            {"center": point(t[:2]), "crownRadiusEstimate": t[2] * FEET, "heightEstimate": t[3]}
            for t in out["trees"]
        ],
        "pool": {
            "center": [(lo + hi) / 2 for lo, hi in bounds],
            "aerialTracedExtent": [hi - lo for lo, hi in bounds],
            "listingDimensions": [20 * 0.3048, 10 * 0.3048],
        },
        "uncertainty": [
            "The listing plan dimensions and traced aerial envelope disagree; neither is a measured survey.",
            "Neighbor heights, crown sizes and tree types are estimates; the aerial was acquired March 27, 2025.",
            "Pool water dimensions use the approximate listing label; the aerial trace appears larger.",
        ],
    }
    return result


def build_site(model, m):
    data = site_data(model)
    (ROOT / "design/site-registration.json").write_text(json.dumps(data, indent=2))
    # Ground under the scene closes the distant horizon. The sunken areaway remains excavated.
    for name, center, size in [
        ("Left ground", (-22, 4, -2.88), (23, 80, 0.15)),
        ("Right ground", (27, 4, -2.88), (32, 80, 0.15)),
        ("Rear ground", (-1, 33, -2.88), (80, 22, 0.15)),
        ("Front ground", (-1, -20, -0.76), (80, 25, 0.15)),
    ]:
        box(name, center, size, m["soil"], 0)
    for neighbor in data["neighbors"]:
        ring = neighbor["outline"]
        base = -0.65
        height = neighbor["eaveHeightEstimate"]
        obj = extrusion("GIS neighbor " + str(neighbor["id"]), ring, base, height, m["stucco"])
        obj["source"] = "Saved DC GIS building footprint"
        obj["height_status"] = "Estimated; not surveyed"
        # A low, recessed roof volume preserves the footprint silhouette without inventing measured roof form.
        cap = extrusion(
            "Neighbor roof " + str(neighbor["id"]), ring, base + height, 0.20, m["asphalt"]
        )
        cap["fidelity"] = "Shade mass only; roof form not yet reconstructed."
    parcel = data["parcel"]
    for a, b in zip(parcel, parcel[1:]):
        if min(a[1], b[1]) < -2:
            continue
        length = (Vector(b) - Vector(a)).length
        if length < 0.1:
            continue
        direction = (Vector(b) - Vector(a)).normalized()
        # Opaque rear/side timber fence visible in photos; measured height unavailable.
        for i in range(math.ceil(length / 0.15)):
            p = Vector(a) + direction * min(length, (i + 0.5) * 0.15)
            board = box(
                "Boundary timber fence board",
                (p.x, p.y, -0.76),
                (0.14, 0.026, 1.75),
                m["wood"],
                0.003,
            )
            board.rotation_euler.z = math.atan2(direction.y, direction.x)
            annotate(board, "boundary_fence", [47, 49, 50])
            board["height_status"] = "Estimated 1.75 m"
    library = ROOT / ".local/realism-assets.blend"
    if library.exists():
        with bpy.data.libraries.load(str(library), link=False) as (src, dst):
            dst.objects = [
                name for name in src.objects if "fir_tree" in name or "tree_small" in name
            ]
        sources = [o for o in dst.objects if o and o.type == "MESH"]
        original_broadleaf = ROOT / ".local/broadleaf-source.blend"
        if original_broadleaf.exists():
            with bpy.data.libraries.load(str(original_broadleaf), link=False) as (src, dst):
                dst.objects = list(src.objects)
            broadleaf = [o for o in dst.objects if o and o.type == "MESH"]
            if broadleaf:
                sources = [o for o in sources if "fir_tree" in o.name] + broadleaf
        # Linked mesh instances keep scanned leaf/needle detail within the 6 GB budget.
        for index, spec in enumerate(data["trees"]):
            pool = [o for o in sources if ("fir_tree" in o.name) == (index in [0, 8, 9, 10])]
            if not pool:
                continue
            source = pool[0]
            obj = source.copy()
            obj.data = source.data
            bpy.context.collection.objects.link(obj)
            obj.name = "Estimated tree " + str(index)
            place_tree(obj, source, spec, index, model)
            obj["tree_id"] = index
            obj["species_status"] = "Representative scanned vegetation; species not verified"
            obj["season"] = "Leaf-on review asset; no measured seasonal transmission yet"
    repair_foliage_opacity()
    return data
