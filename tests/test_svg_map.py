import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('svg_map', ROOT/'recipes'/'svg_map.py')
svg = importlib.util.module_from_spec(spec); spec.loader.exec_module(svg)

POINTS = {'D': (50, 50), 'A': (10, 10), 'B': (90, 10), 'C': (90, 90), 'Z': (5, 95)}
ROUTES = [{'id': 'R1', 'stops': ['D', 'A', 'B', 'D']}, {'id': 'R2', 'stops': ['D', 'C', 'D']}]


class SvgMapTest(unittest.TestCase):
    def test_lines_and_points(self):
        out = svg.render_svg(POINTS, ROUTES, depots=('D',))
        self.assertEqual(out.count('<line '), 3 + 2)           # 구간 수
        self.assertEqual(out.count('<circle '), 4)              # 거점 제외
        self.assertIn('R1 2번째', out)                          # 말풍선에 순서
        self.assertIn('Z · 경로 없음', out)                     # 배정 안 된 점
        self.assertIn('fill="#999"', out)

    def test_projection_inside_canvas(self):
        for mode, pts in (('xy', POINTS), ('latlon', {'a': (37.5, 127.0), 'b': (37.2, 127.4), 'c': (37.4, 126.9)})):
            xy = svg.project(pts, 800, 560, mode=mode)
            self.assertTrue(all(0 <= x <= 800 and 0 <= y <= 560 for x, y in xy.values()))

    def test_escape_and_deterministic(self):
        pts = {'<b>': (0, 0), 'x': (1, 1)}
        routes = [{'id': '<script>', 'stops': ['<b>', 'x']}]
        out = svg.render_html(pts, routes)
        self.assertNotIn('<script>', out)
        self.assertNotIn('<b>', out.replace('<body', ''))
        self.assertEqual(out, svg.render_html(pts, routes))

    def test_table(self):
        t = svg.route_table_html(ROUTES, {'R1': {'거리': 12.5}})
        self.assertIn('id="route-table"', t)
        self.assertIn('D → A → B → D', t)
        self.assertIn('12.5', t)

    @unittest.skipIf(shutil.which('node') is None, 'node 없음')
    def test_js_same_shape(self):
        code = ("const m=require(process.argv[1]);const r=JSON.parse(process.argv[2]);"
                "const s=m.routeMapSVG(r.p,r.r,{depots:['D']});"
                "console.log(JSON.stringify([(s.match(/<line /g)||[]).length,(s.match(/<circle /g)||[]).length,"
                "m.routeTableHTML([{id:'<x>',stops:['A']}]).includes('<x>')]))")
        arg = json.dumps({'p': {k: list(v) for k, v in POINTS.items()}, 'r': ROUTES})
        out = subprocess.run(['node', '-e', code, str(ROOT/'recipes'/'svg_map.js'), arg], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(out.stdout), [5, 4, False])


if __name__ == '__main__':
    unittest.main()
