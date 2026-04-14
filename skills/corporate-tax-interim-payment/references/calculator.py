#!/usr/bin/env python3
"""
법인세 중간예납 계산기 — 법인세법 §63

서브커맨드:
  standard        방법1 (직전사업연도 기준방식)
  estimation      방법2 (가결산 방식)
  compare         두 방식 결과 비교 + 권장안
  exemption-check 면제 대상 판정

공식:
  [방법1] interim = (prior_tax - credits - withholding - occasional) × (current_months / prior_months)
  [방법2] 연환산 과세표준 = interim_taxable × (12 / current_months)
         연환산 산출세액 = 누진세율 (법인세 §55) 적용
         중간예납 산출세액 = 연환산 세액 × (current_months / 12)
         납부세액 = 산출 - 공제감면 - 원천징수

CLI:
  python3 calculator.py standard --prior-tax 50000000 --prior-months 12 --current-period-months 6
  python3 calculator.py estimation --interim-taxable-income 150000000 --current-period-months 6
  python3 calculator.py compare --prior-tax 50000000 --interim-taxable-income 100000000
  python3 calculator.py exemption-check --prior-tax 0

주의:
  - 표준 라이브러리만 사용 (argparse, json, sys)
  - 모든 금액은 int (원 단위 절사)
  - JSON 출력: ensure_ascii=False, indent=2
"""

import argparse
import json
import sys

# ─── 상수 (법인세법 §55 — income-tax 스킬과 일관) ─────────────────────────────
# 각 튜플: (상한 과세표준, 세율, 누진공제액)
CORPORATE_TAX_BRACKETS = [
    (200_000_000,          0.09,              0),
    (20_000_000_000,       0.19,     20_000_000),
    (300_000_000_000,      0.21,    420_000_000),
    (float("inf"),         0.24,  9_420_000_000),
]

DISCLAIMER = (
    "실제 신고는 홈택스·세무서 안내 확인 필요. "
    "원천징수·수시부과·공제감면·가산세 반영 시 차이 발생. "
    "면제 기준 세부 요건은 최신 국세청 안내 우선."
)

DUE_DATE_RULE = "중간예납기간 종료일로부터 2개월 이내"
EXAMPLE_DUE_DATE = "사업연도 1월 1일~12월 31일 기준 8월 31일"


# ─── 내부 유틸 ─────────────────────────────────────────────────────────────────

def _corporate_tax(taxable_income: int) -> tuple[int, list[str]]:
    """누진세율 적용 산출세액 + 사용된 구간 라벨 반환."""
    if taxable_income <= 0:
        return 0, []
    for upper, rate, deduction in CORPORATE_TAX_BRACKETS:
        if taxable_income <= upper:
            tax = int(taxable_income * rate - deduction)
            tax = max(tax, 0)
            labels = _bracket_labels_used(taxable_income)
            return tax, labels
    return 0, []


def _bracket_labels_used(taxable_income: int) -> list[str]:
    """과세표준이 걸친 구간 설명 리스트."""
    labels = []
    thresholds = [
        (200_000_000,          "2억 이하 9%"),
        (20_000_000_000,       "2억 초과 ~ 200억 이하 19%"),
        (300_000_000_000,      "200억 초과 ~ 3000억 이하 21%"),
        (float("inf"),         "3000억 초과 24%"),
    ]
    prev = 0
    for upper, label in thresholds:
        if taxable_income > prev:
            labels.append(label)
        if taxable_income <= upper:
            break
        prev = upper
    return labels


# ─── 핵심 계산 함수 ────────────────────────────────────────────────────────────

def calc_standard(
    prior_tax: int,
    prior_credits: int = 0,
    prior_withholding: int = 0,
    prior_occasional_tax: int = 0,
    prior_months: int = 12,
    current_period_months: int = 6,
) -> dict:
    """방법1 (직전사업연도 기준방식)."""
    if prior_months <= 0:
        return {"error": "prior_months must be positive"}
    if current_period_months <= 0:
        return {"error": "current_period_months must be positive"}

    base_amount = prior_tax - prior_credits - prior_withholding - prior_occasional_tax
    ratio = current_period_months / prior_months
    interim_payment = max(int(base_amount * ratio), 0)

    return {
        "method": "standard",
        "method_name": "방법1 (직전사업연도 기준방식)",
        "prior_tax": prior_tax,
        "prior_credits": prior_credits,
        "prior_withholding": prior_withholding,
        "prior_occasional_tax": prior_occasional_tax,
        "prior_months": prior_months,
        "current_period_months": current_period_months,
        "base_amount": base_amount,
        "ratio": round(ratio, 4),
        "interim_payment": interim_payment,
        "due_date_rule": DUE_DATE_RULE,
        "example_due_date": EXAMPLE_DUE_DATE,
        "formula": "(직전산출세액 - 공제·감면·원천·수시부과) × (중간예납월수 / 직전사업연도월수)",
        "legal_basis": "법인세법 §63 (중간예납)",
        "disclaimer": DISCLAIMER,
    }


