"""제출할 파일을 읽어 서술형 예상 질문을 '6칸'으로 뽑는다 (python3 표준 라이브러리만 · AI 없이).
확인 문제는 제출물·작업 기록에서 사람마다 다르게 나오지만, 10/31 응시자 기록을 겹쳐 보면 칸은 거의 같았다:
  1 방법 선택  2 구조·데이터 흐름  3 구현 vs 가정  4 장애·운영  5 변화·판단  6 AI 협업 사례
칸마다 내 파일 이름·결정 번호·협업 기록을 넣어 질문을 만든다. 전제가 틀린 질문 1개도 섞는다.

  python3 predict_questions.py [과제 폴더]      (기본: 현재 폴더)
출력 끝의 「출제 범위 경고」는 내가 설명하기 어려운 파일이 제출물에 섞였는지 알려 준다.
「과장 단정어 경고」는 문서(.md)의 '최적·항상·보장' 같은 말을 찾는다 — 근거 없는 단정은 그대로 질문이 된다.
종료 코드: 0 · 2 (제출 파일을 하나도 못 찾음)
"""
import re
import subprocess
import sys
from pathlib import Path

CODE = {".py", ".js", ".cjs", ".mjs", ".ts", ".tsx", ".jsx", ".html", ".go", ".java"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".cache", ".codex", ".agents", "kit", "notes"}
EXPECTED_DOCS = {"readme.md", "decisions.md", "ai_collaboration.md", "agents.md", "how_to_run.md", "how_to_use.md", "ai_qa.md", "export_schema.md"}
SIGNS = {
    "권한": r"\b(role|admin|operator|member|login|session|auth)\b|권한|운영자|로그인",
    "저장": r"sqlite|\.db\b|json\.dump|writefile|insert into|update\s+\w+\s+set",
    "동시성": r"\bversion\b|409|transaction|begin\b|lock|os\.replace|rename",
    "비동기": r"\bjob\b|queue|thread|async |await |setinterval|status",
    "알고리즘": r"heuristic|greedy|two_opt|2-?opt|cluster|sweep|solver|optimi|knapsack|dijkstra|휴리스틱|그리디|최적",
    "검증": r"assert|unittest|pytest|node:test|expect\(",
}
# 근거 없이 쓰면 "정말 그런가?" 질문이 되는 단정어. 숫자 앞뒤는 다른 숫자의 일부가 아닐 때만(10건·1100%는 제외).
OVERCLAIM = re.compile(r"최적|모든|항상|완벽|보장|실시간|안전|검증됨|(?<![\d.])100\s?%|(?<![\d.])0\s?건|절대|무조건"
                       r"|\b(?:optimal|always|guarantee[sd]?)\b", re.I)
HEDGED = re.compile(r"않|아니(?:다|며|고|라)|\bnot\b|n't\b|cannot", re.I)  # 부정·한계 문장은 정직한 표현이라 뺀다


def files_of(root):
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout.split("\n")
        paths = [root / p for p in out if p]
    except (subprocess.CalledProcessError, FileNotFoundError):
        paths = [p for p in root.rglob("*") if p.is_file()]
    keep = []
    for p in paths:
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS or (part.startswith(".") and part not in (".dockerignore",)) for part in rel.parts[:-1]):
            continue
        if rel.name.startswith(".") and rel.name != ".dockerignore":
            continue
        keep.append(rel)
    return sorted(keep)


def table_rows(text, prefix):
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and re.fullmatch(prefix + r"\d+", cells[0]) and any(c for c in cells[1:]):
            rows.append(cells)
    return rows


def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def overclaims(root, docs, limit=10):
    """문서에서 단정어가 든 줄을 찾는다. 코드 블록(```) 안과 부정 문장은 뺀다. 반환: (보일 줄, 전체 수)"""
    hits = []
    for rel in docs:
        fence = False
        for no, line in enumerate(read(root / rel).splitlines(), 1):
            if line.lstrip().startswith("```"):
                fence = not fence
                continue
            if fence or HEDGED.search(line):
                continue
            words = list(dict.fromkeys(m.group(0) for m in OVERCLAIM.finditer(line)))
            if words:
                hits.append(f"{rel.as_posix()}:{no} — {', '.join(words)} — {line.strip()[:60]}")
    return hits[:limit], len(hits)


