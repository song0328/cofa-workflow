---
name: verify-small-delivery
description: Build acceptance evidence and a concise handoff for a small app or data deliverable from its actual requirements and observed execution results.
---

실제 README·양식·사용자 지시를 읽고 제출 파일과 필수 범위를 정한다. 보이지 않는 업무 기준을 만들어 내지 않는다. 질문할 수 없으면 가정과 영향을 구분한다.

핵심 요구사항마다 정상·경계·오류 입력 중 의미 있는 사례를 고른다. 기대값을 구현 코드와 독립적으로 정하고 실제 출력과 비교한다. 같은 함수를 두 번 호출한 결과나 구현 복사본을 정답 기준으로 삼지 않는다.

JSON 비교가 필요하면 키트의 `tools/compare_json.py`, CSV 품질 확인은 `tools/csv_check.py`를 사용할 수 있다. 숫자 타입·행 순서·중복 처리 규칙은 요구사항을 따른다. 도구가 업무 결론을 정하지 않는다.

서비스는 검사 출력과 직접 조작한 화면을 구분하고 실패·빈 상태도 확인한다. 자료형 작업은 기준일·버전·분모·제외 항목·계산을 대조한다. 필수가 끝나기 전 선택 기능을 늘리지 않는다.

인계에는 바뀐 파일, 실제 명령·종료 코드, 직접 본 입력·결과, 선택 이유, 미구현·미검증을 남긴다. 실행하지 않은 검사나 사람이 보지 않은 화면을 확인했다고 쓰지 않는다. 실제 외부 전송·공개·접수는 작업 검증과 별도의 사용자 지시를 따른다.