def calc_estimation(
    interim_taxable_income: int,
    current_period_months: int = 6,
    credits: int = 0,
    withholding: int = 0,
) -> dict:
    """방법2 (가결산 방식)."""
    if current_period_months <= 0:
        return {"error": "current_period_months must be positive"}
    if interim_taxable_income < 0:
        return {"error": "interim_taxable_income must be non-negative"}

    # 1) 연환산 과세표준
    annualize_factor = 12 / current_period_months
    annualized_taxable = int(interim_taxable_income * annualize_factor)

    # 2) 연환산 산출세액
    annualized_tax, brackets_used = _corporate_tax(annualized_taxable)

    # 3) 중간예납 산출세액 (연환산 세액 × 기간비율)
    period_ratio = current_period_months / 12
    interim_tax_before_credits = int(annualized_tax * period_ratio)

    # 4) 납부세액 = 산출 - 공제감면 - 원천징수
    interim_payment = max(interim_tax_before_credits - credits - withholding, 0)

    return {
        "method": "estimation",
        "method_name": "방법2 (가결산 방식)",
        "interim_taxable_income": interim_taxable_income,
        "current_period_months": current_period_months,
        "annualized_taxable": annualized_taxable,
        "annualized_tax": annualized_tax,
        "interim_tax_before_credits": interim_tax_before_credits,
        "credits": credits,
        "withholding": withholding,
        "interim_payment": interim_payment,
        "method_formula": "중간예납기간 과세표준 × (12 / 중간예납월수) × 세율 × (중간예납월수 / 12) - 공제감면",
        "tax_brackets_used": brackets_used,
        "due_date_rule": DUE_DATE_RULE,
        "example_due_date": EXAMPLE_DUE_DATE,
        "legal_basis": "법인세법 §63, §55",
        "disclaimer": DISCLAIMER,
    }


def calc_compare(
    prior_tax: int,
    interim_taxable_income: int,
    prior_credits: int = 0,
    prior_withholding: int = 0,
    prior_occasional_tax: int = 0,
    prior_months: int = 12,
    current_period_months: int = 6,
    credits: int = 0,
    withholding: int = 0,
) -> dict:
    """두 방식 비교."""
    std = calc_standard(
        prior_tax=prior_tax,
        prior_credits=prior_credits,
        prior_withholding=prior_withholding,
        prior_occasional_tax=prior_occasional_tax,
        prior_months=prior_months,
        current_period_months=current_period_months,
    )
    est = calc_estimation(
        interim_taxable_income=interim_taxable_income,
        current_period_months=current_period_months,
        credits=credits,
        withholding=withholding,
    )

    std_amt = std.get("interim_payment", 0)
    est_amt = est.get("interim_payment", 0)

    if est_amt < std_amt:
        recommended = "estimation"
        savings = std_amt - est_amt
        rationale = (
            f"가결산 방식이 {savings:,}원 적어 유리. "
            "단, 가결산 작성 추가 비용·노력 감안 필요."
        )
    elif std_amt < est_amt:
        recommended = "standard"
        savings = est_amt - std_amt
        rationale = (
            f"직전년도 기준방식이 {savings:,}원 적어 유리. "
            "가결산 작성 부담 없이 간편한 방식."
        )
    else:
        recommended = "either"
        savings = 0
        rationale = "두 방식 결과 동일. 간편한 방법1(직전기준) 선택 무난."

    return {
        "mode": "compare",
        "standard": std,
        "estimation": est,
        "savings": savings,
        "recommended": recommended,
        "rationale": rationale,
        "disclaimer": DISCLAIMER,
    }


