"""Visible pictures, blinds and dining pendant from the listing references.

Artwork uses UV coordinates into the unmodified reference image. This is an
appearance proxy for a small decorative surface, not a calibrated albedo scan.
"""

import math
from pathlib import Path
import bpy
from ..primitives import box, cylinder_between, annotate
from ..furnishings import group
from ..materials import plain
from .fixtures import lathe

ROOT = Path(__file__).resolve().parents[3]


def picture(name, photo, corners, position, size, angle, m, gold=False):
    before = set(bpy.data.objects)
    w, h = size
    image = bpy.data.images.load(
        str(ROOT / "reference/photos" / f"{photo:02d}.webp"), check_existing=True
    )
    material = plain(name + " photographed artwork", (0.7, 0.7, 0.7), 0.76)
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    material.node_tree.links.new(
        texture.outputs["Color"],
        material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"],
    )
    mesh = bpy.data.meshes.new(name + " canvas")
    mesh.from_pydata(
        [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.update()
    uv = mesh.uv_layers.new(name="ReferenceArtworkUV")
    for index, (x, y) in enumerate(corners):
        uv.data[index].uv = (x / image.size[0], 1 - y / image.size[1])
    canvas = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.collection.objects.link(canvas)
    mesh.materials.append(material)
    frame = m["brass"] if gold else m["wood"]
    box(name + " backing", (0, 0.012, 0), (w, 0.019, h), frame)
    for x in [-w / 2, w / 2]:
        box(name + " frame side", (x, -0.007, 0), (0.025, 0.035, h + 0.025), frame, 0.003)
    for z in [-h / 2, h / 2]:
        box(name + " frame rail", (0, -0.007, z), (w, 0.035, 0.025), frame, 0.003)
    root = group(name, set(bpy.data.objects) - before, position, angle)
    annotate(root, "reference_artwork", [photo])
    root["texture_status"] = "UV projection of pictured artwork; retains source photograph lighting"


def build(m):
    picture(
        "Dining fruit still life",
        15,
        [(758, 386), (914, 382), (914, 277), (758, 311)],
        (-3.26, 4.075, 1.70),
        (1.04, 0.56),
        0,
        m,
        True,
    )
    picture(
        "Blue bedroom landscape",
        35,
        [(602, 364), (805, 366), (809, 248), (602, 246)],
        (3.52, 7.715, 4.99),
        (0.76, 0.43),
        math.pi,
        m,
        True,
    )
    picture(
        "Powder New Yorker print",
        23,
        [(652, 335), (718, 330), (719, 226), (651, 232)],
        (-1.22, 7.44, 1.64),
        (0.24, 0.34),
        0,
        m,
    )
    # Slats modeled separately so direct light can pass through their real gaps.
    for i in range(44):
        z = 1.04 + i * 0.027
        slat = box(
            "Powder Venetian blind slat",
            (-0.565, 7.42, z),
            (0.78, 0.025, 0.0024),
            m["ivory"],
            0.001,
        )
        slat.rotation_euler.x = math.radians(20)
    box("Powder blind headrail", (-0.565, 7.42, 2.25), (0.80, 0.037, 0.034), m["ivory"])
    for x in [-0.83, -0.30]:
        cylinder_between(
            "Powder blind lift cord", (x, 7.400, 1.025), (x, 7.400, 2.23), 0.0012, m["towel"], 8
        )
    # Drum pendant visible in photographs 15–17.
    cylinder_between(
        "Dining pendant suspension", (-3.55, 2.10, 2.16), (-3.55, 2.10, 2.88), 0.008, m["steel"]
    )
    lathe(
        "Dining pendant fabric drum",
        [(1, 0), (1, 0.28), (0.98, 0.28), (0.98, 0), (1, 0)],
        (-3.55, 2.10, 1.98),
        (0.31, 0.31),
        m["towel"],
    )
    data = bpy.data.lights.new("Dining pendant light", "POINT")
    data.energy, data.shadow_soft_size = 24, 0.12
    data.color = (1, 0.82, 0.65)
    obj = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = (-3.55, 2.10, 2.12)
