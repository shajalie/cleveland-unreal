"""Export the authored scene through USD with pivots, units and scanned textures.

This prepares source data; it does not establish that Unreal imported it correctly.
"""

import json
from pathlib import Path

import bpy
from pxr import Usd, UsdGeom, Gf, Sdf, Tf

ROOT = Path(__file__).resolve().parents[1]


def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "SourceAssets/Cleveland-Reconstruction.blend"))
    output = ROOT / "SourceAssets/UnrealTransfer"
    output.mkdir(parents=True, exist_ok=True)
    # Unreal consumes static meshes for wicker, trim and rails, not Blender curve objects.
    bpy.ops.object.select_all(action="DESELECT")
    curves = [obj for obj in bpy.context.scene.objects if obj.type == "CURVE"]
    for obj in curves:
        obj.select_set(True)
    if curves:
        bpy.context.view_layer.objects.active = curves[0]
        bpy.ops.object.convert(target="MESH")
    bpy.ops.object.select_all(action="DESELECT")
    # Export each shared vegetation mesh once. Blender's USD instancing option
    # alone does not deduplicate separate objects that share one mesh datablock.
    bpy.context.view_layer.update()
    prototypes, tree_instances = {}, []
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH" or "tree_id" not in obj:
            continue
        key = obj.data.as_pointer()
        if key not in prototypes:
            prototypes[key] = obj.name
            continue
        tree_instances.append(
            {
                "name": obj.name,
                "prototype": prototypes[key],
                "matrix": [list(row) for row in obj.matrix_world],
                "treeId": int(obj["tree_id"]),
            }
        )
        bpy.data.objects.remove(obj, do_unlink=True)
    materials = []
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        shader = material.node_tree.nodes.get("Principled BSDF")
        if not shader:
            continue
        record = {
            "name": material.name,
            "baseColor": list(shader.inputs["Base Color"].default_value),
            "roughness": shader.inputs["Roughness"].default_value,
            "metallic": shader.inputs["Metallic"].default_value,
            "transmission": shader.inputs["Transmission Weight"].default_value,
            "ior": shader.inputs["IOR"].default_value,
            "repeatMeters": material.get("repeat_m", 1),
            "source": material.get("source", "Authored material"),
            "textureImages": [
                node.image.name
                for node in material.node_tree.nodes
                if node.type == "TEX_IMAGE" and node.image
            ],
        }
        materials.append(record)
        # USD understands a Mapping node, whereas the metric authoring graph used Vector Math.
        for node in list(material.node_tree.nodes):
            if node.type == "VECT_MATH" and node.operation == "SCALE":
                mapping = material.node_tree.nodes.new("ShaderNodeMapping")
                mapping.vector_type = "POINT"
                mapping.inputs["Scale"].default_value = (node.inputs[3].default_value,) * 3
                for link in list(node.inputs[0].links):
                    material.node_tree.links.new(link.from_socket, mapping.inputs["Vector"])
                for link in list(node.outputs[0].links):
                    material.node_tree.links.new(mapping.outputs["Vector"], link.to_socket)
                material.node_tree.nodes.remove(node)
    target = output / "Cleveland.usdc"
    bpy.ops.wm.usd_export(
        filepath=str(target),
        check_existing=False,
        export_animation=False,
        export_materials=True,
        export_textures=True,
        overwrite_textures=True,
        relative_paths=True,
        use_instancing=True,
        export_custom_properties=True,
        author_blender_name=True,
        export_lights=True,
        export_cameras=True,
        convert_world_material=False,
        export_subdivision="TESSELLATE",
        triangulate_meshes=True,
        root_prim_path="/Cleveland",
        convert_scene_units="METERS",
    )
    stage = Usd.Stage.Open(str(target))
    if not stage:
        raise RuntimeError("USD export could not be reopened")
    for instance in tree_instances:
        prototype = "/Cleveland/" + Tf.MakeValidIdentifier(instance["prototype"])
        if not stage.GetPrimAtPath(prototype):
            raise RuntimeError(f"Missing exported tree prototype: {prototype}")
        path = "/Cleveland/" + Tf.MakeValidIdentifier(instance["name"])
        prim = stage.DefinePrim(path, "Xform")
        prim.GetReferences().AddInternalReference(prototype)
        xform = UsdGeom.Xformable(prim)
        xform.ClearXformOpOrder()
        matrix = instance["matrix"]
        transform = Gf.Matrix4d(*[matrix[j][i] for i in range(4) for j in range(4)])
        # Distinct suffix avoids colliding with the prototype's inherited op.
        xform.AddTransformOp(opSuffix="instancePlacement").Set(transform)
        prim.CreateAttribute("userProperties:tree_id", Sdf.ValueTypeNames.Int).Set(
            instance["treeId"]
        )
        prim.SetInstanceable(True)
    stage.GetRootLayer().Save()
    units = UsdGeom.GetStageMetersPerUnit(stage)
    if abs(units - 1) > 1e-6:
        raise RuntimeError(f"Unexpected stage units: {units}")
    prims = list(stage.Traverse())
    doors = [
        str(prim.GetPath())
        for prim in prims
        if "_hinge" in prim.GetName()
        and "shower" not in prim.GetName().lower()
        and not prim.IsA(UsdGeom.Mesh)
    ]
    if not any("study_rear_door" in path for path in doors):
        raise RuntimeError("Rear door pivot missing from exported scene")
    report = {
        "file": "SourceAssets/UnrealTransfer/Cleveland.usdc",
        "bytes": target.stat().st_size,
        "metersPerUnit": units,
        "upAxis": str(UsdGeom.GetStageUpAxis(stage)),
        "meshPrims": sum(prim.IsA(UsdGeom.Mesh) for prim in prims),
        "instances": sum(prim.IsInstance() for prim in prims),
        "sharedTreePrototypes": len(prototypes),
        "doorPivots": doors,
        "materialCount": len(materials),
        "textures": len(list((output / "textures").glob("*"))),
        "nativeMaterialRequired": [
            material["name"] for material in materials if material["transmission"] > 0
        ],
        "materialLimitations": [
            "USD Preview Surface does not preserve Principled transmission; reconstruct glass and water in Unreal.",
            "Procedural water normals and foliage animation require native runtime materials.",
        ],
        "status": "Export validated; Unreal import and visual parity still require verification",
    }
    (output / "material-manifest.json").write_text(json.dumps(materials, indent=2))
    (ROOT / "reports/unreal-export.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
