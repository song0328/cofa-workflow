# 리허설 — 연습 과제 2개로 시험 흐름 한 바퀴

실제 시험과 같은 모양(제공 CSV + 제약 있는 배정·최적화 + 역할 2개 웹 서비스 + Docker + 결정·협업 문서)의 **가상 과제**다. 실제 시험 문제·자료가 아니다. 담당자 역할은 다른 AI가 `FACILITATOR.md` 카드를 보고 맡는다.

| 폴더 | 과제 | 핵심 함정 | 변경본 규칙 |
|---|---|---|---|
| `training-seats/` | 교육 세션 배정(직원 → 세션) | 주 8시간 상한 vs 필수 과목, 정원 빈칸, 자정 넘는 세션 | 틀린 행이 있으면 파일 전체 거절 |
| `inspection-crew/` | 설비 점검 배정(작업 → 기사·시각) | 2인 1조 프레스 점검, 11/24 몰림 vs 연장, 06:00 마감 | 틀린 행만 빼고 반영 |

각 폴더: `README.md`(과제 원문) · `data/`(자료) · `make_data.py`(자료 재생성, seed 고정) · `FACILITATOR.md`(담당자 카드 — **응시자 역할은 보지 않는다**) · `QUESTIONS.md`(모의 확인 문제 — **끝난 뒤에만** 연다).

## 1. 준비 (5분)
과제 README와 `data/`만 **연습실**(시험의 홈 대신)로 복사한다. 키트 폴더 안에서 Codex를 켜지 않는다(담당자 카드가 보인다).
```bash
K=/tmp/kit                 # 키트를 받은 곳 (git clone --depth 1 https://github.com/song0328/cofa-workflow.git /tmp/kit)
T=training-seats           # 또는 inspection-crew
mkdir -p ~/rehearsal/$T && cd ~/rehearsal/$T
cp $K/practice/$T/README.md . && cp -r $K/practice/$T/data .
git init -q && git add README.md data && git commit -qm "과제 원본"
python3 $K/tools/kit_setup.py      # codex를 켜기 전에(상시 규칙·노트·환경 점검)
```
Windows PowerShell이면(키트를 예: 홈에 받은 경우):
```powershell
git clone --depth 1 https://github.com/song0328/cofa-workflow.git $HOME/cofa-workflow
$K="$HOME/cofa-workflow"; $T="training-seats"
mkdir $HOME/rehearsal/$T; cd $HOME/rehearsal/$T; cp $K/practice/$T/README.md .; cp -r $K/practice/$T/data .
git init -q; git add README.md data; git commit -qm "과제 원본"
python $K/tools/kit_setup.py       # Windows는 python3 대신 python일 수 있다
```
`kit_setup.py`는 키트가 `/tmp/kit`가 아니면 AGENTS.md 속 경로를 실제 키트 경로로 바꿔 넣고, 다음에 칠 줄을 그 경로로 알려 준다. 연습실 폴더는 키트 폴더 **밖**이어야 한다(안이면 거절).
자료가 깨졌으면 키트 쪽에서 `python3 make_data.py`로 다시 만든다(같은 결과).

## 2. 담당자 AI 준비 (2분)
- 두 번째 창(다른 Codex 탭을 **키트의 과제 폴더**에서, 또는 아무 챗봇)에 `FACILITATOR.md` 전체를 붙여 넣는다. 첫 줄은 카드 맨 위 안내문 그대로.
- Codex 탭이면: `FACILITATOR.md 읽고 그 역할만 해. 다음 메시지부터 담당자로 답해.`
- 시험처럼: 담당자에게 보내는 말은 **사람이 직접 복사**하고(1000자 이하, 물음표 하나), 받은 답은 메인에 `답: …`으로 붙인다.

## 3. 시작과 시간 (90분 압축 또는 180분 실전)
메인 Codex를 연습실에서 켜고 `kit_setup.py`가 마지막 줄에 알려 준 한 줄(예: `/tmp/kit/KIT-INDEX.md 읽고 시작해.`)을 친다. 타이머를 켠다.

