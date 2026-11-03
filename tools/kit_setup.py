"""Codex를 켜기 **전에** 셸에서 한 번 실행한다 (python3 표준 라이브러리만).
Codex는 지침(AGENTS.md)을 **세션을 시작할 때** 읽는다. 세션 도중 만든 AGENTS.md는 그 세션에 자동으로 들어가지 않는다.
그래서 키트 규칙을 미리 깔아 두고 나서 `codex`를 켠다.

  python3 /tmp/kit/setup.py                      # 과제 폴더 = 현재 폴더(시험: 홈 ~)
  python3 /tmp/kit/setup.py --dir <과제 폴더>

하는 일 (과제 원본은 지우거나 바꾸지 않는다)
1. 과제 폴더 AGENTS.md: 없으면 키트 틀로 만든다. 과제가 준 AGENTS.md가 있으면 원문을 그대로 두고 맨 위에 「0. 상시 규칙」만 덧붙인다. 이미 있으면 아무것도 안 한다.
2. AGENTS.override.md가 있으면 경고한다(AGENTS.md를 가린다 — 건드리지 않고 사람에게 알린다).
3. 키트 폴더에 notes/확인문제-노트.md, work/를 만든다(제출 폴더 밖).
4. 환경을 한 번에 본다: python3·node·git·docker, 쓸 수 있는 라이브러리, 디스크·메모리, 키트 커밋.
마지막 줄에 다음에 칠 것을 알려 준다.
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
MARK = "## 0. 상시 규칙"
LIBS = ["pandas", "numpy", "scipy", "networkx", "ortools", "pulp", "sklearn", "flask", "fastapi", "uvicorn", "pytest"]


def sh(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else "?"
    except (OSError, subprocess.SubprocessError):
        return "없음"


def rules_block(template):
    start = template.index(MARK)
    end = template.index("\n## 1.", start)
    return template[:template.index(MARK)].splitlines()[0] + "\n\n" + template[start:end].rstrip() + "\n"


def setup_agents(task, template):
    if KIT.as_posix() != "/tmp/kit":                     # 연습 노트북 등 키트가 다른 곳이면 실제 경로로 바꿔 넣는다
        template = template.replace("/tmp/kit", KIT.as_posix())
    target = task / "AGENTS.md"
    if target.exists():
        text = target.read_text(encoding="utf-8")
        if MARK in text:
            return "AGENTS.md: 상시 규칙이 이미 있음(그대로 둠)"
        target.write_text(rules_block(template) + "\n## 과제가 준 지침 (원문 그대로 · 지우지 않는다)\n\n" + text, encoding="utf-8")
        return "AGENTS.md: 과제가 준 지침을 보존하고 맨 위에 상시 규칙을 덧붙임"
    target.write_text(template, encoding="utf-8")
    return "AGENTS.md: 키트 틀로 새로 만듦"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=".", help="과제 폴더(기본: 현재 폴더)")
    a = ap.parse_args(argv)
    task = Path(a.dir).resolve()
    if KIT == task or KIT in task.parents:
        print(f"⚠ 과제 폴더({task})가 키트 안이다. 과제 폴더(시험: 홈 ~)에서 실행한다.")
        return 1
    if task in KIT.parents:
        print(f"⚠ 키트({KIT})가 과제 폴더 안에 있다 — 제출물에 섞인다. 키트는 /tmp/kit에 받는다(연습실이면 제출 전 삭제).")
    template = (KIT / "templates" / "AGENTS.md").read_text(encoding="utf-8")
    lines = [setup_agents(task, template)]
    if (task / "AGENTS.override.md").exists():
        lines.append("⚠ AGENTS.override.md가 있다: Codex는 이것을 AGENTS.md보다 먼저 쓴다. 지우지 말고 내용을 확인해 사람이 판단한다.")
    if (Path.home() / ".codex" / "AGENTS.md").exists():
        lines.append("참고: ~/.codex/AGENTS.md(전역 지침)가 있다 — 플랫폼 설정이므로 건드리지 않는다.")
    (KIT / "notes").mkdir(exist_ok=True)
    (KIT / "work").mkdir(exist_ok=True)
    note = KIT / "notes" / "확인문제-노트.md"
    if not note.exists():
        shutil.copy(KIT / "templates" / "answer-notes.md", note)
        lines.append(f"노트: {note} 만듦")
    libs = [m for m in LIBS if importlib.util.find_spec(m)]
    du = shutil.disk_usage(task)
    mem = ""
    try:
        mem = next(l for l in open("/proc/meminfo") if l.startswith("MemAvailable")).split()[1]
        mem = f" · 메모리 여유 {int(mem) // 1024}MB"
    except (OSError, StopIteration):
        pass
    lines += [
        f"환경: {sys.version.split()[0]} (python3) · node {sh(['node', '--version'])} · {sh(['git', '--version'])} · docker {'있음' if shutil.which('docker') else '없음'}",
        f"라이브러리: {', '.join(libs) or '표준 라이브러리만'}  ← 방법 수준 A/B/C 고를 때 근거(DECISIONS에)",
        f"디스크 여유 {du.free // 2**30}GB{mem} · 키트 커밋 {sh(['git', '-C', str(KIT), 'rev-parse', '--short', 'HEAD'])} (AI_COLLABORATION 「4」에 적는다)",
        f"다음: `codex` 실행 → \"{KIT.as_posix()}/KIT-INDEX.md 읽고 시작해.\"",
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
