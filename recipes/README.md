# recipes — 패키지 설치 없이 쓰는 코드 틀

시험 환경은 패키지 설치가 안 되거나 느릴 수 있다(메모리 1.6G). **Node 22·Python 3.11 표준 기능만** 쓰는 틀이다. 과제에 시작 코드·스택이 있으면 **그것을 우선**하고, 빈 폴더에서 서버를 만들어야 할 때만 쓴다.

- 그대로 복사해 과제 파일로 쓰지 말고, **과제 README의 경로·필드·오류 형식에 맞게 고쳐서** 쓴다(키트로 결과물을 통째로 대신하지 않는다). 과제 파일이 키트 경로를 `require`·`import`하면 안 된다.
- 모두 키트 저장 시점에 실제로 실행해 확인했다(아래 "확인" 명령).

| 파일 | 쓰임 | 확인 |
|---|---|---|
| `node-server.cjs` | JSON API + 정적 파일 서버, 본문 크기 제한, 경로 이탈 방지, JSON 파일 저장 | `node node-server.cjs` → `curl -s localhost:3000/api/items` |
| `python_server.py` | 같은 기능의 Python 버전 (`http.server`, `sqlite3` 예시) | `python3 python_server.py` |
| `node-test.cjs` | `node:test` 표 기반 테스트(정상·경계·오류) | `node --test node-test.cjs` |
| `python_test.py` | `unittest` 표 기반 테스트 | `python3 -m unittest python_test.py -v` |

서버는 사람이 새 터미널 탭에서 띄우고 Browser 미리보기 PORT 칸에 포트를 넣는다(`playbooks/flow.md` 「화면 미리보기」).
