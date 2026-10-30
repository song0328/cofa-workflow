---
name: review-local-security
description: Review a small local project for exposed credentials and concrete input, authorization, file-access and output-escaping risks when a security check is requested.
---

요청받은 프로젝트와 제출 범위에서 보안 위험을 확인한다. 업무 기능이나 공개 권한을 확대하지 않는다.

- 먼저 변경 파일과 실행 경로를 읽는다. 비밀 값은 출력하거나 보고서에 복사하지 않는다.
- 프로젝트를 수정하지 않고 문자열 점검부터 하려면 이 키트 루트의 `tools/security_check.py`를 실행한다. 의심 위치와 제외·미검사 파일을 읽는다. 문자열 점검 통과를 보안 통과로 쓰지 않는다.
- 실제 기능에 맞게 인증 전 접근, 다른 사용자 자료 접근, 파일 경로 이탈·링크, 입력 크기·타입, HTML 출력, 로그 노출 중 필요한 것을 확인한다. 정적 의심과 재현된 문제를 구분한다.
- 임의 외부 서버·실제 계정 공격·비밀 자료 열람은 하지 않는다. 수정이 요청되면 원인을 해결하는 작은 변경을 하고 관련 정상·거부 경로를 재확인한다.
- 결과는 위치·영향·재현 또는 근거·수정·미검증 순으로 짧게 쓴다. 의존성 버전 판정이 필요하면 잠금 파일과 공식 보안 공지를 확인한다. 검사 때문에 자동 업그레이드·배포·공개하지 않는다.

키트 도구가 없는 단독 설치 환경에서는 같은 범위의 수동 코드 검토를 하고, 자동 스캔을 실행하지 못했다고 밝힌다.
