"""정확 배정 도구 모음. 과제 계약에 맞게 복사해 고쳐 쓴다. 과제 파일이 이 키트 경로를 import하지 않는다.
Python 3.9+ 표준 라이브러리만. 결과는 결정적이다(행·열은 str(id) 순으로 정렬해 간선을 만든다).
실행: python3 opt_assign.py   → 그리디 vs 최소비용 흐름 비용·위반 표 출력

- assignment_flow: 행(사람·과제)을 열(자리·시간대)에 배정. 정원·행 한도·묶음(같은 묶음은 1개)·금지·고정·미배정 비용.
- brute_force_assignment: 같은 규칙의 완전 탐색(행 8개 이하). 테스트에서 흐름 결과가 최적인지 증명한다.
- constraint_report: 결과만 보고 위반을 종류별로 다시 센다(풀이 내부를 쓰지 않는다).
- knapsack_01: 0/1 배낭(정수 무게) 정확 DP. interval_schedule: 겹치지 않는 구간 최대 개수.
그릇 수 하한은 opt_heuristics.lower_bound_bins를 쓴다(여기 다시 만들지 않는다).
무엇이 hard 제약이고 미배정이 얼마나 나쁜지는 과제 README·담당자 답이 정한다.
"""
import itertools
import random
from collections import deque

EPS = 1e-9


# ---- 공통 준비: 입력 정리 + 고정 배정 먼저 반영 ----
def _limit(row_max, r):
    """row_max는 정수(모든 행 같음) 또는 {행: 한도}."""
    return row_max.get(r, 1) if isinstance(row_max, dict) else row_max


def _prepare(rows, cols, cost, row_max, col_cap, group_of_col, fixed):
    """고정 배정을 먼저 넣고 남은 한도·정원을 계산한다. 충돌한 고정은 넣지 않고 전부 모아 보고한다."""
    rows = sorted(set(rows), key=str)
    cols = sorted(set(cols), key=str)
    if col_cap is None:
        cap = {c: 1 for c in cols}
    else:
        missing = [c for c in cols if c not in col_cap]
        if missing:
            raise ValueError(f"col_cap에 없는 열: {missing[:5]} (조용히 1로 두지 않는다)")
        cap = {c: col_cap[c] for c in cols}
    group = dict(group_of_col or {})
    rowset, colset = set(rows), set(cols)
    taken = {r: [] for r in rows}          # 행별 고정 열
    used_groups = {r: set() for r in rows}
    load = {c: 0 for c in cols}
    conflicts, seen = [], set()
    for r, c in fixed or ():
        why = []
        if r not in rowset:
            why.append("없는 행")
        if c not in colset:
            why.append("없는 열")
        if not why:
            if (r, c) in seen:
                why.append("같은 고정 중복")
            elif cost(r, c) is None:
                why.append("금지 조합")
            if len(taken[r]) >= _limit(row_max, r):
                why.append(f"행 한도 {_limit(row_max, r)} 초과")
            if load[c] >= cap[c]:
                why.append(f"열 정원 {cap[c]} 초과")
            g = group.get(c)
            if g is not None and g in used_groups[r]:
                why.append(f"같은 묶음 {g} 이미 고정")
        seen.add((r, c))
        if why:
            conflicts.append(f"고정 ({r}, {c}): " + ", ".join(why))
            continue
        taken[r].append(c)
        load[c] += 1
        if group.get(c) is not None:
            used_groups[r].add(group[c])
    left_cap = {c: cap[c] - load[c] for c in cols}
    slots = {r: _limit(row_max, r) - len(taken[r]) for r in rows}
    return rows, cols, group, taken, used_groups, left_cap, slots, conflicts


def _allowed(r, cols, cost, group, taken, used_groups):
    """행 r이 아직 고를 수 있는 (열, 비용). 금지·이미 고정·이미 쓴 묶음은 뺀다."""
    out = []
    for c in cols:
        if c in taken[r] or (group.get(c) is not None and group[c] in used_groups[r]):
            continue
        v = cost(r, c)
        if v is not None:
            out.append((c, float(v)))
    return out


