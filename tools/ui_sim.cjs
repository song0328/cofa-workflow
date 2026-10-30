#!/usr/bin/env node
// 브라우저 없이 HTML 화면을 흉내 내 "선택 → 클릭 → 결과 읽기"를 해 보는 도구 (Node 표준 기능만).
// 쓰는 법:
//   node ui_sim.cjs index.html "set employeeId=E1" "set start=2026-11-07" "click request" "read message balances"
//   node ui_sim.cjs index.html --list        # id가 있는 칸·버튼 목록
// 명령: set <id>=<값> · click <id> · submit <id> · read <id> [<id>…] · options <id>
// 한계: 진짜 브라우저가 아니다. 레이아웃·CSS·fetch·서버 응답은 확인하지 못한다. 화면 확인은 사람이 따로 한다.
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');

const [file, ...steps] = process.argv.slice(2);
if (!file) { console.error('사용법: node ui_sim.cjs index.html "set id=값" "click id" "read id"'); process.exit(2); }
const base = path.dirname(path.resolve(file));
const html = fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '');

const strip = s => String(s).replace(/<script[\s\S]*?<\/script>/gi, '').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();
const attr = (tag, name) => { const m = tag.match(new RegExp('\\b' + name + '\\s*=\\s*("([^"]*)"|\'([^\']*)\'|([^\\s>]+))', 'i')); return m ? (m[2] ?? m[3] ?? m[4]) : null; };

