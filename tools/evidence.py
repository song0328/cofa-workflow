"""검사 실행을 증거 번호(E1, E2…)로 남기고, 요구사항(R1…)과 이어 인계 전에 확인한다 (python3 표준 라이브러리만).
기록은 키트의 work/evidence.jsonl(시험: /tmp/kit/work — 제출 폴더 밖)에만 쓴다. 과제 폴더에는 아무것도 쓰지 않는다.

  python3 evidence.py check --name unit --root ~/task --track app,tests -- python3 -m unittest discover -s tests
  python3 evidence.py link R1 E3          # 요구사항 R1의 근거는 E3
  python3 evidence.py status              # 증거 표: PASS/FAIL/NOT_RUN, 이후 파일이 바뀌었으면 STALE
  python3 evidence.py handoff --required R1,R2,R3

check: 명령을 shell 없이 실행(기본 300초 제한)하고 종료 코드·출력 끝 20줄·추적 파일 지문(sha256)을 실행 전후로 남긴다.
  "Ran 0 tests"·"no tests ran"·"collected 0 items"·"0 passed"면 NOT_RUN(검사 대상이 없으면 통과가 아니다).
  실행 중 추적 파일이 바뀌면 「불안정」 표시(검사가 과제 파일을 고쳤다).
handoff: R마다 연결된 검사(같은 이름으로 다시 돌렸으면 그 최신 결과)가 PASS이고 STALE이 아니어야 통과.
종료 코드: check 0 PASS · 1 FAIL · 2 NOT_RUN / handoff 0 통과 · 1 부족 · 2 증거 없음
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__", "node_modules", ".pytest_cache", ".venv", "venv", ".mypy_cache"}
ZERO = re.compile(r"\bRan 0 tests?\b|no tests ran|collected 0 items|(?<![\d.])\b0 passed\b|^# tests 0\b", re.I | re.M)
FAILED = re.compile(r"\b[1-9]\d* (failed|errors?)\b|^FAILED\b|failures=[1-9]", re.I | re.M)


# ---- 저장 ----
def work_dir(arg):
    """기록 폴더 경로. 만들기는 실제로 쓸 때(append) 한다 — 과제 폴더 안이면 만들기 전에 거부한다."""
    return (Path(arg) if arg else KIT / "work").resolve()


def load(d):
    f = d / "evidence.jsonl"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # 깨진 줄은 건너뛴다(다른 탭이 쓰다 끊긴 줄)
    return out


def append(d, rec):
    d.mkdir(parents=True, exist_ok=True)
    with (d / "evidence.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def checks_of(records):
    return [r for r in records if r.get("type") == "check"]


# ---- 지문 ----
def tracked_files(root, patterns, exclude=None):
    """패턴(파일·폴더·glob, root 기준)에 걸린 파일 목록과 못 찾은 패턴."""
    files, missing = set(), []
    for pat in patterns:
        hits = list(root.glob(pat)) if any(ch in pat for ch in "*?[") else [root / pat]
        hits = [h for h in hits if h.exists()]
        if not hits:
            missing.append(pat)
        for h in hits:
            for f in ([h] if h.is_file() else h.rglob("*")):
                if not f.is_file() or f.suffix == ".pyc":
                    continue
                rel = f.relative_to(root)
                if any(part in SKIP for part in rel.parts):
                    continue
                if exclude is not None and f.resolve().is_relative_to(exclude):
                    continue
                files.add(rel.as_posix())
    return sorted(files), missing


def fingerprint(root, patterns, exclude=None):
    """추적 파일의 경로·내용으로 만든 sha256 앞 16자 + 파일 수."""
    files, missing = tracked_files(root, patterns, exclude)
    h = hashlib.sha256()
    for rel in files:
        h.update(rel.encode("utf-8") + b"\0")
        h.update(hashlib.sha256((root / rel).read_bytes()).digest())
    for pat in missing:
        h.update(b"missing:" + pat.encode("utf-8"))
    return {"sha": h.hexdigest()[:16], "files": len(files), "missing": missing}


def current_sha(rec, d):
    root = Path(rec["root"])
    if not root.is_dir():
        return None
    return fingerprint(root, rec["track"], d)["sha"]


# ---- 판정 ----
def judge(code, output):
    """(상태, 요약). 0개 실행은 종료 코드와 무관하게 NOT_RUN(실패 개수가 따로 있으면 FAIL)."""
    if ZERO.search(output) and not FAILED.search(output):
        return "NOT_RUN", "검사 0개 실행"
    status = "PASS" if code == 0 else "FAIL"
    for pat, fmt in ((r"(?:\d+ failed, )?\d+ passed(?:, \d+ failed)?", None), (r"Ran (\d+) tests?", "ran"), (r"^# pass (\d+)", "node")):
        m = re.search(pat, output, re.M)
        if not m:
            continue
        if fmt == "ran":
            fails = re.search(r"FAILED \(([^)]*)\)", output)
            skipped = re.search(r"skipped=(\d+)", output)
            text = f"{m.group(1)}개 중 실패 ({fails.group(1)})" if fails else f"{m.group(1)} passed"
            return status, text + (f", {skipped.group(1)} skipped" if skipped and not fails else "")
        if fmt == "node":
            fail = re.search(r"^# fail (\d+)", output, re.M)
            return status, f"{m.group(1)} passed" + (f", {fail.group(1)} failed" if fail and fail.group(1) != "0" else "")
        return status, m.group(0)
    last = [l.strip() for l in output.splitlines() if l.strip()]
    return status, (last[-1][:60] if last else "(출력 없음)")


def cmd_check(a, d):
    root = Path(a.root).resolve()
    if not root.is_dir():
        sys.exit(f"--root 폴더 없음: {root}")
    if d.is_relative_to(root):
        sys.exit(f"기록 폴더 {d}가 과제 폴더 안이다 — 제출물에 섞인다. --dir로 과제 밖을 준다.")
    if not a.cmd:
        sys.exit("실행할 명령이 없다: check --name 이름 -- 명령 ...")
    track = [p for t in (a.track or ["."]) for p in t.split(",") if p]
    before = fingerprint(root, track, d)
    started = datetime.now()
    try:
        proc = subprocess.run(a.cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=a.timeout, text=True, encoding="utf-8", errors="replace")
        code, output = proc.returncode, proc.stdout or ""
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        code, output = 124, out + f"\n[시간 초과 {a.timeout}초]"
    except OSError as e:
        code, output = 127, f"[실행 못 함] {e}"
    after = fingerprint(root, track, d)
    status, summary = judge(code, output)
    if code in (124, 127):
        status = "FAIL"
    eid = f"E{len(checks_of(load(d))) + 1}"  # 쓰기 직전에 다시 세어 번호를 정한다
    rec = {"type": "check", "id": eid, "name": a.name, "time": started.strftime("%Y-%m-%d %H:%M:%S"),
           "seconds": round((datetime.now() - started).total_seconds(), 1), "cmd": a.cmd, "root": str(root),
           "track": track, "exit": code, "status": status, "summary": summary,
           "unstable": before["sha"] != after["sha"], "fp_before": before, "fp_after": after,
           "tail": output.splitlines()[-20:]}
    append(d, rec)
    note = " · 불안정: 실행 중 추적 파일이 바뀜" if rec["unstable"] else ""
    if after["missing"]:
        note += f" · 추적 패턴 없음: {', '.join(after['missing'])}"
    print(f"{eid} {status} {a.name} (exit {code}) — {summary}{note}")
    return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[status]


def cmd_link(a, d):
    req, eid = a.req.upper(), a.ev.upper()
    if not re.fullmatch(r"R\d+", req) or not re.fullmatch(r"E\d+", eid):
        sys.exit("모양: link R1 E3")
    if eid not in {c["id"] for c in checks_of(load(d))}:
        sys.exit(f"{eid} 없음 (status로 번호 확인)")
    append(d, {"type": "link", "req": req, "ev": eid, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    print(f"{req} ← {eid}")
    return 0


def links_of(records):
    """{R: [E...]} 연결 순서대로(중복 제거)."""
    out = {}
    for r in records:
        if r.get("type") == "link" and r["ev"] not in out.setdefault(r["req"], []):
            out[r["req"]].append(r["ev"])
    return out


def cmd_status(a, d):
    records = load(d)
    checks = checks_of(records)
    if not checks:
        print("증거 없음 — check로 먼저 실행한다")
        return 2
    linked = {}
    for req, evs in links_of(records).items():
        for e in evs:
            linked.setdefault(e, []).append(req)
    print("| E | 이름 | 상태 | exit | 시각 | 신선도 | 요약 | R |\n|---|---|---|---|---|---|---|---|")
    for c in checks:
        sha = current_sha(c, d)
        fresh = "확인 불가" if sha is None else ("최신" if sha == c["fp_after"]["sha"] else "STALE")
        if c.get("unstable"):
            fresh += "·불안정"
        print(f"| {c['id']} | {c['name']} | {c['status']} | {c['exit']} | {c['time'][11:16]} | {fresh} | "
              f"{c['summary'][:40]} | {', '.join(linked.get(c['id'], [])) or '-'} |")
    return 0


def cmd_handoff(a, d):
    records = load(d)
    checks = checks_of(records)
    if not checks:
        print("증거 없음 — 인계 불가. check로 검사부터 남긴다")
        return 2
    by_id = {c["id"]: c for c in checks}
    links = links_of(records)
    required = [r.strip().upper() for r in a.required.split(",") if r.strip()]
    ok, lacking = [], []
    for req in required:
        if not links.get(req):
            lacking.append(f"{req}: 연결된 증거 없음 (link {req} E번호)")
            continue
        problems, shown = [], []
        for name in dict.fromkeys(by_id[e]["name"] for e in links[req]):
            latest = [c for c in checks if c["name"] == name][-1]  # 같은 이름의 최신 실행이 대신한다
            shown.append(latest["id"])
            if latest["status"] != "PASS":
                problems.append(f"{latest['id']} {name} {latest['status']}")
            elif current_sha(latest, d) != latest["fp_after"]["sha"]:
                problems.append(f"{latest['id']} {name} STALE(그 뒤 파일이 바뀜 — 다시 check)")
        if problems:
            lacking.append(f"{req}: " + "; ".join(problems))
        else:
            ok.append(f"{req}: {', '.join(shown)} PASS")
    for line in ok:
        print(f"통과  {line}")
    for line in lacking:
        print(f"부족  {line}")
    print("인계 가능" if not lacking else f"인계 불가 — 부족 {len(lacking)}건")
    return 0 if not lacking else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = []
    if "--" in argv:  # `--` 뒤는 실행할 명령 그대로
        i = argv.index("--")
        argv, cmd = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", help="기록 폴더(기본: 키트/work)")
    sub = ap.add_subparsers(dest="sub", required=True)
    c = sub.add_parser("check")
    c.add_argument("--name", required=True)
    c.add_argument("--root", default=".", help="과제 폴더(명령도 여기서 실행)")
    c.add_argument("--track", action="append", help="지문을 뜰 경로·glob(root 기준, 쉼표 가능). 기본 .")
    c.add_argument("--timeout", type=float, default=300)
    lk = sub.add_parser("link")
    lk.add_argument("req")
    lk.add_argument("ev")
    sub.add_parser("status")
    h = sub.add_parser("handoff")
    h.add_argument("--required", required=True, help="R1,R2,...")
    a = ap.parse_args(argv)
    a.cmd = cmd
    d = work_dir(a.dir)
    return {"check": cmd_check, "link": cmd_link, "status": cmd_status, "handoff": cmd_handoff}[a.sub](a, d)


if __name__ == "__main__":
    sys.exit(main())
