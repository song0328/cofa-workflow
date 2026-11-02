// 화면 동작 틀(빌드·라이브러리 없이). 규칙:
// ① fetch는 4xx/5xx에도 예외를 내지 않는다 → res.ok를 직접 본다 ② 요청 중에는 버튼을 끈다(중복 제출 방지)
// ③ 값은 textContent로만 넣는다(innerHTML 금지 — 입력값이 HTML로 실행되지 않게) ④ 빈 목록·로딩·오류·성공 상태를 모두 보여 준다
const $ = id => document.getElementById(id);

async function api(path, options = {}) {
  try {
    const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  } catch {
    return { ok: false, status: 0, data: { error: 'NETWORK' } };   // 서버가 꺼졌거나 연결이 끊김
  }
}

const MESSAGES = { NAME_REQUIRED: '이름을 입력해 주세요.', INVALID_QTY: '수량은 1 이상의 정수입니다.', NETWORK: '서버에 연결할 수 없습니다. 잠시 뒤 다시 시도해 주세요.' };
function show(text, kind) { const m = $('msg'); m.textContent = text; m.className = `msg ${kind || ''}`; }

function row(cells) {
  const tr = document.createElement('tr');
  cells.forEach(([text, cls]) => { const td = document.createElement('td'); td.textContent = text; if (cls) td.className = cls; tr.append(td); });
  return tr;
}

async function load() {
  const list = $('list');
  list.replaceChildren(row([['불러오는 중…']]));
  const r = await api('/api/items');
  if (!r.ok) return list.replaceChildren(row([[MESSAGES[r.data.error] || '목록을 불러오지 못했습니다.']]));
  const items = r.data.items || [];
  list.replaceChildren(...(items.length ? items.map(it => row([[it.name], [String(it.qty), 'num']])) : [row([['표시할 데이터가 없습니다.']])]));
}

$('form').addEventListener('submit', async e => {
  e.preventDefault();
  const btn = $('save'); btn.disabled = true; show('저장 중…');
  try {
    const r = await api('/api/items', { method: 'POST', body: JSON.stringify({ name: $('name').value, qty: Number($('qty').value) }) });
    if (!r.ok) return show(MESSAGES[r.data.error] || `저장 실패(${r.status})`, 'error');
    show('저장했습니다.', 'ok'); $('form').reset(); await load();
  } finally { btn.disabled = false; }
});

load();