def calc_exemption_check(
    prior_tax: int,
    is_newly_incorporated: bool = False,
    prior_tax_finalized: bool = True,
) -> dict:
    """면제 대상 판정."""
    reasons = []
    if prior_tax == 0:
        reasons.append("직전 사업연도 산출세액 없음")
    if not prior_tax_finalized:
        reasons.append("중간예납기한까지 직전 세액 미확정")
    if is_newly_incorporated:
        reasons.append("분할·신설법인 최초 사업연도")

    exempt = len(reasons) > 0

    return {
        "mode": "exemption-check",
        "exempt": exempt,
        "reasons": reasons,
        "prior_tax": prior_tax,
        "is_newly_incorporated": is_newly_incorporated,
        "prior_tax_finalized": prior_tax_finalized,
        "legal_basis": "법인세법 §63① 단서 및 관련 규정",
        "disclaimer": DISCLAIMER,
    }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="법인세 중간예납 계산기 (법인세법 §63)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # standard
    p_std = sub.add_parser("standard", help="방법1 (직전사업연도 기준방식)")
    p_std.add_argument("--prior-tax", type=int, required=True,
                       help="직전사업연도 산출세액 (원)")
    p_std.add_argument("--prior-credits", type=int, default=0,
                       help="직전연도 공제·감면세액 (원)")
    p_std.add_argument("--prior-withholding", type=int, default=0,
                       help="직전연도 원천징수세액 (원)")
    p_std.add_argument("--prior-occasional-tax", type=int, default=0,
                       help="직전연도 수시부과세액 (원)")
    p_std.add_argument("--prior-months", type=int, default=12,
                       help="직전사업연도 월수 (default 12)")
    p_std.add_argument("--current-period-months", type=int, default=6,
                       help="중간예납기간 월수 (default 6)")

    # estimation
    p_est = sub.add_parser("estimation", help="방법2 (가결산 방식)")
    p_est.add_argument("--interim-taxable-income", type=int, required=True,
                       help="중간예납기간 추정 과세표준 (원)")
    p_est.add_argument("--current-period-months", type=int, default=6,
                       help="중간예납기간 월수 (default 6)")
    p_est.add_argument("--credits", type=int, default=0,
                       help="공제·감면세액 (원)")
    p_est.add_argument("--withholding", type=int, default=0,
                       help="원천징수세액 (원)")

    # compare
    p_cmp = sub.add_parser("compare", help="두 방식 비교 + 권장안")
    p_cmp.add_argument("--prior-tax", type=int, required=True)
    p_cmp.add_argument("--prior-credits", type=int, default=0)
    p_cmp.add_argument("--prior-withholding", type=int, default=0)
    p_cmp.add_argument("--prior-occasional-tax", type=int, default=0)
    p_cmp.add_argument("--prior-months", type=int, default=12)
    p_cmp.add_argument("--interim-taxable-income", type=int, required=True)
    p_cmp.add_argument("--current-period-months", type=int, default=6)
    p_cmp.add_argument("--credits", type=int, default=0)
    p_cmp.add_argument("--withholding", type=int, default=0)

    # exemption-check
    p_ex = sub.add_parser("exemption-check", help="면제 대상 판정")
    p_ex.add_argument("--prior-tax", type=int, required=True,
                      help="직전사업연도 산출세액 (원)")
    p_ex.add_argument("--is-newly-incorporated", action="store_true",
                      help="신설법인 여부 (flag)")
    p_ex.add_argument("--prior-tax-finalized", type=str, default="true",
                      choices=["true", "false"],
                      help="직전년도 세액 확정 여부 (default true)")

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "standard":
        result = calc_standard(
            prior_tax=args.prior_tax,
            prior_credits=args.prior_credits,
            prior_withholding=args.prior_withholding,
            prior_occasional_tax=args.prior_occasional_tax,
            prior_months=args.prior_months,
            current_period_months=args.current_period_months,
        )
    elif args.cmd == "estimation":
        result = calc_estimation(
            interim_taxable_income=args.interim_taxable_income,
            current_period_months=args.current_period_months,
            credits=args.credits,
            withholding=args.withholding,
        )
    elif args.cmd == "compare":
        result = calc_compare(
            prior_tax=args.prior_tax,
            prior_credits=args.prior_credits,
            prior_withholding=args.prior_withholding,
            prior_occasional_tax=args.prior_occasional_tax,
            prior_months=args.prior_months,
            interim_taxable_income=args.interim_taxable_income,
            current_period_months=args.current_period_months,
            credits=args.credits,
            withholding=args.withholding,
        )
    elif args.cmd == "exemption-check":
        result = calc_exemption_check(
            prior_tax=args.prior_tax,
            is_newly_incorporated=args.is_newly_incorporated,
            prior_tax_finalized=(args.prior_tax_finalized == "true"),
        )
    else:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
