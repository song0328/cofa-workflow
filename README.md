# cofa-workflow

AI 코딩 에이전트(Codex 등)와 함께 **README로 주어지는 3시간짜리 업무 과제**를 풀 때 쓰는 작업 키트입니다. 작업 순서(요청문), AGENTS.md 틀, 담당자 질문법, 흔한 함정, 검증·복구 방법, 작은 점검 도구가 들어 있습니다.

시험 자료·문제·정답은 들어 있지 않습니다. 과제의 업무 기준을 대신 정하지 않으며, **실제 과제의 README·제공 파일·담당자 답이 언제나 우선**합니다.

## 쓰는 법

```bash
git clone --depth 1 https://github.com/song0328/cofa-workflow.git kit
python3 kit/setup.py                     # 과제 폴더(시험: 홈 ~)에서, codex를 켜기 전에
```

`kit_setup.py`는 과제 폴더에 `AGENTS.md` 상시 규칙을 깔고(과제가 준 지침은 보존), 노트·작업 폴더를 키트 안에 만들고, 환경(파이썬·라이브러리·Docker·디스크)을 한 번에 보여 줍니다. **Codex는 AGENTS.md를 세션을 시작할 때 읽기 때문에** codex를 켜기 전에 실행합니다. 깜빡하고 세션 중에 만들었다면 `/new`로 새 세션을 열고 이어서 하면 됩니다.

그다음 `codex`를 켜고 AI에게 한 줄만:

```text
kit/KIT-INDEX.md 읽고 시작해.
```

AI가 진행자가 되어 매 답 끝에 `── 다음 ──` 칸(지금 단계 · 사람이 할 일 · 나에게 보낼 말)을 붙입니다. 사용자는 `다음`, `A`/`B`, `답: (담당자 답)`, `막혔어`, `n분 남았어`, `노트 보여 줘`, `모의 확인 문제 해줘`, `답 파일 보여 줘`만 보내면 됩니다.

**토큰을 아끼는 구조**: AI는 목차(`KIT-INDEX.md`)와 **지금 단계 카드 하나**(`stages/`)만 읽고, 더 필요하면 `tools/kit_read.py`로 문서의 **절 하나만** 읽습니다. 세션 시작 때 읽혀 매 요청 맥락에 실리는 과제 `AGENTS.md`의 상시 규칙은 짧게 유지합니다. 카드마다 「놓치면 안 되는 것」과 조건부로 더 읽을 절이 있어, 한 파일만 보다가 중요한 것을 놓치지 않게 했습니다. `tests/test_kit_structure.py`가 크기 상한과 카드가 가리키는 파일·절이 실제로 있는지 검사합니다. 대화가 끊기면 `kit/KIT-INDEX.md 읽고 이어서.`

**키트를 못 받았을 때**(clone 실패): 오타만 확인해 한 번 더 → git만 막힌 경우를 위해 압축 파일로 받기:

```bash
curl -sL https://github.com/song0328/cofa-workflow/archive/main.tar.gz | tar xz && mv cofa-workflow-main kit
# curl도 없으면
python3 -c "import urllib.request as u,tarfile as t;t.open(fileobj=u.urlopen('https://github.com/song0328/cofa-workflow/archive/main.tar.gz'),mode='r|gz').extractall('.')" && mv cofa-workflow-main kit
```

그래도 안 되면(인터넷 자체가 막힘) 키트 없이 같은 순서로 진행한다. AI에게 `코드 고치지 말고 README 분석만 해. 요건표·함정·담당자 질문·가정으로.` → 질문은 한 번에 하나 → 사양 → 한 단계씩 구현·검사 → 요건 대조 → 보고서 → 결정 요약.

단계를 직접 부르고 싶으면 이렇게 짧게 부를 수도 있습니다.

| 단계 | 사용자가 칠 문장 |
|---|---|
| ① 분석 | `kit/prompts/1-analyze.md 대로 분석만 해.` |
| ② 사양 | `kit/prompts/2-spec.md 대로 해. 아래는 내가 담당자에게 확인한 사실이야.` |
| ③ 단계 | `AGENTS.md를 읽고 1단계만.` → `다음 단계만.` |
| ④ 대조 | `kit/prompts/4-check.md 대로 대조해.` |
| ⑤ 보고 | `kit/prompts/5-report.md 대로 <제출 파일명> 채워.` |
| ⑥ 요약 | `kit/prompts/6-summary.md 대로.` |

