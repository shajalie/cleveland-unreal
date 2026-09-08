"""Explicit PBR texture channels for garden assets, independent of USD master switches."""

from pathlib import Path
import unreal
from materials import node, custom_input, color, scalar

ROOT = Path(__file__).resolve().parents[2]
EDIT = unreal.MaterialEditingLibrary
ASSETS = unreal.EditorAssetLibrary
SCANS = ("shrub_04", "fern_02", "periwinkle_plant", "grass_bermuda_01", "flower_gazania")


def create(package, name, foliage=False):
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, package, unreal.Material, unreal.MaterialFactoryNew()
    )
    mat.set_editor_property("used_with_instanced_static_meshes", True)
    if foliage:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        mat.set_editor_property("opacity_mask_clip_value", 0.33)
        mat.set_editor_property("two_sided", True)
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    scalar(mat, 0.2, unreal.MaterialProperty.MP_SPECULAR)
    return mat


def texture(package, path, channel):
    name = "T_" + path.stem
    asset = unreal.load_asset(package + "/Textures/" + name)
    if asset is None:
        task = unreal.AssetImportTask()
        task.filename = str(path)
        task.destination_path = package + "/Textures"
        task.destination_name = name
        task.automated = True
        task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset = unreal.load_asset(package + "/Textures/" + name)
    if not asset:
        raise RuntimeError("Missing garden texture " + str(path))
    asset.set_editor_property("srgb", channel == "color")
    compression = unreal.TextureCompressionSettings.TC_DEFAULT
    if channel == "normal":
        compression = unreal.TextureCompressionSettings.TC_NORMALMAP
        asset.set_editor_property(
            "flip_green_channel", True
        )  # OpenGL source -> Unreal normal convention.
    elif channel == "mask":
        compression = unreal.TextureCompressionSettings.TC_MASKS
    asset.set_editor_property("compression_settings", compression)
    ASSETS.save_loaded_asset(asset)
    return asset


def sample(mat, asset, channel):
    kind = {
        "color": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
        "normal": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
        "mask": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    }[channel]
    return node(mat, unreal.MaterialExpressionTextureSample, texture=asset, sampler_type=kind)


def finish(mat):
    EDIT.layout_material_expressions(mat)
    EDIT.recompile_material(mat)
    ASSETS.save_loaded_asset(mat)
    return mat


def leaf(package, asset):
    cached = unreal.load_asset(f"{package}/M_Leaf_{asset}")
    if cached:
        return cached
    mat = create(package, "M_Leaf_" + asset, foliage=True)
    folder = ROOT / ".local/model-assets" / asset / "textures"
    diffuse = sample(mat, texture(package, folder / f"{asset}_diff_1k.jpg", "color"), "color")
    normal = sample(mat, texture(package, folder / f"{asset}_nor_gl_1k.jpg", "normal"), "normal")
    rough = sample(mat, texture(package, folder / f"{asset}_arm_1k.jpg", "mask"), "mask")
    masks = list(folder.glob(f"{asset}_*alpha.png"))
    if len(masks) != 1:
        raise RuntimeError(f"Expected one unique opacity map for {asset}, found {len(masks)}")
    alpha = sample(mat, texture(package, masks[0], "mask"), "mask")
    EDIT.connect_material_property(diffuse, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    EDIT.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    EDIT.connect_material_property(rough, "G", unreal.MaterialProperty.MP_ROUGHNESS)
    EDIT.connect_material_property(alpha, "R", unreal.MaterialProperty.MP_OPACITY_MASK)
    subsurface = node(mat, unreal.MaterialExpressionMultiply, const_b=0.35)
    EDIT.connect_material_expressions(diffuse, "RGB", subsurface, "A")
    EDIT.connect_material_property(subsurface, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    position = node(mat, unreal.MaterialExpressionWorldPosition)
    time = node(mat, unreal.MaterialExpressionTime)
    strength = node(
        mat,
        unreal.MaterialExpressionScalarParameter,
        parameter_name="BreezeStrength",
        default_value=1.0,
    )
    breeze = node(
        mat,
        unreal.MaterialExpressionCustom,
        output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        inputs=[custom_input("Position"), custom_input("Time"), custom_input("Strength")],
        code="""
float phase=dot(Position.xy,float2(.013,.019));
float sway=sin(Time*1.7+phase)+.3*sin(Time*3.1+phase*2.3);
return Strength*.35*float3(sway,.45*cos(Time*1.3+phase),.06*sway);
""",
    )
    EDIT.connect_material_expressions(position, "", breeze, "Position")
    EDIT.connect_material_expressions(time, "", breeze, "Time")
    EDIT.connect_material_expressions(strength, "", breeze, "Strength")
    EDIT.connect_material_property(breeze, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    return finish(mat)


def petals(package, name):
    mat = create(package, "M_Petals_" + name, foliage=True)
    rgb = {"Pink": (0.6, 0.028, 0.17), "White": (0.78, 0.76, 0.68), "Coral": (0.5, 0.025, 0.012)}[
        name
    ]
    color(mat, rgb, unreal.MaterialProperty.MP_BASE_COLOR)
    color(mat, tuple(v * 0.2 for v in rgb), unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    scalar(mat, 0.7, unreal.MaterialProperty.MP_ROUGHNESS)
    scalar(mat, 1, unreal.MaterialProperty.MP_OPACITY_MASK)
    return finish(mat)


def scanned_surface(package, name, asset, repeat_meters, tint=None):
    mat = create(package, name)
    uv = node(
        mat,
        unreal.MaterialExpressionTextureCoordinate,
        u_tiling=1 / repeat_meters,
        v_tiling=1 / repeat_meters,
    )
    for suffix, channel, output in [
        ("diff", "color", unreal.MaterialProperty.MP_BASE_COLOR),
        ("nor_gl", "normal", unreal.MaterialProperty.MP_NORMAL),
        ("rough", "mask", unreal.MaterialProperty.MP_ROUGHNESS),
    ]:
        tex = sample(
            mat,
            texture(
                package, ROOT / "reference/materials/landscape" / f"{asset}_{suffix}.jpg", channel
            ),
            channel,
        )
        EDIT.connect_material_expressions(uv, "", tex, "Coordinates")
        if suffix == "diff" and tint:
            shade = node(
                mat,
                unreal.MaterialExpressionCustom,
                output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
                inputs=[custom_input("C")],
                code=f"return dot(C,float3(.2126,.7152,.0722))*float3({tint[0]},{tint[1]},{tint[2]});",
            )
            EDIT.connect_material_expressions(tex, "RGB", shade, "C")
            EDIT.connect_material_property(shade, "", output)
        else:
            EDIT.connect_material_property(tex, "R" if channel == "mask" else "RGB", output)
    return finish(mat)
