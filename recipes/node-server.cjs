// 패키지 없이 쓰는 JSON API + 정적 파일 서버 (Node 22 표준 기능만)
// 실행: node node-server.cjs   (PORT=3000 기본, 0.0.0.0에 바인딩, PORT=0이면 빈 포트)
// 과제 README의 경로·필드·상태 코드·오류 형식에 맞게 고쳐 쓴다.
// 안전 기본값: 화면 파일은 public/ 안의 허용 목록만 내보낸다(데이터·소스·.env 노출 금지) ·
//            저장 파일이 깨졌으면 빈 데이터로 덮어쓰지 않고 멈춘다 · 쓰기는 큐 하나로 줄 세운다 ·
//            요청마다 JSON 한 줄 로그와 X-Request-Id.
'use strict';
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const PORT = Number(process.env.PORT ?? 3000);
const PUBLIC = path.join(__dirname, 'public');        // 화면 파일 폴더(코드·데이터와 분리)
const STATIC = { '/': 'index.html', '/index.html': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css' }; // 허용 목록
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, 'data');   // Docker에서는 DATA_DIR=/data(볼륨)
const DATA = path.join(DATA_DIR, 'data.json');
const MAX_BODY = 1024 * 1024;                         // 본문 1MB 제한
const STARTED = new Date().toISOString();

// 저장소: 파일이 없을 때(ENOENT)만 새로 시작. 깨졌거나 권한 오류면 덮어쓰지 않고 오류로 멈춘다(원본 보존).
function load() {
  try { return JSON.parse(fs.readFileSync(DATA, 'utf8')); }
  catch (e) {
    if (e.code === 'ENOENT') return { items: [], seq: 0 };
    throw Object.assign(new Error(`저장 파일을 읽을 수 없음(덮어쓰지 않음): ${e.message}`), { status: 500, code: 'STORE_UNREADABLE' });
  }
}
let db;
try { db = load(); } catch (e) { db = null; console.error(e.message); }
function save() {                                     // 임시 파일에 쓰고 바꿔치기(쓰다 끊겨도 원본 보존)
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(DATA + '.tmp', JSON.stringify(db, null, 2));
  fs.renameSync(DATA + '.tmp', DATA);
}
let queue = Promise.resolve();                        // 읽기→수정→저장을 한 줄로(동시 요청이 서로 덮지 않게)
const serial = task => { const run = queue.then(task); queue = run.catch(() => {}); return run; };

const send = (res, status, body) => {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'X-Request-Id': res.reqId });
  res.end(JSON.stringify(body));
};
const fail = (res, status, code) => { res.errorCode = code; send(res, status, { error: code }); };

function readJson(req) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on('data', c => { size += c.length; if (size <= MAX_BODY) chunks.push(c); });   // 넘치면 버리기만(응답은 끝에서 413)
    req.on('end', () => {
      if (size > MAX_BODY) return reject(Object.assign(Error('TOO_LARGE'), { status: 413 }));
      if (!chunks.length) return resolve({});
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); } catch { reject(Object.assign(Error('INVALID_JSON'), { status: 400 })); } });
    req.on('error', reject);
  });
}

// ── 업무 로직: 서버와 테스트가 같이 쓰도록 순수 함수로(검증 → 반영) ──
function validateItem(input) {
  const name = typeof input.name === 'string' ? input.name.trim() : '';
  if (!name) return { error: 'NAME_REQUIRED' };
  if (!Number.isInteger(input.qty) || input.qty < 1) return { error: 'INVALID_QTY' };
  return { value: { name, qty: input.qty } };
}
function createItem(input) {
  const v = validateItem(input);
  if (v.error) return { status: 400, error: v.error };
  if (!db) return { status: 500, error: 'STORE_UNREADABLE' };
  const item = { id: 'I' + (++db.seq), ...v.value };
  db.items.push(item); save();                        // 저장이 끝난 뒤에만 201
  return { status: 201, item };
}

const routes = {
  'GET /health': async (req, res) => send(res, db ? 200 : 503, { ok: !!db, items: db ? db.items.length : null, started: STARTED }),
  'GET /api/items': async (req, res) => db ? send(res, 200, { items: [...db.items].sort((a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id)) }) : fail(res, 500, 'STORE_UNREADABLE'),
  'POST /api/items': async (req, res) => { const body = await readJson(req); const r = await serial(() => createItem(body)); r.error ? fail(res, r.status, r.error) : send(res, r.status, r.item); },
  'GET /api/items/:id': async (req, res, id) => { const it = db && db.items.find(x => x.id === id); it ? send(res, 200, it) : fail(res, 404, 'NOT_FOUND'); },
};

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };
function serveStatic(req, res, urlPath) {
  const name = STATIC[urlPath];                       // 허용 목록에 없으면 404(소스·데이터·.env를 내보내지 않는다)
  if (!name) return fail(res, 404, 'NOT_FOUND');
  fs.readFile(path.join(PUBLIC, name), (e, buf) => {
    if (e) return fail(res, 404, 'NOT_FOUND');
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(name)] || 'text/plain; charset=utf-8', 'X-Content-Type-Options': 'nosniff', 'X-Request-Id': res.reqId }); res.end(buf);
  });
}

const server = http.createServer(async (req, res) => {
  const t0 = process.hrtime.bigint();
  res.reqId = req.headers['x-request-id'] || crypto.randomUUID().slice(0, 8);
  res.on('finish', () => console.log(JSON.stringify({ ts: new Date().toISOString(), req_id: res.reqId, method: req.method, path: req.url.split('?')[0], status: res.statusCode, ms: Number((process.hrtime.bigint() - t0) / 1000000n), error: res.errorCode })));  // 본문·토큰·개인정보는 로그에 넣지 않는다
  const url = new URL(req.url, 'http://localhost');
  try {
    const exact = routes[`${req.method} ${url.pathname}`];
    if (exact) return await exact(req, res);
    const m = url.pathname.match(/^\/api\/items\/([^/]+)$/);
    if (m && routes[`${req.method} /api/items/:id`]) return await routes[`${req.method} /api/items/:id`](req, res, m[1]);
    if (url.pathname.startsWith('/api/')) return fail(res, 404, 'NOT_FOUND');
    if (req.method === 'GET') return serveStatic(req, res, url.pathname);
    fail(res, 405, 'METHOD_NOT_ALLOWED');
  } catch (e) {
    if (e.status) return fail(res, e.status, e.code || e.message);
    console.error(e); fail(res, 500, 'INTERNAL');                                 // 내부 정보는 로그에만
  }
});

if (require.main === module) server.listen(PORT, '0.0.0.0', () => console.log(`http://0.0.0.0:${server.address().port}`));
module.exports = { validateItem, createItem, server };
