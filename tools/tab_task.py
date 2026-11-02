"""여러 Codex 탭에 일을 나눠 줄 때 쓰는 작업 카드·게시판 (python3 표준 라이브러리만).
메인 탭이 카드를 만들면, 사람은 새 터미널 탭에서 `codex`를 켜고 **짧은 한 줄만** 친다(붙여넣기 불필요).
작업 카드·결과는 키트의 work/ 폴더(시험: /tmp/kit/work — 제출 폴더 밖)에 둔다. 규칙: playbooks/parallel.md

  python3 tab_task.py new T2 --role 탐구 --goal "정원 제약 배정 방법 2가지 비교" --read README.md,data/ --done "비교표와 추천"
  python3 tab_task.py new T3 --role 작업 --goal "화면 지도 표시" --read DECISIONS.md --own web/map.js,web/index.html --done "ui_sim으로 표 읽힘"
  python3 tab_task.py status          # 게시판: 누가 무엇을, 결과가 왔나
  python3 tab_task.py done T2         # 메인이 결과를 반영한 뒤 닫기

역할: 탐구(읽기 전용 · 아이디어·대안·반론·예외 사냥) / 작업(담당 파일만 수정) / 검증(읽기 + 검사 실행, 담당 테스트 파일만 · 판정 형식 포함)
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
RULES = {
    "탐구": "읽기 전용. 과제 파일을 수정·생성·커밋하지 않는다. 결과 파일 하나만 쓴다.",
    "작업": "아래 담당 파일만 만들거나 고친다. 다른 파일·AGENTS.md·DECISIONS.md·노트는 고치지 않는다. 커밋하지 않는다(메인이 한다).",
    "검증": "코드를 고치지 않는다(최소 수정은 제안만). 담당 테스트 파일만 쓰고 검사를 실행한다. 생성 코드의 함수를 재사용하지 말고 규칙에서 직접 기대값을 만든다. 커밋하지 않는다.",
}
# 검증 탭 전용: 읽는 순서·지적 형식·판정. 구현 요약을 먼저 읽으면 그 틀로 보게 되므로 요구사항이 먼저다.
VERIFY = """[검증 순서] ① 원래 요구사항(과제 README·담당자 답)과 확정 결정(DECISIONS.md)을 먼저 읽는다 ② 그다음 구현 요약·코드를 본다.
[꼭 볼 것] git diff로 지워지거나 약해진 assert, 건너뛴 테스트(skip·only·xfail·주석 처리), 지금 코드가 아닌 예전 서버 프로세스(포트를 잡은 옛 인스턴스)가 낸 결과.
[지적 한 건] R번호 / 파일:줄 / 기대 vs 실제 / 재현 명령 / 영향 / 최소 수정. 「꼭 고칠 것」과 「선택」을 나눠 적는다.
[판정] 보고 첫 줄에 승인 / 수정 필요 / 판단 불가(못 본 것) 중 하나. 「지적 없음」도 정상 결과다 — 지적을 지어내지 않는다.
"""
REPORT = {
    "검증": "판정 1줄 → 꼭 고칠 것 → 선택 → 실행한 명령과 결과 → 확인 못 한 것",
}


def work_dir(arg):
    d = Path(arg) if arg else KIT / "work"
    d.mkdir(parents=True, exist_ok=True)
    return d


def board_rows(d):
    b = d / "BOARD.md"
    if not b.exists():
        return []
    return [l for l in b.read_text(encoding="utf-8").splitlines() if re.match(r"\| T\w+ \|", l)]


def cmd_new(a):
    d = work_dir(a.dir)
    tid = a.id.upper()
    if not re.fullmatch(r"T\d+", tid):
        sys.exit("id는 T2, T3 같은 모양")
    card, result = d / f"{tid}.md", d / f"{tid}-result.md"
    if card.exists() and not a.force:
        sys.exit(f"{card} 이미 있음 (--force로 덮기)")
    own = [x for x in (a.own or "").split(",") if x]
    if a.role == "작업" and not own:
        sys.exit("작업 역할은 --own(담당 파일)이 필요하다")
    for row in board_rows(d):
        cells = [c.strip() for c in row.strip("|").split("|")]
        if cells[-1] != "끝" and own and set(own) & set(cells[2].split(", ")):
            sys.exit(f"담당 파일이 진행 중인 {cells[0]}와 겹친다: {cells[2]}")
    text = f"""# {tid} 작업 카드 ({a.role}) — {datetime.now():%H:%M}
너는 보조 탭이다. 과제 AGENTS.md의 「── 다음 ──」 칸·진행 줄·확인문제 노트 갱신은 하지 않는다(메인 탭 몫). 답은 한국어.

[목표] {a.goal}
[읽을 것] {a.read or "(과제 README와 필요한 파일만)"}
[담당 파일] {", ".join(own) or "(없음 — 읽기 전용)"}
[규칙] {RULES[a.role]} 업무 기준이 없으면 추측하지 말고 결과에 「담당자 질문 후보」로 적는다.
{VERIFY if a.role == "검증" else ""}[끝] {a.done}
[보고] `{result}`에 20줄 이내: {REPORT.get(a.role, "결론 3줄 → 근거(파일:줄·명령 출력) → 바꾼 파일 → 확인 못 한 것 → 메인이 정할 것")}. 그 파일을 쓰면 멈춘다.
"""
    card.write_text(text, encoding="utf-8")
    b = d / "BOARD.md"
    if not b.exists():
        b.write_text("# 게시판 (메인 탭만 상태를 바꾼다)\n| id | 역할 | 담당 파일 | 목표 | 상태 |\n|---|---|---|---|---|\n", encoding="utf-8")
    with b.open("a", encoding="utf-8") as f:
        f.write(f"| {tid} | {a.role} | {', '.join(own) or '-'} | {a.goal[:40]} | 진행 |\n")
    print(f"카드: {card}\n새 터미널 탭에서 `codex` 실행 후 이 한 줄만 친다:\n  {card} 읽고 그대로 해.")
    return 0


def cmd_status(a):
    d = work_dir(a.dir)
    rows = board_rows(d)
    if not rows:
        print("게시판 비어 있음")
        return 0
    print("| id | 역할 | 담당 파일 | 목표 | 상태 | 결과 |\n|---|---|---|---|---|---|")
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        res = d / f"{cells[0]}-result.md"
        mark = f"있음({sum(1 for _ in res.open(encoding='utf-8'))}줄)" if res.exists() else "아직"
        print(f"| {' | '.join(cells)} | {mark} |")
    return 0


def cmd_done(a):
    d = work_dir(a.dir)
    b = d / "BOARD.md"
    tid = a.id.upper()
    lines = b.read_text(encoding="utf-8").splitlines() if b.exists() else []
    hit = False
    for i, l in enumerate(lines):
        if l.startswith(f"| {tid} |"):
            lines[i] = re.sub(r"\| [^|]+ \|$", "| 끝 |", l)
            hit = True
    if not hit:
        sys.exit(f"{tid} 없음")
    b.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{tid} 끝으로 표시")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", help="작업 폴더(기본: 키트/work)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("id")
    n.add_argument("--role", choices=list(RULES), required=True)
    n.add_argument("--goal", required=True)
    n.add_argument("--read", default="")
    n.add_argument("--own", default="")
    n.add_argument("--done", required=True)
    n.add_argument("--force", action="store_true")
    sub.add_parser("status")
    dn = sub.add_parser("done")
    dn.add_argument("id")
    a = ap.parse_args(argv)
    return {"new": cmd_new, "status": cmd_status, "done": cmd_done}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
