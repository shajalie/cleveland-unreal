"""Room-side paint follows wall openings, without sealing any doors or windows."""

import copy
from mathutils import Vector
from ..primitives import wall_with_openings
from .domestic import recolor


def paint_room(floor, room, material):
    poly = room["poly"]
    center = sum((Vector(p) for p in poly), Vector((0, 0))) / len(poly)
    for start, end in zip(poly, poly[1:] + poly[:1]):
        a, b = Vector(start), Vector(end)
        direction = (b - a).normalized()
        normal = Vector((-direction.y, direction.x))
        if normal.dot(center - a) < 0:
            normal = -normal
        for wall in floor["walls"]:
            wa, wb = Vector(wall["a"]), Vector(wall["b"])
            if abs(normal.dot(wa - a)) > 0.002 or abs(normal.dot(wb - a)) > 0.002:
                continue
            left, right = sorted([(wa - a).dot(direction), (wb - a).dot(direction)])
            left, right = max(0, left), min((b - a).length, right)
            if right - left < 0.02:
                continue
            offset = normal * ((0.125 if wall["ext"] else 0.075) + 0.004)
            skin = {
                "id": room["name"] + " wall finish",
                "ext": False,
                "thickness": 0.006,
                "a": list(a + direction * left + offset),
                "b": list(a + direction * right + offset),
                "holes": [],
            }
            for hole in wall["holes"]:
                h0, h1 = sorted([(Vector(hole[k]) - a).dot(direction) for k in ["a", "b"]])
                h0, h1 = max(left, h0), min(right, h1)
                if h1 - h0 <= 0.001:
                    continue
                cut = copy.deepcopy(hole)
                cut["a"] = list(a + direction * h0 + offset)
                cut["b"] = list(a + direction * h1 + offset)
                skin["holes"].append(cut)
            wall_with_openings(skin, floor["base"], floor["ceiling"], material)


def build(model, m):
    colors = {
        "Primary bedroom": (0.70, 0.55, 0.46),
        "Bedroom 2": (0.76, 0.71, 0.43),
        "Bedroom 3": (0.49, 0.48, 0.66),
    }
    floor = next(f for f in model["floors"] if f["id"] == "upper")
    for room in floor["rooms"]:
        if room["name"] in colors:
            material = recolor(
                m["plaster"], room["name"] + " reference wall paint", colors[room["name"]]
            )
            paint_room(floor, room, material)
