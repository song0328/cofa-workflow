# git

| 명령 | 언제 |
|---|---|
| `git status` | 무엇이 바뀌었나 |
| `git diff <파일>` | AI가 방금 고친 내용 |
| `git log --oneline -10` | 단계별 커밋 |
| `git add <과제 파일들>` → `git commit -m "단계 n: …"` | 검사 통과한 단계마다 |
| `git restore <파일>` | 마지막 커밋 상태로 되돌리기 |
| `git stash` / `git stash pop` | 잠깐 치워 두기 |

주의
- 홈 폴더가 저장소일 수 있다. **`git add .` 대신 과제 파일을 지정**한다. 환경 파일(`.codex/` 등)을 섞지 않는다.
- 사용자 정보 오류("Please tell me who you are")가 나면 그 저장소에서만: `git config user.name "candidate"` / `git config user.email "candidate@example.com"`.
- push는 하지 않는다(필요 없음, 외부 전송 금지).
- 제출은 화면의 제출 버튼으로만 한다.