def _result(rows, cols, cost, row_max, unassigned_cost, assign, conflicts):
    """출력 모양을 한곳에서 만든다. cost는 배정 비용 합 + (미배정 비용 × 빈 칸)."""
    order = {c: i for i, c in enumerate(cols)}
    assign = {r: sorted(assign[r], key=order.__getitem__) for r in rows}
    total = sum(float(cost(r, c)) for r in rows for c in assign[r])
    short = {r: _limit(row_max, r) - len(assign[r]) for r in rows}
    unassigned = [r for r in rows if short[r] > 0]
    if unassigned_cost is not None:
        total += unassigned_cost * sum(short.values())
    feasible = not conflicts and (unassigned_cost is not None or not unassigned)
    return {"assign": assign, "cost": round(total, 9), "unassigned": unassigned,
            "missing_slots": sum(short.values()), "conflicts": conflicts, "feasible": feasible}


# ---- 최소비용 흐름(연속 최단 경로, SPFA) ----
class _Flow:
    def __init__(self, n):
        self.adj = [[] for _ in range(n)]
        self.edges = []  # [도착, 남은 용량, 비용]; 짝 간선은 i ^ 1

    def add(self, u, v, cap, cost):
        self.adj[u].append(len(self.edges))
        self.edges.append([v, cap, cost])
        self.adj[v].append(len(self.edges))
        self.edges.append([u, 0, -cost])
        return len(self.edges) - 2

    def run(self, s, t):
        """흐름을 최단(최소 비용) 경로로 하나씩 민다. 음수 비용도 된다(SPFA)."""
        n = len(self.adj)
        while True:
            dist, prev, inq = [float("inf")] * n, [-1] * n, [False] * n
            dist[s] = 0.0
            q = deque([s])
            while q:
                u = q.popleft()
                inq[u] = False
                for ei in self.adj[u]:
                    v, cap, w = self.edges[ei]
                    if cap > 0 and dist[u] + w < dist[v] - EPS:
                        dist[v], prev[v] = dist[u] + w, ei
                        if not inq[v]:
                            inq[v] = True
                            q.append(v)
            if dist[t] == float("inf"):
                return
            push, v = float("inf"), t
            while v != s:
                ei = prev[v]
                push = min(push, self.edges[ei][1])
                v = self.edges[ei ^ 1][0]
            v = t
            while v != s:
                ei = prev[v]
                self.edges[ei][1] -= push
                self.edges[ei ^ 1][1] += push
                v = self.edges[ei ^ 1][0]


