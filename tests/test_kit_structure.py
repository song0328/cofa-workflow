"""키트 구조 검사: 처음 읽는 파일이 다시 커지지 않게(토큰), 카드가 가리키는 파일·절이 실제로 있게(놓침 방지)."""
import contextlib
import importlib.util
import io
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kit_read', ROOT/'tools'/'kit_read.py')
kr = importlib.util.module_from_spec(spec); spec.loader.exec_module(kr)

ENTRY = [ROOT/'KIT-INDEX.md', ROOT/'templates'/'AGENTS.md'] + sorted((ROOT/'stages').glob('*.md'))
PATH = re.compile(r"`((?:playbooks|knowledge|recipes|templates|tools|stages|skills|prompts)/[^`\s\"]+?)`")
# `파일` "절" 또는 kit_read.py 파일 "절1" "절2"
REF = re.compile(r"(?:`|kit_read\.py )((?:playbooks|knowledge|recipes|templates|stages)/[\w./-]+\.md)`?((?:\s*(?:·\s*)?\"[^\"]+\")+)")


def text(p):
    return p.read_text(encoding='utf-8')


class KitStructureTest(unittest.TestCase):
    def test_entry_budgets(self):
        self.assertLessEqual(len(text(ROOT/'KIT-INDEX.md')), 4300)
        agents = text(ROOT/'templates'/'AGENTS.md')
        self.assertLessEqual(agents.index('## 1.'), 1500, 'AGENTS.md 상시 규칙은 세션 맥락에 늘 실린다 — 짧게')
        for card in (ROOT/'stages').glob('*.md'):
            self.assertLessEqual(len(text(card)), 1500, card.name)

    def test_stage_cards_chain(self):
        cards = sorted((ROOT/'stages').glob('*.md'))
        self.assertEqual(len(cards), 8)
        index = text(ROOT/'KIT-INDEX.md')
        for c in cards:
            self.assertIn(f'stages/{c.name}', index)
        for c in cards[:-1]:
            self.assertIn('## 다음', text(c), c.name)

    def test_referenced_paths_exist(self):
        for f in ENTRY:
            for rel in PATH.findall(text(f)):
                rel = rel.rstrip('.,)')
                if '<' in rel or '*' in rel:
                    continue
                self.assertTrue((ROOT/rel).exists(), f'{f.name}: {rel} 없음')

    def test_referenced_sections_exist(self):
        checked = 0
        for f in ENTRY:
            for rel, quoted in REF.findall(text(f)):
                _, secs = kr.sections(text(ROOT/rel))
                titles = [t for _, t, _, _ in secs]
                for q in re.findall(r'"([^"]+)"', quoted):
                    if q.startswith('<'):
                        continue
                    self.assertTrue(any(q in t or q.replace(' ', '') in t.replace(' ', '') for t in titles), f'{f.name}: {rel} 「{q}」 절 없음')
                    checked += 1
        self.assertGreater(checked, 15)

    def test_human_messages_fit_input_limit(self):
        """시험 입력창은 한 번에 1000자. 사람이 보낼 예시 문장은 300자, 6칸 지시 틀은 1000자 이내."""
        files = sorted((ROOT/'stages').glob('*.md')) + [ROOT/'playbooks'/p for p in ('lead-like-dev.md', 'stakeholder.md', 'codex.md', 'edge-hunt.md')]
        for f in files:
            for q in re.findall(r'"([^"\n]{20,})"', text(f)):
                self.assertLessEqual(len(q), 300, f'{f.name}: {q[:40]}…')
        block = re.search(r"```\n(\[목표\].*?)```", text(ROOT/'playbooks'/'codex.md'), re.S).group(1)
        self.assertLessEqual(len(block), 1000)

    def test_kit_read(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(kr.main(['playbooks/stakeholder.md', '2차 왕복']), 0)
        out = buf.getvalue()
        self.assertTrue(out.startswith('## 2차 왕복'))
        self.assertNotIn('## 담당자가 답을 돌려 말할 때', out)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(kr.main(['playbooks/stakeholder.md', '없는 절']), 1)
            self.assertEqual(kr.main(['playbooks/codex.md']), 0)


if __name__ == '__main__':
    unittest.main()
