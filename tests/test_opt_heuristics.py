import contextlib
import importlib.util
import io
from pathlib import Path
import random
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('opt_heuristics', ROOT/'recipes'/'opt_heuristics.py')
opt = importlib.util.module_from_spec(spec); spec.loader.exec_module(opt)


def sample(seed=3, n=40):
    rng = random.Random(seed)
    points = {f'p{i:02d}': (rng.uniform(0, 100), rng.uniform(0, 100)) for i in range(n)}
    demand = {pid: rng.randint(1, 6) for pid in points}
    return points, demand


class OptHeuristicsTest(unittest.TestCase):
    def test_ffd_respects_capacity_and_lower_bound(self):
        for seed in range(5):
            _, demand = sample(seed)
            bins = opt.first_fit_decreasing(list(demand.items()), 12)
            self.assertTrue(all(sum(demand[i] for i in b) <= 12 for b in bins))
            self.assertGreaterEqual(len(bins), opt.lower_bound_bins(sum(demand.values()), 12))
            self.assertEqual(sorted(i for b in bins for i in b), sorted(demand))
        with self.assertRaises(ValueError):
            opt.first_fit_decreasing([('big', 13)], 12)

    def test_two_opt_never_longer_and_fixes_crossing(self):
        square = {'s': (0, 0), 'a': (0, 1), 'b': (1, 1), 'c': (1, 0)}
        dist = lambda x, y: opt.euclidean(square[x], square[y])
        crossed = ['s', 'b', 'a', 'c', 's']  # 대각선 두 개가 교차
        fixed = opt.two_opt(crossed, dist, fixed_end=True)
        self.assertEqual((fixed[0], fixed[-1]), ('s', 's'))
        self.assertAlmostEqual(opt.route_length(fixed, dist), 4.0)
        points, _ = sample()
        d = lambda x, y: opt.euclidean(points[x], points[y])
        start = min(points)
        for route in ([start] + sorted(points.keys() - {start}), opt.nearest_neighbor_route(start, points, d)):
            better = opt.two_opt(route, d)
            self.assertEqual(better[0], start)
            self.assertEqual(sorted(better), sorted(route))
            self.assertLessEqual(opt.route_length(better, d), opt.route_length(route, d) + 1e-9)

    def test_sweep_respects_capacity_and_assigns_once(self):
        points, demand = sample()
        clusters = opt.sweep_clusters(points, (50, 50), demand, 12)
        assignment = opt.bins_to_assignment(clusters)
        self.assertEqual(opt.check_assignment(assignment, demand, 12, points), [])
        self.assertEqual(len(assignment), len(points))

    def test_checker_detects_missing_duplicate_and_over_capacity(self):
        sizes = {'a': 5, 'b': 5, 'c': 5}
        self.assertEqual(opt.check_assignment({'a': 1, 'b': 1, 'c': 2}, sizes, 10, sizes), [])
        kinds = lambda v: {x.split(':')[0] for x in v}
        self.assertEqual(kinds(opt.check_assignment({'a': 1, 'b': 1}, sizes, 10, sizes)), {'missing'})
        self.assertEqual(kinds(opt.check_assignment([('a', 1), ('a', 2), ('b', 1), ('c', 2)], sizes, 10, sizes)), {'duplicate'})
        self.assertEqual(kinds(opt.check_assignment({'a': 1, 'b': 1, 'c': 1}, sizes, 10, sizes)), {'over capacity'})

    def test_trap_input_changes_result(self):
        # 제약을 실제로 지키는지: 용량을 넘는 묶음은 위반, 지키는 묶음은 통과해야 한다.
        sizes = {'a': 6, 'b': 6}
        self.assertNotEqual(opt.check_assignment({'a': 1, 'b': 1}, sizes, 10, sizes),
                            opt.check_assignment({'a': 1, 'b': 2}, sizes, 10, sizes))

    def test_same_input_same_output(self):
        points, demand = sample()
        d = lambda x, y: opt.euclidean(points[x], points[y])
        run = lambda: (opt.first_fit_decreasing(list(demand.items()), 12),
                       opt.sweep_clusters(points, (50, 50), demand, 12),
                       opt.two_opt(opt.nearest_neighbor_route('p00', points, d), d))
        self.assertEqual(run(), run())
        outputs = []
        for _ in range(2):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                opt.main()
            outputs.append(buffer.getvalue())
        self.assertEqual(outputs[0], outputs[1])

    def test_distance_helpers(self):
        self.assertAlmostEqual(opt.euclidean((0, 0), (3, 4)), 5.0)
        self.assertAlmostEqual(opt.haversine((0, 0), (0, 1)), 111.19, places=1)
        self.assertEqual(opt.lower_bound_bins(25, 12), 3)


if __name__ == '__main__':
    unittest.main()
