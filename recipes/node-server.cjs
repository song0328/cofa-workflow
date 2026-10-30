// 패키지 없이 쓰는 JSON API + 정적 파일 서버 (Node 22 표준 기능만)
// 실행: node node-server.cjs   (PORT=3000 기본, 0.0.0.0에 바인딩)
// 과제 README의 경로·필드·상태 코드·오류 형식에 맞게 고쳐 쓴다.
'use strict';
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const PORT = Number(process.env.PORT || 3000);
const ROOT = path.resolve(__dirname);                 // 정적 파일 기준 폴더
const DATA = path.join(ROOT, 'data.json');            // 간단한 저장소(필요 없으면 메모리만)
const MAX_BODY = 1024 * 1024;                         // 본문 1MB 제한

let db = { items: [], seq: 0 };
try { db = JSON.parse(fs.readFileSync(DATA, 'utf8')); } catch { /* 처음엔 없음 */ }
function save() {                                     // 임시 파일에 쓰고 바꿔치기(쓰다 끊겨도 원본 보존)
  fs.writeFileSync(DATA + '.tmp', JSON.stringify(db, null, 2));
  fs.renameSync(DATA + '.tmp', DATA);
}

const send = (res, status, body) => {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(body));
};
const fail = (res, status, code) => send(res, status, { error: code });

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

// ── 업무 로직: 서버와 테스트가 같이 쓰도록 순수 함수로 ──
function createItem(input) {
  const name = typeof input.name === 'string' ? input.name.trim() : '';
  if (!name) return { status: 400, error: 'NAME_REQUIRED' };
  if (!Number.isInteger(input.qty) || input.qty < 1) return { status: 400, error: 'INVALID_QTY' };
  const item = { id: 'I' + (++db.seq), name, qty: input.qty };
  db.items.push(item); save();
  return { status: 201, item };
}

const routes = {
  'GET /api/items': async (req, res) => send(res, 200, { items: [...db.items].sort((a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id)) }),
  'POST /api/items': async (req, res) => { const r = createItem(await readJson(req)); r.error ? fail(res, r.status, r.error) : send(res, r.status, r.item); },
  'GET /api/items/:id': async (req, res, id) => { const it = db.items.find(x => x.id === id); it ? send(res, 200, it) : fail(res, 404, 'NOT_FOUND'); },
};

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.cjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png' };
function serveStatic(req, res, urlPath) {
  const rel = decodeURIComponent(urlPath === '/' ? '/index.html' : urlPath);
  const file = path.resolve(ROOT, '.' + rel);
  if (!file.startsWith(ROOT + path.sep)) return fail(res, 403, 'FORBIDDEN');     // ../ 이탈 방지
  fs.readFile(file, (e, buf) => {
    if (e) return fail(res, 404, 'NOT_FOUND');
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' }); res.end(buf);
  });
}

const server = http.createServer(async (req, res) => {
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
    if (e.status) return fail(res, e.status, e.message);
    console.error(e); fail(res, 500, 'INTERNAL');                                 // 내부 정보는 로그에만
  }
});

if (require.main === module) server.listen(PORT, '0.0.0.0', () => console.log(`http://0.0.0.0:${PORT}`));
module.exports = { createItem, server };
