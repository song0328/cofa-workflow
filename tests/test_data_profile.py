import contextlib
import csv
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('data_profile', ROOT/'tools'/'data_profile.py')
dp = importlib.util.module_from_spec(spec); spec.loader.exec_module(dp)


def write(path, rows, enc='utf-8'):
    with open(path, 'w', encoding=enc, newline='') as f:
        csv.writer(f).writerows(rows)


def run(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = dp.main(list(args))
    return code, buf.getvalue()


class DataProfileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name) / 'data'; d.mkdir()
        self.d = d
        write(d/'people.csv', [['person_id', '이름', 'score'], ['P1', '김가', '3'], ['P2', '이나', '-1'], ['P2', '이나', '0'], ['P4', '', '']], enc='cp949')
        write(d/'shifts.csv', [['person_id', 'date', 'start_time', 'end_time', 'status'],
                               ['P1', '2026-09-11', '22:00', '06:00', 'WORK'],
                               ['P1', '2026-09-12', '09:00', '18:00', 'OFF'],
                               ['P3', '2026-09-13', '09:00', '25:30', 'work']])

    def tearDown(self):
        self.tmp.cleanup()

    def test_findings(self):
        code, out = run(str(self.d))
        self.assertEqual(code, 0)
        self.assertIn('인코딩 cp949', out)
        self.assertIn('(개인정보로 보여 값 생략)', out)
        self.assertNotIn('김가', out)                       # 개인정보 값은 찍지 않는다
        self.assertIn('음수 1건', out)
        self.assertIn('대소문자·공백만 다른 값', out)
        self.assertIn('24시 이상 1건', out)
        self.assertIn('`end_time` < `start_time` 1건', out)
        self.assertIn('people.csv에만 2개', out)            # P2, P4
        self.assertIn('shifts.csv에만 1개(예: P3)', out)
        self.assertIn('금1', out)                           # 2026-09-11은 금요일

    def test_compare_and_nonunique_key_warning(self):
        new = Path(self.tmp.name) / 'changed.csv'
        write(new, [['person_id', 'date', 'start_time', 'end_time', 'status'],
                    ['P1', '2026-09-11', '22:00', '06:00', 'WORK'],
                    ['P1', '2026-09-12', '09:00', '18:00', 'WORK'],
                    ['P9', '2026-09-14', '09:00', '18:00', 'WORK']])
        code, out = run('--compare', str(self.d/'shifts.csv'), str(new), '--key', 'person_id')
        self.assertIn('키가 행마다 유일하지 않다', out)
        code, out = run('--compare', str(self.d/'shifts.csv'), str(new), '--key', 'person_id,date')
        self.assertEqual(code, 0)
        self.assertIn('추가 1 · 삭제 1', out)
        self.assertIn('`status` 값이 바뀐 행 1건', out)

    def test_empty_is_not_pass(self):
        empty = Path(self.tmp.name) / 'empty'; empty.mkdir()
        code, out = run(str(empty))
        self.assertEqual(code, 2)


if __name__ == '__main__':
    unittest.main()
