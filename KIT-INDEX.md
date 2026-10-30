# KIT-INDEX — AI가 먼저 읽는 목차

**이 파일만 먼저 읽는다. 키트 전체를 읽지 않는다.** 아래 표에서 지금 상황에 맞는 파일 **하나**만 연다. 토큰 사용량도 평가된다.

**짧은 요청도 바로 실행한다.** 사용자가 `ui_sim 해줘`·`ui_sim으로 확인해`라고 하면 연결 도구를 찾거나 설치를 요구하지 않는다. ui_sim은 이 키트의 **로컬 Node 스크립트**다. 현재 과제의 `AGENTS.md`에 키트 실제 경로와 `node <키트>/tools/ui_sim.cjs <화면 HTML> --list` 명령을 먼저 기록한다(이미 있으면 갱신). `kit/tools/ui_sim.cjs`와 `/tmp/kit/tools/ui_sim.cjs` 중 실제 파일을 확인해 실행하고, 나온 id로 정상·경계·오류 흐름을 검사한다. 실제 파일 확인 전에 "없다"고 말하지 않는다. 자세한 순서는 `playbooks/verification.md`의 「ui_sim 짧은 요청 처리」를 따른다.

키트는 참고 자료다. **실제 과제의 README·제공 파일·담당자 답이 언제나 우선**한다. 키트의 예시를 과제 사양처럼 쓰지 않는다. 키트로 결과물을 통째로 대신 만들지 않는다.

**기본은 진행자 모드다.** 사용자가 "읽고 시작해"·"읽고 이어서"처럼만 말했으면 바로 `playbooks/flow.md`를 열고 그대로 따른다. 과제 폴더는 스스로 찾고, **매 답 끝에 `── 다음 ──` 칸**(단계 · 사람이 할 일 · 나에게 보낼 말)을 붙인다. 이어서 하는 경우는 과제 폴더의 `AGENTS.md` 진행 상태 줄부터 읽는다. 아래 표는 그 안에서 단계별로 열 파일이다.

**키트를 쓰는 동안 `playbooks/reminders.md`의 시점별 한 줄 조언을 사용자에게 먼저 건넨다.**

| 지금 상황 | 열 파일 |
|---|---|
| 진행자 모드(기본) — 단계 순서·매 답 끝 다음 칸·이어하기 | `playbooks/flow.md` |
| 막 시작했다 — 경로·README·환경 확인 | `playbooks/start.md` |
| README를 읽고 분석해야 한다 | `prompts/1-analyze.md` |
| 어떤 종류의 과제인지 판별 (서비스·기존 코드·사내 시스템·데이터 보고·규정 판정·자동화·AI 기능) | `playbooks/task-types.md` → 해당 유형 파일 하나 |
| AI가 혼자 정하면 안 되는 지점인지 | `playbooks/decision-gates.md` |
| 담당자에게 무엇을 어떻게 물을지 | `playbooks/stakeholder.md` |
| 담당자 답을 받았다 — 사양·계획을 세운다 | `prompts/2-spec.md` + `templates/AGENTS.md` |
| 구현을 단계별로 진행한다 | `prompts/3-step.md` |
| 자료끼리 다르다·예외 데이터·경계값이 애매하다 | `playbooks/traps.md` |
| 기능을 더 넣을지·선택조건을 할지 고민 | `playbooks/scope.md` |
| 120분쯤 — 남은 일을 점검한다 | `prompts/3-step.md` 맨 아래 |
| 검사·검증을 어떻게 할지 | `playbooks/verification.md` |
| 서버·미리보기 화면이 안 뜬다, 명령이 실패한다 | `playbooks/environment.md` |
| Codex가 같은 실수를 반복·코드를 망쳤다 | `playbooks/recover.md` |
| 담당자 답이 README와 다름·설치 실패·데이터 깨짐 등 돌발 상황 | `playbooks/situations.md` |
| git 상태·되돌리기·커밋 범위 | `playbooks/git.md` |
| 웹 화면·API 과제 | `playbooks/web-app.md` |
| CSV·표·분석 보고 과제 | `playbooks/data-analysis.md` |
| 보안 점검이 필요하다 | `playbooks/security.md` |
| 요건마다 충족 근거를 대조한다 | `prompts/4-check.md` |
| 제출 문서를 쓴다 | `prompts/5-report.md` + `templates/report.md` |
| 내가 한 결정을 정리한다 | `prompts/6-summary.md` + `playbooks/explain.md` |
| 이 평가가 무엇을 보는지 | `playbooks/evaluation.md` |
| 시험 화면 동작·저장·제출·확인 문제 형식 | `playbooks/exam-screen.md` |
| 배정된 업무 도구(SaaS)가 있다 | `playbooks/saas.md` |
| 확인 문제(제출 후 질문)를 작업 중에 대비 · 확인문제 노트 | `playbooks/followup-prep.md` + `templates/answer-notes.md` |
| 사용자에게 언제 무슨 조언을 할지 | `playbooks/reminders.md` |
| 과제 주제별 지식(보안·결재·날짜·금액·자료 품질·예약·API·화면·외부 연동·AI) | `knowledge/README.md` → 해당 파일 **1~2개만** |
| 패키지 설치 없이 서버·저장·테스트를 만들어야 한다 | `recipes/README.md` |
| 자주 쓰는 셸 명령 | `playbooks/commands.md` |

도구(필요할 때만 실행, `python3` 표준 라이브러리만):

| 도구 | 쓰임 |
|---|---|
| `python3 <키트>/tools/compare_json.py 기대.json 실제.json` | 기대 결과와 실제 결과 비교 |
| `python3 <키트>/tools/csv_check.py 파일.csv --key 열 --number 열` | CSV 중복 키·빈칸·숫자 오류 |
| `python3 <키트>/tools/security_check.py 경로` | 비밀 값 의심 위치(값은 숨김) |
| `node <키트>/tools/ui_sim.cjs index.html "set 칸id=값" "click 버튼id" "read 결과id"` | 브라우저 없이 화면을 흉내 내 선택·클릭 결과 읽기 (`--list`로 칸·버튼 id 목록) |

스킬(선택): `skills/verify-small-delivery/SKILL.md`, `skills/review-local-security/SKILL.md` — 설치하지 않고 읽어서 따른다.
