// node:test 표 기반 테스트 틀 — 실행: node --test node-test.cjs
// 기대값은 README·담당자 답에서 정한다(구현 코드를 정답으로 쓰지 않는다). 각 줄에 출처를 적는다.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');

// 예시 대상: 과제 함수로 바꾼다. (예: const { workdays } = require('./src/leave.js');)
function workdays(start, end, holidays = []) {
  const add = (d, n) => { const t = new Date(d + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + n); return t.toISOString().slice(0, 10); };
  const off = new Set(holidays); let n = 0;
  for (let d = start; d <= end; d = add(d, 1)) { const w = new Date(d + 'T00:00:00Z').getUTCDay(); if (w % 6 && !off.has(d)) n++; }
  return n;
}

const cases = [
  // [이름, 입력, 기대, 출처]
  ['정상: 월~화', ['2026-11-02', '2026-11-03'], 2, '담당자 답(인사팀): 근무일만 센다'],
  ['경계: 토요일 하루', ['2026-11-07', '2026-11-07'], 0, '담당자 답: 주말 제외'],
  ['경계: 금~월', ['2026-11-06', '2026-11-09'], 2, '주말 2일 제외'],
  ['휴일 제외', ['2026-11-02', '2026-11-03', ['2026-11-03']], 1, '제공 holidays 목록'],
];

for (const [name, args, expected, source] of cases) {
  test(`${name} (${source})`, () => assert.equal(workdays(...args), expected));
}
