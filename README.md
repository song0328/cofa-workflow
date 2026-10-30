# cofa-workflow

AI 코딩 에이전트(Codex 등)와 함께 **README로 주어지는 3시간짜리 업무 과제**를 풀 때 쓰는 작업 키트입니다. 작업 순서(요청문), AGENTS.md 틀, 담당자 질문법, 흔한 함정, 검증·복구 방법, 작은 점검 도구가 들어 있습니다.

시험 자료·문제·정답은 들어 있지 않습니다. 과제의 업무 기준을 대신 정하지 않으며, **실제 과제의 README·제공 파일·담당자 답이 언제나 우선**합니다.

## 쓰는 법

```bash
git clone --depth 1 https://github.com/song0328/cofa-workflow.git /tmp/kit
```

그다음 AI에게 한 줄만:

```text
/tmp/kit/KIT-INDEX.md 읽고 시작해.
```

AI가 진행자가 되어 매 답 끝에 `── 다음 ──` 칸(지금 단계 · 사람이 할 일 · 나에게 보낼 말)을 붙입니다. 사용자는 `다음`, `A`/`B`, `답: (담당자 답)`, `막혔어`, `n분 남았어`만 보내면 됩니다(`playbooks/flow.md`). 대화가 끊기면 `/tmp/kit/KIT-INDEX.md 읽고 이어서.`

**키트를 못 받았을 때**(clone 실패): 오타만 확인해 한 번 더 → 그래도 안 되면 키트 없이 같은 순서로 진행한다. AI에게 `코드 고치지 말고 README 분석만 해. 요건표·함정·담당자 질문·가정으로.` → 질문은 한 번에 하나 → 사양 → 한 단계씩 구현·검사 → 요건 대조 → 보고서 → 결정 요약.

단계를 직접 부르고 싶으면 이렇게 짧게 부를 수도 있습니다.

| 단계 | 사용자가 칠 문장 |
|---|---|
| ① 분석 | `/tmp/kit/prompts/1-analyze.md 대로 분석만 해.` |
| ② 사양 | `/tmp/kit/prompts/2-spec.md 대로 해. 아래는 내가 담당자에게 확인한 사실이야.` |
| ③ 단계 | `AGENTS.md를 읽고 1단계만.` → `다음 단계만.` |
| ④ 대조 | `/tmp/kit/prompts/4-check.md 대로 대조해.` |
| ⑤ 보고 | `/tmp/kit/prompts/5-report.md 대로 <제출 파일명> 채워.` |
| ⑥ 요약 | `/tmp/kit/prompts/6-summary.md 대로.` |

## 구성

| 폴더 | 내용 |
|---|---|
| `KIT-INDEX.md` | AI용 목차 — 상황별로 읽을 파일 하나 |
| `prompts/` | ①분석 ②사양 ③단계(120분 점검) ④대조 ⑤보고 ⑥요약 |
| `templates/` | `AGENTS.md`(요건표·확정 사양·가정·금지·규칙), 제출 문서·요구사항·검증 틀 |
| `playbooks/task-types.md` + `playbooks/types/` | 과제 유형 7가지 — 새 서비스, 기존 코드 수정, 사내 업무 시스템(HR·결재·예약 등), 데이터 분석·보고, 규정 해석·판정, 자동화, AI 기능 |
| `playbooks/exam-screen.md` · `followup-prep.md` · `reminders.md` | 시험 화면 동작(저장·제출·권한 창), 확인 문제 대비, AI가 시점마다 건넬 한 줄 조언 |
| `playbooks/decision-gates.md` · `situations.md` | AI가 멈추고 사람이 고를 지점, 돌발 상황 대응 |
| `playbooks/` | 시작 5분, 담당자 질문법, 함정, 범위 조절, 검증, 환경, 복구, git, 웹·API, 자료 분석, 보안, 설명 정리, 평가 관점, 셸 명령 |
| `tools/` | `compare_json.py` · `csv_check.py` · `security_check.py` (python3 표준 라이브러리만) |
| `skills/` | `verify-small-delivery`, `review-local-security` — 설치 없이 읽어서 사용 |

## 개발 확인

```bash
python3 -m unittest discover -s tests -v
```

MIT License. 다운로드한 코드는 실행 전에 읽어 보세요.
