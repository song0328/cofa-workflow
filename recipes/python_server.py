"""패키지 없이 쓰는 JSON API + 정적 파일 서버 (Python 3.11 표준 라이브러리만)
실행: python3 python_server.py   (PORT=3000 기본, 0.0.0.0에 바인딩)
과제 README의 경로·필드·상태 코드·오류 형식에 맞게 고쳐 쓴다.
"""
import json
import os
import re
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ.get("PORT", "3000"))
ROOT = Path(__file__).resolve().parent
MAX_BODY = 1024 * 1024

# 저장소: sqlite3 (파일 하나). 매개변수 바인딩(?)만 쓴다.
DB = sqlite3.connect(os.environ.get("DB_PATH", str(ROOT / "data.sqlite3")), check_same_thread=False)
DB.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, qty INTEGER NOT NULL)")
DB.commit()


def create_item(data):
    """업무 로직: 서버와 테스트가 같이 쓰는 순수 함수에 가깝게."""
    name = data.get("name").strip() if isinstance(data.get("name"), str) else ""
    if not name:
        return 400, {"error": "NAME_REQUIRED"}
    qty = data.get("qty")
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
        return 400, {"error": "INVALID_QTY"}
    with DB:
        cur = DB.execute("INSERT INTO items (name, qty) VALUES (?, ?)", (name, qty))
    return 201, {"id": cur.lastrowid, "name": name, "qty": qty}


def list_items():
    rows = DB.execute("SELECT id, name, qty FROM items ORDER BY name, id").fetchall()
    return 200, {"items": [{"id": r[0], "name": r[1], "qty": r[2]} for r in rows]}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)   # 정적 파일 기준 폴더(../ 이탈은 내부에서 막힘)

    def send_json(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

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

    def do_GET(self):
        if self.path.split("?")[0] == "/api/items":
            return self.send_json(*list_items())
        m = re.fullmatch(r"/api/items/(\d+)", self.path.split("?")[0])
        if m:
            row = DB.execute("SELECT id, name, qty FROM items WHERE id = ?", (int(m.group(1)),)).fetchone()
            return self.send_json(200, {"id": row[0], "name": row[1], "qty": row[2]}) if row else self.send_json(404, {"error": "NOT_FOUND"})
        if self.path.startswith("/api/"):
            return self.send_json(404, {"error": "NOT_FOUND"})
        return super().do_GET()

    def do_POST(self):
        try:
            if self.path.split("?")[0] == "/api/items":
                return self.send_json(*create_item(self.read_json()))
            return self.send_json(404, {"error": "NOT_FOUND"})
        except ValueError as e:
            status, code = e.args
            return self.send_json(status, {"error": code})
        except Exception as e:  # 내부 정보는 로그에만
            self.log_error("internal: %r", e)
            return self.send_json(500, {"error": "INTERNAL"})


if __name__ == "__main__":
    print(f"http://0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
