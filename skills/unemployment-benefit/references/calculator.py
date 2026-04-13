#!/usr/bin/env python3
"""
실업급여(구직급여) 계산기 (고용보험법 §40~50, 2026년 기준)

공식:
  구직급여 일액 = min(상한 66,000, max(하한 64,192, 평균임금 일액 × 0.6))
  소정급여일수  = 가입기간 × 연령 매트릭스 (§50 별표)
  총 지급 추정액 = 구직급여 일액 × 소정급여일수

자격 요건 (4가지 모두 충족):
  1. 이직일 이전 18개월간 피보험단위기간 180일 이상
  2. 비자발적 이직 (자발적 퇴사는 자격 없음 — 정당 사유는 고용센터 심사)
  3. 근로의사·능력 있고 적극적 구직활동 중
  4. 재취업 노력에도 취업하지 못함

CLI: python3 calculator.py calculate --help
"""

import argparse
import json
import sys

# 2025년 기준 상·하한액 (2026년 최저임금 확정 시 하한액 갱신 필요)
DAILY_MAX = 66_000   # 상한액 (원)
DAILY_MIN = 64_192   # 하한액 (원, 2025년 최저임금 9,860원 × 8시간 × 80%)

# 소정급여일수 매트릭스 (고용보험법 §50 별표)
# key: (가입연수 구간 인덱스, 50세 미만 여부)
# 구간: 0=1년 미만, 1=1년~3년, 2=3년~5년, 3=5년~10년, 4=10년 이상
BENEFIT_DAYS_MATRIX = {
    #         50세 미만  50세 이상 또는 장애인
    0: (120,  120),
    1: (150,  180),
    2: (180,  210),
    3: (210,  240),
    4: (240,  270),
}


def _insured_years_to_band(insured_years: float) -> int:
    """가입연수를 소정급여일수 매트릭스 구간 인덱스로 변환."""
    if insured_years < 1:
        return 0
    elif insured_years < 3:
        return 1
    elif insured_years < 5:
        return 2
    elif insured_years < 10:
        return 3
    else:
        return 4


