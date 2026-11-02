# 외부 연동·알림 발송·업무 도구(SaaS)

원칙: **실제로 보내지·결제하지·승인하지 않는다.** 과제는 "보낼 내용을 만들고 기록하는 것"까지인 경우가 대부분이다. 실제 동작이 필요해 보이면 담당자에게 한 문장으로 확인한다.

## 담당자에게 물을 것 (하나씩)
- "알림은 실제로 보내나요, 보낼 내용(초안)만 만드나요?"
- "같은 알림이 두 번 나가면 안 되나요?" (중복 방지 기준: 대상+유형+날짜?)
- "외부 API가 실패하면 다시 시도하나요? 몇 번인가요?"
- "업무 도구 화면의 ○○ 버튼을 제가 직접 눌러도 되나요?" (SaaS)
- "업무 도구 화면의 값과 README 값이 다르면 어느 쪽이 기준인가요?"

## 흔한 함정
| 함정 | 막는 법 |
|---|---|
| 실제 메일·문자 발송, 실제 결제·승인 버튼 | 발송 함수는 "보낼 목록"을 반환·기록만. 버튼은 누르지 않는다 |
| 외부 API 키를 코드에 | 환경 변수. 키가 없으면 모의 응답으로 구조만 |
| 실패를 무시 | 실패 건을 따로 모아 보고, 재시도 횟수 상한 |
| 중복 발송 | 보낸 기록(키)으로 이미 보낸 건 건너뜀 |
| 템플릿 변수 빈칸(`{이름}` 그대로) | 필수 변수 검사 |
| 업무 도구 화면의 정보 누락 | 시작할 때 **SaaS 아이콘(네모 4개)**을 눌러 보고, 그 화면의 데이터·공지를 사용자가 AI에게 요약해 전달 |
| 업무 도구 값과 파일 값 충돌 | 둘 다 기록하고 담당자에게 기준 확인 |
| 외부 호출이 멈춰 요청 전체가 멈춤 | 시간 상한(예: 5초). 넘으면 실패로 보고 대체 결과 |
| 발송·결제 같은 비멱등 호출을 자동 재시도 | 자동 재시도 금지(두 번 나간다). 재시도는 조회처럼 멱등인 호출만 |
| 대체(모의) 결과를 실제처럼 표시 | 결과에 `source`(`live` 또는 `fallback`)를 붙이고 화면에 "데모/대체 결과" 표시 |
| 키를 화면 JS·응답에 | 키는 서버 환경 변수에만. 브라우저는 내 서버만 부른다 |

## 구현 요령
```js
function planNotices(items, sentKeys) {           // 실제 발송 없음
  const out = [];
  for (const it of items) {
    const key = `${it.to}|${it.type}|${it.date}`;
    if (sentKeys.has(key)) continue;
    if (!it.to || !it.name) { out.push({ key, error: 'MISSING_FIELD' }); continue; }
    out.push({ key, to: it.to, text: `${it.name}님, ${it.date} ${it.type} 안내입니다.` });
  }
  return out;
}
```
- 외부 호출은 **감싸는 함수 하나**로만 한다(필요할 때만: 실제 외부 호출이 있을 때).
```js
async function callExternal(url, body) {          // 시간 상한 + 출처 표시, 비멱등이면 재시도 없음
  const ac = new AbortController(); const t = setTimeout(() => ac.abort(), 5000);
  try {
    if (!process.env.API_KEY) return { source: 'fallback', data: mock(body) };
    const res = await fetch(url, { method: 'POST', body: JSON.stringify(body), signal: ac.signal,
      headers: { 'content-type': 'application/json', authorization: `Bearer ${process.env.API_KEY}` } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return { source: 'live', data: await res.json() };
  } catch (e) { return { source: 'fallback', data: mock(body), error: String(e.message) }; }
  finally { clearTimeout(t); }
}
```
- Python은 `urllib.request.urlopen(req, timeout=5)`. 대체 결과를 쓸지(또는 오류로 낼지)는 담당자 답대로.

## 검사 사례
- 같은 대상·유형 두 번 → 한 번만 계획됨
- 필수 값 빈칸 → 오류 목록
- 모의 외부 실패 → 실패 목록, 나머지는 진행
- 응답 지연(6초) → 5초에 끊고 `source: fallback`, 화면에 "데모/대체 결과"
- 발송 호출 실패 → 자동으로 두 번 보내지 않음 / 응답·화면 JS에 키 문자열 없음
- 업무 도구 화면에만 있는 조건(예: 최근 공지) 반영 여부
