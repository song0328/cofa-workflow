"""패키지 없이 쓰는 JSON API + 정적 파일 서버 (Python 3.9+ 표준 라이브러리만)
실행: python3 python_server.py   (PORT=3000 기본, 0.0.0.0에 바인딩, PORT=0이면 빈 포트)
과제 README의 경로·필드·상태 코드·오류 형식에 맞게 고쳐 쓴다.
안전 기본값: 화면 파일은 public/ 안의 허용 목록만 내보낸다(데이터·소스·.env 노출 금지, 폴더 목록 없음) ·
요청마다 DB 연결을 새로 열어 스레드끼리 연결을 공유하지 않는다 · 요청마다 JSON 한 줄 로그와 X-Request-Id.
"""
import json
import os
import re
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ.get("PORT", "3000"))
ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"                                   # 화면 파일 폴더(코드·데이터와 분리)
STATIC = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/style.css": "style.css"}   # 허용 목록
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}
MAX_BODY = 1024 * 1024
DATA_DIR = Path(os.environ.get("DATA_DIR", str(ROOT / "data")))   # Docker에서는 DATA_DIR=/data (볼륨)
DB_PATH = os.environ.get("DB_PATH", str(DATA_DIR / "data.sqlite3"))
STARTED = datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    """요청마다 새 연결(스레드 안전). 매개변수 바인딩(?)만 쓴다."""
    con = sqlite3.connect(DB_PATH, timeout=5)
    con.execute("PRAGMA busy_timeout = 5000")
    return con


def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, qty INTEGER NOT NULL)")


def validate_item(data):
    """업무 로직(검증)은 DB·HTTP를 모르는 순수 함수로."""
    name = data.get("name").strip() if isinstance(data.get("name"), str) else ""
    if not name:
        return None, "NAME_REQUIRED"
    qty = data.get("qty")
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
        return None, "INVALID_QTY"
    return {"name": name, "qty": qty}, None


def create_item(data):
    value, err = validate_item(data)
    if err:
        return 400, {"error": err}
    with connect() as con:                                 # 한 트랜잭션: 실패하면 롤백
        cur = con.execute("INSERT INTO items (name, qty) VALUES (?, ?)", (value["name"], value["qty"]))
    return 201, {"id": cur.lastrowid, **value}


def list_items():
    with connect() as con:
        rows = con.execute("SELECT id, name, qty FROM items ORDER BY name, id").fetchall()
    return 200, {"items": [{"id": r[0], "name": r[1], "qty": r[2]} for r in rows]}


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.req_id, self.t0, self.err = None, time.monotonic(), None

    def send_json(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.err = body.get("error") if isinstance(body, dict) else None
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Request-Id", self.req_id)
        self.end_headers()
        self.wfile.write(raw)

    def log_request(self, code="-", size="-"):             # JSON 한 줄 로그(본문·토큰·개인정보는 넣지 않는다)
        print(json.dumps({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "req_id": self.req_id,
                          "method": self.command, "path": self.path.split("?")[0], "status": int(code) if str(code).isdigit() else code,
                          "ms": round((time.monotonic() - self.t0) * 1000), "error": self.err}, ensure_ascii=False), file=sys.stderr)

    def read_json(self):
        size = int(self.headers.get("Content-Length") or 0)
        if size > MAX_BODY:
            raise ValueError(413, "TOO_LARGE")
        if size == 0:
            return {}
        try:
            data = json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError(400, "INVALID_JSON")
        if not isinstance(data, dict):
            raise ValueError(400, "INVALID_JSON")
        return data

    def handle_one_request(self):
        self.t0 = time.monotonic()
        super().handle_one_request()

    def route(self, method):
        self.req_id = self.headers.get("X-Request-Id") or uuid.uuid4().hex[:8]
        path = self.path.split("?")[0]
        try:
            if method == "GET":
                if path == "/health":                      # 헬스체크: DB까지 확인
                    try:
                        with connect() as con:
                            n = con.execute("SELECT COUNT(*) FROM items").fetchone()[0]
                        return self.send_json(200, {"ok": True, "items": n, "started": STARTED})
                    except sqlite3.Error:
                        return self.send_json(503, {"ok": False, "error": "DB_UNAVAILABLE"})
                if path == "/api/items":
                    return self.send_json(*list_items())
                m = re.fullmatch(r"/api/items/(\d+)", path)
                if m:
                    with connect() as con:
                        row = con.execute("SELECT id, name, qty FROM items WHERE id = ?", (int(m.group(1)),)).fetchone()
                    return self.send_json(200, {"id": row[0], "name": row[1], "qty": row[2]}) if row else self.send_json(404, {"error": "NOT_FOUND"})
                if path in STATIC:                         # 허용 목록만(소스·데이터·.env를 내보내지 않는다)
                    return self.send_file(PUBLIC / STATIC[path])
                return self.send_json(404, {"error": "NOT_FOUND"})
            if method == "POST" and path == "/api/items":
                return self.send_json(*create_item(self.read_json()))
            return self.send_json(404 if path.startswith("/api/") else 405, {"error": "NOT_FOUND" if path.startswith("/api/") else "METHOD_NOT_ALLOWED"})
        except ValueError as e:
            status, code = e.args
            return self.send_json(status, {"error": code})
        except Exception as e:                             # 내부 정보는 로그에만
            self.log_error("internal: %r", e)
            return self.send_json(500, {"error": "INTERNAL"})

    def send_file(self, file):
        try:
            raw = file.read_bytes()
        except OSError:
            return self.send_json(404, {"error": "NOT_FOUND"})
        self.send_response(200)
        self.send_header("Content-Type", TYPES.get(file.suffix, "text/plain; charset=utf-8"))
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Request-Id", self.req_id)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")


def make_server(port=PORT):
    init_db()
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)


if __name__ == "__main__":
    srv = make_server()
    print(f"http://0.0.0.0:{srv.server_address[1]}", flush=True)
    srv.serve_forever()
