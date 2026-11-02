# 자료 품질 — 중복·정정·취소·집계

보고서 숫자가 틀리는 원인은 계산보다 **어떤 행을 세느냐**다. 세기 전에 "포함·제외 규칙"을 표로 확정한다.

## 담당자에게 물을 것 (하나씩)
- "같은 ○○ID가 여러 번 나오면 무엇을 기준으로 하나요?" (최신 / 최초 / 합산)
- "정정 기록은 원래 기록을 대체하나요, 더하나요?"
- "취소·철회된 건은 세나요?"
- "기준일(언제까지의 자료)은 언제인가요? 기간 밖 날짜는?"
- "비율의 분모는 무엇인가요?" (전체 / 응답자 / 유효 건)
- "두 파일의 숫자가 다르면 어느 쪽이 기준인가요?"

## 흔한 함정
| 함정 | 막는 법 |
|---|---|
| 중복을 그냥 셈 | 키 정의 → `tools/csv_check.py --key 열`로 중복부터 확인 |
| 정정·취소 행을 일반 행처럼 집계 | 상태·유형 열 값 목록부터 뽑아 보기 (`cut`/`sort | uniq -c`) |
| BOM·인코딩 (`﻿열이름`) | Python `encoding='utf-8-sig'`, Node `.replace(/^﻿/, '')` |
| 숫자 문자열 `"1,200"`, 빈 칸, `-`, `N/A` | 정규화 규칙 하나, 변환 실패 행은 따로 세서 보고 |
| 날짜 형식 섞임, 기간 밖 | 형식 검증, 기간 밖은 제외 사유와 건수 기록 |
| 분모 바뀜 | 비율마다 "분자/분모" 숫자를 함께 표시 |
| 앞뒤 공백·대소문자 다른 같은 값 | `trim`·대소문자 통일 후 비교 (규칙으로 기록) |
| 원자료 수정 | **원본은 그대로**, 정제 결과는 새 파일 |
| 빈 문자열을 `Number()`에 → 0 | `Number('')`·`Number(' ')`은 0이다. 빈칸을 먼저 거른 뒤 변환, `Number.isFinite` 확인 |
| 헤더 중복·빈 헤더, 줄마다 열 수 다름 | 가져올 때 거절하고 몇 번째 줄인지 알린다(DictReader는 조용히 덮어쓰거나 `None` 키로 넣는다) |
| 내보낸 CSV를 엑셀이 수식으로 실행(`=HYPERLINK(...)`) | 내보낼 때 `= + - @`·탭으로 시작하는 칸 앞에 `'`를 붙인다(CSV를 내보낼 때만) |
| AI가 쓴 요약 숫자를 그대로 인용 | 숫자마다 계산 명령으로 재현 |

## 구현 요령
- 먼저 `python3 <키트>/tools/data_profile.py <자료 폴더>`로 형식·빈칸·범위·표기 변형·파일 간 키 불일치를 한 번에 본다(변경본이 있으면 `--compare`). 찾은 것은 `playbooks/edge-hunt.md`대로 근거 붙은 질문으로.
```python
import csv
from collections import Counter
rows = list(csv.DictReader(open("data.csv", encoding="utf-8-sig", newline="")))
print(Counter(r["status"] for r in rows))                     # 값 목록부터
dup = [k for k, n in Counter(r["id"] for r in rows).items() if n > 1]
latest = {}
for r in sorted(rows, key=lambda r: (r["id"], r["updated_at"])):  # 키별 최신 1건
    latest[r["id"]] = r
```
- 제외 규칙마다 **제외 건수**를 센다: "전체 120 → 중복 4 · 취소 7 · 기간 밖 2 제외 → 107". 보고서 첫 줄에 이 흐름.
- 결과 숫자는 스크립트로 재생성 가능하게(명령 한 줄을 보고서에).
```python
def read_strict(path):                                   # 가져오기: BOM 제거, 헤더·열 수 검사
    rows = list(csv.reader(open(path, encoding="utf-8-sig", newline="")))
    head = [h.strip() for h in rows[0]]
    if "" in head or len(set(head)) != len(head): raise ValueError(f"헤더 문제: {head}")
    bad = [i + 2 for i, r in enumerate(rows[1:]) if len(r) != len(head)]
    if bad: raise ValueError(f"열 수 다른 줄: {bad[:5]}")
    return [dict(zip(head, r)) for r in rows[1:]]
safe_cell = lambda v: "'" + v if str(v)[:1] in ("=", "+", "-", "@", "	") else v   # 내보내기
```
```js
const num = s => (String(s ?? '').trim() === '' ? null : Number(s));   // 빈칸 → null(0 아님), NaN이면 오류 목록
```

## 검사 사례
- 같은 키 2행(정정 전·후) → 1건, 최신 값
- 취소 행 1개 → 집계 제외, 제외 건수 1
- 빈 금액·`N/A` → 오류 목록으로
- 분모 0 → 0으로 나누기 대신 "해당 없음"
- 빈 금액 `""` → 0이 아니라 오류·제외 / 헤더 중복·열 수 다른 줄 → 거절 + 줄 번호
- 이름이 `=1+1`인 행을 내보내기 → 파일에 `'=1+1`
- 합계 대조: 분류별 합 = 전체
