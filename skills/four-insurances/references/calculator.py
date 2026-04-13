#!/usr/bin/env python3
"""
4대보험료 계산기 (2026년 기준 요율)

출처: 국민건강보험공단·근로복지공단·국민연금공단 2026년 고시
  - 국민연금: 총 9% (사업주 4.5% + 근로자 4.5%)
  - 건강보험: 총 7.09% (사업주 3.545% + 근로자 3.545%)
  - 장기요양: 건강보험료 × 12.95% (50:50)
  - 고용(실업급여): 총 1.8% (사업주 0.9% + 근로자 0.9%)
  - 고용(고용안정·직능): 사업주 100% (규모별 0.25%~0.85%)
  - 산재보험: 사업주 100% (업종별 요율)

모드: calculate (항목별 산정) | compare-with-net (세전→실수령 추정)

CLI: python3 calculator.py calculate --help
     python3 calculator.py compare-with-net --help

⚠️ 2026.7 이후 국민연금 기준소득월액 상·하한 변경 시 RATES 수정 필요.
"""

import argparse
import json
import sys

# ─────────────────────────────────────────────────────────────
# 2026년 요율 및 상·하한 (출처: 각 공단 고시)
# ─────────────────────────────────────────────────────────────
RATES = {
    # 국민연금
    "nps_total": 0.09,          # 9%
    "nps_employee": 0.045,      # 4.5%
    "nps_employer": 0.045,      # 4.5%
    "nps_wage_ceiling": 6_170_000,   # 기준소득월액 상한 (2025.7~2026.6)
    "nps_wage_floor": 390_000,       # 기준소득월액 하한

    # 건강보험
    "health_total": 0.0709,     # 7.09%
    "health_employee": 0.03545, # 3.545%
    "health_employer": 0.03545, # 3.545%

    # 장기요양 (건강보험료 × 12.95%, 50:50 분담)
    "ltc_rate": 0.1295,         # 장기요양 = 건강보험료 × 12.95%

    # 고용보험 실업급여
    "ei_ui_total": 0.018,       # 1.8%
    "ei_ui_employee": 0.009,    # 0.9%
    "ei_ui_employer": 0.009,    # 0.9%

    # 고용안정·직업능력개발사업 (사업주 100%, 규모별)
    "ei_stability": {
        "under_150":           0.0025,   # 150인 미만
        "over_150_priority":   0.0045,   # 150인 이상 + 우선지원대상기업
        "over_150":            0.0065,   # 150인 이상~1,000인 미만
        "over_1000":           0.0085,   # 1,000인 이상 또는 국가·지자체
    },

    # 산재보험: 사업주 100%, 업종별 고시 → 인자로 수령
    # 평균 약 1.43% (2026 전 업종 평균 기준)
}

COMPANY_SIZE_LABELS = {
    "under_150":           "150인 미만",
    "over_150_priority":   "150인 이상(우선지원대상기업)",
    "over_150":            "150인 이상~1,000인 미만",
    "over_1000":           "1,000인 이상(또는 국가·지자체)",
}


def _nps_base(monthly_wage: int) -> int:
    """국민연금 기준소득월액 (상·하한 적용, 원 단위 절사)."""
    return int(min(max(monthly_wage, RATES["nps_wage_floor"]), RATES["nps_wage_ceiling"]))


