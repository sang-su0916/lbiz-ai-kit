#!/usr/bin/env python3
"""
연장·야간·휴일 가산수당 계산기 (근기법 §56①②③)

가산율:
  연장근로 (§56①)          : 통상임금 50% 가산
  야간근로 (§56③, 22~06시)  : 통상임금 50% 가산
  휴일근로 8H 이내 (§56②)  : 통상임금 50% 가산
  휴일근로 8H 초과분 (§56②) : 통상임금 100% 가산
  중복 가산: 연장+야간=100% / 휴일+야간=100% / 휴일초과+야간=150%

5인 미만 사업장: §56 가산수당 적용 제외 (시행령 §7 별표)

모드: calculate (복합 가산수당 계산) | breakdown (출퇴근 시각 분해)

CLI: python3 calculator.py calculate --help
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

# ─── 가산율 상수 ────────────────────────────────────────────────────────────────
OVERTIME_PREMIUM = 0.5        # 연장근로 50%
NIGHT_PREMIUM = 0.5           # 야간근로 50%
HOLIDAY_PREMIUM = 0.5         # 휴일근로 8시간 이내 50%
HOLIDAY_OVER_8H_PREMIUM = 1.0 # 휴일근로 8시간 초과분 100%
NIGHT_START_HOUR = 22         # 야간 시작 (오후 10시)
NIGHT_END_HOUR = 6            # 야간 종료 (익일 오전 6시)
LEGAL_DAILY_HOURS = 8         # 법정 1일 근로시간
LEGAL_WEEKLY_HOURS = 40       # 법정 1주 근로시간


def calculate_overtime(
    hourly_wage: float,
    overtime_hours: float = 0.0,
    night_hours: float = 0.0,
    holiday_hours: float = 0.0,
    holiday_over_8_hours: float = 0.0,
    company_size_ge_5: bool = True,
) -> dict:
    """
    복합 가산수당 계산.

    Args:
        hourly_wage: 통상시급 (원)
        overtime_hours: 연장근로 시간 (법정 근로시간 초과분)
        night_hours: 야간근로 시간 (22~06시 구간)
        holiday_hours: 휴일근로 총 시간
        holiday_over_8_hours: 휴일근로 중 8시간 초과분
            예) 휴일 10시간 근무 → holiday_hours=10, holiday_over_8_hours=2
        company_size_ge_5: 상시 5인 이상 사업장 여부 (False면 §56 가산 제외)
    """
    w = float(hourly_wage)

    if not company_size_ge_5:
        # 5인 미만: 원금만 지급, 가산 없음
        total_hours = overtime_hours + night_hours + holiday_hours
        base_pay = round(w * total_hours)
        return {
            "company_size_ge_5": False,
            "notice": (
                "상시 5인 미만 사업장은 근로기준법 §56 가산수당 규정 적용 제외 "
                "(시행령 §7 별표). 통상임금 원금만 지급됩니다."
            ),
            "items": {
                "overtime": {
                    "hours": overtime_hours,
                    "base": round(w * overtime_hours),
                    "premium": 0,
                    "total": round(w * overtime_hours),
                },
                "night": {
                    "hours": night_hours,
                    "base": round(w * night_hours),
                    "premium": 0,
                    "total": round(w * night_hours),
                },
                "holiday": {
                    "hours": holiday_hours,
                    "holiday_over_8_hours": holiday_over_8_hours,
                    "base": round(w * holiday_hours),
                    "premium": 0,
                    "total": round(w * holiday_hours),
                },
            },
            "grand_total": base_pay,
            "disclaimer": (
                "통상임금 범위·포괄임금 약정·단체협약에 따라 실제 금액이 달라질 수 있습니다."
            ),
        }

    # ── 연장근로 ────────────────────────────────────────────────────────────────
    ot_base = w * overtime_hours
    ot_premium = w * overtime_hours * OVERTIME_PREMIUM
    ot_total = ot_base + ot_premium

    # ── 야간근로 ────────────────────────────────────────────────────────────────
    # 야간은 독립 가산 (연장·휴일과 중복 적용)
    # night_hours는 원금이 이미 연장 또는 휴일 항목에 포함될 수 있으므로
    # 야간 구간에서는 가산분(50%)만 추가 청구
    nt_premium = w * night_hours * NIGHT_PREMIUM
    nt_total = nt_premium  # 야간 원금은 연장 또는 정규 근로에 포함됨

    # ── 휴일근로 ────────────────────────────────────────────────────────────────
    holiday_within_8 = holiday_hours - holiday_over_8_hours
    if holiday_within_8 < 0:
        holiday_within_8 = 0.0

    hd_base = w * holiday_hours
    hd_premium_within = w * holiday_within_8 * HOLIDAY_PREMIUM
    hd_premium_over = w * holiday_over_8_hours * HOLIDAY_OVER_8H_PREMIUM
    hd_premium = hd_premium_within + hd_premium_over
    hd_total = hd_base + hd_premium

    grand_total = round(ot_total + nt_total + hd_total)

    return {
        "company_size_ge_5": True,
        "hourly_wage": w,
        "items": {
            "overtime": {
                "hours": overtime_hours,
                "premium_rate": OVERTIME_PREMIUM,
                "base": round(ot_base),
                "premium": round(ot_premium),
                "total": round(ot_total),
                "calculation": (
                    f"{w:,.0f} × {overtime_hours}H × 1.5 = {round(ot_total):,}원"
                    if overtime_hours else "해당 없음"
                ),
            },
            "night": {
                "hours": night_hours,
                "premium_rate": NIGHT_PREMIUM,
                "base": 0,
                "premium": round(nt_premium),
                "total": round(nt_total),
                "note": "야간 원금은 연장 또는 정규 근로 항목에 포함. 가산분(50%)만 표시.",
                "calculation": (
                    f"{w:,.0f} × {night_hours}H × 0.5(야간가산) = {round(nt_premium):,}원"
                    if night_hours else "해당 없음"
                ),
            },
            "holiday": {
                "hours": holiday_hours,
                "holiday_over_8_hours": holiday_over_8_hours,
                "holiday_within_8_hours": round(holiday_within_8, 2),
                "premium_rate_within_8": HOLIDAY_PREMIUM,
                "premium_rate_over_8": HOLIDAY_OVER_8H_PREMIUM,
                "base": round(hd_base),
                "premium": round(hd_premium),
                "total": round(hd_total),
                "calculation": (
                    f"{w:,.0f} × {holiday_within_8}H × 1.5"
                    f" + {w:,.0f} × {holiday_over_8_hours}H × 2.0"
                    f" = {round(hd_total):,}원"
                    if holiday_hours else "해당 없음"
                ),
            },
        },
        "grand_total": grand_total,
        "disclaimer": (
            "통상임금 범위·포괄임금 약정·단체협약에 따라 실제 금액이 달라질 수 있습니다."
        ),
    }


def breakdown_hours(
    clock_in: str,
    clock_out: str,
    is_holiday: bool = False,
    break_minutes: int = 60,
) -> dict:
    """
    출퇴근 시각으로부터 근무 유형별 시간 분해.

    Args:
        clock_in: 출근 시각 "HH:MM" (당일 기준)
        clock_out: 퇴근 시각 "HH:MM" (익일 걸리면 자동 처리)
        is_holiday: 휴일 근무 여부
        break_minutes: 휴게시간 (분)

    Returns:
        {regular_hours, overtime_hours, night_hours,
         holiday_hours, holiday_over8_hours}
    """
    fmt = "%H:%M"
    base_date = datetime(2000, 1, 1)  # 날짜는 임의, 시각 계산용
    ci = datetime.strptime(clock_in, fmt).replace(
        year=base_date.year, month=base_date.month, day=base_date.day
    )
    co = datetime.strptime(clock_out, fmt).replace(
        year=base_date.year, month=base_date.month, day=base_date.day
    )
    if co <= ci:
        co += timedelta(days=1)

    actual_minutes = (co - ci).total_seconds() / 60 - break_minutes
    if actual_minutes < 0:
        actual_minutes = 0.0
    actual_hours = actual_minutes / 60

    # ── 야간 시간 계산 (22:00~익일 06:00) ──────────────────────────────────────
    night_start = ci.replace(hour=NIGHT_START_HOUR, minute=0, second=0)
    next_day_night_end = night_start + timedelta(
        hours=(24 - NIGHT_START_HOUR + NIGHT_END_HOUR)
    )  # 익일 06:00

    # 야간 구간과 실제 근무 구간의 교집합 계산
    work_start = ci
    work_end = co

    # 22:00~익일 06:00 구간
    ns1 = night_start
    ne1 = next_day_night_end

    overlap_start = max(work_start, ns1)
    overlap_end = min(work_end, ne1)
    night_minutes = max(0.0, (overlap_end - overlap_start).total_seconds() / 60)

    # 전날 22:00 이전 야간 구간도 체크 (예: 전날 22시 이전 출근 → 당일 06시까지)
    prev_night_end = ci.replace(hour=NIGHT_END_HOUR, minute=0, second=0)
    if work_start < prev_night_end:
        overlap2_end = min(work_end, prev_night_end)
        night_minutes += max(0.0, (overlap2_end - work_start).total_seconds() / 60)

    # 휴게시간 비례 차감 (단순화: 야간 비율만큼 차감)
    total_raw_minutes = (co - ci).total_seconds() / 60
    if total_raw_minutes > 0:
        night_ratio = night_minutes / total_raw_minutes
    else:
        night_ratio = 0.0
    night_hours_val = round((actual_minutes * night_ratio) / 60, 2)

    # ── 연장·정규·휴일 분류 ──────────────────────────────────────────────────────
    if is_holiday:
        regular_hours = 0.0
        overtime_hours_val = 0.0
        holiday_hours_val = round(actual_hours, 2)
        holiday_over8 = round(max(0.0, actual_hours - LEGAL_DAILY_HOURS), 2)
    else:
        regular_hours = round(min(actual_hours, float(LEGAL_DAILY_HOURS)), 2)
        overtime_hours_val = round(max(0.0, actual_hours - LEGAL_DAILY_HOURS), 2)
        holiday_hours_val = 0.0
        holiday_over8 = 0.0

    return {
        "clock_in": clock_in,
        "clock_out": clock_out,
        "break_minutes": break_minutes,
        "is_holiday": is_holiday,
        "actual_work_hours": round(actual_hours, 2),
        "regular_hours": regular_hours,
        "overtime_hours": overtime_hours_val,
        "night_hours": night_hours_val,
        "holiday_hours": holiday_hours_val,
        "holiday_over8_hours": holiday_over8,
        "note": (
            "야간시간은 22:00~익일 06:00 구간 실근로시간 기준. "
            "연장+야간 중복 시 calculate 모드에서 각각 입력하세요."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="연장·야간·휴일 가산수당 계산기 (근기법 §56)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── calculate ──────────────────────────────────────────────────────────────
    p_calc = sub.add_parser("calculate", help="복합 가산수당 계산")
    p_calc.add_argument(
        "--hourly-wage", type=float, required=True,
        help="통상시급 (원)",
    )
    p_calc.add_argument(
        "--overtime-hours", type=float, default=0.0,
        help="연장근로 시간 (법정 근로시간 초과분, 기본 0)",
    )
    p_calc.add_argument(
        "--night-hours", type=float, default=0.0,
        help="야간근로 시간 (22~06시 구간, 기본 0)",
    )
    p_calc.add_argument(
        "--holiday-hours", type=float, default=0.0,
        help="휴일근로 총 시간 (기본 0)",
    )
    p_calc.add_argument(
        "--holiday-over-8-hours", type=float, default=0.0,
        help="휴일근로 중 8시간 초과분 (기본 0). 예: 휴일 10H → --holiday-hours 10 --holiday-over-8-hours 2",
    )
    p_calc.add_argument(
        "--company-size-ge-5",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="5인 이상 사업장 여부 (기본 True). 5인 미만: --no-company-size-ge-5",
    )

    # ── breakdown ──────────────────────────────────────────────────────────────
    p_bd = sub.add_parser("breakdown", help="출퇴근 시각으로 근무 유형별 시간 분해")
    p_bd.add_argument(
        "--clock-in", type=str, required=True,
        help='출근 시각, 형식 "HH:MM" (예: "09:00")',
    )
    p_bd.add_argument(
        "--clock-out", type=str, required=True,
        help='퇴근 시각, 형식 "HH:MM" (예: "23:30"). 익일 걸리면 자동 처리',
    )
    p_bd.add_argument(
        "--is-holiday",
        action="store_true", default=False,
        help="휴일 근무 여부 (주휴일·법정공휴일·약정휴일)",
    )
    p_bd.add_argument(
        "--break-minutes", type=int, default=60,
        help="휴게시간 (분, 기본 60)",
    )

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "calculate":
        result = calculate_overtime(
            hourly_wage=args.hourly_wage,
            overtime_hours=args.overtime_hours,
            night_hours=args.night_hours,
            holiday_hours=args.holiday_hours,
            holiday_over_8_hours=args.holiday_over_8_hours,
            company_size_ge_5=args.company_size_ge_5,
        )
    elif args.cmd == "breakdown":
        result = breakdown_hours(
            clock_in=args.clock_in,
            clock_out=args.clock_out,
            is_holiday=args.is_holiday,
            break_minutes=args.break_minutes,
        )
    else:
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
