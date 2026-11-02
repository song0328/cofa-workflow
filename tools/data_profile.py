"""제공 자료를 한 번에 진단해 '예외 후보'를 뽑는다 (python3 표준 라이브러리만).
업무 규칙을 정하지 않는다. 찾은 것은 담당자 질문의 근거로만 쓴다(playbooks/edge-hunt.md).

  python3 data_profile.py data/                  # 폴더 안 CSV·JSON 전부 + 파일 간 키 대조
  python3 data_profile.py a.csv b.csv            # 파일 지정
  python3 data_profile.py --compare 원본.csv 변경본.csv --key id,date   # 두 판의 차이(추가·삭제·바뀐 열)

출력: 파일별 행·열·인코딩, 열별 형식·빈칸·고유값·범위·특이값, 날짜 열의 요일 분포,
시작/종료 열 쌍의 역전·자정 넘김, 같은 이름의 키 열이 파일끼리 맞지 않는 값.
개인정보로 보이는 열(이름·전화·메일·주소 등)은 값을 찍지 않고 개수만 보인다.
종료 코드: 0 진단 완료 · 2 읽은 행이 0 (검사 대상이 없으면 통과가 아니다)
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ENCODINGS = ("utf-8-sig", "cp949", "euc-kr")
NA = {"", "na", "n/a", "null", "none", "nan", "-", "#n/a", "없음"}
PII = re.compile(r"name|이름|성명|phone|전화|휴대|mail|메일|주소|address|birth|생년|주민", re.I)
KEYLIKE = re.compile(r"(^|_)(id|code|no)$|번호$|코드$|아이디$", re.I)
START = re.compile(r"start|begin|from|시작|출근|출발", re.I)
END = re.compile(r"end|finish|to$|종료|퇴근|도착", re.I)
DT_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M")
WEEK = "월화수목금토일"


def read_rows(path):
    """CSV·JSON → (rows: list[dict], 인코딩, 구분자). 인코딩은 순서대로 시도한다."""
    raw = path.read_bytes()
    for enc in ENCODINGS:
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("인코딩을 판별하지 못함")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict):  # {"items": [...]} 모양이면 첫 목록을 쓴다
            data = next((v for v in data.values() if isinstance(v, list)), [data])
        return [r for r in data if isinstance(r, dict)], enc, "json"
    sample = text[:4096]
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=",\t;|").delimiter
    except csv.Error:
        delim = ","
    return list(csv.DictReader(text.splitlines(), delimiter=delim)), enc, delim


def parse_num(v):
    try:
        return float(v.replace(",", "")) if re.fullmatch(r"-?[\d,]*\.?\d+", v) else None
    except ValueError:
        return None


def parse_dt(v):
    for f in DT_FORMATS:
        try:
            return datetime.strptime(v, f)
        except ValueError:
            pass
    return None


def parse_time(v):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::\d{2})?", v)
    return (int(m.group(1)), int(m.group(2))) if m else None


def profile_column(name, values):
    vals = [("" if v is None else str(v)).strip() for v in values]
    present = [v for v in vals if v.lower() not in NA]
    out = {"col": name, "n": len(vals), "blank": len(vals) - len(present), "unique": len(set(present))}
    if not present:
        out["kind"] = "빈 열"
        return out
    nums = [parse_num(v) for v in present]
    dts = [parse_dt(v) for v in present]
    tms = [parse_time(v) for v in present]
    notes = []
    if all(x is not None for x in nums):
        out["kind"] = "숫자"
        out["range"] = f"{min(nums):g} ~ {max(nums):g}"
        if any(x < 0 for x in nums):
            notes.append(f"음수 {sum(x < 0 for x in nums)}건")
        if any(x == 0 for x in nums):
            notes.append(f"0 {sum(x == 0 for x in nums)}건")
    elif sum(d is not None for d in dts) >= 0.9 * len(present):
        ok = [d for d in dts if d]
        out["kind"] = "날짜"
        out["range"] = f"{min(ok):%Y-%m-%d} ~ {max(ok):%Y-%m-%d}"
        wk = Counter(d.weekday() for d in ok)
        out["weekday"] = " ".join(f"{WEEK[i]}{wk.get(i, 0)}" for i in range(7))
        if len(ok) < len(present):
            notes.append(f"날짜 형식 아님 {len(present) - len(ok)}건")
    elif sum(t is not None for t in tms) >= 0.9 * len(present):
        ok = [t for t in tms if t]
        out["kind"] = "시각"
        out["range"] = f"{min(ok)[0]:02d}:{min(ok)[1]:02d} ~ {max(ok)[0]:02d}:{max(ok)[1]:02d}"
        late = sum(h >= 24 for h, _ in ok)
        if late:
            notes.append(f"24시 이상 {late}건(다음날 표기?)")
    else:
        out["kind"] = "글자"
        lens = [len(v) for v in present]
        if max(lens) != min(lens):
            out["range"] = f"길이 {min(lens)}~{max(lens)}"
        if any(v != v.strip() or "  " in v for v in present):
            notes.append("앞뒤·이중 공백")
    if PII.search(name):
        out["top"] = "(개인정보로 보여 값 생략)"
    elif out["unique"] <= 12 or out["kind"] == "글자":
        c = Counter(present).most_common(5)
        out["top"] = ", ".join(f"{k}×{n}" for k, n in c)
    if KEYLIKE.search(name) and out["unique"] < len(present):
        notes.append(f"키 열에 같은 값 {len(present) - out['unique']}건(한 대상이 여러 행이면 정상, 목록 파일이면 중복)")
    if out["kind"] == "글자" and len({v.lower().replace(" ", "") for v in present}) < out["unique"]:
        notes.append("대소문자·공백만 다른 값 있음(같은 값인가?)")
    if out["blank"]:
        notes.append(f"빈칸 {out['blank']}건")
    out["notes"] = notes
    return out


def start_end_pairs(rows, cols):
    """시작/종료로 보이는 열 쌍: 종료 < 시작(자정 넘김 또는 오류) 건수"""
    found = []
    for s in [c for c in cols if START.search(c)]:
        stem = START.sub("", s)
        for e in [c for c in cols if END.search(c) and END.sub("", c) == stem]:
            inv = 0
            for r in rows:
                a, b = str(r.get(s) or "").strip(), str(r.get(e) or "").strip()
                pa, pb = parse_dt(a) or parse_time(a), parse_dt(b) or parse_time(b)
                if pa and pb and type(pa) is type(pb) and pb < pa:
                    inv += 1
            if inv:
                found.append(f"`{e}` < `{s}` {inv}건 (자정 넘김인가, 오류인가?)")
    return found


def profile_file(path):
    rows, enc, delim = read_rows(path)
    cols = list(rows[0].keys()) if rows else []
    lines = [f"## {path.name} — {len(rows)}행 · {len(cols)}열 · 인코딩 {enc} · 구분자 {delim!r}"]
    if not rows:
        return lines, rows, cols
    bad = sum(1 for r in rows if None in r or any(v is None for v in r.values()))
    if bad:
        lines.append(f"- ⚠ 열 개수가 맞지 않는 행 {bad}건")
    dup = len(rows) - len({tuple(r.items()) for r in rows})
    if dup:
        lines.append(f"- ⚠ 완전히 같은 행 {dup}건")
    lines.append("| 열 | 형식 | 빈칸 | 고유 | 범위 | 많이 나온 값 | 확인할 것 |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in cols:
        p = profile_column(c, [r.get(c) for r in rows])
        extra = p.get("weekday", "")
        lines.append(f"| {c} | {p.get('kind')} | {p['blank']} | {p['unique']} | {p.get('range', '')} {extra} | {p.get('top', '')} | {'; '.join(p.get('notes', []))} |")
    for s in start_end_pairs(rows, cols):
        lines.append(f"- ⚠ {s}")
    return lines, rows, cols


def cross_keys(tables):
    """같은 이름의 키 열이 여러 파일에 있으면 서로 없는 값을 센다."""
    out = []
    by_col = {}
    for name, (rows, cols) in tables.items():
        for c in cols:
            if KEYLIKE.search(c):
                by_col.setdefault(c, {})[name] = {str(r.get(c) or "").strip() for r in rows} - {""}
    for c, files in sorted(by_col.items()):
        names = sorted(files)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                only_a, only_b = files[a] - files[b], files[b] - files[a]
                if only_a or only_b:
                    ea, eb = (", ".join(sorted(x)[:3]) for x in (only_a, only_b))
                    show = not PII.search(c)
                    out.append(f"- `{c}`: {a}에만 {len(only_a)}개{f'(예: {ea})' if ea and show else ''} · {b}에만 {len(only_b)}개{f'(예: {eb})' if eb and show else ''}")
    return out


def compare(old, new, key):
    ro, _, _ = read_rows(Path(old))
    rn, _, _ = read_rows(Path(new))
    keys = [k.strip() for k in key.split(",")]
    kf = lambda r: "|".join(str(r.get(k, "")).strip() for k in keys)
    mo = {kf(r): r for r in ro}
    mn = {kf(r): r for r in rn}
    lines = [f"## 비교: {Path(old).name} → {Path(new).name} (키 `{key}`)"]
    if len(mo) < len(ro) or len(mn) < len(rn):
        lines.append("- ⚠ 키가 행마다 유일하지 않다 → `--key 열1,열2`처럼 여러 열로 지정")
    lines += [
             f"- 행 {len(ro)} → {len(rn)} · 추가 {len(mn.keys() - mo.keys())} · 삭제 {len(mo.keys() - mn.keys())}"]
    changed = Counter()
    for k in mo.keys() & mn.keys():
        for c in set(mo[k]) | set(mn[k]):
            if str(mo[k].get(c, "")).strip() != str(mn[k].get(c, "")).strip():
                changed[c] += 1
    cols_o, cols_n = set(ro[0]) if ro else set(), set(rn[0]) if rn else set()
    if cols_o != cols_n:
        lines.append(f"- 열 차이: 없어진 {sorted(cols_o - cols_n)} · 생긴 {sorted(cols_n - cols_o)}")
    lines += [f"- `{c}` 값이 바뀐 행 {n}건" for c, n in changed.most_common()]
    added = sorted(mn.keys() - mo.keys())[:5]
    if added:
        lines.append(f"- 추가된 키 예: {', '.join(added)}")
    return lines, len(ro) + len(rn)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--compare", nargs=2, metavar=("OLD", "NEW"))
    ap.add_argument("--key")
    a = ap.parse_args(argv)
    if a.compare:
        if not a.key:
            ap.error("--compare에는 --key가 필요하다")
        lines, n = compare(*a.compare, a.key)
        print("\n".join(lines))
        return 0 if n else 2
    files = []
    for p in map(Path, a.paths or ["."]):
        files += sorted(x for x in p.rglob("*") if x.suffix.lower() in (".csv", ".tsv", ".json")) if p.is_dir() else [p]
    tables, total = {}, 0
    for f in files:
        try:
            lines, rows, cols = profile_file(f)
        except (ValueError, json.JSONDecodeError, csv.Error) as e:
            print(f"## {f.name} — 읽기 실패: {e}")
            continue
        print("\n".join(lines) + "\n")
        tables[f.name] = (rows, cols)
        total += len(rows)
    xs = cross_keys(tables)
    if xs:
        print("## 파일 간 키 대조 (한쪽에만 있는 값 — 누락인가, 정상인가?)")
        print("\n".join(xs))
    if not total:
        print("읽은 행이 0 — 진단 대상 없음")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
