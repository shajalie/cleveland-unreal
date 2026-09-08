"""Preserve imported leaf textures while using Nanite-compatible cutout shading."""

import unreal
from materials import node, custom_input, color

EDIT = unreal.MaterialEditingLibrary
PACKAGE = "/Game/Cleveland/Materials/Native"


def native_leaf_instance(original):
    name = "MI_Cutout_" + original.get_name()
    existing = unreal.load_asset(f"{PACKAGE}/{name}")
    if existing:
        return existing
    base = original
    while isinstance(base, unreal.MaterialInstance):
        base = base.get_editor_property("parent")
    parent_path = f"{PACKAGE}/M_Cutout_{base.get_name()}"
    parent = unreal.load_asset(parent_path)
    if parent is None:
        parent = unreal.EditorAssetLibrary.duplicate_asset(base.get_path_name(), parent_path)
        if not parent:
            raise RuntimeError("Could not create a separate native foliage material")
        opacity = EDIT.get_material_property_input_node(parent, unreal.MaterialProperty.MP_OPACITY)
        output = EDIT.get_material_property_input_node_output_name(
            parent, unreal.MaterialProperty.MP_OPACITY
        )
        if opacity is None:
            raise RuntimeError("Imported leaf material has no opacity texture expression")
        EDIT.connect_material_property(opacity, output, unreal.MaterialProperty.MP_OPACITY_MASK)
        parent.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        parent.set_editor_property("two_sided", True)
        parent.set_editor_property("opacity_mask_clip_value", 0.33)
        parent.set_editor_property(
            "shading_model", unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE
        )
        color(parent, (0.12, 0.20, 0.045), unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
        position = node(parent, unreal.MaterialExpressionWorldPosition)
        clock = node(parent, unreal.MaterialExpressionTime, ignore_pause=False)
        strength = node(
            parent,
            unreal.MaterialExpressionScalarParameter,
            parameter_name="BreezeStrength",
            default_value=0.35,
        )
        breeze = node(
            parent,
            unreal.MaterialExpressionCustom,
            output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
            inputs=[custom_input("Position"), custom_input("Time"), custom_input("Strength")],
            code="""
float phase = dot(Position.xy, float2(0.013, 0.019));
float sway = sin(Time * 1.7 + phase) + 0.3 * sin(Time * 3.1 + phase * 2.3);
return Strength * float3(sway, 0.45 * cos(Time * 1.3 + phase), 0.06 * sway);
""",
        )
        for expression, input_name in [
            (position, "Position"),
            (clock, "Time"),
            (strength, "Strength"),
        ]:
            EDIT.connect_material_expressions(expression, "", breeze, input_name)
        EDIT.connect_material_property(breeze, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        EDIT.recompile_material(parent)
        unreal.EditorAssetLibrary.save_loaded_asset(parent)
    result = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, PACKAGE, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()
    )
    EDIT.set_material_instance_parent(result, parent)
    # The imported two-sided variants inherit parameters through several instances.
    # Resolve and copy those values before replacing that parent chain.
    for kind in ["scalar", "vector", "texture", "static_switch"]:
        names = getattr(EDIT, f"get_{kind}_parameter_names")(original)
        for parameter in names:
            value = getattr(EDIT, f"get_material_instance_{kind}_parameter_value")(
                original, parameter
            )
            if value is None:
                continue
            setter = getattr(EDIT, f"set_material_instance_{kind}_parameter_value")
            if kind == "static_switch":
                setter(result, parameter, value, update_material_instance=False)
            else:
                setter(result, parameter, value)
    EDIT.update_material_instance(result)
    unreal.EditorAssetLibrary.save_loaded_asset(result)
    return result


def configure(actors):
    replaced, meshes = set(), set()
    assignments = 0
    for actor in actors:
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            for index, original in enumerate(component.get_materials()):
                if not original:
                    continue
                name = original.get_name().lower()
                if not any(key in name for key in ["tree_small_02_leaves", "fir_tree_01_twig"]):
                    continue
                material = (
                    original if name.startswith("mi_cutout_") else native_leaf_instance(original)
                )
                component.set_material(index, material)
                if component.static_mesh and component.static_mesh not in meshes:
                    mesh = component.static_mesh
                    if mesh.get_material(index) != material:
                        mesh.set_material(index, material)
                    # Preserve leaf polygons in ray-tracing fallback geometry as well.
                    settings = mesh.get_editor_property("nanite_settings")
                    settings.set_editor_property(
                        "fallback_target", unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
                    )
                    settings.set_editor_property("fallback_relative_error", 0.0)
                    settings.set_editor_property("fallback_percent_triangles", 1.0)
                    mesh.set_editor_property("nanite_settings", settings)
                    meshes.add(mesh)
                component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                replaced.add(material.get_path_name())
                assignments += 1
    for mesh in meshes:
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    fallback = {mesh.get_name(): mesh.get_num_triangles(0) for mesh in meshes}
    if any(count < 1000000 for count in fallback.values()):
        raise RuntimeError(f"Tree ray-tracing fallback lost source leaf geometry: {fallback}")
    if assignments != 14:
        raise RuntimeError(f"Expected 14 tree cutout assignments, found {assignments}")
    return {
        "assignments": assignments,
        "materials": sorted(replaced),
        "rayTracingFallbackTriangles": fallback,
        "breeze": "Sub-centimeter procedural leaf movement; not a measured wind simulation",
    }
