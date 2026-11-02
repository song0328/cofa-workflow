import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('evidence', ROOT/'tools'/'evidence.py')
ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)

PY = sys.executable


def run(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = ev.main(list(args))
    return code, buf.getvalue()


class EvidenceTest(unittest.TestCase):
    def setUp(self):
        self._t1, self._t2 = tempfile.TemporaryDirectory(), tempfile.TemporaryDirectory()
        self.task, self.work = Path(self._t1.name), Path(self._t2.name)
        (self.task/'app.py').write_text('X = 1\n', encoding='utf-8')
        (self.task/'tests').mkdir()
        (self.task/'tests'/'test_app.py').write_text(
            'import unittest\nclass T(unittest.TestCase):\n    def test_a(self): pass\n    def test_b(self): pass\n', encoding='utf-8')

    def tearDown(self):
        self._t1.cleanup(); self._t2.cleanup()

    def check(self, name, *cmd, track=None):
        args = ['--dir', str(self.work), 'check', '--name', name, '--root', str(self.task)]
        for t in track or []:
            args += ['--track', t]
        return run(*args, '--', *cmd)

    def test_pass_fail_and_zero_tests(self):
        code, out = self.check('unit', PY, '-m', 'unittest', 'discover', '-s', 'tests')
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), 'E1 PASS unit (exit 0) — 2 passed')
        code, out = self.check('boom', PY, '-c', 'import sys; print("1 failed, 3 passed"); sys.exit(1)')
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith('E2 FAIL boom (exit 1) — 1 failed, 3 passed'))
        code, out = self.check('empty', PY, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'nothing_*.py')
        self.assertEqual(code, 2)
        self.assertIn('E3 NOT_RUN empty', out)
        code, out = self.check('pyt', PY, '-c', 'print("collected 0 items")')
        self.assertEqual(code, 2)                       # exit 0이어도 0개면 NOT_RUN
        for text, status in [('Ran 0 tests', 'NOT_RUN'), ('no tests ran in 0.01s', 'NOT_RUN'), ('0 passed', 'NOT_RUN'),
                             ('10 passed', 'PASS'), ('0 passed, 2 failed', 'FAIL'), ('# tests 0', 'NOT_RUN')]:
            self.assertEqual(ev.judge(1 if 'failed' in text else 0, text)[0], status, text)
        code, out = self.check('missing-cmd', 'definitely-not-a-command-xyz')
        self.assertEqual(code, 1)
        self.assertIn('exit 127', out)
        self.assertEqual(list(self.task.glob('evidence*')), [])      # 과제 폴더에는 아무것도 안 쓴다
        rec = json.loads((self.work/'evidence.jsonl').read_text(encoding='utf-8').splitlines()[0])
        self.assertEqual(rec['fp_before'], rec['fp_after'])
        self.assertLessEqual(len(rec['tail']), 20)

    def test_unstable_when_command_changes_tracked_files(self):
        code, out = self.check('writer', PY, '-c', 'open("app.py","a").write("Y = 2\\n"); print("1 passed")')
        self.assertEqual(code, 0)
        self.assertIn('불안정', out)
        code, out = self.check('writer', PY, '-c', 'open("out.txt","w").write("x"); print("1 passed")', track=['app.py'])
        self.assertNotIn('불안정', out)                 # 추적 밖 파일은 지문에 안 들어간다

    def test_stale_after_change_and_handoff(self):
        code, _ = run('--dir', str(self.work), 'handoff', '--required', 'R1')
        self.assertEqual(code, 2)                       # 증거가 하나도 없음
        self.check('unit', PY, '-m', 'unittest', 'discover', '-s', 'tests', track=['app.py,tests'])
        self.check('lint', PY, '-c', 'import sys; sys.exit(3)', track=['app.py'])
        run('--dir', str(self.work), 'link', 'R1', 'E1')
        run('--dir', str(self.work), 'link', 'R2', 'E2')
        with self.assertRaises(SystemExit):
            run('--dir', str(self.work), 'link', 'R3', 'E9')
        code, out = run('--dir', str(self.work), 'handoff', '--required', 'R1,R2,R3')
        self.assertEqual(code, 1)
        self.assertIn('통과  R1: E1 PASS', out)
        self.assertIn('R2: E2 lint FAIL', out)
        self.assertIn('R3: 연결된 증거 없음', out)
        self.assertEqual(run('--dir', str(self.work), 'handoff', '--required', 'R1')[0], 0)
        _, out = run('--dir', str(self.work), 'status')
        self.assertIn('| E1 | unit | PASS | 0 |', out)
        self.assertIn('최신', out)
        (self.task/'app.py').write_text('X = 2\n', encoding='utf-8')   # 검사 뒤 코드가 바뀜
        _, out = run('--dir', str(self.work), 'status')
        self.assertIn('STALE', out)
        code, out = run('--dir', str(self.work), 'handoff', '--required', 'R1')
        self.assertEqual(code, 1)
        self.assertIn('STALE', out)
        self.check('unit', PY, '-m', 'unittest', 'discover', '-s', 'tests', track=['app.py,tests'])   # 같은 이름 재실행 = E3
        code, out = run('--dir', str(self.work), 'handoff', '--required', 'R1')
        self.assertEqual(code, 0)
        self.assertIn('R1: E3 PASS', out)

    def test_refuses_work_dir_inside_task(self):
        with self.assertRaises(SystemExit):
            run('--dir', str(self.task/'work'), 'check', '--name', 'x', '--root', str(self.task), '--', PY, '-c', 'pass')
        self.assertFalse((self.task/'work').exists())        # 폴더조차 만들지 않는다


if __name__ == '__main__':
    unittest.main()
