import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tab_task', ROOT/'tools'/'tab_task.py')
tt = importlib.util.module_from_spec(spec); spec.loader.exec_module(tt)


def run(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = tt.main(list(args))
    return code, buf.getvalue()


class TabTaskTest(unittest.TestCase):
    def test_new_status_done(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = run('--dir', d, 'new', 'T2', '--role', '탐구', '--goal', '배정 방법 2가지 비교', '--read', 'README.md', '--done', '비교표와 추천')
            self.assertEqual(code, 0)
            self.assertIn('T2.md 읽고 그대로 해.', out)
            line = [l for l in out.splitlines() if '읽고 그대로 해' in l][0]
            self.assertLess(len(line.strip()), 120)                     # 사람이 손으로 칠 한 줄
            card = (Path(d)/'T2.md').read_text(encoding='utf-8')
            self.assertIn('읽기 전용', card)
            self.assertIn('T2-result.md', card)
            self.assertIn('보조 탭', card)
            _, out = run('--dir', d, 'status')
            self.assertIn('| T2 | 탐구 |', out)
            self.assertIn('아직', out)
            (Path(d)/'T2-result.md').write_text('결론\n', encoding='utf-8')
            _, out = run('--dir', d, 'status')
            self.assertIn('있음(1줄)', out)
            run('--dir', d, 'done', 'T2')
            _, out = run('--dir', d, 'status')
            self.assertIn('| 끝 |', out)

    def test_verify_card_has_verdict_format(self):
        with tempfile.TemporaryDirectory() as d:
            run('--dir', d, 'new', 'T5', '--role', '검증', '--goal', '정원 규칙 독립 검사', '--read', 'README.md,DECISIONS.md',
                '--own', 'tests/test_rules.py', '--done', '판정 1줄')
            card = (Path(d)/'T5.md').read_text(encoding='utf-8')
            self.assertIn('코드를 고치지 않는다', card)
            self.assertLess(card.index('원래 요구사항'), card.index('구현 요약'))   # 요구사항·결정을 먼저 읽는다
            self.assertLess(card.index('DECISIONS.md'), card.index('구현 요약'))
            for word in ('R번호 / 파일:줄 / 기대 vs 실제 / 재현 명령 / 영향 / 최소 수정', '꼭 고칠 것', '선택',
                         '승인 / 수정 필요 / 판단 불가', '지적 없음', 'assert', 'skip', '예전 서버'):
                self.assertIn(word, card)
            self.assertLessEqual(len(card), 1500)                                   # 탭이 한 번에 읽을 길이
            run('--dir', d, 'new', 'T6', '--role', '탐구', '--goal', 'x', '--done', 'y')
            other = (Path(d)/'T6.md').read_text(encoding='utf-8')
            self.assertNotIn('승인 / 수정 필요', other)                              # 다른 역할 카드는 그대로
            self.assertIn('결론 3줄', other)

    def test_owner_overlap_and_worker_needs_files(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                run('--dir', d, 'new', 'T3', '--role', '작업', '--goal', 'x', '--done', 'y')
            run('--dir', d, 'new', 'T3', '--role', '작업', '--goal', '화면', '--own', 'web/map.js', '--done', 'y')
            with self.assertRaises(SystemExit):   # 진행 중인 T3와 담당 파일 겹침
                run('--dir', d, 'new', 'T4', '--role', '작업', '--goal', '다른 일', '--own', 'web/map.js,web/a.js', '--done', 'y')
            run('--dir', d, 'done', 'T3')
            code, _ = run('--dir', d, 'new', 'T4', '--role', '작업', '--goal', '다른 일', '--own', 'web/map.js', '--done', 'y')
            self.assertEqual(code, 0)                  # 끝난 카드와는 겹쳐도 된다


if __name__ == '__main__':
    unittest.main()
