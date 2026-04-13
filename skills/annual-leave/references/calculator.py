#!/usr/bin/env python3
"""
연차유급휴가 계산기 (근로기준법 §60)

공식:
  [1년 미만]  1개월 개근 시 1일 발생 (최대 11일)
  [1년 이상]  출근율 80% 이상 → 기본 15일
  [가산]      3년 이상 근속 시 매 2년마다 1일 가산, 상한 25일
              가산일수 = floor((근속연수 - 1) / 2)

  [미사용수당]  통상임금 1일분 × 미사용일수
              연차사용촉진(§61) 이행 완료 시 → 사용자 지급의무 면제(0원)

모드: entitlement (발생일수) | unused-pay (미사용수당)

CLI: python3 calculator.py entitlement --help
"""

import argparse
import json
import math
import sys
import datetime


def _years_between(hire: datetime.date, base: datetime.date) -> float:
    """입사일~기준일 사이 경과 연수 (소수 포함)."""
    delta = base - hire
    return delta.days / 365


def _months_between(hire: datetime.date, base: datetime.date) -> int:
    """입사일~기준일 사이 완전 경과 개월수."""
    months = (base.year - hire.year) * 12 + (base.month - hire.month)
    # 기준일의 일(day)이 입사일 일(day)보다 작으면 완전 개월 미충족
    if base.day < hire.day:
        months -= 1
    return max(0, months)


