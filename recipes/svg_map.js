// 점·경로를 SVG로 그리는 브라우저용 틀 (빌드·라이브러리·인터넷 없이, 화면 <script>에 그대로)
// 쓰임: 서버 API가 준 점·경로 JSON을 화면에서 그림 + 표로 보여 준다. Python 버전은 svg_map.py.
// 과제 계약(필드 이름·좌표 형식)에 맞게 복사해 고쳐 쓴다. 과제 파일이 이 키트 경로를 불러오지 않는다.
// 규칙: SVG는 문자열로 만들어 innerHTML에 넣는다(ui_sim도 읽을 수 있게) · 번호 글자는 점이 적을 때만 ·
//       자세한 정보는 <title> 말풍선과 클릭 시 #map-info 칸 · 같은 내용을 표로도 낸다 · 색은 경로 순서대로 고정.
(function (global) {
  const PALETTE = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e', '#17becf', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22'];
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  // points: {id: [x, y]} 또는 mode:'latlon'이면 {id: [lat, lon]}
  function project(points, w, h, pad, mode) {
    const ids = Object.keys(points); if (!ids.length) return {};
    let raw = points;
    if (mode === 'latlon') {
      const k = Math.cos((ids.reduce((a, i) => a + points[i][0], 0) / ids.length) * Math.PI / 180);
      raw = Object.fromEntries(ids.map(i => [i, [points[i][1] * k, points[i][0]]]));
    }
    const xs = ids.map(i => raw[i][0]), ys = ids.map(i => raw[i][1]);
    const minX = Math.min(...xs), minY = Math.min(...ys);
    const s = Math.min((w - 2 * pad) / ((Math.max(...xs) - minX) || 1), (h - 2 * pad) / ((Math.max(...ys) - minY) || 1));
    return Object.fromEntries(ids.map(i => [i, [+(pad + (raw[i][0] - minX) * s).toFixed(1), +(h - pad - (raw[i][1] - minY) * s).toFixed(1)]]));
  }

  // routes: [{id:'R1', stops:['D','A','B','D']}] · opts: {width, height, mode, depots:[], labelLimit, info:{id:'말풍선 글'}}
  function routeMapSVG(points, routes, opts = {}) {
    const w = opts.width || 800, h = opts.height || 560, depots = new Set(opts.depots || []), info = opts.info || {};
    const xy = project(points, w, h, 30, opts.mode);
    const order = {};
    let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="100%" role="img" aria-label="경로 지도"><defs>`;
    routes.forEach((r, i) => { s += `<marker id="arrow${i}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${PALETTE[i % PALETTE.length]}"/></marker>`; });
    s += '</defs><rect width="100%" height="100%" fill="#fafafa"/>';
    routes.forEach((r, i) => {
      const c = PALETTE[i % PALETTE.length], pts = r.stops.filter(p => xy[p]).map(p => xy[p]);
      for (let k = 0; k + 1 < pts.length; k++) s += `<line x1="${pts[k][0]}" y1="${pts[k][1]}" x2="${pts[k + 1][0]}" y2="${pts[k + 1][1]}" stroke="${c}" stroke-width="2" opacity="0.8" marker-end="url(#arrow${i})"/>`;
      r.stops.forEach((p, n) => (order[p] = order[p] || []).push(`${r.id} ${n + 1}번째`));
    });
    const ids = Object.keys(xy).sort(), showLabel = ids.length <= (opts.labelLimit || 40);
    for (const id of ids) {
      const [x, y] = xy[id], tip = esc([id, ...(order[id] || ['경로 없음']), ...(info[id] ? [info[id]] : [])].join(' · '));
      s += depots.has(id)
        ? `<rect data-id="${esc(id)}" x="${x - 7}" y="${y - 7}" width="14" height="14" fill="#222"><title>${tip}</title></rect>`
        : `<circle data-id="${esc(id)}" cx="${x}" cy="${y}" r="5" fill="${order[id] ? '#fff' : '#999'}" stroke="#333" style="cursor:pointer"><title>${tip}</title></circle>`;
      if (showLabel) s += `<text x="${x + 7}" y="${y - 7}" font-size="11" fill="#333">${esc(id)}</text>`;
    }
    return s + '</svg>';
  }

  // metrics: {R1: {'거리': 12.3, '인원': 40}} (선택)
  function routeTableHTML(routes, metrics = {}) {
    const keys = [...new Set(Object.values(metrics).flatMap(m => Object.keys(m)))].sort();
    const rows = routes.map((r, i) => `<tr><td><span style="color:${PALETTE[i % PALETTE.length]}">■</span> ${esc(r.id)}</td><td>${r.stops.length}</td><td>${r.stops.map(esc).join(' → ')}</td>${keys.map(k => `<td>${esc((metrics[r.id] || {})[k] ?? '')}</td>`).join('')}</tr>`).join('');
    return `<table id="route-table"><thead><tr><th>경로</th><th>지점 수</th><th>순서</th>${keys.map(k => `<th>${esc(k)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
  }

  // 화면에 붙이기: mapEl에 그림, tableEl에 표, infoEl에 클릭한 점의 정보
  function renderRouteMap(mapEl, points, routes, opts = {}) {
    mapEl.innerHTML = routeMapSVG(points, routes, opts);
    if (opts.tableEl) opts.tableEl.innerHTML = routeTableHTML(routes, opts.metrics);
    if (opts.infoEl && mapEl.addEventListener) {
      mapEl.addEventListener('click', e => {
        const id = e.target && e.target.getAttribute && e.target.getAttribute('data-id');
        if (id) opts.infoEl.textContent = (e.target.querySelector('title') || {}).textContent || id;
      });
    }
  }

  const api = { routeMapSVG, routeTableHTML, renderRouteMap, project };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.RouteMap = api;
})(typeof window !== 'undefined' ? window : globalThis);

// 확인(Node): node -e "const m=require('./svg_map.js');console.log(m.routeTableHTML([{id:'R1',stops:['D','A','D']}]))"
