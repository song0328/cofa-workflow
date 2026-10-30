# KIT-INDEX — AI가 먼저 읽는 목차

**이 파일만 먼저 읽는다. 키트 전체를 읽지 않는다.** 아래 표에서 지금 상황에 맞는 파일 **하나**만 연다. 토큰 사용량도 평가된다.

키트는 참고 자료다. **실제 과제의 README·제공 파일·담당자 답이 언제나 우선**한다. 키트의 예시를 과제 사양처럼 쓰지 않는다. 키트로 결과물을 통째로 대신 만들지 않는다.

| 지금 상황 | 열 파일 |
|---|---|
| 막 시작했다 — 경로·README·환경 확인 | `playbooks/start.md` |
| README를 읽고 분석해야 한다 | `prompts/1-analyze.md` |
| 담당자에게 무엇을 어떻게 물을지 | `playbooks/stakeholder.md` |
| 담당자 답을 받았다 — 사양·계획을 세운다 | `prompts/2-spec.md` + `templates/AGENTS.md` |
| 구현을 단계별로 진행한다 | `prompts/3-step.md` |
| 자료끼리 다르다·예외 데이터·경계값이 애매하다 | `playbooks/traps.md` |
| 기능을 더 넣을지·선택조건을 할지 고민 | `playbooks/scope.md` |
| 120분쯤 — 남은 일을 점검한다 | `prompts/3-step.md` 맨 아래 |
| 검사·검증을 어떻게 할지 | `playbooks/verification.md` |
| 서버·미리보기 화면이 안 뜬다, 명령이 실패한다 | `playbooks/environment.md` |
| Codex가 같은 실수를 반복·코드를 망쳤다 | `playbooks/recover.md` |
| git 상태·되돌리기·커밋 범위 | `playbooks/git.md` |
| 웹 화면·API 과제 | `playbooks/web-app.md` |
| CSV·표·분석 보고 과제 | `playbooks/data-analysis.md` |
| 보안 점검이 필요하다 | `playbooks/security.md` |
| 요건마다 충족 근거를 대조한다 | `prompts/4-check.md` |
| 제출 문서를 쓴다 | `prompts/5-report.md` + `templates/report.md` |
| 내가 한 결정을 정리한다 | `prompts/6-summary.md` + `playbooks/explain.md` |
| 이 평가가 무엇을 보는지 | `playbooks/evaluation.md` |
| 자주 쓰는 셸 명령 | `playbooks/commands.md` |

도구(필요할 때만 실행, `python3` 표준 라이브러리만):

| 도구 | 쓰임 |
|---|---|
| `python3 <키트>/tools/compare_json.py 기대.json 실제.json` | 기대 결과와 실제 결과 비교 |
| `python3 <키트>/tools/csv_check.py 파일.csv --key 열 --number 열` | CSV 중복 키·빈칸·숫자 오류 |
| `python3 <키트>/tools/security_check.py 경로` | 비밀 값 의심 위치(값은 숨김) |

스킬(선택): `skills/verify-small-delivery/SKILL.md`, `skills/review-local-security/SKILL.md` — 설치하지 않고 읽어서 따른다.