def assignment_flow(rows, cols, cost, row_max=1, col_cap=None, group_of_col=None, fixed=(), unassigned_cost=None):
    """정확한 최소비용 배정.
    cost(r, c) → 비용, None이면 금지. row_max: 행이 받을 열 수(정수 또는 {행: 수}) — 이만큼 채우려 한다.
    col_cap: {열: 정원}(None이면 모두 1). group_of_col: {열: 묶음} — 한 행은 묶음마다 열 1개까지(예: 같은 시간대).
    fixed: [(r, c)] 먼저 넣는다. 충돌은 전부 모아 conflicts에 적고 그 고정만 빼고 푼다(feasible=False).
    unassigned_cost: 빈 칸 하나의 비용. None이면 빈 칸을 최대한 줄인 뒤(우선) 비용을 줄인다 — 남으면 feasible=False.
      (배정 비용 == 미배정 비용이면 둘은 동점 — 어느 쪽이 나올지는 정하지 않는다. 채우기를 원하면 미배정 비용을 높인다.)
    반환: {"assign": {r: [c...]}, "cost", "unassigned": [못 채운 행], "missing_slots", "conflicts", "feasible"}"""
    rows, cols, group, taken, used_groups, left_cap, slots, conflicts = _prepare(
        rows, cols, cost, row_max, col_cap, group_of_col, fixed)
    allowed = {r: _allowed(r, cols, cost, group, taken, used_groups) for r in rows}
    if unassigned_cost is None:  # 빈 칸 1개가 어떤 비용 차이보다 크게: 채운 수 우선
        penalty = 1.0 + 2.0 * sum(abs(v) for r in rows for _, v in allowed[r])
    else:
        penalty = float(unassigned_cost)

    # 노드: 0 출발, 1 도착, 행, (행, 묶음), 열
    ids = {}

    def node(key):
        if key not in ids:
            ids[key] = len(ids) + 2
        return ids[key]

    for r in rows:
        node(("row", r))
    for c in cols:
        node(("col", c))
    plan = []  # (출발 노드, 도착 노드, 용량, 비용, 기록할 배정)
    group_nodes = set()
    for r in rows:
        if slots[r] <= 0:
            continue
        rn = node(("row", r))
        plan.append((0, rn, slots[r], 0.0, None))
        for c, v in allowed[r]:
            if left_cap[c] <= 0:
                continue
            g = group.get(c)
            if g is None:
                plan.append((rn, node(("col", c)), 1, v, (r, c)))
            else:
                gn = node(("grp", r, g))
                if gn not in group_nodes:  # 행→(행, 묶음) 용량 1: 묶음마다 1개
                    group_nodes.add(gn)
                    plan.append((rn, gn, 1, 0.0, None))
                plan.append((gn, node(("col", c)), 1, v, (r, c)))
        plan.append((rn, 1, slots[r], penalty, None))  # 빈 칸 간선은 마지막(동점이면 배정 쪽 먼저 탐색)
    for c in cols:
        if left_cap[c] > 0:
            plan.append((node(("col", c)), 1, left_cap[c], 0.0, None))

    flow = _Flow(len(ids) + 2)
    pairs = [(flow.add(u, v, cap, w), tag) for u, v, cap, w, tag in plan]
    flow.run(0, 1)
    assign = {r: list(taken[r]) for r in rows}
    for ei, tag in pairs:
        if tag is not None and flow.edges[ei ^ 1][1] > 0:
            assign[tag[0]].append(tag[1])
    return _result(rows, cols, cost, row_max, unassigned_cost, assign, conflicts)


def brute_force_assignment(rows, cols, cost, row_max=1, col_cap=None, group_of_col=None, fixed=(), unassigned_cost=None):
    """assignment_flow와 같은 규칙의 완전 탐색. 행 8개 이하에서만. 테스트의 정답지로 쓴다.
    목적: unassigned_cost가 None이면 (빈 칸 수, 비용) 사전순, 아니면 비용 + 미배정 비용 × 빈 칸."""
    if len(set(rows)) > 8:
        raise ValueError("brute_force_assignment는 행 8개 이하에서만 쓴다")
    rows, cols, group, taken, used_groups, left_cap, slots, conflicts = _prepare(
        rows, cols, cost, row_max, col_cap, group_of_col, fixed)
    options = []
    for r in rows:
        allowed = _allowed(r, cols, cost, group, taken, used_groups)
        combos = []
        for k in range(max(slots[r], 0), -1, -1):
            for combo in itertools.combinations(allowed, k):
                gs = [group[c] for c, _ in combo if group.get(c) is not None]
                if len(gs) == len(set(gs)):
                    combos.append(combo)
        options.append(combos)
    best = {"key": None, "pick": None}
    load = dict.fromkeys(cols, 0)
    pick = []

    def dfs(i, spent, missing):
        if i == len(rows):
            key = (missing, spent) if unassigned_cost is None else (0, spent + unassigned_cost * missing)
            b = best["key"]
            if b is None or key[0] < b[0] or (key[0] == b[0] and key[1] < b[1] - EPS):
                best["key"], best["pick"] = key, list(pick)
            return
        r = rows[i]
        for combo in options[i]:
            if any(load[c] >= left_cap[c] for c, _ in combo):
                continue
            for c, _ in combo:
                load[c] += 1
            pick.append([c for c, _ in combo])
            dfs(i + 1, spent + sum(v for _, v in combo), missing + slots[r] - len(combo))
            pick.pop()
            for c, _ in combo:
                load[c] -= 1

    dfs(0, 0.0, 0)
    assign = {r: list(taken[r]) + best["pick"][i] for i, r in enumerate(rows)}
    return _result(rows, cols, cost, row_max, unassigned_cost, assign, conflicts)


