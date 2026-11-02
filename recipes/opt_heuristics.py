"""일반 휴리스틱 틀. 과제 계약(입력·제약·목적)에 맞게 복사해 고쳐 쓴다. 과제 파일이 이 키트 경로를 import하지 않는다.
Python 3.9+ 표준 라이브러리만. 결과는 결정적이다(동점은 id 순, 난수는 고정 seed).
실행: python3 opt_heuristics.py   → 기준선 대비 개선 지표표 출력
여기 있는 함수는 업무 규칙이 아니다. 무엇을 최소화할지·무엇이 hard 제약인지는 과제 README·담당자 답이 정한다.
"""
import math
import random


# ---- 거리 ----
def euclidean(a, b):
    """평면 좌표 (x, y) 두 점의 직선 거리."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def haversine(a, b, radius_km=6371.0):
    """위경도 (lat, lon) 두 점의 대원 거리(km). 도로 거리가 아니다 — 과제가 정한 거리 정의를 먼저 확인한다."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * radius_km * math.asin(min(1.0, math.sqrt(h)))


# ---- 하한 ----
def lower_bound_bins(total_demand, capacity):
    """그릇(차량·방·조) 수의 하한 = ceil(총수요 / 용량). 어떤 방법도 이보다 적을 수 없다."""
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    return math.ceil(total_demand / capacity)


# ---- 배정(용량 있음) ----
def first_fit_decreasing(items, capacity):
    """items: [(id, size)]. 큰 것부터 처음 들어가는 그릇에 넣는다.
    반환: [[id, ...], ...]. 용량보다 큰 항목은 넣을 수 없으므로 ValueError (조용히 버리지 않는다)."""
    order = sorted(items, key=lambda t: (-t[1], str(t[0])))  # 동점은 id 순
    bins, loads = [], []
    for item_id, size in order:
        if size > capacity:
            raise ValueError(f"item {item_id} size {size} > capacity {capacity}")
        for i, load in enumerate(loads):
            if load + size <= capacity:
                bins[i].append(item_id)
                loads[i] += size
                break
        else:
            bins.append([item_id])
            loads.append(size)
    return bins


# ---- 묶기(군집) + 용량 ----
def sweep_clusters(points, center, demand, capacity):
    """points: {id: (x, y)}, center: (x, y), demand: {id: 수요}.
    중심에서 본 각도 순(동점은 거리·id 순)으로 훑으며 용량이 차면 새 묶음을 연다.
    반환: [[id, ...], ...]. 묶음 안 순서는 훑은 순서."""
    def key(pid):
        x, y = points[pid][0] - center[0], points[pid][1] - center[1]
        angle = math.atan2(y, x) % (2 * math.pi)
        return (round(angle, 12), round(math.hypot(x, y), 12), str(pid))

    clusters, current, load = [], [], 0
    for pid in sorted(points, key=key):
        d = demand.get(pid, 1)
        if d > capacity:
            raise ValueError(f"point {pid} demand {d} > capacity {capacity}")
        if current and load + d > capacity:
            clusters.append(current)
            current, load = [], 0
        current.append(pid)
        load += d
    if current:
        clusters.append(current)
    return clusters


# ---- 경로 순서 ----
def route_length(route, dist_fn):
    """route: [start, a, b, ...]. 열린 경로 길이(돌아오지 않음). 돌아와야 하면 route 끝에 start를 붙여 넘긴다."""
    return sum(dist_fn(route[i], route[i + 1]) for i in range(len(route) - 1))


def nearest_neighbor_route(start, ids, dist_fn):
    """start에서 가장 가까운 미방문 지점을 차례로 고른다. 동점은 id 순. 반환: [start, ...]."""
    route, left = [start], sorted(set(ids) - {start}, key=str)
    while left:
        last = route[-1]
        nxt = min(left, key=lambda p: (dist_fn(last, p), str(p)))
        route.append(nxt)
        left.remove(nxt)
    return route


