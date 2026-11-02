import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('predict_questions', ROOT/'tools'/'predict_questions.py')
pq = importlib.util.module_from_spec(spec); spec.loader.exec_module(pq)


def run(path):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pq.main([str(path)])
    return code, buf.getvalue()


class PredictQuestionsTest(unittest.TestCase):
    def test_slots_use_my_files(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d/'app').mkdir(); (d/'tests').mkdir()
            (d/'app'/'planner.py').write_text('def greedy(): pass  # 휴리스틱\nimport sqlite3\nrole = "operator"\n', encoding='utf-8')
            (d/'app'/'server.py').write_text('def login(): pass\n', encoding='utf-8')
            (d/'tests'/'test_capacity.py').write_text('assert True\n', encoding='utf-8')
            (d/'verify_plan.py').write_text('print(1)\n', encoding='utf-8')
            (d/'Dockerfile').write_text('FROM python:3.12-slim\n', encoding='utf-8')
            (d/'DECISIONS.md').write_text('| # | 결정 |\n|---|---|\n| D1 | 그리디 + 2-opt로 개선 | 시간 |\n', encoding='utf-8')
            (d/'AI_COLLABORATION.md').write_text('| # | AI 제안 |\n|---|---|\n| A1 | 빈칸을 0으로 처리 | 원자료 대조 | 고침 |\n', encoding='utf-8')
            (d/'NOTES_FROM_AGENT.md').write_text('x', encoding='utf-8')
            code, out = run(d)
        self.assertEqual(code, 0)
        for k in range(1, 7):
            self.assertIn(f'## {k}.', out)
        self.assertIn('D1「그리디 + 2-opt로 개선', out)
        self.assertIn('A1 「빈칸을 0으로 처리', out)
        self.assertIn('`app/planner.py`', out)
        self.assertIn('`verify_plan.py`는 무엇을 보장', out)
        self.assertIn('역할(운영자·이용자 등)', out)
        self.assertIn('`Dockerfile`', out)
        self.assertIn('계산을 작업 큐로 비동기 처리한 이유는?', out)   # 비동기 없음 → 틀린 전제
        self.assertIn('`NOTES_FROM_AGENT.md`', out)                 # 출제 범위 경고

    def test_overclaim_warning(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d/'main.py').write_text('print(1)\n', encoding='utf-8')
            (d/'README.md').write_text('# 배치\n최적 배정을 항상 보장한다.\n위반 0건, 정확도 100%\n'
                                       '최적은 보장하지 않는다(하한 대비 4%).\n10건 처리\n'
                                       '```\npython3 run.py  # always optimal\n```\nIt is always optimal.\n', encoding='utf-8')
            (d/'DECISIONS.md').write_text('| # | 결정 |\n|---|---|\n| D1 | 실시간 대신 버튼 계산 | 근거 |\n', encoding='utf-8')
            code, out = run(d)
            self.assertEqual(code, 0)
            part = out.split('## 과장 단정어 경고')[1]
            self.assertIn('README.md:2 — 최적, 항상, 보장 — 최적 배정을 항상 보장한다.', part)
            self.assertIn('README.md:3 — 0건, 100%', part)
            self.assertIn('README.md:9 — always, optimal', part)
            self.assertIn('DECISIONS.md:3 — 실시간', part)
            self.assertNotIn('README.md:4', part)          # 부정·한계 문장은 정직한 표현
            self.assertNotIn('README.md:5', part)          # 10건은 0건이 아니다
            self.assertNotIn('README.md:7', part)          # 코드 블록 안
            self.assertIn('하한 대비', part)
            many = '\n'.join(f'{i}번 항상 된다' for i in range(15))
            (d/'NOTES.md').write_text(many, encoding='utf-8')
            _, out = run(d)
            part = out.split('## 과장 단정어 경고')[1]
            self.assertEqual(sum(1 for l in part.splitlines() if ' — ' in l and l.startswith('- ') and '.md:' in l), 10)
            self.assertIn('… 외', part)
            (d/'NOTES.md').unlink(); (d/'README.md').write_text('하한 대비 3% 위\n', encoding='utf-8')
            (d/'DECISIONS.md').write_text('기록\n', encoding='utf-8')
            _, out = run(d)
            self.assertNotIn('과장 단정어 경고', out)

    def test_missing_material_and_empty(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d/'main.py').write_text('print(1)\n', encoding='utf-8')
            code, out = run(d)
            self.assertIn('왜 별도의 최적화', out)
            self.assertIn('재료 부족', out)
            empty = d/'empty'; empty.mkdir()
            self.assertEqual(run(empty)[0], 2)


if __name__ == '__main__':
    unittest.main()
