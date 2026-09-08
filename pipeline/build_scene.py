"""Build an editable reference-check scene and render named review cameras.

Run with Blender 4.5 LTS --background --python this_file -- --views living,rear.
This authoring scene is not the Unreal runtime or a calibrated lighting survey.
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from geometry.layout import build_layout
from geometry.materials import palette
from geometry.architecture import build_house, build_terraces, roof
from geometry.site import build_site
from geometry.furnishings import living_room, dining_room, study, patio
from geometry.rooms.kitchen import build as kitchen
from geometry.rooms.bathrooms import build as bathrooms
from geometry.rooms.bedrooms import build as bedrooms
from geometry.rooms.library import build as library
from geometry.rooms.finishes import build as room_finishes
from geometry.rooms.textiles import build as textiles
from geometry.rooms.living_details import build as living_details
from geometry.rooms.reference_details import build as reference_details
from geometry.primitives import box


def collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    layer = bpy.context.view_layer.layer_collection.children[col.name]
    bpy.context.view_layer.active_layer_collection = layer
    return col


def configure_render(scene, samples):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 16
    scene.cycles.diffuse_bounces = 8
    scene.cycles.glossy_bounces = 8
    scene.cycles.transmission_bounces = 12
    scene.cycles.transparent_max_bounces = 12
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    gpu = [d for d in prefs.devices if d.type == "OPTIX"]
    if not gpu:
        raise RuntimeError("A dedicated NVIDIA OptiX GPU is required for this render profile.")
    for device in prefs.devices:
        device.use = device.type == "OPTIX"
    scene.cycles.device = "GPU"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    return [d.name for d in gpu]


def lighting(scene):
    world = bpy.data.worlds.new("Physical clear sky")
    world.use_nodes = True
    scene.world = world
    sky = world.node_tree.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(47)
    sky.sun_rotation = math.radians(110)
    sky.sun_intensity = 1
    sky.sun_size = math.radians(0.545)
    sky.air_density = 1
    sky.dust_density = 0.6
    world.node_tree.links.new(sky.outputs[0], world.node_tree.nodes["Background"].inputs["Color"])
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
    # Small practical lamps are modeled as actual interior light sources.
    for x, y in [(4.45, 4.00), (4.45, 5.2)]:
        bpy.ops.object.light_add(type="POINT", location=(x, y, 1.88))
        light = bpy.context.object
        light.name = "Warm fireplace sconce"
        light.data.energy = 18
        light.data.color = (1, 0.72, 0.42)
        light.data.shadow_soft_size = 0.08
    scene["lighting_status"] = "Review sky; not yet tied to a selected geographic date/time."


def pool(m):
    center = (-4.8, 18.5)
    water_top = -1.78
    bottom = -3.08
    box("Pool basin bottom", (*center, bottom - 0.07), (6.096, 3.048, 0.14), m["concrete"])
    for x in [center[0] - 3.048, center[0] + 3.048]:
        box("Pool long wall", (x, center[1], -2.4), (0.12, 3.17, 1.36), m["concrete"])
    for y in [center[1] - 1.524, center[1] + 1.524]:
        box("Pool short wall", (center[0], y, -2.4), (6.12, 0.12, 1.36), m["concrete"])
    water = box(
        "Contained water volume",
        (*center, (bottom + water_top) / 2),
        (5.97, 2.92, water_top - bottom),
        m["water"],
        0,
    )
    n = m["water"].node_tree.nodes
    links = m["water"].node_tree.links
    coord = n.new("ShaderNodeTexCoord")
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 7
    noise.inputs["Detail"].default_value = 2
    noise.inputs["Roughness"].default_value = 0.62
    links.new(coord.outputs["Object"], noise.inputs["Vector"])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.009
    bump.inputs["Strength"].default_value = 0.3
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], n.get("Principled BSDF").inputs["Normal"])
    water["animation_status"] = (
        "Static review ripple; runtime wind and circulation remain to be implemented."
    )
    for i in range(3):
        box(
            "Submerged entry tread",
            (-2.13 - i * 0.25, 17.48, -1.95 - i * 0.24),
            (0.48 + i * 0.15, 0.79 + i * 0.12, 0.15),
            m["concrete"],
            0.06,
        )


def camera(name, position, target, lens):
    bpy.ops.object.camera_add(location=position)
    obj = bpy.context.object
    obj.name = "Review_" + name
    obj.data.lens = lens
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    obj.data.clip_start = 0.035
    obj.data.clip_end = 250
    return obj


def mesh_checks(model):
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    # Ray checks target the actual saved floor geometry, not just semantic links.
    findings = []
    upper = bpy.data.objects["upper_floor"]
    evaluated = upper.evaluated_get(deps)
    for y in [3.0, 4.2, 5.8]:
        origin = Vector((0.13, y, 3.7))
        direction = Vector((0, 0, -1))
        hit, *_ = evaluated.ray_cast(
            evaluated.matrix_world.inverted() @ origin, direction, distance=1
        )
        findings.append({"check": "upper_stairwell_clear", "point": [0.13, y], "pass": not hit})
    porch = bpy.data.objects["porch"].evaluated_get(deps)
    hit, *_ = porch.ray_cast(Vector((6.15, -1.6, 0.5)), Vector((0, 0, -1)), distance=1)
    findings.append({"check": "carport_floor_removed", "pass": not hit})
    for fid in ["study_rear_door", "kitchen_rear_door", "basement_garden_door"]:
        leaves = [o for o in bpy.data.objects if o.get("portal_id") == fid]
        findings.append({"check": "separate_hinged_leaves", "portal": fid, "pass": bool(leaves)})
    if not all(f["pass"] for f in findings):
        raise AssertionError(findings)
    return findings


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--views", default="living,rear,stair")
    parser.add_argument("--samples", type=int, default=96)
    parser.add_argument("--no-render", action="store_true")
    options = parser.parse_args(args)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1
    devices = configure_render(scene, options.samples)
    m = palette()
    model = build_layout()
    (ROOT / "design/spatial-model.json").write_text(json.dumps(model, indent=2))
    for name, build in [
        ("01 Architecture", lambda: build_house(model, m)),
        ("02 Garden levels", lambda: (build_terraces(model, m), pool(m))),
        ("03 Living room", lambda: living_room(m)),
        ("04 Dining room", lambda: dining_room(m)),
        ("05 Kitchen", lambda: kitchen(m)),
        ("06 Study", lambda: study(m)),
        ("07 Patio furnishings", lambda: patio(m)),
        ("08 Roof", lambda: roof(m)),
        ("09 Site context", lambda: build_site(model, m)),
        ("10 Bathrooms and laundry", lambda: bathrooms(m)),
        ("11 Bedrooms and sunroom", lambda: bedrooms(m)),
        ("12 Lower library", lambda: library(m)),
        ("13 Room paint", lambda: room_finishes(model, m)),
        ("14 Patterned textiles", lambda: textiles(m)),
        ("15 Living and study details", lambda: living_details(m)),
        ("16 Reference decor", lambda: reference_details(m)),
    ]:
        print("BUILD_STAGE", name, flush=True)
        collection(name)
        build()
    collection("08 Lighting and review cameras")
    lighting(scene)
    cameras = {
        "living": camera("living", (1.20, 6.95, 1.55), (3.18, 3.25, 1.36), 22),
        "rear": camera("rear", (-1.8, 17.1, 0.30), (0.65, 10.75, 1.1), 24),
        "stair": camera("stair", (-0.71, 0.56, 1.57), (0.08, 4.74, 1.69), 23),
        "study": camera("study", (3.22, 8.13, 1.57), (2.96, 12.6, 1.20), 24),
        "kitchen": camera("kitchen", (-3.72, 8.10, 1.56), (-4.57, 5.27, 1.32), 22),
        "dining": camera("dining", (-1.85, 0.65, 1.57), (-4.1, 3.59, 1.29), 22),
        "powder": camera("powder", (-0.55, 6.30, 1.49), (-1.10, 7.27, 1.11), 19),
        "primary_bath": camera("primary_bath", (-1.25, 1.38, 4.62), (0.52, 1.41, 4.29), 18),
        "hall_bath": camera("hall_bath", (1.08, 6.96, 4.64), (3.58, 5.45, 4.30), 20),
        "primary": camera("primary", (-1.89, 5.42, 4.70), (-4.38, 4.22, 4.14), 23),
        "sunroom": camera("sunroom", (-4.22, 7.89, 4.70), (-4.14, 10.46, 4.31), 23),
        "blue_bedroom": camera("blue_bedroom", (1.53, 10.09, 4.69), (3.49, 8.69, 4.21), 22),
        "yellow_bedroom": camera("yellow_bedroom", (1.14, 2.58, 4.68), (3.48, 3.65, 4.35), 23),
    }
    scene.camera = cameras["living"]
    checks = mesh_checks(model)
    out = ROOT / "SourceAssets"
    out.mkdir(exist_ok=True)
    # Pack only referenced asset textures. Authentication and service state never enter the scene.
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "Cleveland-Reconstruction.blend"))
    report = {
        "engine": bpy.app.version_string,
        "device": "OPTIX",
        "gpus": devices,
        "samples": options.samples,
        "objects": len(bpy.data.objects),
        "meshChecks": checks,
        "renders": [],
        "status": "Authoring review; see unreal-import.json for the separate engine integration status.",
        "knownIncomplete": [
            "Exact furniture shapes, decorative objects, artwork and textile patterns",
            "Neighbor facade detailing and verified vegetation species",
            "Photo-calibrated cameras and materials",
            "Internal basement stair",
            "Runtime interaction and streaming",
            "Date/time sun calibration",
            "Dynamic wind/water",
        ],
    }
    if not options.no_render:
        for name in options.views.split(","):
            scene.camera = cameras[name]
            scene.render.filepath = str(ROOT / "reports" / (name + "-review.png"))
            scene.view_settings.exposure = 2.1 if name != "rear" else -0.2
            t = time.time()
            bpy.ops.render.render(write_still=True)
            report["renders"].append(
                {
                    "view": name,
                    "seconds": round(time.time() - t, 2),
                    "exposureStops": scene.view_settings.exposure,
                }
            )
            (ROOT / "reports/scene-build.json").write_text(json.dumps(report, indent=2))
    (ROOT / "reports/scene-build.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
