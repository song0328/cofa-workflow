import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kit_setup', ROOT/'tools'/'kit_setup.py')
ks = importlib.util.module_from_spec(spec); spec.loader.exec_module(ks)


def run(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = ks.main(list(args))
    return code, buf.getvalue()


class KitSetupTest(unittest.TestCase):
    def test_creates_agents_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = run('--dir', d)
            self.assertEqual(code, 0)
            text = (Path(d)/'AGENTS.md').read_text(encoding='utf-8')
            self.assertIn('## 0. 상시 규칙', text)
            self.assertIn('## 1. 요건표', text)
            self.assertIn('codex', out)
            run('--dir', d)
            self.assertEqual((Path(d)/'AGENTS.md').read_text(encoding='utf-8'), text)   # 두 번 돌려도 그대로

    def test_preserves_task_agents_and_warns_override(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'AGENTS.md').write_text('# 과제 지침\n원문 줄\n', encoding='utf-8')
            (Path(d)/'AGENTS.override.md').write_text('x', encoding='utf-8')
            code, out = run('--dir', d)
            text = (Path(d)/'AGENTS.md').read_text(encoding='utf-8')
            self.assertTrue(text.index('## 0. 상시 규칙') < text.index('원문 줄'))
            self.assertIn('과제가 준 지침', text)
            self.assertNotIn('## 1. 요건표', text)          # 과제 지침이 있으면 상시 규칙만 덧붙인다
            self.assertIn('AGENTS.override.md', out)
            self.assertEqual((Path(d)/'AGENTS.override.md').read_text(encoding='utf-8'), 'x')

    def test_refuses_kit_folder_as_task(self):
        code, out = run('--dir', str(ROOT))
        self.assertEqual(code, 1)


if __name__ == '__main__':
    unittest.main()
