#!/usr/bin/env python3
"""
종합소득세 계산기 — 소득세법 §55

공식:
  산출세액 = 과세표준 × 세율 - 누진공제
  지방소득세 = 산출세액 × 10% (별도, 지방세법)
  최종부담세액 = 산출세액 + 지방소득세 - 세액공제 - 기납부세액

모드: calculate | effective-rate

CLI:
  python3 calculator.py calculate --taxable-income 50000000
  python3 calculator.py effective-rate --taxable-income 50000000

주의:
  - 표준 라이브러리만 사용 (argparse, json, sys)
  - 모든 금액은 int (원 단위 절사)
  - JSON 출력: ensure_ascii=False, indent=2
  - 세액공제·기납부세액·분리과세는 미반영 (SKILL.md 한계 참고)
"""

import argparse
import json
import sys

# ─── 상수 (소득세법 §55, 2023년 귀속분부터 현행, 2026년 기준 동일) ───────────────
# 국세청 nts.go.kr 팩트체크 완료 (2026-04-14)
# 각 튜플: (상한 과세표준, 세율, 누진공제액)
TAX_BRACKETS = [
    (14_000_000,        0.06,          0),
    (50_000_000,        0.15,  1_260_000),
    (88_000_000,        0.24,  5_760_000),
    (150_000_000,       0.35, 15_440_000),
    (300_000_000,       0.38, 19_940_000),
    (500_000_000,       0.40, 25_940_000),
    (1_000_000_000,     0.42, 35_940_000),
    (float("inf"),      0.45, 65_940_000),
]

# 지방소득세 (지방세법 §92, 산출세액의 10%)
LOCAL_TAX_RATE = 0.10


# ─── 내부 유틸 ─────────────────────────────────────────────────────────────────

def _lookup_bracket(taxable_income: int) -> tuple[int | float, float, int]:
    """과세표준이 속한 구간을 반환 (상한, 세율, 누진공제)."""
    for upper, rate, deduction in TAX_BRACKETS:
        if taxable_income <= upper:
            return upper, rate, deduction
    # 이론상 도달 불가 (마지막 구간이 inf)
    return TAX_BRACKETS[-1]


def _bracket_desc(upper: int | float, rate: float, deduction: int) -> str:
    """사람이 읽기 좋은 구간 설명."""
    if upper == float("inf"):
        lo = TAX_BRACKETS[-2][0]
        return f"{lo:,}원 초과 구간 (세율 {int(rate*100)}%, 누진공제 {deduction:,}원)"
    # 하한 찾기
    idx = next(i for i, (u, _, _) in enumerate(TAX_BRACKETS) if u == upper)
    lo = 0 if idx == 0 else TAX_BRACKETS[idx - 1][0]
    return (
        f"{lo:,}원 초과 ~ {int(upper):,}원 이하 "
        f"(세율 {int(rate*100)}%, 누진공제 {deduction:,}원)"
    )


# ─── 핵심 계산 함수 ────────────────────────────────────────────────────────────

def calculate_tax(taxable_income: int) -> dict:
    """
    종합소득세 산출세액 계산 (소득세법 §55).

    Args:
        taxable_income: 과세표준 (원). 종합소득금액 - 종합소득공제.

    Returns:
        dict: 산출세액·지방소득세·실효세율·산식 포함.
    """
    if taxable_income < 0:
        return {"error": "과세표준은 0 이상이어야 합니다"}

    upper, rate, deduction = _lookup_bracket(taxable_income)
    national_tax = max(0, int(taxable_income * rate - deduction))
    local_tax = int(national_tax * LOCAL_TAX_RATE)
    total = national_tax + local_tax

    if taxable_income > 0:
        effective_rate_pct = round((national_tax / taxable_income) * 100, 2)
        total_effective_pct = round((total / taxable_income) * 100, 2)
    else:
        effective_rate_pct = 0.0
        total_effective_pct = 0.0

    return {
        "mode": "calculate",
        "taxable_income": taxable_income,
        "marginal_rate_pct": int(rate * 100),
        "progressive_deduction": deduction,
        "national_income_tax": national_tax,
        "local_income_tax": local_tax,
        "total_tax": total,
        "effective_rate_pct": effective_rate_pct,
        "total_effective_rate_pct": total_effective_pct,
        "take_home": taxable_income - total,
        "calculation": (
            f"{taxable_income:,} × {int(rate*100)}% - {deduction:,} "
            f"= {national_tax:,}원 (지방소득세 {local_tax:,}원 별도)"
        ),
        "bracket": _bracket_desc(upper, rate, deduction),
        "disclaimer": (
            "산출세액 기준 참고치. 세액공제·기납부세액·분리과세·감면은 미반영. "
            "최종 세액은 홈택스(hometax.go.kr) 또는 세무사 확인 필요."
        ),
    }


def effective_rate(taxable_income: int) -> dict:
    """
    평균세율(실효세율) 빠른 조회.

    한계세율 vs. 실효세율 비교용. 과세표준 기준 산출세액 / 과세표준.
    """
    if taxable_income <= 0:
        return {"error": "과세표준은 양수여야 합니다"}

    base = calculate_tax(taxable_income)
    return {
        "mode": "effective-rate",
        "taxable_income": taxable_income,
        "marginal_rate_pct": base["marginal_rate_pct"],
        "national_effective_rate_pct": base["effective_rate_pct"],
        "total_effective_rate_pct": base["total_effective_rate_pct"],
        "national_income_tax": base["national_income_tax"],
        "local_income_tax": base["local_income_tax"],
        "calculation": base["calculation"],
        "disclaimer": base["disclaimer"],
    }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="종합소득세 계산기 (소득세법 §55, 8단계 누진세율)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_calc = sub.add_parser(
        "calculate",
        help="과세표준 → 산출세액 + 지방소득세 + 실효세율",
    )
    p_calc.add_argument(
        "--taxable-income", type=int, required=True,
        help="과세표준 (원). 종합소득금액에서 종합소득공제를 뺀 금액.",
    )

    p_eff = sub.add_parser(
        "effective-rate",
        help="한계세율 vs. 실효세율 비교 (평균세율 조회)",
    )
    p_eff.add_argument(
        "--taxable-income", type=int, required=True,
        help="과세표준 (원)",
    )

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "calculate":
        result = calculate_tax(taxable_income=args.taxable_income)
    elif args.cmd == "effective-rate":
        result = effective_rate(taxable_income=args.taxable_income)
    else:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
