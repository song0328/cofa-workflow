"""키트 문서에서 필요한 절(## 제목)만 읽는다 — 파일 전체를 읽지 않아 토큰을 아낀다 (python3 표준 라이브러리만).

  python3 kit_read.py <파일>                 # 목차: 절 제목과 크기만
  python3 kit_read.py <파일> "제목 일부"      # 그 절 하나(다음 같은 수준 제목 전까지)
  python3 kit_read.py <파일> "제목1" "제목2"  # 여러 절

파일 경로는 키트 루트 기준(예: playbooks/stakeholder.md)이나 절대 경로. 제목은 일부만 맞아도 된다.
못 찾으면 목차를 보여 주고 종료 코드 1.
"""
import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
HEAD = re.compile(r"^(#{1,4})\s+(.*)$")


def sections(text):
    """[(수준, 제목, 시작 줄, 끝 줄)] — 코드 블록 안의 #은 제목으로 보지 않는다."""
    lines, heads, fence = text.splitlines(), [], False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else HEAD.match(line)
        if m:
            heads.append((len(m.group(1)), m.group(2).strip(), i))
    out = []
    for k, (lvl, title, start) in enumerate(heads):
        end = next((h[2] for h in heads[k + 1:] if h[0] <= lvl), len(lines))
        out.append((lvl, title, start, end))
    return lines, out


def resolve(name):
    p = Path(name)
    if not p.is_absolute():
        p = KIT / name
    if not p.exists():
        hits = sorted(KIT.rglob(Path(name).name))
        if hits:
            p = hits[0]
    return p


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    path = resolve(argv[0])
    if not path.exists():
        print(f"파일 없음: {argv[0]}")
        return 1
    lines, secs = sections(path.read_text(encoding="utf-8"))
    if len(argv) == 1:
        print(f"# {path.relative_to(KIT) if KIT in path.parents else path} — 절 {len(secs)}개")
        for lvl, title, s, e in secs:
            size = sum(len(l) for l in lines[s:e])
            print(f"{'  ' * (lvl - 1)}- {title}  ({size}자)")
        return 0
    code = 0
    for q in argv[1:]:
        hit = next((x for x in secs if q in x[1]), None) or next((x for x in secs if q.replace(" ", "") in x[1].replace(" ", "")), None)
        if not hit:
            print(f"[절 없음: {q}] 목차:")
            for lvl, title, _, _ in secs:
                print(f"{'  ' * (lvl - 1)}- {title}")
            code = 1
            continue
        print("\n".join(lines[hit[2]:hit[3]]).rstrip() + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