def main(argv):
    root = Path(argv[0] if argv else ".").resolve()
    rels = files_of(root)
    if not rels:
        print("제출 파일을 찾지 못함")
        return 2
    code = [r for r in rels if r.suffix in CODE and not re.search(r"(^|/)tests?/|test_|\.test\.|_test\.", r.as_posix())]
    tests = [r for r in rels if re.search(r"(^|/)tests?/|test_|\.test\.|_test\.", r.as_posix())]
    checks = [r for r in rels if re.search(r"verify|check|validat|검증", r.name, re.I) and r not in tests]
    docs = [r for r in rels if r.suffix.lower() == ".md"]
    docker = [r for r in rels if r.name.lower().startswith(("dockerfile", "compose", "docker-compose"))]
    blob = "\n".join(read(root / r) for r in code)[:2_000_000].lower()
    has = {k: bool(re.search(v, blob)) for k, v in SIGNS.items()}
    # README가 요구한 문서 안에 결정·협업 기록을 넣는 것이 우선이다. 별도 파일만 가정하지 않는다.
    doc_blob = "\n".join(read(root / r) for r in docs)
    decisions = table_rows(doc_blob, "D")
    ai_rows = table_rows(doc_blob, "A")
    names = ", ".join(f"`{r.as_posix()}`" for r in code[:6]) or "(코드 파일 없음)"

    q = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    if has["알고리즘"] or "기준선" in doc_blob:
        q[1].append("핵심 계산에서 더 단순한 방법 대신 이 방식을 택한 근거(요구사항·담당자 답)와 대안과의 차이, 감수한 한계는?")
    else:
        q[1].append("왜 별도의 최적화·탐색 알고리즘 없이 규칙 방식으로 했나? 그 한계와 다음 개선안은?")
    for d in decisions[:2]:
        q[1].append(f"{d[0]}「{d[1][:40]}」을 고른 이유와 버린 대안, 그 선택의 약점은?")
    q[2].append(f"입력이 들어와 결과가 화면에 보이기까지 거치는 모듈({names})의 책임과 데이터 흐름은?")
    if has["저장"]:
        q[2].append("계획·상태 데이터는 어디에 저장되고 누가 바꾸며 누가 읽나?")
    security_scope = has['권한'] or bool(re.search(r'권한|운영자|관리자|로그인|비밀번호|개인정보|\b(?:role|admin|operator|login|session|auth)\b', doc_blob, re.I))
    if security_scope:
        q[2].append("사용자·운영자·담당자 중 실제 역할 하나의 입력이 어느 파일·함수에서 검증되고 어떤 상태를 바꾼 뒤 다음 역할의 화면에 보이나? 권한은 어디서 막나?")
        q[2].append('README·담당자 답의 어떤 보안 요구를 SSOT 권한표로 옮겼고, 그 표의 한 행을 실제 어느 파일·함수/API가 강제하며 어떤 권한 밖 요청으로 확인했나?')
        q[3].append('화면에서 숨긴 것과 실제 서버 권한 검사를 구분하면? 관리자 비밀번호·세션·다른 사용자 자료 접근 중 구현한 것, 가정한 것, 운영 전에 할 것은?')
    proof = ", ".join(f"`{r.as_posix()}`" for r in (tests + checks)[:4]) or "(검사 파일 없음)"
    q[3].append(f"실제로 구현·검증한 것과 가정으로 둔 것을 구분하면? 평가자가 확인할 경로는({proof})?")
    for r in (checks or tests)[:1]:
        q[3].append(f"`{r.as_posix()}`는 무엇을 보장하고 무엇은 보장하지 못하나?")
    q[4].append("계산·저장 중 오류가 나면 코드상 어떻게 되나? 이전 결과는 어떻게 되나?")
    q[4].append("다른 운영자가 동시에 수정하거나 같은 요청이 두 번 오면?" + ("" if has["동시성"] else " (지금 구현에 대책이 없다면 운영 전에 무엇을 넣나?)"))
    if docker:
        q[4].append(f"`{docker[0].as_posix()}`로 운영 환경에 올린다면 운영 전에 무엇을 더 해야 하나?")
    q[5].append("데이터가 10배가 되거나 조건이 바뀌면 어디가 먼저 문제가 되고, 결과를 믿기 전에 무엇을 추가로 검증하나?")
    q[5].append("선택한 방식의 트레이드오프를 숫자로 말하면? 같은 입력에 같은 결과가 나오나(동점 규칙)?")
    q[5].append("AI가 만든 결과(코드·숫자)를 무엇을 근거로 믿었나?")
    for a in ai_rows[:3]:
        q[6].append(f"{a[0]} 「{a[1][:40]}」 — AI 첫 제안에 무엇을 다시 생각하라고 했거나 어떤 주장을 냈나? 최종 결정과 바뀐 파일·검사 증거는?")
    if not ai_rows:
        q[6].append("AI가 생성한 코드를 반영할 때 엔지니어로서 가장 중요하게 검증한 항목은 무엇이며 그 이유는? 실제 사례 하나는?")
    q[6].append("AI 제안을 그대로 받지 않고 다시 생각하게 한 실제 사례는? 내 주장, 재비교한 대안, 최종 선택과 확인 증거를 순서대로 말하면?")

    false_premise = ("계산을 작업 큐로 비동기 처리한 이유는?" if not has["비동기"] else
                     "DB 트랜잭션 격리 수준을 어떻게 정했나?" if not has["동시성"] else
                     "마이크로서비스로 나눈 이유는?")
    titles = {1: "방법 선택", 2: "구조·데이터 흐름", 3: "구현 vs 가정", 4: "장애·운영", 5: "변화·판단", 6: "AI 협업 사례"}
    print(f"# 예상 서술형 질문 — {root.name} (코드 {len(code)} · 검사 {len(tests) + len(checks)} · 문서 {len(docs)})")
    print("답 틀: 결정·이유 → 약점 → 파급 → 다음 검증 (playbooks/answer-cards.md)\n")
    for k in range(1, 7):
        print(f"## {k}. {titles[k]}")
        for line in q[k]:
            print(f"- {line}")
        print()
    print(f"## 전제가 틀린 질문 연습\n- {false_premise} → 첫 문장: \"질문은 ○○를 전제했지만 실제 구현은 …\"\n")

    warn = [f"`{d.as_posix()}`" for d in docs if d.name.lower() not in EXPECTED_DOCS]
    nested = [r.as_posix() for r in rels if "worktree" in r.as_posix().lower()]
    if warn or nested or (root / "kit").exists():
        print("## 출제 범위 경고 (이 파일에서도 질문이 나온다 — 설명할 수 있나, 아니면 뺄 것인가)")
        if warn:
            print("- 따로 생긴 문서: " + ", ".join(warn[:10]))
        if nested:
            print("- worktree 흔적: " + ", ".join(nested[:5]))
        if (root / "kit").exists():
            print("- 과제 폴더 안에 `kit/`가 있다(제출물에 섞인다)")
    if not decisions or not ai_rows:
        print()
        print("## 재료 부족 (답할 사례가 없으면 질문이 일반론으로 나와 더 어렵다)")
    if not decisions:
        print("- README 요구 문서나 `DECISIONS.md`의 결정 표(D1…)가 비어 있다 → 1번 칸 재료가 없다")
    if not ai_rows:
        print("- README 요구 문서의 협업 기록이나 별도 요구된 `AI_COLLABORATION.md`의 판단 표(A1…)가 비어 있다 → 6번 칸 재료가 없다")
    shown, total = overclaims(root, sorted(docs, key=lambda r: (r.name.lower() not in EXPECTED_DOCS, r.as_posix())))
    if shown:
        print()
        print("## 과장 단정어 경고 (근거 있는 표현으로 바꾼다 — 단정은 그대로 질문이 된다)")
        print('- 예: "최적" → "실행 가능, 하한 대비 n%" · "항상" → "검사한 n개 경우에서" · "보장" → "테스트 E3로 확인한 범위에서"')
        for line in shown:
            print(f"- {line}")
        if total > len(shown):
            print(f"- … 외 {total - len(shown)}줄")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
