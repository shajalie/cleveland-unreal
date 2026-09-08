"""Refresh vegetation in a generated scene without rebuilding every room.

Uses the same placement/material functions as a complete authoring rebuild.
Run after build_scene has finished; never edit the same blend concurrently.
"""

import argparse
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from geometry.layout import build_layout
from geometry.site import site_data, place_tree, repair_foliage_opacity
from build_scene import configure_render


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--views", default="primary,sunroom,blue_bedroom,yellow_bedroom,living,rear"
    )
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    path = ROOT / "SourceAssets/Cleveland-Reconstruction.blend"
    bpy.ops.wm.open_mainfile(filepath=str(path))
    model = build_layout()
    data = site_data(model)
    library = ROOT / ".local/broadleaf-source.blend"
    original = None
    if library.exists():
        with bpy.data.libraries.load(str(library), link=False) as (src, dst):
            dst.objects = list(src.objects)
        original = next((o for o in dst.objects if o and o.type == "MESH"), None)
    records = []
    for obj in list(bpy.data.objects):
        if "tree_id" not in obj:
            continue
        index = int(obj["tree_id"])
        source = (original if original and index not in [0, 8, 9, 10] else obj).copy()
        if original and index not in [0, 8, 9, 10]:
            obj.data = original.data
        else:
            source.rotation_euler.z -= index * 2.39996
        place_tree(obj, source, data["trees"][index], index, model)
        bpy.data.objects.remove(source)
        records.append({"tree": index, "crownRadiusMeters": obj["crown_radius_m"]})
    repair_foliage_opacity()
    bpy.context.view_layer.update()
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    (ROOT / "reports/foliage-repair.json").write_text(
        json.dumps(
            {
                "trees": records,
                "opacity": "Original Poly Haven 2k masks; JPG alpha connection removed",
                "limits": "Species and crown measurements remain estimates; this is a geometry/material repair",
            },
            indent=2,
        )
    )
    scene = bpy.context.scene
    configure_render(scene, 128)
    for name in args.views.split(","):
        if not name:
            continue
        scene.camera = bpy.data.objects["Review_" + name]
        scene.view_settings.exposure = -0.2 if name == "rear" else 2.1
        scene.render.filepath = str(ROOT / "reports" / (name + "-review.png"))
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