def greedy_assignment(rows, cols, cost, row_max=1, col_cap=None, group_of_col=None, fixed=(), unassigned_cost=None):
    """기준선: 행을 id 순으로 돌며 남은 열 중 가장 싼 것부터 고른다(미배정 비용보다 비싸면 비운다)."""
    rows, cols, group, taken, used_groups, left_cap, slots, conflicts = _prepare(
        rows, cols, cost, row_max, col_cap, group_of_col, fixed)
    assign = {r: list(taken[r]) for r in rows}
    for r in rows:
        groups_used = set(used_groups[r])
        for c, v in sorted(_allowed(r, cols, cost, group, taken, used_groups), key=lambda t: (t[1], str(t[0]))):
            if len(assign[r]) - len(taken[r]) >= slots[r]:
                break
            if left_cap[c] <= 0 or (group.get(c) is not None and group[c] in groups_used):
                continue
            if unassigned_cost is not None and v >= unassigned_cost:
                continue
            assign[r].append(c)
            left_cap[c] -= 1
            if group.get(c) is not None:
                groups_used.add(group[c])
    return _result(rows, cols, cost, row_max, unassigned_cost, assign, conflicts)


# ---- 독립 검사기 ----
def constraint_report(assign, row_max=1, col_cap=None, group_of_col=None, forbidden_fn=None):
    """배정 결과만 보고 위반을 종류별로 센다. 풀이 함수·내부 상태를 쓰지 않는다.
    assign: {r: [c...]}. forbidden_fn(r, c) → True면 금지. col_cap None이면 열마다 1, 표에 없는 열은 unknown_col.
    반환: {"row_over", "col_over", "group_clash", "forbidden", "duplicate", "unknown_col", "total", "details": [...]}"""
    count = dict.fromkeys(["row_over", "col_over", "group_clash", "forbidden", "duplicate", "unknown_col"], 0)
    details, load = [], {}
    groups = group_of_col or {}
    for r in sorted(assign, key=str):
        picked = list(assign[r])
        limit = row_max.get(r, 1) if isinstance(row_max, dict) else row_max
        if len(picked) > limit:
            count["row_over"] += 1
            details.append(f"row_over: {r} {len(picked)} > {limit}")
        for c in sorted(set(picked), key=str):
            if picked.count(c) > 1:
                count["duplicate"] += 1
                details.append(f"duplicate: {r} takes {c} x{picked.count(c)}")
        seen_group = {}
        for c in picked:
            load[c] = load.get(c, 0) + 1
            if forbidden_fn is not None and forbidden_fn(r, c):
                count["forbidden"] += 1
                details.append(f"forbidden: {r}-{c}")
            g = groups.get(c)
            if g is not None:
                if g in seen_group and seen_group[g] != c:
                    count["group_clash"] += 1
                    details.append(f"group_clash: {r} has {seen_group[g]} and {c} in {g}")
                seen_group.setdefault(g, c)
    for c in sorted(load, key=str):
        if col_cap is not None and c not in col_cap:
            count["unknown_col"] += 1
            details.append(f"unknown_col: {c}")
            continue
        cap = 1 if col_cap is None else col_cap[c]
        if load[c] > cap:
            count["col_over"] += 1
            details.append(f"col_over: {c} {load[c]} > {cap}")
    count["total"] = sum(count.values())
    count["details"] = details
    return count