const byId = new Map();
class El {
  constructor(tag, id) { this.tagName = tag.toUpperCase(); this.id = id || ''; this.children = []; this.attrs = {}; this.listeners = {}; this.style = {}; this.dataset = {}; this._text = ''; this._value = ''; this.checked = false; this.disabled = false; this.hidden = false; this.parentNode = null;
    this.classList = { _s: new Set(), add: (...c) => c.forEach(x => this.classList._s.add(x)), remove: (...c) => c.forEach(x => this.classList._s.delete(x)), toggle: (c, f) => { const on = f ?? !this.classList._s.has(c); on ? this.classList._s.add(c) : this.classList._s.delete(c); return on; }, contains: c => this.classList._s.has(c) }; }
  get value() { if (this.tagName === 'SELECT' && this._value === '' && this.options.length) return this.options[0].value; return this._value; }
  set value(v) { this._value = String(v); }
  get options() { return this.children.filter(c => c.tagName === 'OPTION'); }
  get selectedIndex() { return this.options.findIndex(o => o.value === this.value); }
  get textContent() { return this.children.length ? this.children.map(c => c.textContent).join(this.tagName === 'TR' ? ' | ' : this.tagName.match(/^(TBODY|TABLE|UL|OL|SELECT|DIV|SECTION)$/) ? '\n' : ' ') : this._text; }
  set textContent(t) { this.children = []; this._text = String(t ?? ''); }
  get innerText() { return this.textContent; } set innerText(t) { this.textContent = t; }
  get innerHTML() { return this._text; }
  set innerHTML(h) { this.children = []; const s = String(h ?? '');
    const rows = s.match(/<(tr|li|option)\b[\s\S]*?<\/\1>/gi);
    if (rows) for (const r of rows) { const tag = r.match(/^<(\w+)/)[1]; const c = new El(tag); if (tag.toLowerCase() === 'option') c.value = attr(r, 'value') ?? strip(r);
      if (tag.toLowerCase() === 'tr') for (const td of r.match(/<t[dh]\b[\s\S]*?<\/t[dh]>/gi) || []) { const d = new El('td'); d._text = strip(td); c.appendChild(d); } else c._text = strip(r); this.appendChild(c); }
    else this._text = strip(s); }
  append(...n) { n.forEach(x => this.appendChild(typeof x === 'string' ? Object.assign(new El('#text'), { _text: x }) : x)); }
  appendChild(n) { n.parentNode = this; this.children.push(n); if (n.id) byId.set(n.id, n); return n; }
  prepend(...n) { n.reverse().forEach(x => { x.parentNode = this; this.children.unshift(x); }); }
  replaceChildren(...n) { this.children = []; this._text = ''; this.append(...n); }
  insertAdjacentHTML(_p, h) { const keep = this.children; this.innerHTML = h; this.children = keep.concat(this.children); }
  remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter(c => c !== this); }
  setAttribute(k, v) { this.attrs[k] = String(v); if (k === 'id') { this.id = v; byId.set(v, this); } if (k === 'value') this.value = v; }
  getAttribute(k) { return this.attrs[k] ?? null; } removeAttribute(k) { delete this.attrs[k]; }
  addEventListener(t, f) { (this.listeners[t] ||= []).push(f); } removeEventListener(t, f) { this.listeners[t] = (this.listeners[t] || []).filter(x => x !== f); }
  querySelector(s) { return query(s, this)[0] || null; } querySelectorAll(s) { return query(s, this); }
  closest() { return null; } focus() {} blur() {} reset() {}
  fire(type) { const ev = { type, target: this, currentTarget: this, preventDefault() {}, stopPropagation() {} }; const h = this['on' + type]; if (typeof h === 'function') h.call(this, ev); for (const f of this.listeners[type] || []) f.call(this, ev); }
  click() { this.fire('click'); }
}
function all(root) { const out = []; const walk = n => { for (const c of n.children) { out.push(c); walk(c); } }; walk(root); return out; }
function query(sel, root) { const s = sel.trim();
  if (s.startsWith('#')) { const e = byId.get(s.slice(1).split(/[\s.\[]/)[0]); return e ? [e] : []; }
  const pool = root === doc ? [...byId.values(), ...all(body)] : all(root);
  const m = s.match(/^(\w+)?(?:\[name=["']?([^"'\]]+)["']?\])?(?:\.([\w-]+))?$/); if (!m) return [];
  return [...new Set(pool)].filter(e => (!m[1] || e.tagName === m[1].toUpperCase()) && (!m[2] || e.attrs.name === m[2]) && (!m[3] || e.classList.contains(m[3]))); }

const body = new El('body');
// HTML에서 id가 있는 요소를 만든다. select 안의 option, input의 value·type도 가져온다.
for (const m of html.matchAll(/<(\w+)\b([^>]*\bid\s*=[^>]*)>/gi)) {
  const [tag, , rest] = [m[1], m[0], m[0]]; const id = attr(rest, 'id'); if (!id) continue;
  const e = new El(tag, id); for (const k of ['type', 'name', 'value', 'placeholder', 'class']) { const v = attr(rest, k); if (v != null) e.setAttribute(k, v); }
  if (e.attrs.class) e.attrs.class.split(/\s+/).forEach(c => e.classList.add(c));
  if (/\bchecked\b/i.test(rest)) e.checked = true;
  if (tag.toLowerCase() === 'select') { const end = html.indexOf('</select>', m.index); const inner = html.slice(m.index, end);
    for (const o of inner.matchAll(/<option\b([^>]*)>([\s\S]*?)<\/option>/gi)) { const oe = new El('option'); oe.value = attr(o[1], 'value') ?? strip(o[2]); oe._text = strip(o[2]); e.appendChild(oe); if (/\bselected\b/i.test(o[1])) e.value = oe.value; } }
  else if (tag.toLowerCase() === 'textarea') { const end = html.indexOf('</textarea>', m.index); e.value = html.slice(m.index + m[0].length, end); }
  e._pos = m.index; byId.set(id, e); body.appendChild(e);
}
// form은 id가 없어도 만든다(제출 버튼 → submit 연결용).
const forms = [];
for (const m of html.matchAll(/<form\b([^>]*)>/gi)) { const id = attr(m[1], 'id'); const f = (id && byId.get(id)) || new El('form', id); if (!f.parentNode) body.appendChild(f); forms.push({ f, start: m.index, end: html.indexOf('</form>', m.index) }); }
const formOf = e => (forms.find(r => e._pos > r.start && e._pos < r.end) || {}).f;

const docListeners = {};
const doc = { body, documentElement: body, readyState: 'loading',
  getElementById: id => byId.get(id) || null, querySelector: s => query(s, doc)[0] || null, querySelectorAll: s => query(s, doc),
  getElementsByTagName: t => query(t, doc), getElementsByClassName: c => query('.' + c, doc),
  createElement: t => new El(t), createTextNode: t => Object.assign(new El('#text'), { _text: String(t) }), createDocumentFragment: () => new El('fragment'),
  addEventListener: (t, f) => (docListeners[t] ||= []).push(f), removeEventListener() {} };
const store = new Map();
const logs = [];
const sandbox = { document: doc, console: { log: (...a) => logs.push(a.join(' ')), error: (...a) => logs.push('[error] ' + a.join(' ')), warn: (...a) => logs.push('[warn] ' + a.join(' ')), info() {} },
  localStorage: { getItem: k => store.has(k) ? store.get(k) : null, setItem: (k, v) => store.set(k, String(v)), removeItem: k => store.delete(k), clear: () => store.clear() },
  alert: m => logs.push('[alert] ' + m), confirm: () => true, prompt: () => '', setTimeout: (f) => { f(); return 0; }, clearTimeout() {}, requestAnimationFrame: f => f(0),
  Intl, Date, Math, JSON, Map, Set, Promise, structuredClone, navigator: { language: 'ko-KR' }, location: { hash: '', search: '', href: 'http://localhost/' } };
sandbox.window = sandbox; sandbox.self = sandbox; sandbox.globalThis = sandbox; sandbox.addEventListener = (t, f) => (docListeners[t] ||= []).push(f);
vm.createContext(sandbox);

let failed = false;
for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
  const src = attr(m[1], 'src'); const type = attr(m[1], 'type');
  if (type && !/javascript|module/i.test(type)) continue;
  const name = src || 'inline <script>'; let code = m[2];
  if (src) { if (/^https?:/i.test(src)) { console.log(`· 건너뜀(외부): ${src}`); continue; } const p = path.join(base, src); if (!fs.existsSync(p)) { console.log(`✗ 파일 없음: ${src}`); failed = true; continue; } code = fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''); }
  try { vm.runInContext(code, sandbox, { filename: name }); } catch (e) { console.log(`✗ 스크립트 오류 (${name}): ${e.message}`); failed = true; }
}
doc.readyState = 'complete';
for (const t of ['DOMContentLoaded', 'load']) for (const f of docListeners[t] || []) { try { f({ type: t }); } catch (e) { console.log(`✗ ${t} 처리 오류: ${e.message}`); failed = true; } }

