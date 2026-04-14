#!/usr/bin/env python3
"""
주휴수당 계산기 (근로기준법 §55, 시행령 §30)

공식:
  주 40시간 이상: 주휴수당 = 통상시급 × 8
  주 15~39시간:  주휴수당 = 통상시급 × (주 소정근로시간 / 40) × 8
  주 15시간 미만: 미발생

발생 요건: 1주 소정근로시간 15시간 이상 + 소정근로일 개근
모드: eligibility (발생 여부) | calculate (금액 산정)

CLI: python3 calculator.py calculate --help
"""

import argparse
import json
import sys

WEEKS_PER_MONTH = 4.345
STANDARD_HOURS = 40.0
MIN_HOURS = 15.0


def check_eligibility(weekly_hours: float, worked_all_days: bool) -> dict:
    """주휴수당 발생 요건 판정."""
    hours_ok = weekly_hours >= MIN_HOURS
    attendance_ok = worked_all_days

    eligible = hours_ok and attendance_ok

    if not hours_ok:
        reason = f"1주 소정근로시간 {weekly_hours}시간 — 15시간 미달로 주휴수당 미발생 (시행령 §30)"
    elif not attendance_ok:
        reason = "소정근로일 개근 미충족 — 결근이 있으면 해당 주 주휴수당 미발생"
    else:
        reason = "요건 충족 — 주휴수당 발생"

    return {
        "eligible": eligible,
        "reason": reason,
        "requirements": {
            "weekly_hours_15_or_more": {
                "required": True,
                "actual": weekly_hours,
                "satisfied": hours_ok,
            },
            "worked_all_scheduled_days": {
                "required": True,
                "actual": worked_all_days,
                "satisfied": attendance_ok,
                "note": "조퇴·지각은 개근으로 인정, 결근만 미충족 사유",
            },
        },
    }


def calculate_weekly_holiday_pay(
    weekly_hours: float,
    hourly_wage: int,
    worked_all_days: bool,
) -> dict:
    """주휴수당 금액 산정."""
    eligibility = check_eligibility(weekly_hours, worked_all_days)

    if not eligibility["eligible"]:
        return {
            "eligible": False,
            "reason": eligibility["reason"],
            "requirements": eligibility["requirements"],
            "paid_hours": 0.0,
            "amount": 0,
            "monthly_amount": 0,
        }

    # 비례 지급 시간수 산정
    if weekly_hours >= STANDARD_HOURS:
        paid_hours = 8.0
        calc_note = f"주 {weekly_hours}시간 (40시간 이상) → 8시간 전액"
    else:
        paid_hours = round((weekly_hours / STANDARD_HOURS) * 8, 4)
        calc_note = f"주 {weekly_hours}시간 ÷ 40 × 8 = {paid_hours}시간 (비례)"

    amount = round(hourly_wage * paid_hours)
    monthly_amount = round(amount * WEEKS_PER_MONTH)

    return {
        "eligible": True,
        "reason": eligibility["reason"],
        "requirements": eligibility["requirements"],
        "paid_hours": paid_hours,
        "hourly_wage": hourly_wage,
        "amount": amount,
        "monthly_amount": monthly_amount,
        "calculation": (
            f"{hourly_wage:,}원 × {paid_hours}시간 = {amount:,}원 / 주 "
            f"| 월 환산: {amount:,} × 4.345 = {monthly_amount:,}원"
        ),
        "calc_note": calc_note,
        "disclaimer": (
            "조퇴·지각은 개근으로 인정. 결근 1회만 있어도 해당 주 주휴수당 미발생. "
            "미지급 시 임금체불로 고용노동부 진정 대상."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="calculator.py", description="주휴수당 계산기")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_elig = sub.add_parser("eligibility", help="발생 여부 판정")
    p_elig.add_argument(
        "--weekly-hours", type=float, required=True,
        help="1주 소정근로시간 (예: 40, 20, 15)",
    )
    p_elig.add_argument(
        "--worked-all-days", action="store_true", default=False,
        help="소정근로일 개근 여부 (플래그 지정 시 개근, 미지정 시 결근 있음)",
    )

    p_calc = sub.add_parser("calculate", help="주휴수당 금액 산정")
    p_calc.add_argument(
        "--weekly-hours", type=float, required=True,
        help="1주 소정근로시간 (예: 40, 20, 15)",
    )
    p_calc.add_argument(
        "--hourly-wage", type=int, required=True,
        help="통상시급 (원, 예: 10320)",
    )
    p_calc.add_argument(
        "--worked-all-days", action="store_true", default=False,
        help="소정근로일 개근 여부 (플래그 지정 시 개근, 미지정 시 결근 있음)",
    )

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "eligibility":
        result = check_eligibility(args.weekly_hours, args.worked_all_days)
    elif args.cmd == "calculate":
        result = calculate_weekly_holiday_pay(
            args.weekly_hours, args.hourly_wage, args.worked_all_days,
        )
    else:
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
