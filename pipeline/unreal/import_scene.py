"""Import the USD into persistent Unreal assets, then verify actual scene contents."""

import json
import sys
import time
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from materials import replace_transmission
from doors import configure as configure_doors
from motion import configure_fans


def main():
    start = time.monotonic()
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.new_level("/Game/Cleveland/Maps/Cleveland"):
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
    transmission = replace_transmission(actors)
    doors = configure_doors(actors)
    fans = configure_fans(actors)
    sun = actors_api.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 1500), unreal.Rotator(-47, 110, 0)
    )
    sun.set_actor_label("Review sun - geographic calibration pending")
    sunlight = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sunlight.set_editor_property("intensity", 80000.0)
    sunlight.set_editor_property("atmosphere_sun_light", True)
    actors_api.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector())
    sky = actors_api.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1200))
    sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property(
        "real_time_capture", True
    )
    actors_api.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(300, -200, 100), unreal.Rotator(0, -90, 0)
    )
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(300, -200, 165), unreal.Rotator(0, -90, 0)
    )
    levels.save_current_level()
    unreal.EditorAssetLibrary.save_directory(
        "/Game/Cleveland", only_if_is_dirty=True, recursive=True
    )
    report = {
        "status": "Imported assets and native transmission materials; visual and walking verification pending",
        "engine": unreal.SystemLibrary.get_engine_version(),
        "meshComponents": len(components),
        "uniqueMeshes": len(meshes),
        "nativeTransmissionAssignments": transmission,
        "interactiveDoors": doors,
        "animatedFans": fans,
        "seconds": round(time.monotonic() - start, 1),
        "map": "/Game/Cleveland/Maps/Cleveland",
        "lighting": "Review sun; not yet geographically calibrated",
    }
    (ROOT / "reports/unreal-import.json").write_text(json.dumps(report, indent=2))
    unreal.log(json.dumps(report))


if __name__ == "__main__":
    main()
