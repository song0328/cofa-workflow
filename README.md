# cofa-workflow

AI 코딩 에이전트(Codex 등)와 함께 **README로 주어지는 3시간짜리 업무 과제**를 풀 때 쓰는 작업 키트입니다. 작업 순서(요청문), AGENTS.md 틀, 담당자 질문법, 흔한 함정, 검증·복구 방법, 작은 점검 도구가 들어 있습니다.

시험 자료·문제·정답은 들어 있지 않습니다. 과제의 업무 기준을 대신 정하지 않으며, **실제 과제의 README·제공 파일·담당자 답이 언제나 우선**합니다.

## 쓰는 법

```bash
git clone --depth 1 https://github.com/song0328/cofa-workflow.git /tmp/kit
```

그다음 AI에게:

```text
/tmp/kit/KIT-INDEX.md만 먼저 읽어. 지금 상황에 맞는 파일 하나만 열고 그대로 따라. 과제 폴더는 <경로>야. 키트 전체를 읽지 마.
```

단계마다 짧게 부르면 됩니다.

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
| `playbooks/decision-gates.md` · `situations.md` | AI가 멈추고 사람이 고를 지점, 돌발 상황 대응 |
| `playbooks/` | 시작 5분, 담당자 질문법, 함정, 범위 조절, 검증, 환경, 복구, git, 웹·API, 자료 분석, 보안, 설명 정리, 평가 관점, 셸 명령 |
| `tools/` | `compare_json.py` · `csv_check.py` · `security_check.py` (python3 표준 라이브러리만) |
| `skills/` | `verify-small-delivery`, `review-local-security` — 설치 없이 읽어서 사용 |

## 개발 확인

```bash
python3 -m unittest discover -s tests -v
```

MIT License. 다운로드한 코드는 실행 전에 읽어 보세요.
