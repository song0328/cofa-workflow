"""unittest 표 기반 테스트 틀 — 실행: python3 -m unittest python_test.py -v
기대값은 README·담당자 답에서 정한다(구현 코드를 정답으로 쓰지 않는다). 각 줄에 출처를 적는다.
"""
import unittest
from decimal import Decimal, ROUND_HALF_UP


def vat(amount_won):
    """예시 대상: 과제 함수로 바꾼다. 부가세 10%, 원 단위 반올림(가정)."""
    return int((Decimal(amount_won) * Decimal("0.1")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


CASES = [
    # (이름, 입력, 기대, 출처)
    ("정상", 10000, 1000, "README: 부가세 10%"),
    ("경계: 반올림 .5", 15, 2, "담당자 답: 반올림(사사오입)"),
    ("경계: 0원", 0, 0, "README"),
]


class TableTest(unittest.TestCase):
    def test_cases(self):
        for name, given, expected, source in CASES:
            with self.subTest(f"{name} ({source})"):
                self.assertEqual(vat(given), expected)


if __name__ == "__main__":
    unittest.main()
