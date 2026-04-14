#!/usr/bin/env python3
"""
최저임금 위반 체크기 (최저임금법 §5·§6)

공식:
  소정근로시간(월) = (주간소정근로시간 + 주휴시간) × 4.345
  시간당 실임금 = (기본급 + 월정기상여금 + 월복리후생비) ÷ 소정근로시간(월)
  위반: 시간당 실임금 < MIN_WAGE_2026

2026년 기준: 시급 10,320원 (2026.1.1 ~ 2026.12.31 시행)
산입범위: 기본급 + 매월 지급 정기상여금 + 매월 지급 복리후생비 (연장·야간·휴일수당 제외)

모드: check (위반 여부 판정) | monthly-equivalent (월 환산액 산출)

CLI: python3 calculator.py check --help
"""

import argparse
import json
import sys

# ── 2026년 최저임금 상수 ──────────────────────────────────────────────────────
MIN_WAGE_2026 = 10_320          # 시급 (원) — 최저임금법 §5 고시
MONTHLY_EQUIV_209H = 2_156_880  # 월 환산액 (209시간, 주40H 기준)
DAILY_8H = 82_560               # 일급 (8시간 기준)
WEEKS_PER_MONTH = 4.345         # 월평균 주수 (365 / 12 / 7)


def _monthly_hours(weekly_hours: float) -> float:
    """
    월 소정근로시간 산출.
    - 주 40시간: 고시 기준 209시간 고정 (최저임금 월 환산 2,156,880원의 기준)
    - 주 40시간 미만: 209시간 × (weekly_hours / 40) 비례 계산
      (주휴 포함 비례: 단시간근로자 주휴수당은 주 15시간 이상 시 비례 발생)
    - 주 15시간 미만: 주휴 미발생 → weekly_hours × WEEKS_PER_MONTH
    """
    if weekly_hours <= 0:
        raise ValueError("주간 근로시간은 0보다 커야 합니다.")
    if weekly_hours >= 40:
        # 고시 기준 209시간 (주40H 법정 기준)
        return 209.0
    if weekly_hours < 15:
        # 주휴 미발생 — 소정근로시간만
        return weekly_hours * WEEKS_PER_MONTH
    # 주 15시간 이상 단시간: 209시간 비례
    return 209.0 * (weekly_hours / 40)


def check_violation(
    monthly_wage: int,
    weekly_hours: float = 40.0,
    regular_bonus: int = 0,
    welfare_pay: int = 0,
) -> dict:
    """
    최저임금 위반 여부 판정.

    산입범위:
      - monthly_wage  : 기본급 (소정근로 대가, 매월 지급) — 필수
      - regular_bonus : 매월 지급 정기상여금 — 선택 (분기/연간은 산입 제외)
      - welfare_pay   : 매월 지급 복리후생비 (식대·교통비·숙박비 등) — 선택

    산입 제외 (입력 분리):
      - 연장·야간·휴일 근로수당 (소정근로 외 가산분)
      - 분기·반기·연간 상여금
      - 현물급여
    """
    # 산입범위 합산 임금
    included_wage = monthly_wage + regular_bonus + welfare_pay

    # 월 소정근로시간
    monthly_hours = _monthly_hours(weekly_hours)

    # 시간당 실임금 (원 단위 절사)
    hourly_rate_actual = int(included_wage / monthly_hours)

    # 위반 판정
    violation = hourly_rate_actual < MIN_WAGE_2026
    shortfall_per_hour = max(0, MIN_WAGE_2026 - hourly_rate_actual)
    monthly_shortfall = int(shortfall_per_hour * monthly_hours)

    return {
        "mode": "check",
        "year": 2026,
        "inputs": {
            "monthly_wage": monthly_wage,
            "regular_bonus_monthly": regular_bonus,
            "welfare_pay_monthly": welfare_pay,
            "weekly_hours": weekly_hours,
        },
        "included_wage_total": included_wage,
        "monthly_hours": round(monthly_hours, 2),
        "hourly_rate_actual": hourly_rate_actual,
        "minimum_wage_2026": MIN_WAGE_2026,
        "violation": violation,
        "shortfall_per_hour": shortfall_per_hour,
        "monthly_shortfall": monthly_shortfall,
        "verdict": "⚠️ 최저임금 위반" if violation else "✅ 최저임금 충족",
        "calculation": (
            f"산입임금 {included_wage:,}원"
            f" ÷ {round(monthly_hours, 2)}시간"
            f" = 시간당 {hourly_rate_actual:,}원"
            f" (기준 {MIN_WAGE_2026:,}원)"
            + (f" → 시간당 {shortfall_per_hour:,}원 부족, 월 {monthly_shortfall:,}원 미달" if violation else " → 충족")
        ),
        "disclaimer": (
            "수습기간(최초 3개월, 1년 이상 계약) 90% 감액·단순노무직 예외·감시단속 근로자 특례는 "
            "본 계산기 미반영 — 해당 케이스는 별도 확인 필요."
        ),
    }


def monthly_equivalent(
    hourly_wage: int,
    weekly_hours: float = 40.0,
) -> dict:
    """
    임의 시급의 월 환산액 산출.
    월환산 = 시급 × 월 소정근로시간
    """
    hours = _monthly_hours(weekly_hours)
    equiv = int(hourly_wage * hours)

    return {
        "mode": "monthly-equivalent",
        "hourly_wage": hourly_wage,
        "weekly_hours": weekly_hours,
        "monthly_hours": round(hours, 2),
        "monthly_equivalent": equiv,
        "reference_minimum_wage_2026": MIN_WAGE_2026,
        "reference_monthly_equiv_209h": MONTHLY_EQUIV_209H,
        "calculation": (
            f"{hourly_wage:,}원 × {round(hours, 2)}시간 = {equiv:,}원/월"
        ),
    }


