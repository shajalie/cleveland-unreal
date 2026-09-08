"""Preserve the original broadleaf mesh and UVs, without decimating leaf cards."""

import json
from pathlib import Path
import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / ".local/model-assets/tree_small_02/tree_small_02_1k.gltf"
    if not source.exists():
        raise RuntimeError("Run fetch_assets.py to download the verified broadleaf source.")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("Original broadleaf source contains no meshes")
    # Bake scene transforms into mesh data so later placement has one clear meter frame.
    bpy.context.view_layer.update()
    for obj in meshes:
        transform = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
        obj.data.transform(transform)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / ".local/broadleaf-source.blend"))
    (ROOT / "reports/broadleaf-source.json").write_text(
        json.dumps(
            {
                "source": "https://polyhaven.com/a/tree_small_02",
                "license": "CC0",
                "meshes": [
                    {
                        "name": o.name,
                        "polygons": len(o.data.polygons),
                        "uvLayers": [u.name for u in o.data.uv_layers],
                    }
                    for o in meshes
                ],
                "simplification": "None; preserve original leaf cards and UV seams",
                "species": "Representative asset; species identity at the house remains unverified",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
