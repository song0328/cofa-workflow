# 과제 유형 판별

분석(①) 때 README·제공 파일을 보고 유형을 **하나 또는 둘** 고른 뒤 해당 파일만 연다. 섞여 있으면 결과물(제출물) 기준으로 주 유형을 정한다.

| 단서 | 유형 | 열 파일 |
|---|---|---|
| "API를 만들어라", "화면을 구현", 빈 프로젝트·시작 코드 | 새 서비스 | `playbooks/types/service.md` |
| 이미 동작하는 코드 + "기능 추가/버그/개선" | 기존 코드 수정 | `playbooks/types/existing-code.md` |
| 휴가·결재·채용·근태·예약·재고·정산·권한 같은 사내 업무 규칙 | 사내 업무 시스템 | `playbooks/types/internal-system.md` |
| CSV·엑셀·로그·설문 + "분석·집계·보고서" | 데이터 분석·보고 | `playbooks/types/data-report.md` |
| 규정·정책·약관 + "판정·검토·답변 작성", 코드 거의 없음 | 규정 해석·판정 | `playbooks/types/policy-review.md` |
| 파일 변환·배치·정리·알림, "자동화" | 자동화 스크립트 | `playbooks/types/automation.md` |
| "AI/LLM 기능을 넣어라", 요약·분류·추천 | AI 기능 포함 | `playbooks/types/ai-feature.md` |

공통: 유형과 무관하게 `prompts/` 순서, `playbooks/decision-gates.md`의 결정 지점, `playbooks/verification.md`의 검증 원칙은 같다.