const show = id => { const e = byId.get(id); if (!e) return `${id}: (없음)`; const t = /^(INPUT|SELECT|TEXTAREA)$/.test(e.tagName) ? `값=${JSON.stringify(e.value)}` : e.textContent.trim(); return `${id}: ${t || '(비어 있음)'}`; };
if (steps[0] === '--list') { for (const [id, e] of byId) if (e.parentNode === body) console.log(`${e.tagName.toLowerCase().padEnd(8)} #${id}${e.tagName === 'SELECT' ? '  선택지: ' + e.options.map(o => o.value).join(', ') : ''}`); process.exit(failed ? 1 : 0); }

for (const step of steps) {
  const [cmd, ...rest] = step.trim().split(/\s+/); const arg = rest.join(' ');
  try {
    if (cmd === 'set') { const i = arg.indexOf('='); const id = arg.slice(0, i), v = arg.slice(i + 1); const e = byId.get(id); if (!e) throw Error(`#${id} 없음`);
      if (e.tagName === 'SELECT' && e.options.length && !e.options.some(o => o.value === v)) console.log(`! #${id}에 "${v}" 선택지가 없음 (있는 것: ${e.options.map(o => o.value).join(', ')})`);
      if (e.attrs.type === 'checkbox' || e.attrs.type === 'radio') e.checked = v === 'true' || v === 'on'; else e.value = v; e.fire('input'); e.fire('change'); console.log(`→ set ${id}=${v}`); }
    else if (cmd === 'click') { const e = byId.get(arg); if (!e) throw Error(`#${arg} 없음`); e.click(); if (e.attrs.type === 'submit' || (e.tagName === 'BUTTON' && !e.attrs.type)) { const f = formOf(e); if (f) f.fire('submit'); } console.log(`→ click ${arg}`); }
    else if (cmd === 'submit') { const e = byId.get(arg) || (arg === 'form' ? forms[0]?.f : null); if (!e) throw Error(`#${arg} 없음`); e.fire('submit'); console.log(`→ submit ${arg}`); }
    else if (cmd === 'read') rest.forEach(id => console.log('  ' + show(id).replace(/\n/g, '\n    ')));
    else if (cmd === 'options') { const e = byId.get(arg); console.log(`  ${arg} 선택지: ${e ? e.options.map(o => `${o.value}(${o.textContent})`).join(', ') || '(없음)' : '(없음)'}`); }
    else throw Error(`모르는 명령: ${cmd}`);
  } catch (e) { console.log(`✗ ${step}: ${e.message}`); failed = true; }
}
for (const l of logs) console.log('  console ' + l);
process.exit(failed ? 1 : 0);