# ---- 배낭·구간 ----
def knapsack_01(items, capacity):
    """items: [(id, 무게, 가치)], 무게·capacity는 0 이상 정수(소수는 배율을 곱해 정수로).
    반환: (최대 가치, [고른 id — 입력 순서]). 표 크기 = 항목 수 × (capacity+1)."""
    if not isinstance(capacity, int) or capacity < 0:
        raise ValueError("capacity는 0 이상 정수")
    for item_id, w, _ in items:
        if not isinstance(w, int) or w < 0:
            raise ValueError(f"{item_id}: 무게는 0 이상 정수")
    n = len(items)
    best = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i, (_, w, v) in enumerate(items, 1):
        prev, row = best[i - 1], best[i]
        for cap in range(capacity + 1):
            row[cap] = prev[cap]
            if w <= cap and prev[cap - w] + v > row[cap]:  # 같으면 안 넣는다(동점 규칙)
                row[cap] = prev[cap - w] + v
    chosen, cap = [], capacity
    for i in range(n, 0, -1):
        if best[i][cap] != best[i - 1][cap]:
            chosen.append(items[i - 1][0])
            cap -= items[i - 1][1]
    return best[n][capacity], chosen[::-1]


def interval_schedule(intervals):
    """intervals: [(id, 시작, 끝)]. 서로 겹치지 않는 구간을 최대 개수로 고른다(끝이 이른 순 그리디, 정확).
    끝 == 다음 시작은 겹치지 않음으로 본다 — 과제가 경계를 어떻게 정했는지 먼저 확인한다. 반환: [id...]"""
    for item_id, s, e in intervals:
        if e < s:
            raise ValueError(f"{item_id}: 끝 {e} < 시작 {s}")
    picked, last_end = [], None
    for item_id, s, e in sorted(intervals, key=lambda t: (t[2], t[1], str(t[0]))):
        if last_end is None or s >= last_end:
            picked.append(item_id)
            last_end = e
    return picked


# ---- 데모: 그리디 vs 최소비용 흐름 ----
def demo_case(seed=11, n_rows=10):
    """사람 n명 × 근무칸 4개(AM 2, PM 2). 한 사람 최대 2칸, 같은 시간대 1칸, 일부 금지."""
    rng = random.Random(seed)
    rows = [f"p{i:02d}" for i in range(n_rows)]
    cols = ["AM1", "AM2", "PM1", "PM2"]
    table = {(r, c): (None if rng.random() < 0.15 else rng.randint(1, 40)) for r in rows for c in cols}
    return {"rows": rows, "cols": cols, "cost": lambda r, c: table[(r, c)], "row_max": 2,
            "col_cap": {"AM1": 4, "AM2": 3, "PM1": 4, "PM2": 3},
            "group_of_col": {"AM1": "AM", "AM2": "AM", "PM1": "PM", "PM2": "PM"}, "unassigned_cost": 60}


def main(seed=11):
    case = demo_case(seed)
    forbidden = lambda r, c: case["cost"](r, c) is None
    print(f"seed={seed} 행 {len(case['rows'])} · 열 {len(case['cols'])} · row_max {case['row_max']} · 미배정 비용 {case['unassigned_cost']}")
    print("| 방법 | 총비용 | 빈 칸 | 검사기 위반 |")
    print("|---|---|---|---|")
    for name, fn in (("그리디(행 id 순)", greedy_assignment), ("최소비용 흐름", assignment_flow)):
        res = fn(**case)
        rep = constraint_report(res["assign"], case["row_max"], case["col_cap"], case["group_of_col"], forbidden)
        print(f"| {name} | {res['cost']:.1f} | {res['missing_slots']} | {rep['total']} |")
    bad = assignment_flow(**dict(case, fixed=[("p00", "AM1"), ("p00", "AM2"), ("zz", "PM1")]))
    print("고정 충돌 보고(한 번에): " + " / ".join(bad["conflicts"]))


if __name__ == "__main__":
    main()
