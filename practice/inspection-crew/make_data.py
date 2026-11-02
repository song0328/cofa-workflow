"""연습 과제 「설비 점검 배정」 자료 생성기 (표준 라이브러리만 · seed 고정 · 실행할 때마다 같은 결과).

  python3 make_data.py        # 이 파일 옆 data/ 를 다시 만든다

자료에는 일부러 함정을 넣었다(내용은 FACILITATOR.md 끝 「채점 참고」). 응시자 역할은 이 파일을 읽지 않는다.
"""
import csv
import random
from pathlib import Path

SEED = 20261124
OUT = Path(__file__).resolve().parent / "data"
DAYS = ["2026-11-23", "2026-11-24", "2026-11-25"]
CERT_OF = {"PRESS": "PRESS", "PANEL": "ELEC", "ROBOT": "ELEC", "BOILER": "BOILER", "CONVEYOR": "MECH", "PUMP": "MECH"}


def write(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"{path.relative_to(OUT.parent).as_posix()}: {len(rows)} rows")


def main():
    rng = random.Random(SEED)

    # 기사: 주간 08:00-17:00 18명, 야간 22:00-06:00 8명
    techs = []
    day_certs = (["ELEC"] * 5 + ["MECH"] * 4 + ["ELEC;MECH"] * 3 + ["BOILER"] * 2 + ["MECH;BOILER"] * 1)
    rng.shuffle(day_certs)
    press_day = {"T003": "PRESS", "T008": "PRESS;MECH", "T012": "PRESS", "T015": "press;ELEC"}  # 소문자 1명
    it = iter(day_certs)
    for i in range(1, 19):
        tid = f"T{i:03d}"
        certs = press_day.get(tid) or next(it)
        techs.append([tid, rng.choice(["A조", "B조"]), certs, "08:00", "17:00", rng.choice(["S1", "S2"]), "ON"])
    night_certs = ["PRESS", "ELEC", "ELEC;MECH", "MECH", "BOILER", "ELEC", "MECH", ""]   # T026 자격 빈칸(신입)
    for i, c in zip(range(19, 27), night_certs):
        techs.append([f"T{i:03d}", "C조", c, "22:00", "06:00", rng.choice(["S1", "S2"]), "ON"])
    techs[6][6] = "on"                       # 표기 변형
    techs[13][6] = "On"
    techs[22][6] = "LEAVE"                   # 장기 휴직(T023)
    techs.insert(17, list(techs[16]))        # T017 완전 중복 행
    write(OUT / "technicians.csv", ["tech_id", "team", "certs", "shift_start", "shift_end", "home_site", "status"], techs)

    # 설비
    types = ["PRESS"] * 6 + ["PANEL"] * 8 + ["ROBOT"] * 6 + ["BOILER"] * 4 + ["CONVEYOR"] * 8 + ["PUMP"] * 4
    equips = []
    for i, t in enumerate(types, start=1):
        site = "S1" if t == "PRESS" else rng.choice(["S1", "S2"])
        equips.append([f"EQ-{i:03d}", f"L{(i - 1) % 6 + 1}", site, t])
    write(OUT / "equipment.csv", ["equipment_id", "line", "site", "type"], equips)
    eq_type = {e[0]: e[3] for e in equips}
    press_eq = [e[0] for e in equips if e[3] == "PRESS"]
    other_eq = [e[0] for e in equips if e[3] != "PRESS"]

    # 점검 작업
    tasks = []
    n = 0

    def add(eq, cert, dur, pri, due):
        nonlocal n
        n += 1
        tasks.append([f"W{n:04d}", eq, cert, dur, pri, due])

    counts = {"2026-11-23": 34, "2026-11-24": 40, "2026-11-25": 34}
    for day in DAYS:
        if day == "2026-11-24":
            for k in range(10):                                   # 법정 프레스 점검 10건(같은 S1)
                add(press_eq[k % len(press_eq)], "PRESS", 120, "P1", f"{day} 20:00")
        for _ in range(counts[day]):
            eq = rng.choice(other_eq)
            cert = CERT_OF[eq_type[eq]]
            if eq_type[eq] == "CONVEYOR" and rng.random() < 0.4:
                cert = ""                                         # 자격 무관 일반 점검
            pri = rng.choices(["P1", "P2", "P3"], [2, 5, 4])[0]
            hh = rng.choice(["12:00", "15:00", "17:00", "17:00", "18:00"])
            add(eq, cert, rng.choice([30, 45, 60, 60, 90]), pri, f"{day} {hh}")
        if day != "2026-11-25":
            nxt = DAYS[DAYS.index(day) + 1]
            for _ in range(4):                                    # 야간조가 끝나는 06:00 마감
                eq = rng.choice(other_eq)
                add(eq, CERT_OF[eq_type[eq]], rng.choice([60, 90]), rng.choice(["P1", "P2"]), f"{nxt} 06:00")
    add(press_eq[0], "PRESS", 90, "P2", "2026-11-25 17:00")
    add(press_eq[1], "PRESS", 60, "P3", "2026-11-23 17:00")

    # 함정
    for idx in (5, 30, 77, 101):
        tasks[idx][3] = ""                                        # 작업 시간 빈칸
    for idx in (9, 50, 96):
        tasks[idx][4] = "p1"                                      # 우선순위 소문자
    tasks[20][1] = "EQ-041"                                       # 설비 목록에 없음
    tasks[60][1] = "eq-005"                                       # 대소문자만 다름
    tasks[88][1] = "EQ-05"                                        # 자릿수 다름
    tasks.insert(40, list(tasks[39]))                             # 완전 중복
    dup = list(tasks[76]); dup[3] = 90 if dup[3] != 90 else 45    # 같은 id, 시간만 다름
    tasks.insert(78, dup)
    write(OUT / "tasks.csv", ["task_id", "equipment_id", "cert_required", "duration_min", "priority", "due_at"], tasks)

    leave = [
        ["T005", "2026-11-23", "FULL"],
        ["T010", "2026-11-24", "AM"],
        ["T019", "2026-11-25", "PM"],
        ["T002", "2026-11-25", "full"],
        ["T031", "2026-11-24", "FULL"],       # 기사 목록에 없음
        ["T021", "2026-11-23", "FULL"],       # 야간 기사 — 어느 밤 근무가 휴가인가
    ]
    write(OUT / "leave.csv", ["tech_id", "date", "type"], leave)

    # 관리자가 내일 올릴 변경본(오류 검증용)
    v2 = [list(t) for t in tasks if t[0] != "W0030"]               # 취소 1건
    seen = set()
    v2 = [t for t in v2 if not (t[0] in seen or seen.add(t[0]))]   # 원본 중복은 정리된 판
    for t in v2:
        if t[0] == "W0012":
            t[4] = "P1"                                            # 우선순위 상향
    v2 += [
        ["W0200", "EQ-010", "ELEC", -30, "P2", "2026-11-24 15:00"],          # 음수 시간
        ["W0201", "EQ-020", "WELD", 60, "P2", "2026-11-24 15:00"],           # 없는 자격
        ["W0202", "EQ-030", "MECH", 45, "P3", "2026/11/24 10:00"],           # 날짜 형식 다름
        ["W0050", "EQ-012", "ELEC", 60, "P2", "2026-11-25 12:00"],           # 기존 id 재사용
    ]
    write(OUT / "changed" / "tasks_v2.csv", ["task_id", "equipment_id", "cert_required", "duration_min", "priority", "due_at"], v2)


if __name__ == "__main__":
    main()