def calculate_insurance(
    monthly_wage: int,
    company_size: str = "under_150",
    industry_rate: float = 0.0143,
) -> dict:
    """
    월 보수 기준 4대보험료 항목별 산정.

    Returns:
        dict — 항목별 {employee, employer, total} + 총합
    """
    if company_size not in RATES["ei_stability"]:
        return {"error": f"company_size 값 오류: {company_size}. 허용값: {list(RATES['ei_stability'].keys())}"}
    if monthly_wage <= 0:
        return {"error": "monthly_wage는 양수여야 합니다."}

    wage = monthly_wage
    nps_base = _nps_base(wage)

    # ── 국민연금 ──────────────────────────────────────────────
    nps_employee = int(nps_base * RATES["nps_employee"])
    nps_employer = int(nps_base * RATES["nps_employer"])

    # ── 건강보험 ──────────────────────────────────────────────
    health_employee = int(wage * RATES["health_employee"])
    health_employer = int(wage * RATES["health_employer"])

    # ── 장기요양보험 (건강보험료 × 12.95%, 50:50) ─────────────
    health_premium_total = health_employee + health_employer
    ltc_total = int(health_premium_total * RATES["ltc_rate"])
    ltc_employee = int(ltc_total / 2)
    ltc_employer = ltc_total - ltc_employee   # 홀수 원 처리: 사업주에 나머지

    # ── 고용보험 실업급여 ────────────────────────────────────
    ei_ui_employee = int(wage * RATES["ei_ui_employee"])
    ei_ui_employer = int(wage * RATES["ei_ui_employer"])

    # ── 고용안정·직능 (사업주 100%) ─────────────────────────
    ei_stab_rate = RATES["ei_stability"][company_size]
    ei_stab_employer = int(wage * ei_stab_rate)

    # ── 산재보험 (사업주 100%) ───────────────────────────────
    wc_employer = int(wage * industry_rate)

    # ── 총합 ─────────────────────────────────────────────────
    employee_total = nps_employee + health_employee + ltc_employee + ei_ui_employee
    employer_total = (
        nps_employer + health_employer + ltc_employer
        + ei_ui_employer + ei_stab_employer + wc_employer
    )
    grand_total = employee_total + employer_total

    return {
        "mode": "calculate",
        "monthly_wage": wage,
        "company_size": COMPANY_SIZE_LABELS[company_size],
        "industry_rate_pct": round(industry_rate * 100, 4),
        "items": {
            "national_pension": {
                "label": "국민연금",
                "nps_base_wage": nps_base,
                "employee": nps_employee,
                "employer": nps_employer,
                "total": nps_employee + nps_employer,
            },
            "health_insurance": {
                "label": "건강보험",
                "employee": health_employee,
                "employer": health_employer,
                "total": health_employee + health_employer,
            },
            "long_term_care": {
                "label": "장기요양보험",
                "basis": f"건강보험료 합계 {health_premium_total:,}원 × {RATES['ltc_rate']*100:.2f}%",
                "employee": ltc_employee,
                "employer": ltc_employer,
                "total": ltc_total,
            },
            "employment_insurance_ui": {
                "label": "고용보험(실업급여)",
                "employee": ei_ui_employee,
                "employer": ei_ui_employer,
                "total": ei_ui_employee + ei_ui_employer,
            },
            "employment_insurance_stability": {
                "label": f"고용보험(고용안정·직능) — {COMPANY_SIZE_LABELS[company_size]}",
                "rate_pct": round(ei_stab_rate * 100, 2),
                "employee": 0,
                "employer": ei_stab_employer,
                "total": ei_stab_employer,
            },
            "workers_compensation": {
                "label": "산재보험",
                "rate_pct": round(industry_rate * 100, 4),
                "employee": 0,
                "employer": wc_employer,
                "total": wc_employer,
            },
        },
        "summary": {
            "employee_total": employee_total,
            "employer_total": employer_total,
            "grand_total": grand_total,
        },
        "disclaimer": (
            "고용형태(일용직·외국인·대표이사 등), 보수 외 소득, 업종 변경 등에 따라 "
            "실제 금액이 달라질 수 있습니다. 산재요율은 업종별 고시 확인 필요."
        ),
    }


def compare_with_net(gross_monthly_wage: int) -> dict:
    """
    세전 → 4대보험 근로자 부담분 차감 후 추정 실수령액.
    소득세·지방소득세 미반영 (단순 참고용).
    """
    if gross_monthly_wage <= 0:
        return {"error": "gross_monthly_wage는 양수여야 합니다."}

    wage = gross_monthly_wage
    nps_base = _nps_base(wage)

    nps_employee = int(nps_base * RATES["nps_employee"])
    health_employee = int(wage * RATES["health_employee"])
    health_premium_employee_total = health_employee * 2   # 근로자+사업주 합산 기준으로 ltc 계산
    ltc_total = int(health_premium_employee_total * RATES["ltc_rate"])
    ltc_employee = int(ltc_total / 2)
    ei_ui_employee = int(wage * RATES["ei_ui_employee"])

    total_deduction = nps_employee + health_employee + ltc_employee + ei_ui_employee
    estimated_net = wage - total_deduction

    return {
        "mode": "compare-with-net",
        "gross_monthly_wage": wage,
        "deductions": {
            "national_pension": nps_employee,
            "health_insurance": health_employee,
            "long_term_care": ltc_employee,
            "employment_insurance_ui": ei_ui_employee,
        },
        "total_insurance_deduction": total_deduction,
        "estimated_net_wage": estimated_net,
        "note": (
            "소득세·지방소득세 미적용 단순 추정값입니다. "
            "실제 실수령액은 간이세액표 기준 소득세 추가 공제 후 달라집니다."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="4대보험료 계산기 (2026년 기준)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── calculate ────────────────────────────────────────────
    p_calc = sub.add_parser("calculate", help="항목별 4대보험료 산정")
    p_calc.add_argument(
        "--monthly-wage", type=int, required=True,
        help="월 보수(세전 급여, 원)",
    )
    p_calc.add_argument(
        "--company-size",
        choices=["under_150", "over_150_priority", "over_150", "over_1000"],
        default="under_150",
        help=(
            "사업장 규모: under_150(기본)/over_150_priority/"
            "over_150/over_1000"
        ),
    )
    p_calc.add_argument(
        "--industry-rate", type=float, default=0.0143,
        help="산재보험 요율 (소수, 예: 0.0143). 기본값 평균 1.43%%",
    )

    # ── compare-with-net ─────────────────────────────────────
    p_net = sub.add_parser(
        "compare-with-net",
        help="세전 → 4대보험 공제 후 추정 실수령액 (소득세 미포함)",
    )
    p_net.add_argument(
        "--gross-monthly-wage", type=int, required=True,
        help="세전 월급 (원)",
    )

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "calculate":
        result = calculate_insurance(
            monthly_wage=args.monthly_wage,
            company_size=args.company_size,
            industry_rate=args.industry_rate,
        )
    elif args.cmd == "compare-with-net":
        result = compare_with_net(gross_monthly_wage=args.gross_monthly_wage)
    else:
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