def two_opt(route, dist_fn, max_rounds=50, fixed_end=False):
    """구간 뒤집기로 길이를 줄인다. route[0](출발점)은 고정. 길이가 늘지 않는다.
    돌아오는 경로(끝 = 출발점)는 fixed_end=True로 끝점도 고정한다.
    max_rounds로 시간 상한을 둔다(한 바퀴 O(n²) 쌍 검사)."""
    best = list(route)
    n = len(best)
    last = n - 1 if fixed_end else n
    for _ in range(max_rounds):
        improved = False
        for i in range(1, last - 1):
            for j in range(i + 1, last):
                a, b = best[i - 1], best[i]
                c = best[j]
                d = best[j + 1] if j + 1 < n else None
                old = dist_fn(a, b) + (dist_fn(c, d) if d is not None else 0)
                new = dist_fn(a, c) + (dist_fn(b, d) if d is not None else 0)
                if new < old - 1e-9:  # 부동소수 오차로 무한 반복하지 않게
                    best[i:j + 1] = reversed(best[i:j + 1])
                    improved = True
        if not improved:
            break
    return best


# ---- 독립 검사기 ----
def check_assignment(assignment, sizes, capacity, all_items):
    """생성기 함수를 쓰지 않고 결과만 다시 센다. 위반 문장 목록을 반환(빈 목록 = 위반 없음).
    assignment: {item: group} 또는 [(item, group)] (중복 배정을 보려면 목록으로 넘긴다)."""
    pairs = list(assignment.items()) if isinstance(assignment, dict) else list(assignment)
    violations, seen, loads = [], {}, {}
    for item, group in pairs:
        if item in seen:
            violations.append(f"duplicate: {item} in {seen[item]} and {group}")
            continue
        seen[item] = group
        if item not in sizes:
            violations.append(f"unknown item: {item}")
            continue
        loads[group] = loads.get(group, 0) + sizes[item]
    for item in sorted(set(all_items) - set(seen), key=str):
        violations.append(f"missing: {item}")
    for group in sorted(loads, key=str):
        if loads[group] > capacity:
            violations.append(f"over capacity: {group} load {loads[group]} > {capacity}")
    return violations


def bins_to_assignment(bins):
    """[[id, ...], ...] → [(id, 묶음번호)] (중복도 그대로 남겨 검사기가 잡게 한다)."""
    return [(item, g) for g, members in enumerate(bins) for item in members]


# ---- 데모: 기준선 vs 개선 ----
def main(seed=7, n=60, capacity=12):
    rng = random.Random(seed)  # 고정 seed → 같은 출력
    points = {f"p{i:02d}": (rng.uniform(0, 100), rng.uniform(0, 100)) for i in range(n)}
    demand = {pid: rng.randint(1, 6) for pid in points}
    depot = "depot"
    coords = dict(points, depot=(50.0, 50.0))

    def dist(a, b):
        return euclidean(coords[a], coords[b])

    # 기준선: id 순서 그대로 방문 / 개선: 최근접 이웃 → 2-opt
    base = [depot] + sorted(points)
    nn = nearest_neighbor_route(depot, points, dist)
    opt = two_opt(nn, dist)

    lb = lower_bound_bins(sum(demand.values()), capacity)
    naive = []  # 기준선: id 순서로 채우다 넘치면 새 그릇
    for pid in sorted(points):
        if not naive or sum(demand[x] for x in naive[-1]) + demand[pid] > capacity:
            naive.append([])
        naive[-1].append(pid)
    ffd = first_fit_decreasing(list(demand.items()), capacity)
    sweep = sweep_clusters(points, coords[depot], demand, capacity)

    rows = [
        ("경로 길이(열린 경로)", f"{route_length(base, dist):.1f}", f"NN {route_length(nn, dist):.1f} → 2-opt {route_length(opt, dist):.1f}", "-"),
        ("그릇 수", str(len(naive)), f"FFD {len(ffd)} / sweep {len(sweep)}", str(lb)),
        ("검사기 위반 수(FFD)", "-", str(len(check_assignment(bins_to_assignment(ffd), demand, capacity, points))), "0"),
    ]
    print(f"seed={seed} n={n} capacity={capacity}")
    print("| 지표 | 기준선 | 개선 | 하한/목표 |")
    print("|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(r) + " |")


if __name__ == "__main__":
    main()
