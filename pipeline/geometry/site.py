"""Unwarped GIS surroundings. Building heights and tree species remain estimates."""

import json
import math
from pathlib import Path
import bpy
from mathutils import Vector
from .primitives import box, extrusion, annotate

ROOT = Path(__file__).resolve().parents[2]
FEET = 1200 / 3937


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
            coords = [source.matrix_world @ Vector(v) for v in source.bound_box]
            lo = Vector([min(v[i] for v in coords) for i in range(3)])
            hi = Vector([max(v[i] for v in coords) for i in range(3)])
            # Apply height scaling to the source transform, keeping natural relative branch proportions.
            factor = spec["heightEstimate"] / max(0.01, hi.z - lo.z)
            obj.scale = source.scale * factor
            obj.rotation_euler.z += index * 2.39996
            obj.location = (
                Vector((*spec["center"], -1.65))
                - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)) * factor
            )
            obj["tree_id"] = index
            obj["species_status"] = "Representative scanned vegetation; species not verified"
            obj["season"] = "Leaf-on review asset; no measured seasonal transmission yet"
    return data
