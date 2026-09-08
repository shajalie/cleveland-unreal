"""Landscape v3, in model metres (+Y rear). Heights remain photo estimates."""

import math

HOUSE = [
    (-5.5, 0),
    (4.7624, 0),
    (4.7624, 11.2776),
    (1.1044, 11.2776),
    (1.1044, 7.62),
    (-2.75, 7.62),
    (-2.75, 11.2776),
    (-5.5, 11.2776),
]
AREAWAY = [(-5.5, 11.2776), (-2.75, 11.2776), (-2.75, 14.1), (-5.5, 14.1)]
POOL = [(-7.848, 16.976), (-1.752, 16.976), (-1.752, 20.024), (-7.848, 20.024)]
DRIVE = [
    (5.35, -16),
    (9.05, -16),
    (8.95, -10),
    (8.55, -6),
    (7.56, -2.7),
    (7.56, 0.08),
    (4.76, 0.08),
    (4.76, -2.8),
    (5.1, -7),
]
PATH = [
    (-0.2, -3.9),
    (-0.2, -4.5),
    (0.2, -5.1),
    (1.4, -5.8),
    (2.7, -7),
    (3.8, -9),
    (4.65, -11.4),
    (5.0, -14.8),
]
# Curved raised beds beside the terraces, leaving the existing basement stairs open.
REAR_BEDS = [
    {
        "id": "east_terrace",
        "z": -0.47,
        "poly": [
            (0.32, 15.10),
            (5.52, 15.10),
            (5.8, 16.5),
            (5.25, 17.2),
            (4.3, 17.35),
            (3.1, 17.1),
            (1.7, 16.65),
            (0.32, 16.0),
        ],
    },
    {
        "id": "west_terrace",
        "z": -0.90,
        "poly": [
            (-9.4, 10.8),
            (-5.53, 10.8),
            (-5.53, 14.12),
            (-5.9, 14.65),
            (-6.85, 15.25),
            (-8.0, 15.8),
            (-9.4, 15.85),
        ],
    },
]


def soften_corners(ring, fraction=0.08):
    """Round the planter silhouette without moving its long retaining edges."""
    result = []
    for a, b in zip(ring, ring[1:] + ring[:1]):
        result += [
            tuple(a[i] * (1 - fraction) + b[i] * fraction for i in range(2)),
            tuple(a[i] * fraction + b[i] * (1 - fraction) for i in range(2)),
        ]
    return result


for bed in REAR_BEDS:
    bed["poly"] = soften_corners(soften_corners(bed["poly"]), 0.15)


def inside(x, y, ring):
    result = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            result = not result
    return result


def segment_distance(x, y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - a[0] - t * dx, y - a[1] - t * dy)


def path_distance(x, y):
    return min(segment_distance(x, y, a, b) for a, b in zip(PATH, PATH[1:]))


def grade(x, y):
    """Continuous side grades meeting the existing porch/terrace elevations."""
    if y <= 0:
        return -0.60 if y > -15 else -0.60 - min(0.25, (-15 - y) * 0.035)
    if y < 11.28:
        return -0.60 + (y / 11.28) * (-0.40 if x < 0 else 0.11)
    if y < 15.1:
        # Lower patio ground stays below the slabs and stair treads.
        if -5.5 < x < 0.30:
            return -1.65
        return -1.0 if x < 0 else -0.49
    if x > 5.5 and y < 22.2:
        return -0.49 - (y - 15.1) / 7.1 * 1.17
    if x < -8 and y < 17.0:
        return -1.0 - (y - 15.1) / 1.9 * 0.66
    return -1.66 if y < 23 else -1.66 - (y - 23) * 0.055


def excluded(x, y, margin=0):
    return any(inside(x, y, p) for p in (HOUSE, AREAWAY, POOL)) or (
        margin > 0
        and any(
            segment_distance(x, y, a, b) < margin
            for p in (HOUSE, AREAWAY, POOL)
            for a, b in zip(p, p[1:] + p[:1])
        )
    )


def front_bed(x, y):
    return ((-6.2 < x < -1.3) or (1.1 < x < 4.3)) and -5.3 < y < -3.5


def lawn(x, y, margin=0):
    if excluded(x, y, 0.30 + margin) or inside(x, y, DRIVE) or path_distance(x, y) < 0.7 + margin:
        return False
    if any(inside(x, y, b["poly"]) for b in REAR_BEDS) or front_bed(x, y):
        return False
    front = -9.0 + margin < x < 5.5 - margin and -13.65 + margin < y < -3.85 - margin
    rear = 5.95 + margin < x < 9.15 - margin and 10.7 + margin < y < 21.7 - margin
    side = 5.8 + margin < x < 8.9 - margin and 0.4 + margin < y < 10.7 - margin
    return front or rear or side


def bed_height(x, y):
    for bed in REAR_BEDS:
        if inside(x, y, bed["poly"]):
            return bed["z"]
    return grade(x, y)


def planting(x, y):
    if excluded(x, y, 0.4) or path_distance(x, y) < 0.9 or inside(x, y, DRIVE):
        return False
    if any(inside(x, y, b["poly"]) for b in REAR_BEDS):
        return True
    return (-10.2 < x < -6.2 and -10 < y < 16) or (9.3 < x < 10.1 and -3 < y < 22)


# Walking probes use actual capsule movement, including former uncovered areas.
WALK_ROUTES = [
    {"id": "front_lawn", "start": [-4, -11, -0.60], "end": [-4, -6, -0.60]},
    {"id": "driveway", "start": [6.2, -12, -0.58], "end": [6.2, -4, -0.58]},
    {"id": "right_side", "start": [8, 1, -0.59], "end": [8, 10, -0.50]},
    {"id": "rear_lawn", "start": [8, 12, -0.49], "end": [8, 20, -1.30]},
    {"id": "pool_deck", "start": [-0.8, 18, -1.62], "end": [-0.8, 21, -1.62]},
    {"id": "left_side", "start": [-7, 1, -0.64], "end": [-7, 9, -0.92]},
]
