#!/usr/bin/env python3
"""
통상임금·평균임금 계산기 (근로기준법 §2)

통상임금 공식:
  209시간 = (주 40시간 + 유급주휴 8시간) × 365/12/7 = 208.57... → 209시간
  시급 = 월급 ÷ 209
  일급 = 시급 × 8
  월급 = 시급 × 209

평균임금 공식:
  1일 평균임금 = (3개월 임금총액 + 상여금/연차수당의 3개월분) ÷ 3개월 일수

비교 (근로기준법 §2②):
  적용 일급 = max(통상임금 일급, 평균임금 일급)

서브커맨드: ordinary | average | compare

CLI: python3 calculator.py ordinary --help
"""

import argparse
import json
import sys

STATUTORY_MONTHLY_HOURS = 209  # (40 + 8) × 365/12/7 ≈ 209.143 → 209
DAILY_WORK_HOURS = 8


def calc_ordinary(
    base_wage: int,
    base_type: str,
    weekly_hours: int = 40,
) -> dict:
    """통상임금 환산: monthly / hourly / daily → 전 단위 출력."""
    if base_wage <= 0:
        return {"error": "base_wage must be > 0"}
    if base_type not in ("monthly", "hourly", "daily"):
        return {"error": "base_type must be monthly, hourly, or daily"}

    # 주휴 포함 월 환산시간: (weekly_hours + weekly_hours/5) × 365/12/7
    # 법정 40시간제는 209시간 고정; 다른 소정근로시간은 비례 계산
    if weekly_hours == 40:
        monthly_hours = STATUTORY_MONTHLY_HOURS
    else:
        weekly_holiday_hours = weekly_hours / 5  # 1일분 주휴
        monthly_hours = round((weekly_hours + weekly_holiday_hours) * 365 / 12 / 7)

    if base_type == "monthly":
        hourly = base_wage / monthly_hours
        daily = hourly * DAILY_WORK_HOURS
        monthly = base_wage
    elif base_type == "hourly":
        hourly = base_wage
        daily = hourly * DAILY_WORK_HOURS
        monthly = round(hourly * monthly_hours)
    else:  # daily
        hourly = base_wage / DAILY_WORK_HOURS
        daily = base_wage
        monthly = round(hourly * monthly_hours)

    return {
        "subcommand": "ordinary",
        "input": {"base_wage": base_wage, "base_type": base_type, "weekly_hours": weekly_hours},
        "monthly_hours_basis": monthly_hours,
        "hourly": round(hourly),
        "daily": round(daily),
        "weekly": round(hourly * weekly_hours),
        "monthly": round(monthly),
        "calculation": (
            f"기준 {base_type}={base_wage:,}원 → "
            f"시급 {round(hourly):,}원 (월{monthly_hours}시간 기준) | "
            f"일급 {round(daily):,}원 (×{DAILY_WORK_HOURS}h) | "
            f"월급 {round(monthly):,}원 (×{monthly_hours}h)"
        ),
        "disclaimer": (
            "단체협약·취업규칙·소정근로시간에 따라 실제 금액이 달라질 수 있습니다. "
            "통상임금 해당 여부(정기성·일률성·고정성)는 법적 판단 영역입니다."
        ),
    }


def calc_average(
    three_month_wage_total: int,
    days_in_3month: int,
    annual_bonus: int = 0,
    annual_leave_pay: int = 0,
) -> dict:
    """평균임금 산정: 직전 3개월 임금총액 ÷ 3개월 일수."""
    if three_month_wage_total <= 0:
        return {"error": "three_month_wage_total must be > 0"}
    if days_in_3month <= 0:
        return {"error": "days_in_3month must be > 0"}

    bonus_portion = (annual_bonus + annual_leave_pay) * 3 / 12
    numerator = three_month_wage_total + bonus_portion
    daily_avg = numerator / days_in_3month

    return {
        "subcommand": "average",
        "input": {
            "three_month_wage_total": three_month_wage_total,
            "days_in_3month": days_in_3month,
            "annual_bonus": annual_bonus,
            "annual_leave_pay": annual_leave_pay,
        },
        "bonus_portion_3m": round(bonus_portion),
        "numerator": round(numerator),
        "daily_avg_wage": round(daily_avg),
        "calculation": (
            f"({three_month_wage_total:,} + 상여/연차 3개월분 {round(bonus_portion):,})"
            f" ÷ {days_in_3month}일 = 1일 평균임금 {round(daily_avg):,}원"
        ),
        "note": (
            "상여금 산정 방식은 '연간 상여금 ÷ 12 × 3' 단순화. "
            "정직·휴직·육아휴직 기간 제외 보정은 미반영."
        ),
        "disclaimer": (
            "단체협약·취업규칙에 따라 실제 금액이 달라질 수 있습니다."
        ),
    }