## 구성

| 폴더 | 내용 |
|---|---|
| `KIT-INDEX.md` | AI용 목차 — 읽는 법, 단계 카드 표, 상황별로 더 읽을 절, 도구 |
| `stages/` | 단계 카드 8장(⓪시작 ~ ⑦제출) — 할 일·놓치면 안 되는 것·조건부로 더 읽을 절·사용자에게 건넬 말 |
| `prompts/` | ①분석 ②사양 ③단계(120분 점검) ④대조 ⑤보고 ⑥대비(외울 것 · 모의 확인 문제) |
| `knowledge/` | 주제별 지식 — 최적화, 서비스 구조(책임 분리·동시 수정·비동기·운영 전 점검), 보안(인증·권한·격리), 승인·결재, 날짜·시간, 금액, 자료 품질, 예약·재고, API, 화면, 외부 연동, AI 기능 (물을 것·함정·구현 요령·검사 사례) |
| `recipes/` | 패키지 없이 쓰는 서버·테스트·인증·휴리스틱 틀과 Docker 예시 (Node 22·Python 표준 기능, 실행 확인) |
| `templates/` | `AGENTS.md`(요건표·확정 사양·가정·금지·규칙), README가 문서를 요구하지 않을 때만 쓰는 `DECISIONS.md`, 별도 요구 시 쓰는 `AI_COLLABORATION.md`, 확인문제 노트, 제출 루트에 두는 예상 질문·답 `Answers.md`, 요구사항·검증 틀 |
| `playbooks/task-types.md` + `playbooks/types/` | 과제 유형 8가지 — 새 서비스, 기존 코드 수정, 사내 업무 시스템(HR·결재·예약 등), 데이터 분석·보고, 규정 해석·판정, 자동화, AI 기능, 최적화·배정·경로 |
| `practice/` · `playbooks/rehearsal.md` | 연습 과제 2개(자료·담당자 역할 카드·예상 질문)와 시험 전 키트 행동 점검 시나리오 9장 |
| `playbooks/parallel.md` | 선택 절차 — 계약 확정 뒤 읽기 전용 검증 탭 하나가 꼭 필요할 때만 |
| `playbooks/lead-like-dev.md` · `dev-glossary.md` | 사람이 개발자처럼 이끄는 10가지 순간과 보낼 문장, 용어 30개(뜻·쓰는 문장) |
| `playbooks/answer-cards.md` · `followup-prep.md` | 확인 문제 9가지 답 카드(4단계 뼈대·5분 쓰는 법), 작업 중 대비·이해 체크포인트·모의 확인 문제 |
| `playbooks/exam-screen.md` · `codex.md` · `reminders.md` | 시험 화면 동작(저장·제출·환경 사실·시간표), Codex 운용(모델·승인·끊김·토큰), AI가 시점마다 건넬 한 줄 조언 |
| `playbooks/decision-gates.md` · `situations.md` | AI가 멈추고 사람이 고를 지점, 돌발 상황 대응 |
| `playbooks/` | 시작 5분, 담당자 질문법, 함정, 범위 조절, 검증, 환경, 복구, git, 웹·API, 자료 분석, 보안, 설명 정리, 평가 관점, 셸 명령 |
| `setup.py` · `tools/` | `setup.py`(codex 전 설정) · `kit_read.py`(문서의 절만 읽기) · `data_profile.py`(예외 후보 진단) · `predict_questions.py`(내 제출물로 서술형 예상 질문) · `tab_task.py`(선택: 읽기 전용 검증 카드) · `evidence.py`(검사 증거·오래된 증거) · `compare_json.py` · `csv_check.py` · `security_check.py` (python3 표준 라이브러리만) · `ui_sim.cjs`(Node, 화면 흉내) |
| `skills/` | `verify-small-delivery`, `review-local-security` — 설치 없이 읽어서 사용 |

## 개발 확인

```bash
python3 -m unittest discover -s tests -v
```

MIT License. 다운로드한 코드는 실행 전에 읽어 보세요.