| 단계 | 90분 압축 | 180분 실전 |
|---|---|---|
| ⓪ 시작 · ① 분석·자료 진단 | 0~15 | 0~25 |
| ①-질문(기다리며 뼈대) · ② 계획·2차 왕복 | ~30 | ~45 |
| ③ 구현 — 첫 완주 | ~60 | ~90 |
| ③ 개선·기능 동결 | ~70 | ~130 |
| ④ 대조 · ⑤ 문서 · ⑥ 모의 확인 문제 | ~85 | ~165 |
| ⑦ 제출 정리 | ~90 | ~180 |

추천(11/3): 오전에 `training-seats` 90분 압축 → 채점·고칠 점 정리 → 오후에 `inspection-crew` 180분 실전. **같은 과제를 두 번 하지 않는다**(함정을 알고 나면 연습 가치가 줄어든다).

## 4. 끝난 뒤 (30분)
1. 연습실에서 `python3 /tmp/kit/tools/predict_questions.py .` → 「출제 범위 경고」·「재료 부족」 확인.
2. 메인에 `모의 확인 문제 해줘` → 한 문항씩 답한다(전제 틀린 문항 포함).
3. AI를 닫고 `QUESTIONS.md` 8문항 중 4문항 이상을 5분 타이머로 손으로 쓴다.
4. `FACILITATOR.md` 끝 「채점 참고」로 놓친 함정을 세고, 아래 채점표를 채운다.
5. 키트 쪽 문제(AI가 카드를 안 따름 등)는 `playbooks/rehearsal.md` 카드로 다시 확인한다.

## 5. 채점표 (스스로 체크 · 기록 근거를 보고 판단)
| # | 확인할 것 | 기준 | 어디서 보나 |
|---|---|---|---|
| 1 | 담당자에게 보낸 메시지가 전부 물음표 하나였나 | 묶음 0건 | 담당자 창 기록 |
| 2 | 질문에 근거(파일·열·건수)를 붙였나 | 절반 이상 | 담당자 창 기록 |
| 3 | 숨은 규칙을 몇 개 찾았나 · **상충 쌍**을 찾았나 | 18칸 중 10+ · 상충 찾음 | `FACILITATOR.md` 표와 대조 |
| 4 | 돌려 말한 답을 닫힌 질문 → 제안 → 가정으로 닫았나 | 같은 주제 재질문 0 | AGENTS.md 「3. 가정」 |
| 5 | **2차 왕복**: 기준선 숫자를 붙인 2~3안을 보냈나 | 1회 이상 | 담당자 창 기록 |
| 6 | 기준선 vs 개선 표(같은 지표·위반 수 0) | DECISIONS 「5」에 두 줄 | `DECISIONS.md` |
| 7 | 결정 기록: 이유와 버린 대안이 있는 결정 | D행 3개 이상 | `DECISIONS.md` 「4」 |
| 8 | AI 판단 기록: 계기·증거가 있는 행 | A행 2개 이상 | `AI_COLLABORATION.md` 「2」 |
| 9 | 역할 격리를 서버에서 막고 검사로 확인했나 | 다른 사람 조회 → 거절 검사 1개 | 테스트 출력 |
| 10 | 변경본을 과제 규칙대로 처리했나 | A 전체 거절 / B 4행만 거절 | 테스트 출력 |
| 11 | 검사 출력으로 증명했나(0개 실행을 통과로 안 봄) | 실행 수 > 0, 미검증 표시 | 대화 기록 |
| 12 | 첫 완주 시각 | 압축 60분 · 실전 90분 안 | 커밋 시각 |
| 13 | 제출 정리 | `git status -s` 깨끗, 잡문서·키트 참조 0, 출제 범위 경고 0 | 명령 출력 |
| 14 | 모의 답이 4단계(결정→약점→파급→다음 검증) + 실제 숫자 | 4문항 이상 | 손으로 쓴 답 |
| 15 | 사람이 AI를 의심해 고친 순간 · 이유 붙인 결정 | 2회 · 3회 | 대화 기록 |

점수보다 **놓친 칸 하나당 다음에 보낼 문장 하나**를 적는다(예: 3번을 놓쳤으면 "인원·자격 질문을 첫 5개 안에").
