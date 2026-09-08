"""Photograph-informed topology with coherent metric heights and circulation.

The earlier trace provides relative positions, not authoritative dimensions.
Shared-wall anchor transforms preserve topology while correcting its oversized
living room to the approximate dimension printed on listing plan 55.
"""

from pathlib import Path
import copy
import json

ROOT = Path(__file__).resolve().parents[2]
LEVELS = {
    "main": 0.0,
    "upper": 3.12,
    "lower": -2.72,
    "porch": -0.09,
    "front_grade": -0.60,
    "sitting": -0.45,
    "dining_terrace": -1.11,
    "pool_deck": -1.62,
}


def interpolate(value, anchors):
    for (a, x), (b, y) in zip(anchors, anchors[1:]):
        if value <= b:
            return x + (value - a) / (b - a) * (y - x)
    (a, x), (b, y) = anchors[-2:]
    return x + (value - a) / (b - a) * (y - x)


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def build_layout():
    baseline = json.loads((ROOT / "reference/model-data.json").read_text())["indoor"]
    floors = copy.deepcopy(baseline["floors"])
    x_anchors = [
        (4.359, -5.50),
        (7.915, -2.75),
        (9.515, -1.46),
        (11.915, 0.80),
        (12.449, 1.1044),
        (17.071, 4.7624),
    ]
    y_anchors = [(13.655, 0), (18.473, 4.166), (22.024, 7.62), (26.335, 11.2776)]
    for index, floor in enumerate(floors):
        xa = (
            x_anchors
            if index == 0
            else [(4.359, -5.5), (7.115, -2.75), (9.337, -1.46), (12.182, 0.80), (17.16, 4.7624)]
        )
        ya = (
            y_anchors
            if index == 0
            else [(13.655, 0), (16.974, 2.8), (19.357, 4.7244), (22.08, 7.62), (26.505, 11.2776)]
        )

        def transform(point):
            return [round(interpolate(point[0], xa), 5), round(interpolate(point[1], ya), 5)]

        floor["id"] = "main" if index == 0 else "upper"
        floor["base"] = LEVELS[floor["id"]]
        floor["ceiling"] = 2.8956 if index == 0 else 2.7432
        floor["outline"] = [transform(p) for p in floor["outline"]]
        for room in floor["rooms"]:
            room["poly"] = [transform(p) for p in room["poly"]]
            room["label"] = transform(room["label"])
            room["evidence"] = "55"
        for wi, wall in enumerate(floor["walls"]):
            wall["a"], wall["b"] = transform(wall["a"]), transform(wall["b"])
            wall["id"] = floor["id"] + f"_wall_{wi:02d}"
            for hi, hole in enumerate(wall["holes"]):
                hole["a"], hole["b"] = transform(hole["a"]), transform(hole["b"])
                hole["id"] = floor["id"] + f"_opening_{wi:02d}_{hi:02d}"
                hole["operable"] = False
                if "door" in hole.get("type", "").lower():
                    hole.update(operable=True, window=False, floorGlass=True)
        if index == 0:
            # Actual rear study portal (photos 10/14/47), not a window collider.
            study = floor["walls"][2]["holes"][0]
            study.update(
                id="study_rear_door",
                head=2.44,
                arch=True,
                operable=True,
                sill=0,
                door_width=1.26,
                leaf_count=2,
                evidence=[10, 14, 47],
            )
            mid = (study["a"][0] + study["b"][0]) / 2
            study["a"], study["b"] = [mid - 0.63, 11.2776], [mid + 0.63, 11.2776]
            front = floor["walls"][0]["holes"][-1]
            front.update(id="front_door", operable=True, sill=0, head=2.54, evidence=[3, 4, 5])
            dining = floor["walls"][0]["holes"][0]
            dining.update(
                id="dining_porch_doors", operable=True, sill=0, head=2.3, evidence=[15, 16, 17]
            )
            # Photos 07/08 show one paired French door in the living front wall.
            floor["walls"][0]["holes"] = [
                dining,
                front,
                {
                    "id": "living_porch_doors",
                    "a": [2.21, 0],
                    "b": [3.63, 0],
                    "window": False,
                    "floorGlass": True,
                    "operable": True,
                    "sill": 0,
                    "head": 2.3,
                    "leaf_count": 2,
                    "evidence": [7, 8],
                },
            ]
            # Two side windows flank the fireplace; the coarse trace overstated their width.
            floor["walls"][1]["holes"][0].update(
                a=[4.7624, 6.73], b=[4.7624, 5.68], sill=0.62, head=2.38, evidence=[7, 8]
            )
            floor["walls"][1]["holes"][1].update(
                a=[4.7624, 3.60], b=[4.7624, 2.18], sill=0.62, head=2.38, evidence=[7, 8]
            )
            # A real kitchen side exit is visible on the inside face of the wing.
            floor["walls"][5]["holes"] = [
                {
                    "id": "kitchen_rear_door",
                    "a": [-2.75, 10.12],
                    "b": [-2.75, 11.02],
                    "window": False,
                    "floorGlass": True,
                    "operable": True,
                    "sill": 0,
                    "head": 2.16,
                    "evidence": [47, 52],
                    "type": "Kitchen terrace door",
                },
                {
                    "id": "kitchen_court_window",
                    "a": [-2.75, 8.2],
                    "b": [-2.75, 9.45],
                    "window": True,
                    "sill": 0.98,
                    "head": 2.3,
                    "evidence": [18, 21],
                },
            ]
            # Main opening reads as a doorway, not a removed whole wall.
            floor["walls"][9]["holes"] = [
                {
                    "id": "foyer_living",
                    "a": [0.8, 0.95],
                    "b": [0.8, 2.8],
                    "window": False,
                    "sill": 0,
                    "head": 2.55,
                    "evidence": [5, 6, 25],
                }
            ]
    lower_outline = rect(-5.5, 0, -1.46, 11.2776)
    lower_walls = []
    for i, (a, b) in enumerate(zip(lower_outline, lower_outline[1:] + lower_outline[:1])):
        lower_walls.append({"id": f"lower_wall_{i}", "a": a, "b": b, "ext": True, "holes": []})
    lower_walls[2]["holes"] = [
        {
            "id": "basement_garden_door",
            "a": [-4.95, 11.2776],
            "b": [-3.9, 11.2776],
            "window": False,
            "floorGlass": True,
            "operable": True,
            "sill": 0,
            "head": 2.10,
            "type": "Lower-level garden exit",
            "evidence": [51, 52],
        }
    ]
    floors.append(
        {
            "id": "lower",
            "name": "Lower recreation level",
            "base": -2.72,
            "ceiling": 2.35,
            "outline": lower_outline,
            "rooms": [
                {
                    "name": "Recreation",
                    "poly": lower_outline,
                    "label": [-3.48, 5.7],
                    "evidence": [43, 44, 55],
                    "uncertainty": "Envelope inferred; partition survey unavailable",
                }
            ],
            "walls": lower_walls,
        }
    )
    surfaces = [
        {"id": "porch", "z": -0.09, "poly": rect(-5.85, -3.2, 7.8, 0)},
        {"id": "front_grade", "z": -0.60, "poly": rect(-8, -17, 8, -3.71)},
        {"id": "sitting", "z": -0.45, "poly": rect(0.30, 11.2776, 5.5, 15.1)},
        {
            "id": "dining_terrace",
            "z": -1.11,
            "poly": [
                [-2.75, 7.62],
                [1.1044, 7.62],
                [1.1044, 11.2776],
                [0.30, 11.2776],
                [0.30, 14.1],
                [-2.75, 14.1],
            ],
        },
        {"id": "pool_deck", "z": -1.62, "poly": rect(-8.0, 14.1, 5.5, 22.2)},
        {"id": "basement_areaway", "z": -2.72, "poly": rect(-5.5, 11.2776, -2.75, 14.1)},
        {"id": "kitchen_landing", "z": -0.12, "poly": rect(-2.75, 9.97, -1.45, 11.2776)},
        {"id": "study_threshold", "z": 0, "poly": rect(2.27, 11.2776, 3.60, 11.55)},
    ]
    stairs = [
        {
            "id": "front_steps",
            "from": "front_grade",
            "to": "porch",
            "low": -0.6,
            "high": -0.09,
            "start": [-0.20, -4.01],
            "direction": [0, 1],
            "width": 1.90,
            "tread": 0.27,
            "risers": 3,
            "evidence": [3],
        },
        {
            "id": "study_steps",
            "from": "sitting",
            "to": "main",
            "low": -0.45,
            "high": 0,
            "start": [2.94, 12.36],
            "direction": [0, -1],
            "width": 1.40,
            "tread": 0.27,
            "risers": 3,
            "evidence": [47],
        },
        {
            "id": "terrace_link",
            "from": "dining_terrace",
            "to": "sitting",
            "low": -1.11,
            "high": -0.45,
            "start": [-0.78, 12.55],
            "direction": [1, 0],
            "width": 1.1,
            "tread": 0.27,
            "risers": 4,
            "evidence": [51, 52],
        },
        {
            "id": "pool_steps",
            "from": "pool_deck",
            "to": "dining_terrace",
            "low": -1.62,
            "high": -1.11,
            "start": [-1.66, 14.91],
            "direction": [0, -1],
            "width": 1.24,
            "tread": 0.27,
            "risers": 3,
            "evidence": [52],
        },
        {
            "id": "kitchen_steps",
            "from": "dining_terrace",
            "to": "kitchen_landing",
            "low": -1.11,
            "high": -0.12,
            "start": [-1.92, 12.95],
            "direction": [0, -1],
            "width": 1.06,
            "tread": 0.28,
            "risers": 6,
            "evidence": [47, 52],
        },
        {
            "id": "areaway_steps",
            "from": "basement_areaway",
            "to": "pool_deck",
            "low": -2.72,
            "high": -1.62,
            "start": [-3.32, 12.14],
            "direction": [0, 1],
            "width": 1.05,
            "tread": 0.28,
            "risers": 7,
            "evidence": [51, 52],
        },
        {
            "id": "main_stair",
            "from": "main",
            "to": "upper",
            "low": 0,
            "high": 3.12,
            "start": [0.13, 1.40],
            "direction": [0, 1],
            "width": 1.10,
            "tread": 0.27,
            "risers": 18,
            "evidence": [5, 6, 25, 26],
        },
    ]
    portals = [
        {"id": "front_door", "spaces": ["main", "porch"]},
        {"id": "dining_porch_doors", "spaces": ["main", "porch"]},
        {"id": "study_rear_door", "spaces": ["main", "sitting"]},
        {"id": "kitchen_rear_door", "spaces": ["main", "kitchen_landing"]},
        {"id": "basement_garden_door", "spaces": ["lower", "basement_areaway"]},
    ]
    return {
        "units": "meters",
        "coordinateSystem": "+X front-right, +Y rear, +Z up",
        "levelHeights": LEVELS,
        "floors": floors,
        "surfaces": surfaces,
        "stairs": stairs,
        "portals": portals,
        "sunOrientation": {
            "ux": baseline["ux"],
            "uy": baseline["uy"],
            "latitude": baseline["lat"],
            "longitude": baseline["lon"],
        },
        "assumptions": [
            "Door and stair heights are inferred from photographs, not surveyed.",
            "Garden levels are constrained for connectivity; exact elevations remain estimates.",
            "Kitchen and areaway riser counts are unresolved; modeled flights use consistent safe geometry.",
            "Lower-level partitions and internal basement stair are not yet resolved.",
        ],
    }


if __name__ == "__main__":
    (ROOT / "design/spatial-model.json").write_text(json.dumps(build_layout(), indent=2))
