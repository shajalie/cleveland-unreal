"""Rebuild owned architecture/dining/decor collections after reference corrections."""

import argparse
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from build_scene import collection, camera, configure_render
from geometry.materials import palette
from geometry.layout import build_layout
from geometry.architecture import build_house
from geometry.furnishings import dining_room
from geometry.rooms.reference_details import build as reference_details


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--views", default="dining,kitchen,powder,blue_bedroom")
    options = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    path = ROOT / "SourceAssets/Cleveland-Reconstruction.blend"
    bpy.ops.wm.open_mainfile(filepath=str(path))
    existing = {m.name: m for m in bpy.data.materials}
    fresh = palette()
    materials = {}
    for key, value in fresh.items():
        original_name = value.name.rsplit(".", 1)[0]
        materials[key] = existing.get(original_name, value)
    model = build_layout()
    builds = {
        "01 Architecture": lambda: build_house(model, materials),
        "04 Dining room": lambda: dining_room(materials),
        "16 Reference decor": lambda: reference_details(materials),
    }
    for name, build in builds.items():
        previous = bpy.data.collections.get(name)
        if previous:
            for obj in list(previous.all_objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(previous)
        collection(name)
        build()
    for material in fresh.values():
        if material.users == 0:
            bpy.data.materials.remove(material)
    if not bpy.data.objects.get("Review_dining"):
        camera("dining", (-1.85, 0.65, 1.57), (-4.1, 3.59, 1.29), 22)
    (ROOT / "design/spatial-model.json").write_text(json.dumps(model, indent=2))
    bpy.context.view_layer.update()
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    scene = bpy.context.scene
    configure_render(scene, 128)
    for name in options.views.split(","):
        if not name:
            continue
        scene.camera = bpy.data.objects["Review_" + name]
        scene.view_settings.exposure = 2.1
        scene.render.filepath = str(ROOT / "reports" / (name + "-review.png"))
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
