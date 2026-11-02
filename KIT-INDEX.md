# KIT-INDEX — AI가 먼저 읽는 목차

## 읽는 법 (토큰도 채점된다)
1. **이 파일 → 지금 단계 카드 하나**(`stages/`). 카드에 할 일·놓치면 안 되는 것·조건부로 더 읽을 절이 다 있다.
2. 더 필요하면 파일 전체가 아니라 **절만**: `python3 <키트>/tools/kit_read.py <파일> "<절 제목 일부>"` (목차만: 파일 이름만 준다).
3. 단계 카드의 「놓치면 안 되는 것」은 다음 단계로 넘어가기 전에 확인한다. 아래 「상황별」 표에 해당하면 그 절도 읽는다 — 카드 하나만 보다가 놓치지 않게.
4. 키트는 참고 자료다. **과제 README·제공 자료·담당자 답이 언제나 우선**한다. 키트 예시를 사양으로 쓰지 않고, 키트로 결과물을 통째로 대신 만들지 않는다.

## 시작·이어하기
- `읽고 시작해` → `stages/0-start.md`부터.
- `읽고 이어서` → 과제 `AGENTS.md` 진행 줄의 단계 카드부터. 「0. 상시 규칙」이 없으면 `templates/AGENTS.md`에서 그 칸만 복구한다. `<키트>/notes/확인문제-노트.md`가 없으면 `templates/answer-notes.md`로 만들고 실제 기록에서 확인되는 사실만 채운다. 계획 승인·검사·담당자 답을 꾸며 만들지 않는다.
- `/tmp/kit`이 사라졌으면 사람에게 키트를 다시 받게 한다(`README.md` 받기 줄).

## 단계 카드 (3시간 기준 대략 시각 · 화면 타이머가 우선)
| 단계 | 카드 | 시각 |
|---|---|---|
| ⓪ 시작 | `stages/0-start.md` | 0~5분 |
| ① 분석 · 자료 진단 · 예외 후보 | `stages/1-analyze.md` | ~25분 |
| ①-질문 담당자 | `stages/2-ask.md` | ~40분(기다리며 다른 일) |
| ② 사양·계획·구조 (최적화면 모델 계약·방법 수준·2차 왕복) | `stages/3-plan.md` | ~45분 |
| ③ 구현 (첫 완주 ~90분 · 기능 동결 ~150분) | `stages/4-build.md` | ~150분 |
| ④ 대조 · ⑤ 제출 문서 | `stages/5-check-report.md` | +15분 |
| ⑥ 서술형 대비 · 모의 확인 문제 | `stages/6-prepare.md` | +15분 |
| ⑦ 제출 (종료 −50분) | `stages/7-submit.md` | — |

## 상황별 — 해당하면 이 절을 더 읽는다
| 상황 | 파일 · 절 |
|---|---|
| 자료에서 예외·숨은 조건 찾기 | `playbooks/edge-hunt.md` |
| 계산·배정·경로·일정·"최적" | `playbooks/types/optimization.md` · 지식 `knowledge/optimization.md` · 틀 `recipes/opt_heuristics.py` |
| 과제 유형 판별(서비스·기존 코드·사내 시스템·데이터 보고·규정·자동화·AI 기능) | `playbooks/task-types.md` → 유형 파일 하나 |
| 주제 지식(날짜·금액·예약·API·화면·외부 연동·AI·자료 품질) | `knowledge/README.md` 표 → 파일 1~2개의 "담당자에게 물을 것"·"흔한 함정" |
| 로그인·역할·데이터 격리 | `knowledge/security.md` · 틀 `recipes/python_auth.py` |
| 구조·동기/비동기·동시 수정·실패 시 보존·운영 전 점검 | `knowledge/service-architecture.md` |
| 담당자 질문 더(여럿·예·리뷰어로 쓰기·2차 왕복) | `playbooks/stakeholder.md` |
| AI가 혼자 정하면 안 되는 지점 | `playbooks/decision-gates.md` |
| 자료끼리 다름·단서 조항·경계값 | `playbooks/traps.md` |
| 기능을 더 넣을지·과설계 | `playbooks/scope.md` |
| 검증 방법·ui_sim·지도 화면 | `playbooks/verification.md` |
| 서버·미리보기·환경 오류 | `playbooks/flow.md` "화면 미리보기" · `playbooks/environment.md` |
| Codex가 같은 실수·코드를 망침 | `playbooks/recover.md` · `playbooks/git.md` |
| 담당자 답 변경·설치 실패·데이터 깨짐 등 돌발 | `playbooks/situations.md` |
| 모델·생각 강도·승인 창·끊김·재접속·토큰 | `playbooks/codex.md` |
| 시험 화면 동작·제출 흐름·환경 사실 | `playbooks/exam-screen.md` |
| 서술형 답 틀(9가지 카드) · 노트 규칙 | `playbooks/answer-cards.md` · `playbooks/followup-prep.md` |
| 사람이 보낼 수 있는 말 전체 · 고득점 자동 행동 · 자주 나온 실수 | `playbooks/flow.md` 해당 절 |
| 평가가 보는 것 | `playbooks/evaluation.md` |
| 사람이 개발자처럼 이끌 문장·생각할 순간 · 용어 | `playbooks/lead-like-dev.md` · `playbooks/dev-glossary.md` |
| Docker · 지도 시각화 · 서버·테스트 틀 | `recipes/README.md` |

## 도구 (필요할 때만 · 출력을 그대로 보인다)
| 명령 | 쓰임 |
|---|---|
| `python3 <키트>/tools/kit_read.py <파일> ["절"]` | 키트 문서의 목차·절만 읽기 |
| `python3 <키트>/tools/data_profile.py <자료 폴더>` · `--compare 원본 변경본 --key 열1,열2` | 예외 후보 진단(형식·빈칸·범위·요일 분포·표기 변형·자정 넘김·키 불일치), 두 판의 차이 |
| `python3 <키트>/tools/csv_check.py 파일.csv --key 열 --number 열` | CSV 중복 키·빈칸·숫자 오류(값은 숨김) |
| `python3 <키트>/tools/compare_json.py 기대.json 실제.json` | 기대 결과와 실제 결과 비교 |
| `python3 <키트>/tools/security_check.py 경로` | 비밀 값 의심 위치(값은 숨김) |
| `node <키트>/tools/ui_sim.cjs index.html --list` · `"set id=값" "click id" "read id"` | 브라우저 없이 화면 입력·클릭·표시 확인. `ui_sim 해줘`만 받아도 이 로컬 파일을 찾아 실행한다(연결·설치 요구 금지) |

스킬(선택, 읽어서 따름): `skills/verify-small-delivery/SKILL.md`, `skills/review-local-security/SKILL.md`