# ── 검증 시나리오 (python3 calculator.py --run-tests) ──────────────────────
def _run_tests() -> None:
    """
    팩트체크 완료 시나리오 4개 검증.
    실패 시 AssertionError 발생.
    """
    # 시나리오 1: 월 2,000,000 / 주40H → 위반 (시간당 751원 부족)
    r1 = check_violation(monthly_wage=2_000_000, weekly_hours=40)
    assert r1["violation"] is True, f"시나리오1 위반 기대: {r1}"
    assert r1["shortfall_per_hour"] == 751, (
        f"시나리오1 시간당 부족 751원 기대, 실제: {r1['shortfall_per_hour']}"
    )
    # 월 부족: 751 × 209 = 156,959원 (int 절사 기준)
    assert r1["monthly_shortfall"] == 156_959, (
        f"시나리오1 월 부족 156,959원 기대, 실제: {r1['monthly_shortfall']}"
    )

    # 시나리오 2: 월 2,156,880 / 주40H → 정확히 최저임금 (미위반)
    r2 = check_violation(monthly_wage=2_156_880, weekly_hours=40)
    assert r2["violation"] is False, f"시나리오2 미위반 기대: {r2}"
    assert r2["hourly_rate_actual"] == MIN_WAGE_2026, (
        f"시나리오2 시간당 {MIN_WAGE_2026}원 기대, 실제: {r2['hourly_rate_actual']}"
    )

    # 시나리오 3: 기본급 1,900,000 + 정기상여 200,000 + 식대 100,000 / 주40H → 미위반
    r3 = check_violation(
        monthly_wage=1_900_000,
        weekly_hours=40,
        regular_bonus=200_000,
        welfare_pay=100_000,
    )
    assert r3["violation"] is False, f"시나리오3 미위반 기대: {r3}"
    # 시간당 실임금: 2,200,000 / 209 ≈ 10,526
    assert r3["hourly_rate_actual"] >= 10_500, (
        f"시나리오3 시간당 약 10,526원 기대, 실제: {r3['hourly_rate_actual']}"
    )

    # 시나리오 4: 월 1,800,000 / 주30H → 209 × 30/40 = 156.75H → 시급 11,483 → 미위반
    # (주휴 비례 포함 기준: 단시간근로자도 주15H 이상이면 주휴 비례 발생)
    r4 = check_violation(monthly_wage=1_800_000, weekly_hours=30)
    assert r4["violation"] is False, f"시나리오4 미위반 기대: {r4}"
    assert r4["hourly_rate_actual"] == 11_483, (
        f"시나리오4 시간당 11,483원 기대, 실제: {r4['hourly_rate_actual']}"
    )

    print(json.dumps({
        "status": "all_tests_passed",
        "scenarios": [
            {"id": 1, "hourly_rate_actual": r1["hourly_rate_actual"], "violation": r1["violation"],
             "shortfall_per_hour": r1["shortfall_per_hour"], "monthly_shortfall": r1["monthly_shortfall"]},
            {"id": 2, "hourly_rate_actual": r2["hourly_rate_actual"], "violation": r2["violation"]},
            {"id": 3, "hourly_rate_actual": r3["hourly_rate_actual"], "violation": r3["violation"]},
            {"id": 4, "hourly_rate_actual": r4["hourly_rate_actual"], "violation": r4["violation"]},
        ],
    }, ensure_ascii=False, indent=2))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="최저임금 위반 체크기 (2026년 10,320원 기준)",
    )
    parser.add_argument("--run-tests", action="store_true",
                        help="팩트체크 검증 시나리오 4개 실행")

    sub = parser.add_subparsers(dest="cmd")

    # check 서브커맨드
    p_check = sub.add_parser("check", help="최저임금 위반 여부 판정")
    p_check.add_argument("--monthly-wage", type=int, required=True,
                         help="기본급 (원, 월 지급액)")
    p_check.add_argument("--weekly-hours", type=float, default=40.0,
                         help="주간 소정근로시간 (기본 40)")
    p_check.add_argument("--regular-bonus", type=int, default=0,
                         help="매월 지급 정기상여금 (원, 분기·연간 제외)")
    p_check.add_argument("--welfare-pay", type=int, default=0,
                         help="매월 지급 복리후생비 — 식대·교통비·숙박비 (원)")

    # monthly-equivalent 서브커맨드
    p_me = sub.add_parser("monthly-equivalent", help="시급 → 월 환산액 산출")
    p_me.add_argument("--hourly-wage", type=int, required=True,
                      help="시급 (원)")
    p_me.add_argument("--weekly-hours", type=float, default=40.0,
                      help="주간 소정근로시간 (기본 40)")

    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.run_tests:
        _run_tests()
        return 0

    if args.cmd is None:
        parser.print_help()
        return 2

    if args.cmd == "check":
        result = check_violation(
            monthly_wage=args.monthly_wage,
            weekly_hours=args.weekly_hours,
            regular_bonus=args.regular_bonus,
            welfare_pay=args.welfare_pay,
        )
    elif args.cmd == "monthly-equivalent":
        result = monthly_equivalent(
            hourly_wage=args.hourly_wage,
            weekly_hours=args.weekly_hours,
        )
    else:
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