def calculate_unemployment_benefit(
    avg_daily_wage: int,
    insured_days: int,
    insured_years: float,
    age: int,
    voluntary: bool,
    has_disability: bool,
) -> dict:
    """
    구직급여 자격 판정 + 일액 + 소정급여일수 + 총액 산정.

    Args:
        avg_daily_wage:  이직 전 평균임금 일액 (원)
        insured_days:    이직 전 18개월간 피보험단위기간 (일)
        insured_years:   고용보험 가입 총 연수
        age:             만 나이
        voluntary:       자발적 퇴사 여부 (True = 자발적)
        has_disability:  장애인 여부

    Returns:
        dict with eligible, reason(불자격 시), daily_benefit, benefit_days,
        total_benefit, calculation, disclaimer
    """
    # 자격 판정 1: 피보험단위기간
    if insured_days < 180:
        return {
            "eligible": False,
            "reason": (
                f"피보험단위기간 {insured_days}일 — 180일 미달 "
                "(고용보험법 §40①1, 이직일 이전 18개월간 180일 이상 필요)"
            ),
            "daily_benefit": 0,
            "benefit_days": 0,
            "total_benefit": 0,
        }

    # 자격 판정 2: 이직 사유
    if voluntary:
        return {
            "eligible": False,
            "reason": (
                "자발적 퇴사 — 원칙적으로 구직급여 수급 불가 (고용보험법 §58). "
                "단, 임금체불·근로조건 저하·통근곤란(왕복 3시간 이상)·결혼·임신·출산·"
                "사업장 이전 등 정당한 사유에 해당하면 수급 가능. "
                "해당 여부는 가까운 고용센터에서 확인하세요."
            ),
            "daily_benefit": 0,
            "benefit_days": 0,
            "total_benefit": 0,
        }

    # 구직급여 일액 산정
    raw_benefit = round(avg_daily_wage * 0.6)
    daily_benefit = min(DAILY_MAX, max(DAILY_MIN, raw_benefit))

    cap_note = ""
    if raw_benefit > DAILY_MAX:
        cap_note = f"상한 적용 (산출 {raw_benefit:,}원 → 상한 {DAILY_MAX:,}원)"
    elif raw_benefit < DAILY_MIN:
        cap_note = f"하한 적용 (산출 {raw_benefit:,}원 → 하한 {DAILY_MIN:,}원)"
    else:
        cap_note = f"상·하한 미적용 (산출 {raw_benefit:,}원)"

    # 소정급여일수 매트릭스 조회
    band = _insured_years_to_band(insured_years)
    senior = age >= 50 or has_disability
    benefit_days = BENEFIT_DAYS_MATRIX[band][1 if senior else 0]

    # 가입기간 구간 텍스트
    band_labels = ["1년 미만", "1년~3년", "3년~5년", "5년~10년", "10년 이상"]
    age_label = "50세 이상 또는 장애인" if senior else "50세 미만"

    total_benefit = daily_benefit * benefit_days

    return {
        "eligible": True,
        "insured_days": insured_days,
        "insured_years": insured_years,
        "age": age,
        "senior_or_disability": senior,
        "avg_daily_wage": avg_daily_wage,
        "daily_benefit": daily_benefit,
        "cap_note": cap_note,
        "benefit_days_band": band_labels[band],
        "age_group": age_label,
        "benefit_days": benefit_days,
        "total_benefit": total_benefit,
        "calculation": (
            f"평균임금 {avg_daily_wage:,}원 × 0.6 = {raw_benefit:,}원 → {cap_note} → "
            f"일액 {daily_benefit:,}원 × "
            f"소정급여일수 {benefit_days}일 (가입 {band_labels[band]}, {age_label}) "
            f"= 총 {total_benefit:,}원"
        ),
        "disclaimer": (
            "총액은 구직활동 인정, 조기재취업수당, 취업촉진수당 등 실제 지급 조건에 따라 "
            "달라질 수 있습니다. 정확한 수급 여부는 가까운 고용센터에서 확인하세요. "
            "하한액은 2025년 기준(64,192원)이며 최저임금 인상 시 변동됩니다."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="실업급여(구직급여) 계산기 (고용보험법 §40~50, 2026년 기준)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("calculate", help="자격 판정 + 일액 + 소정급여일수 + 총액")
    p.add_argument(
        "--avg-daily-wage", type=int, required=True,
        help="이직 전 평균임금 일액 (원). 월급 기준이면 ÷30 환산.",
    )
    p.add_argument(
        "--insured-days", type=int, required=True,
        help="이직일 이전 18개월간 피보험단위기간 (일). 180일 미만 시 자격 없음.",
    )
    p.add_argument(
        "--insured-years", type=float, required=True,
        help="고용보험 가입 총 연수 (소수점 가능, 예: 5.5). 소정급여일수 매트릭스 조회에 사용.",
    )
    p.add_argument(
        "--age", type=int, required=True,
        help="만 나이. 50세 이상이면 소정급여일수 우대 구간 적용.",
    )
    p.add_argument(
        "--voluntary", choices=["yes", "no"], required=True,
        help="자발적 퇴사 여부. yes=자발적(원칙 불가), no=비자발적(권고사직·계약만료 등).",
    )
    p.add_argument(
        "--has-disability", choices=["yes", "no"], required=True,
        help="장애인 여부. yes이면 50세 이상과 동일 우대 구간 적용.",
    )

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "calculate":
        result = calculate_unemployment_benefit(
            avg_daily_wage=args.avg_daily_wage,
            insured_days=args.insured_days,
            insured_years=args.insured_years,
            age=args.age,
            voluntary=(args.voluntary == "yes"),
            has_disability=(args.has_disability == "yes"),
        )
    else:
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
