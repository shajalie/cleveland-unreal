"""Finish a saved Unreal import without rebuilding its mesh assets."""

import json
import time
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from materials import replace_transmission
from doors import configure as configure_doors
from motion import configure_fans
from foliage import configure as configure_foliage

ROOT = Path(__file__).resolve().parents[2]


def finalize(actors, start, staging, stamp):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    components = [
        c
        for a in actors
        for c in a.get_components_by_class(unreal.StaticMeshComponent)
        if c.static_mesh
    ]
    meshes = {c.static_mesh.get_path_name(): c.static_mesh for c in components}
    transmission = replace_transmission(actors)
    foliage = configure_foliage(actors)
    doors = configure_doors(actors)
    fans = configure_fans(actors)
    # USD already carries the authoring sun; use one native review sun, not two.
    for actor in actors:
        if isinstance(
            actor,
            (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere, unreal.PlayerStart),
        ):
            actors_api.destroy_actor(actor)
    sun = actors_api.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0, 0, 1500),
        unreal.Rotator(pitch=-47, yaw=110, roll=0),
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
        unreal.PlayerStart,
        unreal.Vector(300, -200, 100),
        unreal.Rotator(pitch=0, yaw=-90, roll=0),
    )
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(300, -200, 165), unreal.Rotator(pitch=0, yaw=-90, roll=0)
    )
    levels.save_current_level()
    unreal.EditorAssetLibrary.save_directory(
        "/Game/Cleveland", only_if_is_dirty=True, recursive=True
    )
    # The report selects a completed versioned map. No rename or overwrite of old maps.
    report = {
        "status": "Imported assets and native transmission materials; visual and walking verification pending",
        "engine": unreal.SystemLibrary.get_engine_version(),
        "meshComponents": len(components),
        "uniqueMeshes": len(meshes),
        "nativeTransmissionAssignments": transmission,
        "interactiveDoors": doors,
        "animatedFans": fans,
        "foliage": foliage,
        "seconds": round(time.monotonic() - start, 1),
        "map": staging,
        "lighting": "Review sun; not yet geographically calibrated",
    }
    (ROOT / "reports/unreal-import.json").write_text(json.dumps(report, indent=2))
    config = ROOT / "runtime/ClevelandReal/Config/DefaultEngine.ini"
    config.write_text(
        re.sub(
            r"(?m)^(EditorStartupMap|GameDefaultMap)=.*$",
            lambda match: f"{match.group(1)}={staging}",
            config.read_text(),
        )
    )
    unreal.log(json.dumps(report))


def resume():
    directory = ROOT / "runtime/ClevelandReal/Content/Cleveland/Maps/ImportStaging"
    saved = max(directory.glob("Cleveland_*.umap"), key=lambda path: path.stat().st_mtime)
    staging = "/Game/Cleveland/Maps/ImportStaging/" + saved.stem
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(staging):
        raise RuntimeError(f"Could not load {staging}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    expected = json.loads((ROOT / "reports/unreal-export.json").read_text())["meshPrims"]
    count = sum(
        bool(c.static_mesh)
        for a in actors
        for c in a.get_components_by_class(unreal.StaticMeshComponent)
    )
    if count < expected:
        raise RuntimeError(
            f"Staging scene incomplete: {count} components, expected at least {expected}"
        )
    finalize(
        actors, time.monotonic(), staging, datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    )


if __name__ == "__main__":
    resume()
