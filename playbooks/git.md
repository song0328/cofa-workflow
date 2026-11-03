# git

먼저 `git rev-parse --show-toplevel`로 **과제 폴더를 포함하는 의도된 기존 저장소**인지 확인한다. 저장소가 아니거나 `.git`에 쓸 수 없으면 `git init`·커밋 재시도를 하지 않는다. 플랫폼 저장을 쓰고 `AGENTS.md`에 `Git 미사용(저장소 없음/쓰기 불가)` 한 줄만 남긴다.

| 명령 | 언제 |
|---|---|
| `git status` | 무엇이 바뀌었나 |
| `git diff <파일>` | AI가 방금 고친 내용 |
| `git log --oneline -10` | 단계별 커밋 |
| `git add <과제 파일들>` → `git commit -m "R번호: …"` | 위 확인을 통과했을 때만 2~4회. 위험한 변경 직전·제출 직전 |
| `git restore <파일>` | 마지막 커밋 상태로 되돌리기 |
| `git stash` / `git stash pop` | 잠깐 치워 두기 |

주의
- 홈 폴더가 저장소일 수 있다. **`git add .` 대신 과제 파일을 지정**한다. 환경 파일(`.codex/` 등)을 섞지 않는다.
- 상위의 무관한 저장소가 잡히거나 `index.lock` 권한 오류가 나면 즉시 Git을 생략한다. 새 저장소·worktree로 우회하지 않는다.
- 사용자 정보 오류("Please tell me who you are")가 나면 그 저장소에서만: `git config user.name "candidate"` / `git config user.email "candidate@example.com"`.
- push는 하지 않는다(필요 없음, 외부 전송 금지).
- 제출은 화면의 제출 버튼으로만 한다.
