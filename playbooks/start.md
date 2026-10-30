# 시작 5분

## 1. 위치와 환경 (셸에서, AI 없이도 가능)
```bash
pwd; ls -la
git status 2>&1 | head -5
python3 --version; node --version; git --version
```
- `python` 명령이 없을 수 있다 → 항상 `python3`.
- 홈 폴더(`~`)에 환경 파일(`.codex/` 등)이 있을 수 있다. 과제 폴더를 정확히 확인한다.

## 2. README 읽기
```bash
cat README.md          # 디렉터리로 cd 하지 말고 파일은 cat으로 읽는다
ls -R | head -50       # 제공 파일 구조
```
볼 것: 필수조건 번호·개수 / 선택조건 유무 / 제출 파일 이름 / 실행·검사 명령 / 제공 데이터.

## 3. AI 시작
- 모델·권한 확인 후 짧은 지시부터: `prompts/1-analyze.md`.
- "다 만들어 줘"로 시작하지 않는다. 10분 만에 결과는 나오지만 고치느라 토큰과 시간을 다 쓴다.
