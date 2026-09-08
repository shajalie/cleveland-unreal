"""Add landscape v3 to a copy of the completed map; never modify its source assets."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "pipeline"), str(Path(__file__).resolve().parent)]
from landscape.layout import grade
import landscape_materials as garden_materials
from materials import node, custom_input, color, scalar

EDIT = unreal.MaterialEditingLibrary
ASSETS = unreal.EditorAssetLibrary


def grass_material(package):
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_GrassBlade", package, unreal.Material, unreal.MaterialFactoryNew()
    )
    mat.set_editor_property("two_sided", True)
    mat.set_editor_property("used_with_instanced_static_meshes", True)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    color(mat, (0.07, 0.16, 0.025), unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    scalar(mat, 0.76, unreal.MaterialProperty.MP_ROUGHNESS)
    position = node(mat, unreal.MaterialExpressionWorldPosition)
    vertex = node(mat, unreal.MaterialExpressionVertexColor)
    time = node(mat, unreal.MaterialExpressionTime)
    strength = node(
        mat,
        unreal.MaterialExpressionScalarParameter,
        parameter_name="BreezeStrength",
        default_value=1.0,
    )
    shade = node(
        mat,
        unreal.MaterialExpressionCustom,
        output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        inputs=[custom_input("Position"), custom_input("Height")],
        code="""
float n = .5 + .5*sin(Position.x*.023)*sin(Position.y*.017);
float3 root = float3(.014,.035,.004);
float3 tip = lerp(float3(.044,.105,.012),float3(.10,.17,.025),n);
return lerp(root,tip,saturate(.2+Height*.8));
""",
    )
    EDIT.connect_material_expressions(position, "", shade, "Position")
    EDIT.connect_material_expressions(vertex, "G", shade, "Height")
    EDIT.connect_material_property(shade, "", unreal.MaterialProperty.MP_BASE_COLOR)
    breeze = node(
        mat,
        unreal.MaterialExpressionCustom,
        output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        inputs=[
            custom_input("Position"),
            custom_input("Time"),
            custom_input("Height"),
            custom_input("Strength"),
        ],
        code="""
