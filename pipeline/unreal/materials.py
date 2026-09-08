"""Native transmission and small pool ripples, absent from USD Preview Surface."""

import unreal

EDIT = unreal.MaterialEditingLibrary
PACKAGE = "/Game/Cleveland/Materials/Native"


def custom_input(name):
    value = unreal.CustomInput()
    value.set_editor_property("input_name", name)
    return value


def node(material, kind, **properties):
    result = EDIT.create_material_expression(material, kind)
    for name, value in properties.items():
        result.set_editor_property(name, value)
    return result


def scalar(material, value, output):
    expression = node(material, unreal.MaterialExpressionConstant, r=value)
    EDIT.connect_material_property(expression, "", output)
    return expression


def color(material, rgb, output=None):
    expression = node(
        material,
        unreal.MaterialExpressionConstant3Vector,
        constant=unreal.LinearColor(*rgb, 1),
    )
    if output is not None:
        EDIT.connect_material_property(expression, "", output)
    return expression


def create(name):
    path = f"{PACKAGE}/{name}"
    material = unreal.load_asset(path)
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, PACKAGE, unreal.Material, unreal.MaterialFactoryNew()
        )
    EDIT.delete_all_material_expressions(material)
    return material


def finish(material):
    EDIT.layout_material_expressions(material)
    EDIT.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def glass():
    material = create("M_ClearWindowGlass")
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("two_sided", True)
    material.set_editor_property(
        "translucency_lighting_mode",
        unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING,
    )
    color(material, (0.98, 0.99, 1.0), unreal.MaterialProperty.MP_BASE_COLOR)
    scalar(material, 0.03, unreal.MaterialProperty.MP_ROUGHNESS)
    scalar(material, 0.0, unreal.MaterialProperty.MP_METALLIC)
    scalar(material, 0.0, unreal.MaterialProperty.MP_OPACITY)
    scalar(material, 1.52, unreal.MaterialProperty.MP_REFRACTION)
    return finish(material)


def pool_water():
    material = create("M_PoolWater")
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property(
        "shading_model", unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER
    )
    color(material, (0.005, 0.015, 0.02), unreal.MaterialProperty.MP_BASE_COLOR)
    scalar(material, 0.035, unreal.MaterialProperty.MP_ROUGHNESS)
    scalar(material, 0.0, unreal.MaterialProperty.MP_METALLIC)
    scalar(material, 0.1, unreal.MaterialProperty.MP_OPACITY)
    water = node(material, unreal.MaterialExpressionSingleLayerWaterMaterialOutput)
    scattering = color(material, (0.00012, 0.00018, 0.00021))
    absorption = color(material, (0.004, 0.001, 0.0004))
    EDIT.connect_material_expressions(scattering, "", water, "ScatteringCoefficients")
    EDIT.connect_material_expressions(absorption, "", water, "AbsorptionCoefficients")
    position = node(material, unreal.MaterialExpressionWorldPosition)
    time = node(material, unreal.MaterialExpressionTime, ignore_pause=False)
    # Analytic slopes of three small waves. World position is in centimeters.
    # These alter surface normals, not pool level or the architectural basin.
    normal = node(
        material,
        unreal.MaterialExpressionCustom,
        output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        inputs=[custom_input("Position"), custom_input("Time")],
        code="""
float2 p = Position.xy * 0.01;
float a = dot(p, float2(8.0, 2.2)) - Time * 2.1;
float b = dot(p, float2(-3.1, 10.0)) - Time * 2.8;
float c = dot(p, float2(18.0, 13.0)) - Time * 4.2;
float2 slope = 0.003 * cos(a) * float2(8.0, 2.2)
             + 0.0018 * cos(b) * float2(-3.1, 10.0)
             + 0.0007 * cos(c) * float2(18.0, 13.0);
return normalize(float3(-slope, 1.0));
""",
    )
    EDIT.connect_material_expressions(position, "", normal, "Position")
    EDIT.connect_material_expressions(time, "", normal, "Time")
    EDIT.connect_material_property(normal, "", unreal.MaterialProperty.MP_NORMAL)
    return finish(material)


def replace_transmission(actors):
    replacements = {"Clear_4mm_glass": glass(), "Pool_water_IOR": pool_water()}
    counts = dict.fromkeys(replacements, 0)
    for actor in actors:
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            for index, original in enumerate(component.get_materials()):
                if not original:
                    continue
                for name, material in replacements.items():
                    if name.lower() in original.get_name().lower() or original == material:
                        component.set_material(index, material)
                        counts[name] += 1
    if not all(counts.values()):
        raise RuntimeError(f"Transmission material assignment incomplete: {counts}")
    return counts
