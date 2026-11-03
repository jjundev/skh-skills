import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import dataset, jobs, planner  # noqa: E402
from src.dataset import Dataset  # noqa: E402


def small_ds(version=1):
    members = {"m1": "s1", "m2": "s2", "m3": "s3"}
    travel = {}
    for a in ["s1", "s2", "s3", "OFFICE"]:
        for b in ["s1", "s2", "s3", "OFFICE"]:
            travel[(a, b)] = 7.4 if a != b else 0
    return Dataset(version, members, {m: 540 for m in members}, {"v1": 2, "v2": 2}, travel)


class PlannerTest(unittest.TestCase):
    def test_minutes_are_rounded_up(self):
        ds = small_ds()
        sch = planner.schedule(ds, ["m1", "m2"])
        # two 7.4-min legs -> 8 + 8, not 7 + 7
        self.assertEqual(sch[-1][1] - sch[0][1], 16)

    def test_plan_respects_capacity_and_ride_limit(self):
        ds = small_ds()
        routes, _ = planner.plan(ds)
        self.assertEqual(planner.validate_plan(ds, routes), [])

    def test_not_enough_seats_raises(self):
        ds = small_ds()
        ds = Dataset(1, ds.members, ds.arrive_by, {"v1": 1}, ds.travel)
        with self.assertRaises(ValueError):
            planner.baseline(ds)


class JobTest(unittest.TestCase):
    def test_dataset_swap_marks_stale(self):
        dataset.activate(small_ds(1))
        jid = jobs.submit()
        orig = planner.plan

        def swap_midway(ds, **kw):
            dataset.activate(small_ds(2))
            return orig(ds, **kw)

        planner.plan = swap_midway
        try:
            jobs.run(jid)
        finally:
            planner.plan = orig
        self.assertEqual(jobs.JOBS[jid]["status"], "STALE")


if __name__ == "__main__":
    unittest.main()
