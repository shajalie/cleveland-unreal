"""Physically scaled materials for the reconstruction and its review renders."""

from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]


def plain(name, color, roughness=0.5, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    mat.diffuse_color = (*color, 1)
    return mat


def scanned(name, asset, size=1, detail=False, tint=None):
    mat = plain(name, tint or (0.5, 0.5, 0.5))
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeVectorMath")
    mapping.operation = "SCALE"
    mapping.inputs[3].default_value = 1 / size
    links.new(coord.outputs["UV"], mapping.inputs[0])
    folder = ROOT / "reference/materials" / ("detail" if detail else "scanned")
    for suffix, socket in [
        ("diff", "Base Color"),
        ("rough", "Roughness"),
        ("normal" if detail else "nor_gl", "Normal"),
    ]:
        path = folder / (asset + "_" + suffix + ".jpg")
        if not path.exists():
            continue
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(path), check_existing=True)
        links.new(mapping.outputs[0], tex.inputs["Vector"])
        if suffix != "diff":
            tex.image.colorspace_settings.name = "Non-Color"
        if socket == "Normal":
            normal = nodes.new("ShaderNodeNormalMap")
            normal.inputs["Strength"].default_value = 0.65
            links.new(tex.outputs["Color"], normal.inputs["Color"])
            links.new(normal.outputs[0], shader.inputs[socket])
        elif tint and suffix == "diff":
            mix = nodes.new("ShaderNodeMixRGB")
            mix.blend_type = "MULTIPLY"
            mix.inputs[0].default_value = 0.55
            mix.inputs[2].default_value = (*tint, 1)
            links.new(tex.outputs["Color"], mix.inputs[1])
            links.new(mix.outputs[0], shader.inputs[socket])
        else:
            links.new(tex.outputs["Color"], shader.inputs[socket])
    mat["source"] = "https://polyhaven.com/a/" + asset
    mat["repeat_m"] = size
    return mat


def plaster():
    mat = scanned("Ivory hand-troweled plaster", "white_plaster_rough_02", 1.1, True)
    n = mat.node_tree.nodes
    p = n.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (0.78, 0.77, 0.73, 1)
    p.inputs["Roughness"].default_value = 0.86
    mat["reference_photos"] = "5,7,10,25"
    mat["fidelity"] = "Scanned relief approximation; not scanned from this house."
    return mat


def palette():
    glass = plain("Clear 4mm glass", (0.98, 0.99, 1), 0.03)
    p = glass.node_tree.nodes.get("Principled BSDF")
    p.inputs["Transmission Weight"].default_value = 1
    p.inputs["IOR"].default_value = 1.52
    water = plain("Pool water IOR 1.333", (0.77, 0.92, 0.98), 0.035)
    p = water.node_tree.nodes.get("Principled BSDF")
    p.inputs["Transmission Weight"].default_value = 1
    p.inputs["IOR"].default_value = 1.333
    out = water.node_tree.nodes.get("Material Output")
    vol = water.node_tree.nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = (0.35, 0.78, 0.85, 1)
    vol.inputs["Density"].default_value = 0.15
    water.node_tree.links.new(vol.outputs[0], out.inputs["Volume"])
    return dict(
        plaster=plaster(),
        stucco=scanned(
            "Exterior fine rough stucco", "white_stucco", 2, True, tint=(0.92, 0.89, 0.82)
        ),
        wood=scanned("Dark oak joinery", "fine_grained_wood", 1, True, tint=(0.65, 0.42, 0.20)),
        floor=scanned("Long oak floorboards", "wood_floor", 2, tint=(0.42, 0.31, 0.22)),
        tile=scanned("Terracotta terrace", "terracotta_floor_tiles", 1.5),
        brick=scanned("Brick thresholds", "brown_brick_02", 1.2),
        concrete=scanned("Aged concrete and limestone", "concrete_floor_worn_001", 2, True),
        leather=scanned("Warm brown leather", "brown_leather", 0.8, True),
        fabric=scanned("Woven patterned upholstery", "fabric_pattern_05", 0.8, True),
        iron=plain("Blackened iron", (0.018, 0.023, 0.021), 0.34, 0.65),
        brass=plain("Aged brass", (0.42, 0.27, 0.075), 0.29, 0.75),
        ivory=plain("Warm white painted cabinetry", (0.79, 0.77, 0.70), 0.42),
        rug=plain("Natural woven sisal", (0.40, 0.27, 0.13), 0.95),
        sage=plain("Sage upholstery", (0.21, 0.28, 0.17), 0.85),
        glass=glass,
        water=water,
        soil=plain("Soil", (0.06, 0.038, 0.019), 0.98),
        leaf=plain("Broadleaf foliage", (0.085, 0.19, 0.025), 0.63),
        asphalt=plain("Asphalt", (0.038, 0.039, 0.04), 0.93),
    )
