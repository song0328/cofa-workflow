import contextlib
import importlib.util
import io
import itertools
from pathlib import Path
import random
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('opt_assign', ROOT/'recipes'/'opt_assign.py')
oa = importlib.util.module_from_spec(spec); spec.loader.exec_module(oa)


def random_case(seed, n_rows, n_cols, row_max=1, groups=False, forbid=0.2, unassigned=None):
    rng = random.Random(seed)
    rows = [f'r{i}' for i in range(n_rows)]
    cols = [f'c{j}' for j in range(n_cols)]
    table = {(r, c): (None if rng.random() < forbid else rng.randint(-5, 30)) for r in rows for c in cols}
    case = {'rows': rows, 'cols': cols, 'cost': lambda r, c: table[(r, c)], 'row_max': row_max,
            'col_cap': {c: rng.randint(1, 2) for c in cols}, 'unassigned_cost': unassigned}
    if groups:
        case['group_of_col'] = {c: f'g{j % 2}' for j, c in enumerate(cols)}
    return case


def check(case, res):
    forbidden = lambda r, c: case['cost'](r, c) is None
    return oa.constraint_report(res['assign'], case['row_max'], case['col_cap'], case.get('group_of_col'), forbidden)


class OptAssignTest(unittest.TestCase):
    def test_flow_matches_brute_force(self):
        settings = [(6, 3, 1, False, None), (6, 4, 1, False, 12), (5, 4, 2, True, None), (5, 4, 2, True, 8), (7, 3, 1, False, 0)]
        for seed in range(6):
            for n_rows, n_cols, row_max, groups, unassigned in settings:
                case = random_case(seed, n_rows, n_cols, row_max, groups, unassigned=unassigned)
                flow, brute = oa.assignment_flow(**case), oa.brute_force_assignment(**case)
                with self.subTest(seed=seed, setting=(n_rows, n_cols, row_max, groups, unassigned)):
                    if unassigned is None:   # 미배정 비용이 있으면 빈 칸과 같은 비용의 배정은 동점이다
                        self.assertEqual(flow['missing_slots'], brute['missing_slots'])
                    self.assertAlmostEqual(flow['cost'], brute['cost'], places=6)
                    self.assertEqual(check(case, flow)['total'], 0)
                    self.assertEqual(check(case, brute)['total'], 0)

    def test_flow_beats_or_ties_greedy(self):
        for seed in range(5):
            case = random_case(seed, 12, 5, 2, True, unassigned=25)
            flow, greedy = oa.assignment_flow(**case), oa.greedy_assignment(**case)
            self.assertLessEqual(flow['cost'], greedy['cost'] + 1e-9)
            self.assertEqual(check(case, greedy)['total'], 0)

    def test_caps_groups_and_forbidden_respected(self):
        cost = lambda r, c: None if (r, c) == ('a', 'x') else 1
        res = oa.assignment_flow(['a', 'b', 'c'], ['x', 'y', 'z'], cost, row_max=2,
                                 col_cap={'x': 1, 'y': 3, 'z': 3}, group_of_col={'y': 'G', 'z': 'G'})
        self.assertNotIn('x', res['assign']['a'])
        for r, picked in res['assign'].items():
            self.assertLessEqual(len([c for c in picked if c in ('y', 'z')]), 1)   # 같은 묶음은 1개
        self.assertEqual(sum('x' in p for p in res['assign'].values()), 1)            # x 정원 1
        self.assertEqual(len(res['assign']['a']), 1)                                 # a는 x 금지 → 1칸만
        self.assertEqual(res['missing_slots'], 2)                                    # 채울 수 있는 칸은 x 1 + 묶음 3
        self.assertFalse(res['feasible'])
        with self.assertRaises(ValueError):
            oa.assignment_flow(['a'], ['x', 'y'], cost, col_cap={'x': 1})              # 정원 표 누락은 오류

    def test_fixed_conflicts_reported_all_at_once(self):
        cost = lambda r, c: None if (r, c) == ('b', 'y') else 5
        fixed = [('a', 'x'), ('b', 'x'), ('b', 'y'), ('a', 'x'), ('zz', 'x'), ('c', 'nope')]
        res = oa.assignment_flow(['a', 'b', 'c'], ['x', 'y'], cost, fixed=fixed, unassigned_cost=100)
        text = '\n'.join(res['conflicts'])
        self.assertEqual(len(res['conflicts']), 5)
        for word in ('열 정원 1 초과', '금지 조합', '같은 고정 중복', '없는 행', '없는 열'):
            self.assertIn(word, text)
        self.assertEqual(res['assign']['a'], ['x'])     # 유효한 고정은 들어간다
        self.assertFalse(res['feasible'])
        group = oa.assignment_flow(['a'], ['x', 'y'], lambda r, c: 1, row_max=2, col_cap={'x': 1, 'y': 1},
                                   group_of_col={'x': 'G', 'y': 'G'}, fixed=[('a', 'x'), ('a', 'y')])
        self.assertIn('같은 묶음 G 이미 고정', group['conflicts'][0])

    def test_fixed_is_kept_even_if_expensive(self):
        cost = lambda r, c: {('a', 'x'): 50, ('a', 'y'): 1, ('b', 'x'): 1, ('b', 'y'): 50}[(r, c)]
        free = oa.assignment_flow(['a', 'b'], ['x', 'y'], cost)
        self.assertEqual(free['cost'], 2)
        pinned = oa.assignment_flow(['a', 'b'], ['x', 'y'], cost, fixed=[('a', 'x')])
        self.assertEqual(pinned['assign'], {'a': ['x'], 'b': ['y']})
        self.assertEqual(pinned['cost'], 100)
        self.assertEqual(pinned, oa.brute_force_assignment(['a', 'b'], ['x', 'y'], cost, fixed=[('a', 'x')]))

    def test_unassigned_handling(self):
        cost = lambda r, c: {'a': 10, 'b': 40, 'c': 3}[r]
        rows, cols = ['a', 'b', 'c'], ['x']
        must = oa.assignment_flow(rows, cols, cost, col_cap={'x': 2})            # 빈 칸 최소 → 비용
        self.assertEqual((must['missing_slots'], must['cost']), (1, 13))
        self.assertEqual(must['unassigned'], ['b'])
        cheap_skip = oa.assignment_flow(rows, cols, cost, col_cap={'x': 2}, unassigned_cost=5)
        self.assertEqual(cheap_skip['assign'], {'a': [], 'b': [], 'c': ['x']})  # 10·40은 비워 두는 게 싸다
        self.assertEqual(cheap_skip['cost'], 3 + 5 * 2)
        self.assertTrue(cheap_skip['feasible'])

    def test_negative_costs_and_per_row_limits(self):
        cost = lambda r, c: -1 * (ord(c) - ord('w'))
        res = oa.assignment_flow(['a', 'b'], ['x', 'y', 'z'], cost, row_max={'a': 2, 'b': 1},
                                 col_cap={'x': 1, 'y': 1, 'z': 1})
        self.assertEqual(sum(len(v) for v in res['assign'].values()), 3)
        self.assertAlmostEqual(res['cost'], -6)
        self.assertEqual(res['cost'], oa.brute_force_assignment(['a', 'b'], ['x', 'y', 'z'], cost, row_max={'a': 2, 'b': 1},
                                                                col_cap={'x': 1, 'y': 1, 'z': 1})['cost'])

    def test_constraint_report_counts_each_kind(self):
        assign = {'a': ['x', 'x', 'y'], 'b': ['x'], 'c': ['q']}
        rep = oa.constraint_report(assign, row_max=2, col_cap={'x': 2, 'y': 1}, group_of_col={'x': 'G', 'y': 'G'},
                                   forbidden_fn=lambda r, c: (r, c) == ('b', 'x'))
        expect = {'row_over': 1, 'duplicate': 1, 'group_clash': 1, 'forbidden': 1, 'col_over': 1, 'unknown_col': 1}
        self.assertEqual({k: rep[k] for k in expect}, expect)
        self.assertEqual(rep['total'], 6)
        clean = oa.constraint_report({'a': ['x'], 'b': ['y']})
        self.assertEqual(clean['total'], 0)

    def test_deterministic(self):
        case = random_case(4, 12, 5, 2, True, unassigned=20)
        self.assertEqual(oa.assignment_flow(**case), oa.assignment_flow(**case))
        reordered = dict(case, rows=case['rows'][::-1], cols=case['cols'][::-1])
        self.assertEqual(oa.assignment_flow(**case), oa.assignment_flow(**reordered))   # 입력 순서와 무관
        outs = []
        for _ in range(2):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                oa.main()
            outs.append(buf.getvalue())
        self.assertEqual(outs[0], outs[1])
        self.assertIn('최소비용 흐름', outs[0])
        self.assertIn('고정 충돌 보고', outs[0])
        with self.assertRaises(ValueError):
            oa.brute_force_assignment([f'r{i}' for i in range(9)], ['x'], lambda r, c: 1)

    def test_knapsack_matches_subsets(self):
        for seed in range(8):
            rng = random.Random(seed)
            items = [(f'i{k}', rng.randint(0, 9), rng.randint(-2, 20)) for k in range(8)]
            cap = rng.randint(0, 25)
            value, chosen = oa.knapsack_01(items, cap)
            best = max(sum(v for _, _, v in s) for n in range(len(items) + 1)
                       for s in itertools.combinations(items, n) if sum(w for _, w, _ in s) <= cap)
            self.assertEqual(value, best)
            picked = [t for t in items if t[0] in chosen]
            self.assertLessEqual(sum(w for _, w, _ in picked), cap)
            self.assertEqual(sum(v for _, _, v in picked), value)
        with self.assertRaises(ValueError):
            oa.knapsack_01([('a', 1.5, 3)], 4)

    def test_interval_schedule_is_maximum(self):
        for seed in range(8):
            rng = random.Random(seed)
            iv = []
            for k in range(8):
                s = rng.randint(0, 20)
                iv.append((f'j{k}', s, s + rng.randint(0, 6)))
            picked = oa.interval_schedule(iv)
            chosen = sorted((t for t in iv if t[0] in picked), key=lambda t: (t[2], t[1]))
            self.assertTrue(all(a[2] <= b[1] for a, b in zip(chosen, chosen[1:])))
            ok = lambda s: all(a[2] <= b[1] for a, b in zip(s, s[1:]))
            best = max(n for n in range(len(iv) + 1) for s in itertools.combinations(sorted(iv, key=lambda t: (t[1], t[2])), n) if ok(s))
            self.assertEqual(len(picked), best)
        self.assertEqual(oa.interval_schedule([('a', 0, 2), ('b', 2, 4)]), ['a', 'b'])   # 끝 = 시작은 허용
        with self.assertRaises(ValueError):
            oa.interval_schedule([('bad', 3, 1)])


if __name__ == '__main__':
    unittest.main()
