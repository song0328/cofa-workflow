# recipes — 패키지 설치 없이 쓰는 코드 틀

시험 환경은 패키지 설치가 안 되거나 느릴 수 있다(메모리 1.6G). **Node 22·Python 3.11 표준 기능만** 쓰는 틀이다. 과제에 시작 코드·스택이 있으면 **그것을 우선**하고, 빈 폴더에서 서버를 만들어야 할 때만 쓴다.

- 그대로 복사해 과제 파일로 쓰지 말고, **과제 README의 경로·필드·오류 형식에 맞게 고쳐서** 쓴다(키트로 결과물을 통째로 대신하지 않는다). 과제 파일이 키트 경로를 `require`·`import`하면 안 된다.
- 모두 키트 저장 시점에 실제로 실행해 확인했다(아래 "확인" 명령).

| 파일 | 쓰임 | 확인 |
|---|---|---|
| `node-server.cjs` | JSON API + 정적 파일 서버, 본문 크기 제한, 경로 이탈 방지, JSON 파일 저장(`DATA_DIR`), `GET /health` | `node node-server.cjs` → `curl -s localhost:3000/api/items` |
| `python_server.py` | 같은 기능의 Python 버전 (`http.server`, `sqlite3`, `DATA_DIR`, `GET /health`) | `python3 python_server.py` |
| `node-test.cjs` | `node:test` 표 기반 테스트(정상·경계·오류) | `node --test node-test.cjs` |
| `python_test.py` | `unittest` 표 기반 테스트 | `python3 -m unittest python_test.py -v` |
| `python_auth.py` | 비밀번호 해시·세션 만료·역할 확인·본인 데이터만 (표준 라이브러리) | `python3 python_auth.py` |
| `opt_heuristics.py` | 일반 휴리스틱 틀: 하한, FFD 묶기, sweep 군집, 최근접 경로 + 2-opt, 독립 검사기 예시 | `python3 opt_heuristics.py` (기준선 vs 개선 표 출력) |
| `svg_map.py` · `svg_map.js` | 점·경로를 SVG 지도로 그리기(위경도·평면, 방향 화살표, 말풍선, 같은 내용의 표 `#route-table`). 서버에서 그리거나(Python) 화면에서 그린다(JS) | `python3 svg_map.py` → `demo_map.html` |
| `docker/` | Dockerfile(Python·Node)·compose·dockerignore 예시와 기동 점검 순서 | `recipes/docker/README.md` |

서버는 사람이 새 터미널 탭에서 띄우고 Browser 미리보기 PORT 칸에 포트를 넣는다(`playbooks/flow.md` 「화면 미리보기」).
