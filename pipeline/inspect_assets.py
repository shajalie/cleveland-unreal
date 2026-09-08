"""Render actual source-model silhouettes before choosing furnishings."""

from pathlib import Path
import bpy
import json
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new("Studio")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.55, 0.55, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5
bpy.ops.object.light_add(type="AREA", location=(2, -3, 5))
key = bpy.context.object
key.data.energy = 600
key.data.shape = "DISK"
key.data.size = 4
key.rotation_euler = (Vector((0, 0, 0.8)) - key.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.mesh.primitive_plane_add(size=200)
ground = bpy.context.object
mat = bpy.data.materials.new("Preview floor")
mat.diffuse_color = (0.28, 0.28, 0.28, 1)
ground.data.materials.append(mat)
bpy.ops.object.camera_add()
camera = bpy.context.object
scene.camera = camera
camera.data.lens = 48
out = ROOT / "reports/asset-previews"
out.mkdir(parents=True, exist_ok=True)
reports = []
for asset in [
    "sofa_02",
    "sofa_03",
    "modern_arm_chair_01",
    "mid_century_lounge_chair",
    "outdoor_table_chair_set_01",
    "dining_chair_02",
    "Rockingchair_01",
]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(
        filepath=str(ROOT / ".local/model-assets" / asset / (asset + "_1k.gltf"))
    )
    objects = list(set(bpy.data.objects) - before)
    meshes = [o for o in objects if o.type == "MESH"]
    corners = [o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
    lo = Vector([min(v[i] for v in corners) for i in range(3)])
    hi = Vector([max(v[i] for v in corners) for i in range(3)])
    center = (lo + hi) / 2
    distance = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z) * 2.3
    camera.location = center + Vector((0.9, -1.7, 0.9)).normalized() * distance
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    ground.location.z = lo.z - 0.01
    scene.render.filepath = str(out / (asset + ".png"))
    bpy.ops.render.render(write_still=True)
    reports.append(
        {
            "asset": asset,
            "boundsMeters": list(hi - lo),
            "faces": sum(len(o.data.polygons) for o in meshes),
            "meshObjects": len(meshes),
        }
    )
    for o in objects:
        bpy.data.objects.remove(o, do_unlink=True)
(ROOT / "reports/asset-inspection.json").write_text(json.dumps(reports, indent=2))
