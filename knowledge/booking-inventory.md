# 예약·재고·한정 수량

핵심 불변식: **남은 수량은 0 미만이 되지 않는다**, **같은 요청은 한 번만 반영된다.** 모든 테스트가 이 둘을 지키는지 본다.

## 담당자에게 물을 것 (하나씩)
- "예약할 때 바로 수량을 줄이나요, 확정할 때 줄이나요?"
- "예약이 일정 시간 안에 확정되지 않으면 풀리나요? 몇 분인가요?"
- "취소하면 수량을 바로 돌려놓나요?"
- "남은 수량보다 많이 요청하면 거절인가요, 가능한 만큼만인가요?"
- "같은 사람이 같은 것을 여러 번 예약할 수 있나요?"
- "비활성·품절 상품은 예약 목록에서 빼나요, 오류인가요?"

## 흔한 함정
| 함정 | 막는 법 |
|---|---|
| 검사와 차감 사이에 다른 요청 (동시성) | 한 함수 안에서 "검사 → 차감"을 끊김 없이. 파일·DB면 한 번에 쓰기(트랜잭션) |
| 같은 요청 재전송으로 두 번 차감 | 요청 ID(멱등 키)를 기록, 같은 ID는 첫 결과를 그대로 반환 |
| 취소 두 번으로 두 번 복원 | 상태가 "예약됨"일 때만 복원 |
| 만료 처리를 잊음 | "기준 시각"을 받아 만료된 예약을 먼저 정리한 뒤 계산 |
| 수량 0·음수·소수 요청 허용 | 1 이상 정수만 |
| 남은 수량 계산을 여러 곳에서 | 계산 함수 하나 |

## 구현 요령
```js
function reserve(db, { requestId, itemId, qty, now }) {
  if (db.requests[requestId]) return db.requests[requestId];          // 멱등
  expire(db, now);                    // 만료 먼저 (만료 규칙에 맞게 직접 만드는 함수)
  const item = db.items[itemId]; if (!item) return save('NOT_FOUND');
  if (!Number.isInteger(qty) || qty < 1) return save('INVALID_QTY');
  if (item.stock < qty) return save('OUT_OF_STOCK');
  item.stock -= qty; /* 예약 기록 */ return save(null);
  function save(error) { return (db.requests[requestId] = { error, stock: item ? item.stock : null }); }
}
```
## 검사 사례
- 재고 1에 2명이 1개씩 → 한 명만 성공
- 같은 requestId 두 번 → 재고 1만 줄고 같은 응답
- 정확히 남은 수량만큼 ✓, 하나 더 ✗
- 만료 직전·직후(정확히 n분 포함 여부는 담당자 답)
- 취소 → 복원, 취소 두 번 → 두 번째 오류
