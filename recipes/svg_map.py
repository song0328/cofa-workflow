"""점·경로를 SVG로 그리는 틀 (Python 3.9+ 표준 라이브러리만 · 지도 라이브러리·인터넷 없이)
쓰임: 거점·방문지·배정 결과를 화면이나 보고서에 그림으로 보여 줄 때. 서버가 SVG 문자열을 만들어 HTML에 넣는다.
과제 계약(좌표 형식·경로 구조)에 맞게 복사해 고쳐 쓴다. 과제 파일이 이 키트 경로를 import하지 않는다.
실행: python3 svg_map.py  → demo_map.html 생성 (브라우저 미리보기로 확인)

규칙
- 좌표가 위경도면 mode="latlon"(경도에 cos(위도)를 곱해 찌그러짐을 줄인다), 평면이면 mode="xy".
- 글자 겹침을 막으려고 번호 글자는 점이 적을 때(label_limit 이하)만 쓴다. 자세한 정보는 점의 <title>(마우스를 올리면 뜨는 말풍선)에 넣는다.
- 그림만으로는 검사가 어렵다 → 같은 내용을 표(route_table_html)로 함께 낸다. 표는 ui_sim·테스트로 읽을 수 있다.
- 색은 경로 순서대로 고정 팔레트(같은 입력 → 같은 그림).
"""
import html
import math

PALETTE = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"]


def project(points, width=800, height=560, pad=30, mode="xy"):
    """points: {id: (x, y)} 또는 {id: (lat, lon)} → {id: (px, py)} (화면 좌표, y는 아래로 증가)"""
    if not points:
        return {}
    if mode == "latlon":
        lat0 = sum(p[0] for p in points.values()) / len(points)
        k = math.cos(math.radians(lat0))
        raw = {i: (lon * k, lat) for i, (lat, lon) in points.items()}
    else:
        raw = dict(points)
    xs = [p[0] for p in raw.values()]
    ys = [p[1] for p in raw.values()]
    w = (max(xs) - min(xs)) or 1.0
    h = (max(ys) - min(ys)) or 1.0
    s = min((width - 2 * pad) / w, (height - 2 * pad) / h)
    return {i: (round(pad + (x - min(xs)) * s, 1), round(height - pad - (y - min(ys)) * s, 1)) for i, (x, y) in raw.items()}


def render_svg(points, routes, width=800, height=560, mode="xy", depots=(), label_limit=40, info=None):
    """routes: [{"id": "R1", "stops": [id, ...], "label": "설명(선택)"}]
    depots: 출발·도착 거점 id들(네모로 표시). info: {id: "말풍선에 더할 글"}(선택)"""
    info = info or {}
    xy = project(points, width, height, mode=mode)
    esc = html.escape
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="경로 지도">',
           '<defs>']
    for i, _ in enumerate(routes):
        c = PALETTE[i % len(PALETTE)]
        out.append(f'<marker id="arrow{i}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
                   f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
    out.append('</defs><rect width="100%" height="100%" fill="#fafafa"/>')
    order = {}
    for i, r in enumerate(routes):
        c = PALETTE[i % len(PALETTE)]
        pts = [xy[s] for s in r["stops"] if s in xy]
        for k in range(len(pts) - 1):   # 구간마다 화살표 — 방향이 보이게
            (x1, y1), (x2, y2) = pts[k], pts[k + 1]
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="2" opacity="0.8" marker-end="url(#arrow{i})"/>')
        for n, s in enumerate(r["stops"], 1):
            order.setdefault(s, []).append(f'{r["id"]} {n}번째')
    for i, (pid, (x, y)) in enumerate(sorted(xy.items(), key=lambda kv: str(kv[0]))):
        tip = esc(" · ".join([str(pid)] + order.get(pid, ["경로 없음"]) + ([str(info[pid])] if pid in info else [])))
        if pid in depots:
            out.append(f'<rect x="{x - 7}" y="{y - 7}" width="14" height="14" fill="#222"><title>{tip}</title></rect>')
        else:
            fill = "#999" if pid not in order else "#fff"
            out.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{fill}" stroke="#333"><title>{tip}</title></circle>')
        if len(xy) <= label_limit:
            out.append(f'<text x="{x + 7}" y="{y - 7}" font-size="11" fill="#333">{esc(str(pid))}</text>')
    out.append("</svg>")
    return "".join(out)


def route_table_html(routes, metrics=None):
    """그림과 같은 내용을 표로. metrics: {route_id: {"거리": 12.3, "인원": 40}} (선택)"""
    metrics = metrics or {}
    keys = sorted({k for m in metrics.values() for k in m})
    head = "".join(f"<th>{html.escape(k)}</th>" for k in keys)
    rows = []
    for i, r in enumerate(routes):
        c = PALETTE[i % len(PALETTE)]
        cells = "".join(f"<td>{html.escape(str(metrics.get(r['id'], {}).get(k, '')))}</td>" for k in keys)
        stops = " → ".join(html.escape(str(s)) for s in r["stops"])
        rows.append(f'<tr><td><span style="color:{c}">■</span> {html.escape(str(r["id"]))}</td><td>{len(r["stops"])}</td><td>{stops}</td>{cells}</tr>')
    return (f'<table id="route-table"><thead><tr><th>경로</th><th>지점 수</th><th>순서</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def render_html(points, routes, title="경로 지도", **kw):
    metrics = kw.pop("metrics", None)
    return (f'<!doctype html><html lang="ko"><meta charset="utf-8"><title>{html.escape(title)}</title>'
            '<style>body{font-family:system-ui,sans-serif;margin:16px}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px 8px;font-size:13px}</style>'
            f'<h1>{html.escape(title)}</h1><div id="map">{render_svg(points, routes, **kw)}</div>'
            f'<p>점에 마우스를 올리면 경로·순서가 뜹니다. 회색 점 = 경로에 없음, 검은 네모 = 거점.</p>{route_table_html(routes, metrics)}</html>')


def main():
    import random
    rnd = random.Random(3)
    pts = {f"P{i:02d}": (rnd.uniform(0, 100), rnd.uniform(0, 100)) for i in range(1, 25)}
    pts["D"] = (50.0, 50.0)
    ids = sorted(p for p in pts if p != "D")
    routes = [{"id": f"R{k + 1}", "stops": ["D"] + ids[k::3] + ["D"]} for k in range(3)]
    metrics = {r["id"]: {"지점": len(r["stops"]) - 2} for r in routes}
    with open("demo_map.html", "w", encoding="utf-8") as f:
        f.write(render_html(pts, routes, title="데모 경로 지도", depots=("D",), metrics=metrics))
    print("demo_map.html 생성: 경로", len(routes), "개, 점", len(pts), "개")


if __name__ == "__main__":
    main()
