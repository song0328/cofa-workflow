"""연습 과제 「교육 세션 배정」 자료 생성기 (표준 라이브러리만 · seed 고정 · 실행할 때마다 같은 결과).

  python3 make_data.py        # 이 파일 옆 data/ 를 다시 만든다

자료에는 일부러 함정을 넣었다(내용은 FACILITATOR.md 끝 「채점 참고」). 응시자 역할은 이 파일을 읽지 않는다.
"""
import csv
import random
from pathlib import Path

SEED = 20261103
OUT = Path(__file__).resolve().parent / "data"


def write(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"{path.relative_to(OUT.parent).as_posix()}: {len(rows)} rows")


COURSES = [
    # course_id, title, hours, mandatory_roles
    ("C01", "안전보건 기초", 2, "ALL"),
    ("C02", "정보보안 기초", 2, "engineer;office;manager"),
    ("C03", "설비 안전 실습", 4, "technician"),
    ("C04", "데이터 리터러시", 3, ""),
    ("C05", "리더십 기초", 3, "manager"),
    ("C06", "화학물질 취급", 3, "technician"),
    ("C07", "생성형 AI 활용", 2, ""),
]

SESSIONS = [
    # session_id, course_id, date, start, end, room, capacity
    ("S01", "C01", "2026-11-16", "09:00", "11:00", "R101", "24"),
    ("S02", "C01", "2026-11-17", "13:00", "15:00", "R101", "24"),
    ("S03", "C01", "2026-11-18", "09:00", "11:00", "R101", "24"),
    ("S04", "C01", "2026-11-19", "15:00", "17:00", "R101", ""),      # 정원 빈칸
    ("S05", "C01", "2026-11-20", "09:00", "11:00", "R101", "24"),
    ("S06", "C02", "2026-11-16", "13:00", "15:00", "R201", "24"),
    ("S07", "C02", "2026-11-17", "09:00", "11:00", "R201", "24"),
    ("S08", "C02", "2026-11-19", "09:00", "11:00", "R201", "24"),
    ("S09", "C03", "2026-11-16", "13:00", "17:00", "LAB1", "16"),
    ("S10", "C03", "2026-11-18", "08:00", "12:00", "LAB1", "16"),
    ("S11", "C03", "2026-11-19", "13:00", "17:00", "LAB1", "16"),
    ("S12", "C06", "2026-11-17", "15:00", "18:00", "LAB1", "20"),    # S02 끝 = S12 시작
    ("S13", "C06", "2026-11-20", "13:00", "16:00", "LAB1", "20"),
    ("S14", "C06", "2026-11-19", "22:00", "01:00", "LAB1", "15"),    # 자정 넘김
    ("S15", "C05", "2026-11-18", "09:00", "12:00", "R301", "12"),
    ("S16", "C04", "2026-11-17", "09:00", "12:00", "R301", "20"),
    ("S17", "C04", "2026-11-20", "13:00", "16:00", "R301", "20"),
    ("S18", "C07", "2026-11-16", "15:00", "17:00", "R201", "24"),    # S06 끝 = S18 시작
    ("S19", "C07", "2026-11-18", "10:00", "12:00", "R201", "24"),
    ("S20", "C07", "2026-11-19", "13:00", "15:00", "R201", "24"),    # S20 끝 = S04 시작
]
# 11/18(수)은 오전 세션만 있다(오후가 비는 이유는 자료에 없다).

DEPTS = {"technician": ["생산1팀", "생산2팀", "설비팀"], "engineer": ["설비팀", "품질팀", "연구소"],
         "office": ["경영지원팀", "품질팀"], "manager": ["생산1팀", "생산2팀", "설비팀", "품질팀", "경영지원팀", "연구소"]}


def main():
    rng = random.Random(SEED)
    roles = ["technician"] * 44 + ["engineer"] * 30 + ["office"] * 30 + ["manager"] * 11 + [""] * 3
    rng.shuffle(roles)
    emps = []
    night_left = 14
    for i, role in enumerate(roles, start=1):
        eid = f"E{i:04d}"
        dept = rng.choice(DEPTS.get(role) or ["생산1팀", "경영지원팀"])
        shift = "DAY"
        if role == "technician" and night_left and rng.random() < 0.45:
            shift, night_left = "NIGHT", night_left - 1
        updated = f"2026-10-{rng.randint(1, 28):02d}"
        emps.append([eid, dept, role, shift, "ACTIVE", updated])
    # 상태 표기 변형과 휴직
    picks = rng.sample(range(len(emps)), 8)
    for idx in picks[:4]:
        emps[idx][4] = "LEAVE"
    for idx in picks[4:7]:
        emps[idx][4] = "active"
    emps[picks[7]][4] = "Active"
    # 같은 사람의 정정 행(나중 updated_at이 맞다) — 직무가 바뀌었다
    e34 = emps[33]
    fixed = list(e34)
    e34[2], e34[1], e34[5] = "office", "경영지원팀", "2026-09-30"
    fixed[2], fixed[1], fixed[3], fixed[5] = "technician", "생산2팀", "DAY", "2026-10-29"
    emps.insert(80, fixed)
    write(OUT / "employees.csv", ["emp_id", "dept", "job_role", "shift", "status", "updated_at"], emps)

    write(OUT / "courses.csv", ["course_id", "title", "hours", "mandatory_roles"], COURSES)
    write(OUT / "sessions.csv", ["session_id", "course_id", "date", "start_time", "end_time", "room", "capacity"], SESSIONS)

    prefs = []
    seen = set()
    for e in emps:
        if e[0] in seen:
            continue
        seen.add(e[0])
        if rng.random() < 0.7:
            first = rng.choice(["C04", "C07"])
            prefs.append([e[0], first, 1, f"2026-10-{rng.randint(20, 31):02d}"])
            if rng.random() < 0.5:
                prefs.append([e[0], "C07" if first == "C04" else "C04", 2, f"2026-10-{rng.randint(20, 31):02d}"])
    prefs.sort(key=lambda r: (r[3], r[0]))
    extra = [
        ["E0050", "C07", 1, "2026-10-21"], ["E0050", "C07", 2, "2026-10-30"],   # 같은 사람·과목 두 줄
        ["e0012", "C04", 1, "2026-10-25"],                                    # 대소문자만 다른 키
        ["E0999", "C07", 1, "2026-10-26"], ["E0131", "C04", 1, "2026-10-27"],  # 직원 목록에 없는 키
        ["E0007", "C01", 1, "2026-10-22"], ["E0091", "C03", 1, "2026-10-23"],  # 필수 과목에 선호
    ]
    prefs = prefs + extra
    write(OUT / "preferences.csv", ["emp_id", "course_id", "rank", "submitted_at"], prefs)

    # 다음 주 운영자가 올릴 변경본(오류 검증용)
    v2 = [list(s) for s in SESSIONS if s[0] != "S12"]                      # S12 취소
    for s in v2:
        if s[0] == "S07":
            s[6] = "18"                                                       # 정원 축소
    v2 += [
        ["S21", "C04", "2026-11-19", "16:00", "14:00", "R301", "20"],        # 종료 < 시작(오타)
        ["S22", "C09", "2026-11-20", "09:00", "11:00", "R201", "24"],        # 없는 과목
        ["S23", "C07", "2026-11-18", "14:00", "16:00", "R201", "24"],        # 11/18 오후
    ]
    write(OUT / "changed" / "sessions_v2.csv", ["session_id", "course_id", "date", "start_time", "end_time", "room", "capacity"], v2)


if __name__ == "__main__":
    main()