def calc_compare(
    ordinary_daily: int,
    average_daily: int,
) -> dict:
    """통상임금 vs 평균임금 비교 — 큰 쪽 적용 (근로기준법 §2②)."""
    if ordinary_daily <= 0 or average_daily <= 0:
        return {"error": "ordinary_daily and average_daily must be > 0"}

    if ordinary_daily >= average_daily:
        applied = ordinary_daily
        basis = "통상임금"
        reason = "통상임금 일급이 평균임금 일급 이상 → 통상임금 적용 (근로기준법 §2②)"
    else:
        applied = average_daily
        basis = "평균임금"
        reason = "평균임금 일급이 통상임금 일급보다 큼 → 평균임금 적용"

    return {
        "subcommand": "compare",
        "input": {"ordinary_daily": ordinary_daily, "average_daily": average_daily},
        "ordinary_daily": ordinary_daily,
        "average_daily": average_daily,
        "applied_daily": applied,
        "applied_basis": basis,
        "reason": reason,
        "difference": ordinary_daily - average_daily,
        "calculation": (
            f"통상임금 일급 {ordinary_daily:,}원 vs 평균임금 일급 {average_daily:,}원"
            f" → {basis} {applied:,}원 적용"
        ),
        "disclaimer": (
            "퇴직금·휴업수당 산정 시 두 금액 중 큰 쪽을 기준임금으로 사용합니다. "
            "단체협약·취업규칙에 따라 달라질 수 있습니다."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="통상임금·평균임금 계산기 (근로기준법 §2)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- ordinary ---
    p_ord = sub.add_parser("ordinary", help="통상임금 환산 (monthly/hourly/daily → 전 단위)")
    p_ord.add_argument("--base-wage", type=int, required=True,
                       help="기준 임금 금액 (원)")
    p_ord.add_argument("--base-type", choices=["monthly", "hourly", "daily"], required=True,
                       help="기준 임금 단위: monthly=월급, hourly=시급, daily=일급")
    p_ord.add_argument("--weekly-hours", type=int, default=40,
                       help="주 소정근로시간 (기본 40시간)")

    # --- average ---
    p_avg = sub.add_parser("average", help="평균임금 산정 (직전 3개월 기준)")
    p_avg.add_argument("--three-month-wage-total", type=int, required=True,
                       help="직전 3개월 임금 총액 (원)")
    p_avg.add_argument("--days-in-3month", type=int, required=True,
                       help="직전 3개월 일수 (89~92)")
    p_avg.add_argument("--annual-bonus", type=int, default=0,
                       help="연간 상여금 (원, 기본 0)")
    p_avg.add_argument("--annual-leave-pay", type=int, default=0,
                       help="연간 연차수당 (원, 기본 0)")

    # --- compare ---
    p_cmp = sub.add_parser("compare", help="통상임금 vs 평균임금 비교 — 큰 쪽 판정")
    p_cmp.add_argument("--ordinary-daily", type=int, required=True,
                       help="통상임금 일급 (원)")
    p_cmp.add_argument("--average-daily", type=int, required=True,
                       help="평균임금 일급 (원)")

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "ordinary":
        result = calc_ordinary(args.base_wage, args.base_type, args.weekly_hours)
    elif args.cmd == "average":
        result = calc_average(
            args.three_month_wage_total,
            args.days_in_3month,
            args.annual_bonus,
            args.annual_leave_pay,
        )
    elif args.cmd == "compare":
        result = calc_compare(args.ordinary_daily, args.average_daily)
    else:
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
