"""Geometric checks against the evaluated, saved Blender scene."""

import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from geometry.layout import build_layout


def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "SourceAssets/Cleveland-Reconstruction.blend"))
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()
    model = build_layout()
    checks = []
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        shader = material.node_tree.nodes.get("Principled BSDF")
        if not shader:
            continue
        for link in shader.inputs["Alpha"].links:
            texture = link.from_node
            invalid = (
                texture.type == "TEX_IMAGE"
                and texture.image
                and texture.image.file_format == "JPEG"
                and link.from_socket.name == "Alpha"
            )
            checks.append(
                {"check": "opacity_has_real_mask", "material": material.name, "pass": not invalid}
            )
    for obj in bpy.data.objects:
        if "tree_id" in obj and "crown_radius_m" in obj:
            diameter = max(obj.dimensions.x, obj.dimensions.y)
            checks.append(
                {
                    "check": "tree_crown_extent",
                    "tree": obj.name,
                    "diameterMeters": round(diameter, 3),
                    "pass": diameter <= 2 * obj["crown_radius_m"] + 0.01,
                }
            )
    # Catch the transform regression that previously made tiny fixture knobs huge.
    for obj in bpy.data.objects:
        if obj.type == "MESH" and ("knob" in obj.name.lower() or "lamp bulb" in obj.name.lower()):
            evaluated = obj.evaluated_get(deps)
            corners = [evaluated.matrix_world @ Vector(p) for p in evaluated.bound_box]
            extent = max(max(p[i] for p in corners) - min(p[i] for p in corners) for i in range(3))
            checks.append(
                {
                    "check": "fixture_scale",
                    "object": obj.name,
                    "largestDimensionMeters": round(extent, 4),
                    "pass": extent < 0.10,
                }
            )
    # A duvet can look smooth yet intersect the mattress; measure actual surfaces.
    for name, width in [
        ("Primary upholstered bed", 1.65),
        ("Blue bedroom bed", 1.32),
        ("Yellow bedroom storage bed", 1.40),
    ]:
        root = bpy.data.objects.get(name)
        if not root:
            continue
        duvet = bpy.data.objects[name + " draped duvet"].evaluated_get(deps)
        mattress = bpy.data.objects[name + " mattress"].evaluated_get(deps)
        clearances = []
        for x in [-width * 0.37, 0, width * 0.37]:
            for y in [-0.80, -0.35, 0.15]:
                origin = root.matrix_world @ Vector((x, y, 1.6))
                heights = []
                for obj in [duvet, mattress]:
                    inverse = obj.matrix_world.inverted()
                    hit, point, *_ = obj.ray_cast(
                        inverse @ origin, inverse.to_3x3() @ Vector((0, 0, -1)), distance=2
                    )
                    heights.append((obj.matrix_world @ point).z if hit else None)
                if None in heights:
                    raise RuntimeError(f"Missing bedding surface at {name}: {x}, {y}")
                clearances.append(heights[0] - heights[1])
        checks.append(
            {
                "check": "duvet_above_mattress",
                "bed": name,
                "minimumClearanceMeters": round(min(clearances), 4),
                "pass": min(clearances) > 0.004,
            }
        )
    stair = next(s for s in model["stairs"] if s["id"] == "main_stair")
    for i in range(stair["risers"]):
        x = stair["start"][0]
        y = stair["start"][1] + (i + 0.5) * stair["tread"]
        z = (i + 1) * stair["high"] / stair["risers"]
        hit, point, normal, index, obj, matrix = scene.ray_cast(
            deps, Vector((x, y, z + 0.01)), Vector((0, 0, 1)), distance=2
        )
        checks.append(
            {
                "check": "stair_headroom_2m",
                "step": i + 1,
                "pass": not hit,
                "obstacle": obj.name if hit else None,
            }
        )
    # Check that both leaf frames belong to the actual portal and rotate around its jamb.
    holes = {h["id"]: h for f in model["floors"] for w in f["walls"] for h in w["holes"]}
    for root in [o for o in bpy.data.objects if o.get("interaction") == "hinged_door"]:
        hole = holes[root["portal_id"]]
        center = (Vector(hole["a"]) + Vector(hole["b"])) / 2
        meshes = [o for o in root.children if o.type == "MESH"]
        corners = [o.matrix_world @ Vector(p) for o in meshes for p in o.bound_box]
        mean = sum(corners, Vector((0, 0, 0))) / len(corners)
        distance = (Vector((mean.x, mean.y)) - center).length
        checks.append(
            {
                "check": "door_leaf_registered",
                "door": root.name,
                "distanceFromPortalMeters": round(distance, 4),
                "pass": distance < 1.5,
            }
        )
        closed = [o.matrix_world.copy() for o in meshes]
        root.rotation_euler.z = 0.7
        bpy.context.view_layer.update()
        moved = any(
            (o.matrix_world.translation - m.translation).length > 0.01
            for o, m in zip(meshes, closed)
        )
        checks.append({"check": "door_leaf_moves_about_hinge", "door": root.name, "pass": moved})
        root.rotation_euler.z = 0
        bpy.context.view_layer.update()
    report = {
        "checks": checks,
        "passed": sum(c["pass"] for c in checks),
        "failed": sum(not c["pass"] for c in checks),
        "scope": "Geometry-only checks; not a runtime navigation, collision or lighting validation.",
    }
    (ROOT / "reports/geometry-validation.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"passed": report["passed"], "failed": report["failed"]}), flush=True)
    if report["failed"]:
        raise RuntimeError("Geometry check failed; see reports/geometry-validation.json")


if __name__ == "__main__":
    main()
