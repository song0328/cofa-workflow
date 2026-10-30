# 날짜·시간·기간·SLA

날짜 버그는 대부분 **경계**와 **시간대**에서 난다. 규칙을 문장으로 확정하고, 계산은 한 함수로 모은다.

## 담당자에게 물을 것 (하나씩)
- "시작일과 종료일을 둘 다 포함해서 세나요?"
- "주말·공휴일은 빼나요? 공휴일 목록은 어디 것을 쓰나요?" (제공 파일이 있으면 묻지 않음)
- "정확히 마감 시각(예: 18:00:00)에 들어온 건은 마감 전인가요?"
- "시간은 어느 시간대 기준인가요?" (보통 한국 시간 KST, +09:00)
- "업무 시간 밖에는 SLA 시계가 멈추나요?" / "보류 상태에서는 멈추나요?"
- "말일·윤년(2월 29일)은 어떻게 처리하나요?" (월 단위 계산이 있을 때)

## 흔한 함정
| 함정 | 막는 법 |
|---|---|
| `new Date('2026-11-02')`가 **UTC 자정** → 한국에선 전날 09시처럼 보임 | 날짜만 다룰 땐 문자열 `YYYY-MM-DD` 그대로 비교하거나 UTC 기준으로만 계산 |
| 하루 = 86400000ms 가정 (서머타임 지역) | 날짜는 UTC로 하루씩 더한다 |
| 포함/제외 혼동 (`<` vs `<=`) | 규칙을 "이상·이하·초과·미만"으로 적고 테스트로 고정 |
| 공휴일이 주말과 겹쳐 두 번 뺌 | 날짜마다 "근무일인가?" 한 번만 판단 |
| 종료일 < 시작일 허용 | 입력 검증 오류 |
| 월 더하기: 1/31 + 1개월 | 규칙 확인(말일로 맞춤 등), 가정 기록 |
| 문자열 날짜 형식 섞임 (`2026/11/2`, `11-02-2026`) | 입력 형식을 하나로 검증, 아니면 오류 |
| 현재 시각을 코드 곳곳에서 `Date.now()` | "기준 시각"을 인자로 받기 → 테스트가 고정됨 |

## 구현 요령
```js
// 날짜 문자열(YYYY-MM-DD)만으로 하루씩 순회 — 시간대 영향 없음
const addDays = (d, n) => { const t = new Date(d + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + n); return t.toISOString().slice(0, 10); };
const dow = d => new Date(d + 'T00:00:00Z').getUTCDay(); // 0=일 6=토
function workdays(start, end, holidays) {
  const off = new Set(holidays); let n = 0;
  for (let d = start; d <= end; d = addDays(d, 1)) if (dow(d) % 6 !== 0 && !off.has(d)) n++;
  return n;
}
const valid = d => { if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return false; const t = new Date(d + 'T00:00:00Z'); return !isNaN(t) && t.toISOString().slice(0, 10) === d; }; // 2026-02-30·2026-13-01 거절
```
```python
from datetime import date, datetime, timedelta, timezone
KST = timezone(timedelta(hours=9))
d = date.fromisoformat("2026-11-02")          # 잘못된 날짜는 ValueError
now = datetime.now(KST)                         # 시간대 붙은 현재 시각
```
- 기간 겹침: `a.start <= b.end && b.start <= a.end` (양끝 포함일 때).
- SLA: "업무 시간만 센다"면 분 단위로 업무 구간과 겹치는 시간만 더한다. 보류 구간은 이벤트 이력으로 빼고 센다.

## 검사 사례
- 금요일~월요일 → 근무일 2 / 토요일 하루 → 0 (오류 여부는 규칙대로)
- 공휴일 하루 / 공휴일이 토요일
- 정확히 마감 시각, 1초 전, 1초 후
- 2월 28일·29일(윤년 2028), 12/31 → 1/1
- `2026-02-30`, `2026/11/02` → 형식 오류
