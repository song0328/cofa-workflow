# 자주 쓰는 셸 명령 (Linux)

| 하고 싶은 것 | 명령 |
|---|---|
| 현재 위치·목록 | `pwd` · `ls -la` |
| 파일 내용 | `cat 파일` · `head -50 파일` · `tail -50 파일` |
| 전체 구조 | `ls -R \| head -80` · `find . -name "*.js" -not -path "*/node_modules/*"` |
| 글자 찾기 | `grep -rn "찾을말" --include="*.js" .` |
| 줄 수 | `wc -l 파일` |
| JSON 보기 | `python3 -m json.tool 파일.json` |
| 정적 서버 | `python3 -m http.server 3000 --bind 0.0.0.0` |
| Node 실행·테스트 | `node 파일.js` · `node --test` · `npm test` |
| 파이썬 테스트 | `python3 -m unittest -v` · `python3 -m pytest -q`(설치돼 있을 때) |
| 요청 보내기 | `curl -s -i http://localhost:3000/경로` |
| 포트 쓰는 프로세스 | `ss -ltnp \| grep 3000` |
| 프로세스 끄기 | `kill <PID>` (서버 탭에서는 Ctrl+C) |
| 디스크·메모리 | `df -h .` · `free -m` |
