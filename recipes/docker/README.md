# recipes/docker — 컨테이너 틀 (README가 Docker를 요구할 때만)

과제 README가 Docker·컨테이너 실행을 요구할 때만 쓴다. (2026-11-02 실제 확인: `Dockerfile.python`+`python_server.py`, `Dockerfile.node`+`node-server.cjs` 각각 build → healthy → 자료 생성 → `docker restart` 뒤 보존 → 비루트 실행, `compose.yaml` up → healthy.) 과제에 Dockerfile이 있으면 그것을 우선한다. 과제 계약에 맞게 복사해 고쳐 쓴다.

| 파일 | 과제 루트에 둘 이름 |
|---|---|
| `Dockerfile.python` / `Dockerfile.node` | `Dockerfile` (하나만) |
| `compose.yaml` | `compose.yaml` (README가 compose를 요구할 때만) |
| `dockerignore.example` | `.dockerignore` |

## 고칠 곳
- 진입 파일(`CMD`), 포트(`PORT`·`EXPOSE`·`-p`), 데이터 경로(`DATA_DIR=/data`)를 과제대로. 셋 다 맞아야 접속된다.
- 서버가 `PORT`·`DATA_DIR`를 읽고 `0.0.0.0`에 바인딩하게. 키트의 `python_server.py`·`node-server.cjs`는 이미 `PORT`·`DATA_DIR`를 읽고 `GET /health`가 있다.
- `/health`가 없으면 `GET /health → 200 {"ok":true}`를 추가한다(DB 연결까지 확인하면 더 좋다).
- `.dockerignore` 허용 목록을 실제 파일·폴더 이름으로 고친다.

## 확인 순서 (각 줄의 실제 출력을 보고서에 붙인다)
```bash
docker info >/dev/null && echo daemon-ok              # 실패면 아래 「데몬이 없을 때」
docker build -t app .
docker run -d --name app -p 3000:3000 -v app-data:/data app
curl -s localhost:3000/health                          # 200
docker inspect --format '{{.State.Health.Status}}' app # healthy (10초쯤 뒤)
# 역할마다 한 번씩 로그인 (운영자·이용자) → 자료 하나 만들기
docker restart app && curl -s localhost:3000/health    # 만든 자료가 그대로인지 조회
docker rm -f app                                        # 정리 (볼륨은 남는다)
```

## 데몬이 없을 때
`docker info`가 실패하면 설치·데몬 실행에 시간을 쓰지 않는다. Dockerfile은 남기고 보고서에 `Docker 실행: N/A(데몬 없음, docker info 출력)`이라고 쓴다. 대신 같은 환경변수로 직접 실행한 근거를 남긴다.
```bash
PORT=3000 DATA_DIR=./data python3 server.py   # → /health → 역할별 로그인 → 재시작 뒤 자료 보존
```
빌드하지 않은 이미지를 "확인했다"고 쓰지 않는다.

## 흔한 실패
| 증상 | 원인 | 고침 |
|---|---|---|
| 컨테이너는 도는데 접속 안 됨 | 서버가 `127.0.0.1`·`localhost`에 바인딩 | `0.0.0.0` |
| connection refused | `-p`·`PORT`·`EXPOSE`가 서로 다름 | 셋을 같게. 8090·8081·2222는 피한다 |
| 재시작하니 자료 사라짐 | 데이터가 `/app` 안, 볼륨 없음 | `DATA_DIR=/data` + `-v app-data:/data` |
| `/data` Permission denied | 바인드 마운트 폴더 소유자가 다름 | 이름 있는 볼륨 사용 |
| root로 실행 | `USER` 없음 | `USER app`(Python)·`USER node` |
| 빌드 느림·이미지 큼·비밀 유출 | 홈 전체(`.git`·`.ssh`·`.cache`·`.env`)가 맥락에 | `.dockerignore` 허용 목록 |
| `unhealthy` | `/health` 없음·포트 다름 | 경로 추가, 포트 맞춤 |
| `python: not found`(호스트) | 시험 환경은 `python3`만 | 호스트는 `python3`, 컨테이너 안은 `python` |
