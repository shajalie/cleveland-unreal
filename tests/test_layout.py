"""Check architectural constraints that a good-looking render cannot establish."""

from pathlib import Path
import sys
import unittest
import math

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from geometry.layout import build_layout


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = build_layout()

    def test_all_levels_are_reachable_through_real_connections(self):
        graph = {}
        for edge in self.model["stairs"]:
            a, b = edge["from"], edge["to"]
            graph.setdefault(a, set()).add(b)
            graph.setdefault(b, set()).add(a)
        for door in self.model["portals"]:
            a, b = door["spaces"]
            graph.setdefault(a, set()).add(b)
            graph.setdefault(b, set()).add(a)
        seen = {"main"}
        pending = ["main"]
        while pending:
            for other in graph.get(pending.pop(), set()) - seen:
                seen.add(other)
                pending.append(other)
        self.assertTrue(
            {"main", "upper", "lower", "porch", "pool_deck", "sitting", "dining_terrace"} <= seen
        )

    def test_risers_are_consistent_and_no_floating_stair_end(self):
        levels = {x["id"]: x["z"] for x in self.model["surfaces"]}
        levels.update({x["id"]: x["base"] for x in self.model["floors"]})
        for stair in self.model["stairs"]:
            with self.subTest(stair=stair["id"]):
                rise = (stair["high"] - stair["low"]) / stair["risers"]
                self.assertGreaterEqual(rise, 0.12)
                self.assertLessEqual(rise, 0.20)
                self.assertGreaterEqual(stair["tread"], 0.25)
                self.assertAlmostEqual(stair["low"], levels[stair["from"]])
                self.assertAlmostEqual(stair["high"], levels[stair["to"]])
                self.assertAlmostEqual(math.hypot(*stair["direction"]), 1)

    def test_operable_rear_doors_are_not_marked_as_windows(self):
        openings = {
            h["id"]: h for f in self.model["floors"] for w in f["walls"] for h in w["holes"]
        }
        for name in ["study_rear_door", "kitchen_rear_door", "basement_garden_door"]:
            self.assertIn(name, openings)
            self.assertTrue(openings[name]["operable"])
            self.assertFalse(openings[name]["window"])
            self.assertEqual(openings[name]["sill"], 0)

    def test_living_room_uses_printed_plan_dimensions(self):
        room = next(r for r in self.model["floors"][0]["rooms"] if r["name"] == "Living")
        xs, ys = zip(*room["poly"])
        self.assertAlmostEqual(max(xs) - min(xs), 13 * 0.3048, places=4)
        self.assertAlmostEqual(max(ys) - min(ys), 25 * 0.3048, places=4)

    def test_openings_lie_on_their_wall_segments(self):
        for floor in self.model["floors"]:
            for wall in floor["walls"]:
                a, b = wall["a"], wall["b"]
                dx, dy = b[0] - a[0], b[1] - a[1]
                length = math.hypot(dx, dy)
                self.assertGreater(length, 0)
                for opening in wall["holes"]:
                    with self.subTest(opening=opening["id"]):
                        for p in [opening["a"], opening["b"]]:
                            self.assertLess(
                                abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / length, 0.025
                            )
                            t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (length * length)
                            self.assertGreaterEqual(t, -0.01)
                            self.assertLessEqual(t, 1.01)


if __name__ == "__main__":
    unittest.main()
