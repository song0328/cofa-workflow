# 보안 — 작은 업무 서비스에서 실제로 문제 되는 것

## 담당자에게 물을 것 (파일에 없을 때만, 하나씩)
- "다른 사람의 자료(신청·주문·계정)를 볼 수 있는 역할이 있나요?" (관리자·팀장 범위)
- "로그인한 사용자는 어떤 값으로 구분하나요?" (헤더·토큰·세션 — README에 있으면 그대로)
- "응답·화면에 보여 주면 안 되는 필드가 있나요?" (원가·주민번호·연락처·내부 메모)
- "같은 요청이 두 번 오면 두 번 처리하나요?"
- "실패 이유를 사용자에게 자세히 알려 줘도 되나요?" (계정 존재 여부 노출 등)

## 흔한 함정
| 함정 | 예 | 막는 법 |
|---|---|---|
| 화면에서만 막음 | 버튼은 숨겼지만 API는 누구나 호출 | **서버에서** 역할·소유자 검사 |
| ID만 바꾸면 남의 자료 (IDOR) | `GET /requests/12` → 13으로 바꾸면 남의 것 | 조회·수정·삭제 모두 "요청자 = 소유자 또는 권한자" 검사 |
| 입력을 HTML로 출력 (XSS) | 이름에 `<img onerror=…>` | 화면은 `textContent`, 서버 HTML은 이스케이프 |
| 문자열로 SQL·명령 조립 (주입) | `"… WHERE id=" + id` | 매개변수 바인딩, 셸 대신 인자 배열 |
| 경로 이탈 | 파일명 `../../etc/passwd` | 기준 폴더 안인지 정규화 후 확인 |
| 비밀 값 하드코딩·로그 출력 | API 키·비밀번호를 코드·로그·오류에 | 환경 변수, 로그에는 마스킹 |
| 비밀번호 평문 저장·단순 해시 | `sha256(pw)` | `scrypt`/`pbkdf2` + 소금, 비교는 상수 시간 |
| 과다 응답 | 목록 API가 내부 필드까지 통째로 | 응답 필드를 계약대로 골라서 |
| 오류에 내부 정보 | 스택·SQL·경로를 응답에 | 사용자에겐 코드·짧은 문구, 자세한 건 서버 로그 |
| 중복·재시도 | 결제·지급·승인이 두 번 | 상태 확인 후 처리(멱등), 같은 요청 ID 재사용 거절 |
| 크기 제한 없음 | 큰 본문·큰 파일로 메모리 부족 | 본문 크기 상한(예: 1MB), 목록 개수 상한 |

## 구현 요령 (표준 라이브러리)
```js
// Node: HTML 이스케이프
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Node: 비밀번호 해시와 비교
const crypto = require('node:crypto');
const hash = (pw, salt = crypto.randomBytes(16)) => salt.toString('hex') + ':' + crypto.scryptSync(pw, salt, 32).toString('hex');
const check = (pw, stored) => { const [s, h] = stored.split(':'); const a = crypto.scryptSync(pw, Buffer.from(s, 'hex'), 32); return crypto.timingSafeEqual(a, Buffer.from(h, 'hex')); };
// Node: 기준 폴더 안의 경로만
const path = require('node:path');
const safeJoin = (base, rel) => { const p = path.resolve(base, '.' + path.sep + rel); return p.startsWith(path.resolve(base) + path.sep) ? p : null; };
```
```python
# Python: 매개변수 바인딩, 경로 확인, 비밀번호
cur.execute("SELECT * FROM items WHERE owner = ? AND id = ?", (user_id, item_id))
from pathlib import Path
def safe_join(base, rel):
    p = (Path(base) / rel).resolve()
    return p if p.is_relative_to(Path(base).resolve()) else None
import hashlib, hmac, os
def hash_pw(pw, salt=None):
    salt = salt or os.urandom(16); return salt.hex() + ':' + hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1).hex()
def check_pw(pw, stored):
    s, h = stored.split(':'); return hmac.compare_digest(hash_pw(pw, bytes.fromhex(s)).split(':')[1], h)
```
- 권한 검사는 **한 함수**로 모은다(`canView(user, item)`, `canApprove(user, item)`). 모든 경로가 그 함수를 지나게.
- 검사 순서가 README·담당자 답에 있으면 그대로(예: 없음 → 본인 → 권한 → 상태). 없으면 "존재 → 권한 → 상태 → 입력값"을 가정으로 쓰고 확인받는다.

## 검사 사례 (정상·경계·거절)
- 본인 자료 조회 ✓ / 남의 ID로 조회 → 거절(403 또는 README가 정한 코드) / 관리자 조회 ✓
- 이름에 `<script>alert(1)</script>` → 글자 그대로 표시, 실행 안 됨
- 파일명 `../secret` → 거절
- 같은 승인 요청 두 번 → 두 번째는 상태 오류, 잔액·재고 변화 없음
- 응답 JSON에 금지 필드 없음 (`grep`으로 응답 확인)
- `python3 <키트>/tools/security_check.py .` — 비밀 값 의심 위치. 통과가 보안 인증은 아니다.

보고 형식: 위치 · 영향 · 재현 · 수정 · 미검증. 자세히는 `skills/review-local-security/SKILL.md`.
