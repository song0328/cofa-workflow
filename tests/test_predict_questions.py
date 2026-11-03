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
            (d/'HOW_TO_USE.md').write_text('| # | 결정·협업 |\n|---|---|\n| D2 | 단일 저장소 유지 | 운영 규모 |\n| A2 | 캐시 제안 재검토 | 내 주장은 최신성 우선 | 수정 |\n', encoding='utf-8')
            (d/'NOTES_FROM_AGENT.md').write_text('x', encoding='utf-8')
            code, out = run(d)
        self.assertEqual(code, 0)
        for k in range(1, 7):
            self.assertIn(f'## {k}.', out)
        self.assertIn('D1「그리디 + 2-opt로 개선', out)
        self.assertIn('A1 「빈칸을 0으로 처리', out)
        self.assertIn('D2「단일 저장소 유지', out)
        self.assertIn('A2 「캐시 제안 재검토', out)
        self.assertIn('`app/planner.py`', out)
        self.assertIn('`verify_plan.py`는 무엇을 보장', out)
        self.assertIn('사용자·운영자·담당자 중 실제 역할', out)
        self.assertIn('어떤 보안 요구를 SSOT 권한표로 옮겼고', out)
        self.assertIn('화면에서 숨긴 것과 실제 서버 권한 검사', out)
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

    def test_data_error_ownership(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d/'main.py').write_text('print(1)\n', encoding='utf-8')
            (d/'HOW_TO_USE.md').write_text('틀린 행은 오류 목록에 남긴다.\n', encoding='utf-8')
            _, out = run(d)
            part = out.split('## 4.')[1].split('## 5.')[0]
            self.assertIn('누가 발견하고, 누가 고치고, 누가 승인하고', part)
            self.assertIn('제출 문서에 없는 것: 데이터 소유자, 수정 승인, 복구 주체)', part)
            self.assertNotIn('오류 격리', part)
            (d/'HOW_TO_USE.md').write_text('원자료 정정은 인사팀(데이터 소유자)이, 확정 결과 변경은 팀장이 승인한다.\n'
                                           '틀린 행은 원문·사유와 함께 격리하고, 운영자가 정정본으로 재처리한다.\n', encoding='utf-8')
            _, out = run(d)
            self.assertNotIn('누가 발견하고, 누가 고치고', out)

    def test_focus_and_answers_file(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d/'main.py').write_text('print(1)\n', encoding='utf-8')
            (d/'HOW_TO_USE.md').write_text('| # | 결정 |\n|---|---|\n| D1 | 정원 초과는 대기 명단으로 | 담당자 답 |\n', encoding='utf-8')
            _, out = run(d)
            self.assertIn('핵심 로직이 실제로 무엇을 하는지', out)
            self.assertIn('서비스 장애는 어디서 가장 먼저', out.split('## 4.')[1].split('## 5.')[0])
            focus = out.split('## 집중 질문')[1].split('## ')[0]
            self.assertEqual(focus.count('D1「정원 초과는 대기 명단으로」:'), 6)
            self.assertIn('- 없음 → ⑥에서 제출 루트에 `templates/Answers.md`', out)
            (d/'Answers.md').write_text((ROOT/'templates'/'Answers.md').read_text(encoding='utf-8'), encoding='utf-8')
            _, out = run(d)
            part = out.split('## Answers.md 점검')[1]
            self.assertIn('틀 안내 줄(>) 6개', part)
            self.assertIn('비어 있는 답 8개', part)
            self.assertIn('「핵심 결정 집중」 빈 칸 6개', part)
            self.assertNotIn('따로 생긴 문서: `Answers.md`', out)   # 출제 범위 경고 대상 아님
            (d/'Answers.md').write_text('# Answers\n## 1. 핵심 로직은?\n정원을 넘으면 대기로 보낸다.\n\n## 2. 장애는?\n(답)\n', encoding='utf-8')
            _, out = run(d)
            self.assertIn('비어 있는 답 1개', out)                    # 괄호 안내만 남은 2번
            (d/'Answers.md').write_text('# Answers\n| 각도 | 답 |\n|---|---|\n| 왜 | 대기가 공정하다 |\n\n'
                                        '## 1. 핵심 로직은?\n정원을 넘으면 대기로 보낸다.\n\n## 2. 장애는?\n업로드가 먼저다.\n', encoding='utf-8')
            _, out = run(d)
            self.assertIn('`Answers.md` 준비됨', out)
            # 가상 예시는 안내 줄(>)만 빼면 그대로 통과하고 과장 단정어도 없어야 한다(따라 쓰는 본보기).
            example = (ROOT/'templates'/'Answers-example.md').read_text(encoding='utf-8')
            (d/'Answers.md').write_text('\n'.join(l for l in example.splitlines() if not l.startswith('>')), encoding='utf-8')
            _, out = run(d)
            self.assertIn('`Answers.md` 준비됨', out)
            self.assertNotIn('Answers.md:', out)
            self.assertEqual(example.count('\n## ') - 2, 8)             # 한눈에·핵심 결정 집중 + 번호 질문 8개
            self.assertNotIn('근거:', example)
            self.assertNotIn('Q1', example)

    def test_plain_test_file_is_a_check(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d/'src').mkdir()
            (d/'src'/'app.js').write_text('module.exports={}\n', encoding='utf-8')
            (d/'test.cjs').write_text("require('node:assert');\n", encoding='utf-8')
            _, out = run(d)
            self.assertIn('코드 1 · 검사 1', out)
            self.assertIn('`test.cjs`', out)

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