def calculate_entitlement(
    hire_date: datetime.date,
    base_date: datetime.date,
    base_type: str = "hire",
    attendance_rate: float = 1.0,
) -> dict:
    """
    연차 발생일수 산정.

    base_type:
      'hire'   — 입사일 기준 (개인별 관리)
      'fiscal' — 회계연도 기준 (사업장 일괄 관리, 첫해 비례 발생)
    """
    if base_date < hire_date:
        return {"error": "base_date는 hire_date 이후여야 합니다."}

    service_days = (base_date - hire_date).days
    service_years_float = service_days / 365

    # ── 1년 미만 ──────────────────────────────────────────────
    if service_days < 365:
        completed_months = _months_between(hire_date, base_date)
        entitlement = min(completed_months, 11)
        return {
            "mode": "entitlement",
            "base_type": base_type,
            "hire_date": hire_date.isoformat(),
            "base_date": base_date.isoformat(),
            "service_days": service_days,
            "service_years": round(service_years_float, 2),
            "attendance_rate": attendance_rate,
            "period": "under_1_year",
            "completed_months": completed_months,
            "entitlement_days": entitlement,
            "calculation": f"1년 미만: 완전 경과 개월 {completed_months}개월 → {entitlement}일 (상한 11일)",
            "disclaimer": (
                "단체협약·취업규칙에 따라 실제 일수가 달라질 수 있습니다. "
                "출근율 산정 시 산재·출산휴가 등 법정 산입 사유 별도 검토 필요."
            ),
        }

    # ── 출근율 80% 미만 ───────────────────────────────────────
    if attendance_rate < 0.8:
        return {
            "mode": "entitlement",
            "base_type": base_type,
            "hire_date": hire_date.isoformat(),
            "base_date": base_date.isoformat(),
            "service_days": service_days,
            "service_years": round(service_years_float, 2),
            "attendance_rate": attendance_rate,
            "period": "over_1_year_low_attendance",
            "entitlement_days": 0,
            "calculation": f"출근율 {attendance_rate*100:.1f}% < 80% → 연차 발생 없음",
            "disclaimer": (
                "결근 사유별 출근 산입 여부(산재·출산휴가·육아휴직 등)는 별도 검토 필요."
            ),
        }

    # ── 1년 이상, 출근율 80% 이상 ────────────────────────────
    # 입사일 기준: 근속연수 = 경과 완전 연수
    completed_years = int(service_days // 365)

    if base_type == "fiscal":
        # 회계연도 기준: 첫해 비례 발생 후, 이후 연도는 입사일 기준과 동일하게 산정
        # (본 구현은 현재 시점의 해당연도 연차발생일수를 반환)
        # 첫 회계연도 비례: 입사일~그해 12/31까지 일수 / 365 × 15
        first_year_end = datetime.date(hire_date.year, 12, 31)
        days_first = (first_year_end - hire_date).days + 1
        proportional = round(days_first / 365 * 15, 2)
        base_days = 15
        add_days = math.floor((completed_years - 1) / 2) if completed_years >= 3 else 0
        total = min(base_days + add_days, 25)
        return {
            "mode": "entitlement",
            "base_type": "fiscal",
            "hire_date": hire_date.isoformat(),
            "base_date": base_date.isoformat(),
            "service_days": service_days,
            "service_years": round(service_years_float, 2),
            "completed_years": completed_years,
            "attendance_rate": attendance_rate,
            "period": "over_1_year",
            "first_year_proportional_days": proportional,
            "base_days": base_days,
            "add_days": add_days,
            "entitlement_days": total,
            "calculation": (
                f"회계연도 기준 | 첫해 비례 {proportional}일 "
                f"| 현재 {completed_years}년차: 기본 {base_days}일 + 가산 {add_days}일 = {total}일 (상한 25일)"
            ),
            "disclaimer": (
                "단체협약·취업규칙에 따라 실제 일수가 달라질 수 있습니다. "
                "중도 퇴사 시 잔여 비례정산은 별도 산정 필요."
            ),
        }

    # 입사일 기준 (hire)
    base_days = 15
    add_days = math.floor((completed_years - 1) / 2) if completed_years >= 3 else 0
    total = min(base_days + add_days, 25)

    return {
        "mode": "entitlement",
        "base_type": "hire",
        "hire_date": hire_date.isoformat(),
        "base_date": base_date.isoformat(),
        "service_days": service_days,
        "service_years": round(service_years_float, 2),
        "completed_years": completed_years,
        "attendance_rate": attendance_rate,
        "period": "over_1_year",
        "base_days": base_days,
        "add_days": add_days,
        "entitlement_days": total,
        "calculation": (
            f"입사일 기준 | {completed_years}년차: 기본 {base_days}일 + 가산 {add_days}일 = {total}일 (상한 25일)"
        ),
        "disclaimer": (
            "단체협약·취업규칙에 따라 실제 일수가 달라질 수 있습니다. "
            "출근율 80% 미만 연도는 별도 확인 필요."
        ),
    }


def calculate_unused_pay(
    daily_ordinary_wage: int,
    unused_days: int,
    promotion_completed: bool = False,
) -> dict:
    """
    미사용 연차수당 산정.

    promotion_completed:
      True  — 연차사용촉진(§61) 절차 이행 완료 → 사용자 지급의무 면제
      False — 미이행 또는 미적용 → 수당 지급
    """
    if daily_ordinary_wage < 0:
        return {"error": "daily_ordinary_wage는 0 이상이어야 합니다."}
    if unused_days < 0:
        return {"error": "unused_days는 0 이상이어야 합니다."}

    if promotion_completed:
        return {
            "mode": "unused-pay",
            "daily_ordinary_wage": daily_ordinary_wage,
            "unused_days": unused_days,
            "promotion_completed": True,
            "unused_pay": 0,
            "calculation": (
                f"연차사용촉진(§61) 이행 완료 → 사용자 미사용수당 지급의무 면제 "
                f"({daily_ordinary_wage:,}원 × {unused_days}일 = 면제)"
            ),
            "note": (
                "근로자가 촉진 통보를 무시하고 미사용한 경우 사용자 책임 없음. "
                "촉진 절차(1차 서면통보 10일→근로자 미제출→2차 개별지정)가 완전히 이행된 경우에 한함."
            ),
            "disclaimer": "단체협약·취업규칙에 따라 면제 범위가 달라질 수 있습니다.",
        }

    pay = daily_ordinary_wage * unused_days
    return {
        "mode": "unused-pay",
        "daily_ordinary_wage": daily_ordinary_wage,
        "unused_days": unused_days,
        "promotion_completed": False,
        "unused_pay": pay,
        "calculation": f"{daily_ordinary_wage:,}원 × {unused_days}일 = {pay:,}원",
        "disclaimer": (
            "통상임금 1일분 산정 기준(소정근로시간 × 시간급)은 취업규칙·단체협약 확인 필요. "
            "연차수당 청구권 소멸시효는 3년 (민법 §163)."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="calculator.py", description="연차유급휴가 계산기 (근로기준법 §60)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── entitlement subcommand ────────────────────────────────
    p_ent = sub.add_parser("entitlement", help="연차 발생일수 산정")
    p_ent.add_argument(
        "--hire-date", required=True,
        help="입사일 (YYYY-MM-DD)",
    )
    p_ent.add_argument(
        "--base-date", required=True,
        help="기준일 (YYYY-MM-DD, 보통 오늘 또는 퇴직일)",
    )
    p_ent.add_argument(
        "--base-type", choices=["hire", "fiscal"], default="hire",
        help="기준유형: hire(입사일 기준, 기본값) | fiscal(회계연도 기준)",
    )
    p_ent.add_argument(
        "--attendance-rate", type=float, default=1.0,
        help="출근율 0.0~1.0 (기본값 1.0 = 100%%)",
    )

    # ── unused-pay subcommand ─────────────────────────────────
    p_pay = sub.add_parser("unused-pay", help="미사용 연차수당 산정")
    p_pay.add_argument(
        "--daily-ordinary-wage", type=int, required=True,
        help="통상임금 1일분 (원)",
    )
    p_pay.add_argument(
        "--unused-days", type=int, required=True,
        help="미사용 연차일수",
    )
    p_pay.add_argument(
        "--promotion-completed", type=lambda x: x.lower() in ("true", "1", "yes"),
        default=False,
        help="연차사용촉진(§61) 절차 이행 완료 여부: true | false (기본값 false)",
    )

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "entitlement":
        try:
            hire = datetime.date.fromisoformat(args.hire_date)
            base = datetime.date.fromisoformat(args.base_date)
        except ValueError as e:
            print(json.dumps({"error": f"날짜 형식 오류: {e}"}, ensure_ascii=False, indent=2))
            return 1
        result = calculate_entitlement(hire, base, args.base_type, args.attendance_rate)

    elif args.cmd == "unused-pay":
        result = calculate_unused_pay(
            args.daily_ordinary_wage,
            args.unused_days,
            args.promotion_completed,
        )
    else:
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
