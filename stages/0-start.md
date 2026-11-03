# ⓪ 시작 (0~5분)

## 할 일
1. 명령 한 번: `pwd; date; ls -ld /tmp; ls; git status -s | head; sed -n '1,12p' AGENTS.md`
2. **AGENTS.md에 「0. 상시 규칙」이 있나?** Codex는 지침을 세션 시작 때 읽는다.
   - 있음(사람이 codex 전에 `kit_setup.py`를 돌림) → 그대로 진행.
   - 없음 → 사람에게: `"새 터미널 탭에서 python3 /tmp/kit/setup.py 실행 → 여기서 /new → /tmp/kit/KIT-INDEX.md 읽고 이어서."`
   - 과제가 준 AGENTS.md·`AGENTS.override.md`가 있으면 원문을 지우지 않는다. override가 있으면 사람에게 알린다.
3. 키트는 먼저 `/tmp/kit`에 두고 사람에게 **File → Add Folder to Workspace → `/tmp/kit`**을 안내한다. 안 되면 `Open File`·`Ctrl+P`·`code -r /tmp/kit/<파일>`을 안내한다. 그래도 직접 보기 어렵다고 할 때만 제출 루트의 `./kit`을 쓰고 「제출 전 이동/삭제할 로컬 키트」라고 진행 줄에 표시한다.
4. 과제 README를 찾는다(키트·홈 숨김 폴더 제외). 언어별 README가 여럿이면 다 본다.
5. AGENTS.md 「7」칸에 **과제 타이머의 남은 시간**을 적고 상대 기준을 고정한다: 60분 남으면 기능 동결, 45분 남으면 검사·문서, 15분 남으면 제출 시작. kit_setup 출력의 라이브러리 목록·키트 커밋도 적어 둔다.

## 놓치면 안 되는 것
- [ ] 사람에게: SaaS 아이콘(네모 4개) 한 번 눌러 보기, DMs 담당자 이름·역할 알려 주기
- [ ] 키트가 과제 폴더(홈) 안에 있지 않은지. 홈 = 제출 폴더다
- [ ] Codex를 제출 루트에서 실행했고, `/tmp/kit`은 참고용이며 제출 파일은 현재 폴더에만 만든다고 확인
- [ ] 이어하기면 AGENTS.md 진행 줄부터 읽고 그 단계 카드로 간다

## 사용자에게 건넬 말
"왼쪽 폴더창에서 Add Folder to Workspace로 `/tmp/kit`을 추가해 보세요. 안 되면 알려 주세요. 제출 파일은 현재 폴더에만 만들겠습니다. SaaS 아이콘과 담당자 목록도 확인해 주세요."

## 다음: `stages/1-analyze.md`
