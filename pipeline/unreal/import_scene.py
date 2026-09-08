"""Import the USD into persistent Unreal assets, then verify actual scene contents."""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from finalize_scene import finalize


def main():
    start = time.monotonic()
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    staging = f"/Game/Cleveland/Maps/ImportStaging/Cleveland_{stamp}"
    if not levels.new_level(staging):
        raise RuntimeError("Could not create the reconstruction level")
    options = unreal.UsdStageImportOptions()
    for name, value in {
        "import_actors": True,
        "import_geometry": True,
        "import_materials": True,
        "import_only_used_materials": True,
        "import_skeletal_animations": False,
        "import_level_sequences": False,
        "import_groom_assets": False,
        "import_sparse_volume_textures": False,
        "share_assets_for_identical_prims": True,
        "use_prim_kinds_for_collapsing": False,
        "nanite_triangle_threshold": 20000,
        "fallback_collision_type": unreal.UsdCollisionType.CUBE,
        "existing_asset_policy": unreal.ReplaceAssetPolicy.REPLACE,
        "existing_actor_policy": unreal.ReplaceActorPolicy.REPLACE,
    }.items():
        options.set_editor_property(name, value)
    task = unreal.AssetImportTask()
    task.filename = str(ROOT / "SourceAssets/UnrealTransfer/Cleveland.usdc")
    task.destination_path = "/Game/Cleveland/Imported"
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.factory = unreal.UsdStageImportFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    actors = actors_api.get_all_level_actors()
    components = [
        component
        for actor in actors
        for component in actor.get_components_by_class(unreal.StaticMeshComponent)
        if component.static_mesh
    ]
    export_report = json.loads((ROOT / "reports/unreal-export.json").read_text())
    expected_meshes = export_report["meshPrims"]
    if len(components) < expected_meshes:
        raise RuntimeError(
            f"Incomplete import: {len(components)} mesh components for {expected_meshes} exported meshes"
        )
    meshes = {
        component.static_mesh.get_path_name(): component.static_mesh for component in components
    }
    for mesh in meshes.values():
        body = mesh.get_editor_property("body_setup")
        if body:
            body.set_editor_property(
                "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
            )
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    for component in components:
        component.set_collision_profile_name("BlockAll")
        if (
            "Contained_water" in component.get_name()
            or "Estimated_tree" in component.get_owner().get_actor_label()
        ):
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    levels.save_current_level()
    finalize(actors, start, staging, stamp)


if __name__ == "__main__":
    main()