float phase=dot(Position.xy,float2(.024,.019));
float sway=sin(Time*2.1+phase)+.25*sin(Time*3.2+phase*1.7);
return float3(sway,.4*sway,0)*Height*Height*.8*Strength;
""",
    )
    for expression, output, name in [
        (position, "", "Position"),
        (time, "", "Time"),
        (vertex, "G", "Height"),
        (strength, "", "Strength"),
    ]:
        EDIT.connect_material_expressions(expression, output, breeze, name)
    EDIT.connect_material_property(breeze, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    EDIT.layout_material_expressions(mat)
    EDIT.recompile_material(mat)
    ASSETS.save_loaded_asset(mat)
    return mat


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def main():
    previous = json.loads((ROOT / "reports/unreal-import.json").read_text())
    if "LandscapeV3" in previous["map"]:
        # Iteration always starts with the preserved lighting-v2 map.
        previous = json.loads((ROOT / "reports/landscape-base-map.json").read_text())
    else:
        (ROOT / "reports/landscape-base-map.json").write_text(json.dumps(previous, indent=2))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    target = f"/Game/Cleveland/Maps/LandscapeV3_{stamp}"
    package = f"/Game/Cleveland/LandscapeV3/{stamp}"
    if not ASSETS.duplicate_asset(previous["map"], target):
        raise RuntimeError("Map backup/copy failed")
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(target):
        raise RuntimeError("Versioned map did not load")
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    original_actors = list(actors_api.get_all_level_actors())
    options = unreal.UsdStageImportOptions()
    for key, value in {
        "import_actors": True,
        "import_geometry": True,
        "import_materials": True,
        "import_only_used_materials": True,
        "import_skeletal_animations": False,
        "import_level_sequences": False,
        "share_assets_for_identical_prims": False,
        "use_prim_kinds_for_collapsing": False,
        "nanite_triangle_threshold": 10000000,
        "fallback_collision_type": unreal.UsdCollisionType.CUBE,
    }.items():
        options.set_editor_property(key, value)
    task = unreal.AssetImportTask()
    task.filename = str(ROOT / "SourceAssets/Landscape-v3/Landscape.usdc")
    task.destination_path = package
    task.automated = True
    task.save = True
    task.factory = unreal.UsdStageImportFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    new_actors = [a for a in actors_api.get_all_level_actors() if a not in original_actors]
    manifest = json.loads((ROOT / "SourceAssets/Landscape-v3/landscape.json").read_text())
    prototype_keys = {safe_name(key): key for key in manifest["prototypes"]}
    meshes = {}
    components = []
    aggregate = None
    for actor in new_actors:
        for c in actor.get_components_by_class(unreal.StaticMeshComponent):
            if not c.static_mesh:
                continue
            components.append(c)
            name = c.static_mesh.get_name().removeprefix("SM_")
            # USD keeps a mesh data name; Blender object names may differ after import.
            combined = " ".join([name, c.get_name(), actor.get_actor_label()])
            if "AggregateSwatch" in combined:
                aggregate = c.get_material(0)
            for safe, key in prototype_keys.items():
                if (
                    safe == name
                    or safe == safe_name(actor.get_actor_label())
                    or safe == safe_name(c.get_name())
                ):
                    meshes[key] = c.static_mesh
            body = c.static_mesh.get_editor_property("body_setup")
            if body:
                body.set_editor_property(
                    "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
                )
                ASSETS.save_loaded_asset(c.static_mesh)
            c.set_collision_profile_name("BlockAll")
    if len(meshes) != len(prototype_keys):
        info = [
            {
                "actor": a.get_actor_label(),
                "components": [
                    {
                        "name": c.get_name(),
                        "mesh": c.static_mesh.get_name() if c.static_mesh else None,
                    }
                    for c in a.get_components_by_class(unreal.StaticMeshComponent)
                ],
            }
            for a in new_actors
        ]
        (ROOT / ".local/landscape-import-debug.json").write_text(json.dumps(info, indent=2))
        raise RuntimeError(
            f"Prototype import incomplete: {len(meshes)}/{len(prototype_keys)}; inspect debug report"
        )
    material_package = package + "/Materials/Native"
    grass = grass_material(material_package)
    living_lawn = garden_materials.scanned_surface(
        material_package, "M_LivingLawn", "Grass004", 1.4
    )
    stone = garden_materials.scanned_surface(
        material_package, "M_BlueGrayStone", "slate_floor_02", 1.2, tint=(0.58, 0.70, 0.78)
    )
    aggregate = garden_materials.scanned_surface(
        material_package, "M_ExposedAggregate", "pebble_embedded_pavement", 1.4
    )
    for c in components:
        for i, old in enumerate(c.get_materials()):
            if old and "LV3_LivingLawn" in old.get_name():
                c.set_material(i, living_lawn)
            if old and "LV3_SlateApproach" in old.get_name():
                c.set_material(i, stone)
    for key, mesh in meshes.items():
        spec = manifest["prototypes"][key]
        kind = spec["kind"]
        if kind == "grass":
            mesh.set_material(0, grass)
        elif kind != "pot":
            asset = next(
                (a for a in garden_materials.SCANS if spec["sourceName"].startswith(a)), None
            )
            material = (
                garden_materials.leaf(material_package, asset)
                if asset
                else garden_materials.petals(
                    material_package, spec["sourceName"].removeprefix("AzaleaFlowers_")
                )
            )
            for i in range(mesh.get_num_sections(0)):
                mesh.set_material(i, material)
        ASSETS.save_loaded_asset(mesh)
    cluster_class = unreal.load_class(None, "/Script/ClevelandReal.LandscapeCluster")
    if not cluster_class:
        raise RuntimeError("Compile the editor target with LandscapeCluster first")
    total = 0
    for key, records in manifest["instances"].items():
        if not records:
            continue
        actor = actors_api.spawn_actor_from_class(cluster_class, unreal.Vector())
        actor.set_actor_label(key.replace("PROTO_", "Garden_"))
        kind = manifest["prototypes"][key]["kind"]
        if kind == "grass":
            actor.set_editor_property("tags", ["ClevelandGrass"])
        elif kind != "pot":
            actor.set_editor_property("tags", ["ClevelandPlants"])
        c = actor.get_editor_property("instances")
        c.set_static_mesh(meshes[key])
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        end = manifest["prototypes"][key]["cullCm"]
        c.set_cull_distances(int(end * 0.8), end)
        transforms = []
        for record in records:
            x, y, z = record["position"]
            rotation = unreal.Rotator(pitch=0, yaw=-record["yaw"], roll=0)
            if "normal" in record:
                nx, ny, nz = record["normal"]
                tilt = unreal.MathLibrary.make_rot_from_z(unreal.Vector(nx, -ny, nz))
                rotation = unreal.MathLibrary.compose_rotators(rotation, tilt)
            transforms.append(
                unreal.Transform(
                    location=unreal.Vector(x * 100, -y * 100, z * 100),
                    rotation=rotation,
                    scale=unreal.Vector(*record["scale"]),
                )
            )
        c.add_instances(transforms, False, True)
        if c.get_instance_count() != len(records):
            raise RuntimeError("Instance count mismatch")
        total += len(records)
    # Prototype/swatch actors are authoring-only, never rendered at the origin.
    for c in components:
        if c.static_mesh in meshes.values() or "AggregateSwatch" in c.static_mesh.get_name():
            c.set_visibility(False, False)
            c.set_hidden_in_game(True, False)
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    replaced = []
    deck_count = 0
    tree_count = 0
    tree_specs = json.loads((ROOT / "design/site-registration.json").read_text())["trees"]
    for actor in original_actors:
        for c in actor.get_components_by_class(unreal.StaticMeshComponent):
            if not c.static_mesh:
                continue
            name = c.static_mesh.get_name()
            if name in ("SM_Vehicle_lane", "SM_Pedestrian_approach"):
                c.set_visibility(False, False)
                c.set_hidden_in_game(True, False)
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                replaced.append(name)
            if name == "SM_pool_deck":
                if not aggregate:
                    raise RuntimeError("Pool deck aggregate material missing")
                c.set_material(0, aggregate)
                deck_count += 1
        match = re.fullmatch(r"Estimated_tree_(\d+)", actor.get_actor_label())
        if match:
            x, y = tree_specs[int(match[1])]["center"]
            actor.add_actor_world_offset(
                unreal.Vector(0, 0, (grade(x, y) + 1.65) * 100), False, True
            )
            tree_count += 1
    if deck_count != 1 or len(replaced) != 2:
        raise RuntimeError(
            f"Existing surface replacements incomplete: {replaced}; decks {deck_count}"
        )
    levels.save_current_level()
    ASSETS.save_directory(package, only_if_is_dirty=True, recursive=True)
    report = {
        **previous,
        "map": target,
        "landscapeVersion": 3,
        "landscape": {
            "baseMap": previous["map"],
            "assetPackage": package,
            "instances": total,
            "prototypes": len(meshes),
            "replacedSurfaces": replaced,
            "aggregateDecks": deck_count,
            "treeGradeCorrections": tree_count,
            "status": "Cooked runtime collision and visual review pending",
        },
    }
    (ROOT / "reports/unreal-import.json").write_text(json.dumps(report, indent=2))
    config = ROOT / "runtime/ClevelandReal/Config/DefaultEngine.ini"
    config.write_text(
        re.sub(
            r"(?m)^(EditorStartupMap|GameDefaultMap)=.*$",
            lambda m: f"{m[1]}={target}",
            config.read_text(),
        )
    )
    unreal.log("LANDSCAPE_IMPORT_COMPLETE " + json.dumps(report["landscape"]))


if __name__ == "__main__":
    main()
