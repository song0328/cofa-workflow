"""서버 틀 통합 검사: 허용 목록 밖 파일 404(데이터·소스·.env 노출 금지), 동시 쓰기, 재시작 보존, 깨진 저장 파일 보존."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / 'recipes'


def call(base, path, body=None):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), method='POST' if body is not None else 'GET',
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


def load_python_server(data_dir):
    os.environ['DATA_DIR'] = data_dir
    os.environ.pop('DB_PATH', None)
    spec = importlib.util.spec_from_file_location(f'pyserver_{abs(hash(data_dir))}', RECIPES/'python_server.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


class PythonServerTest(unittest.TestCase):
    def start(self, data_dir):
        mod = load_python_server(data_dir)
        mod.Handler.log_request = lambda *a, **k: None          # 테스트 출력 조용히
        srv = mod.make_server(0)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close); self.addCleanup(srv.shutdown)
        return f'http://127.0.0.1:{srv.server_address[1]}'

    def test_static_allowlist_concurrency_persistence(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)                    # 서버 종료 뒤에 지운다(Windows 파일 잠금)
        if True:
            base = self.start(d)
            self.assertEqual(call(base, '/health')[0], 200)
            status, raw, headers = call(base, '/')
            self.assertEqual(status, 200); self.assertIn('<html', raw.decode())
            self.assertIn('X-Request-Id', headers)
            for leak in ('/python_server.py', '/data/data.sqlite3', '/.env', '/public/../python_server.py', '/../README.md'):
                self.assertEqual(call(base, leak)[0], 404, leak)
            self.assertEqual(call(base, '/api/items', {'name': ' ', 'qty': 1})[0], 400)
            barrier = threading.Barrier(12)
            codes = []
            def post(i):
                barrier.wait(); codes.append(call(base, '/api/items', {'name': f'p{i:02d}', 'qty': 1})[0])
            ts = [threading.Thread(target=post, args=(i,)) for i in range(12)]
            [t.start() for t in ts]; [t.join() for t in ts]
            self.assertEqual(codes.count(201), 12)
            base2 = self.start(d)                                  # 같은 DATA_DIR로 다시 띄움 = 재시작
            items = json.loads(call(base2, '/api/items')[1])['items']
            self.assertEqual(len(items), 12)


@unittest.skipIf(shutil.which('node') is None, 'node 없음')
class NodeServerTest(unittest.TestCase):
    def start(self, data_dir):
        p = subprocess.Popen(['node', str(RECIPES/'node-server.cjs')], env={**os.environ, 'PORT': '0', 'DATA_DIR': data_dir},
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(p.wait); self.addCleanup(p.kill)
        line = p.stdout.readline()
        port = re.search(r':(\d+)', line).group(1)
        return f'http://127.0.0.1:{port}'

    def test_static_allowlist_and_concurrency(self):
        with tempfile.TemporaryDirectory() as d:
            base = self.start(d)
            self.assertEqual(call(base, '/')[0], 200)
            for leak in ('/node-server.cjs', '/data.json', '/.env', '/../README.md', '/public/app.js'):
                self.assertEqual(call(base, leak)[0], 404, leak)
            barrier = threading.Barrier(12)
            codes = []
            def post(i):
                barrier.wait(); codes.append(call(base, '/api/items', {'name': f'n{i:02d}', 'qty': 2})[0])
            ts = [threading.Thread(target=post, args=(i,)) for i in range(12)]
            [t.start() for t in ts]; [t.join() for t in ts]
            self.assertEqual(codes.count(201), 12)
            saved = json.loads((Path(d)/'data.json').read_text(encoding='utf-8'))
            self.assertEqual(len(saved['items']), 12)
            self.assertEqual(len({i['id'] for i in saved['items']}), 12)

    def test_corrupted_store_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'data.json').write_text('{broken', encoding='utf-8')
            base = self.start(d)
            self.assertEqual(call(base, '/health')[0], 503)
            self.assertEqual(call(base, '/api/items', {'name': 'x', 'qty': 1})[0], 500)
            self.assertEqual((Path(d)/'data.json').read_text(encoding='utf-8'), '{broken')   # 원본 보존


if __name__ == '__main__':
    unittest.main()
