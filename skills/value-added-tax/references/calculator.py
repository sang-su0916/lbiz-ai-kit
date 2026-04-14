#!/usr/bin/env python3
"""
부가가치세 계산기 — 부가가치세법 §30 / §61 / §63② / §69

서브커맨드:
  general      일반과세 납부세액 (매출세액 - 매입세액)
  simplified   간이과세 납부세액 (공급대가 × 업종별 부가가치율 × 10%)
  eligibility  간이과세 적격 판정
  compare      일반 vs 간이 비교 + 권장안

CLI:
  python3 calculator.py general --sales-supply 100000000 --purchase-supply 60000000
  python3 calculator.py simplified --supply-price 80000000 --industry retail
  python3 calculator.py eligibility --prior-year-supply-price 90000000
  python3 calculator.py compare --sales-supply 100000000 --purchase-supply 60000000 \
    --supply-price 110000000 --industry retail

주의:
  - 표준 라이브러리만 사용 (argparse, json, sys)
  - 모든 금액은 int (원 단위 절사)
  - JSON 출력: ensure_ascii=False, indent=2
"""

import argparse
import json
import sys

# ─── 상수 ─────────────────────────────────────────────────────────────────────

VAT_RATE = 0.10  # 부가가치세법 §30 — 세율 10%

# 간이과세 업종별 부가가치율 (부가가치세법 §63②, 2021.7.1 이후)
INDUSTRY_RATES = {
    "retail": {
        "rate": 0.15,
        "label": "소매업·재생용 재료수집 및 판매업·음식점업",
    },
    "manufacturing": {
        "rate": 0.20,
        "label": "제조업·농업·임업·어업·소화물 전문 운송업",
    },
    "lodging": {
        "rate": 0.25,
        "label": "숙박업",
    },
    "construction": {
        "rate": 0.30,
        "label": "건설업·운수 및 창고업·정보통신업",
    },
    "service": {
        "rate": 0.40,
        "label": "금융·보험·부동산·전문과학기술·사업지원·기타서비스",
    },
}

# 간이과세 기준: 직전연도 공급대가 1억 400만원 미만 (2024.7.1 이후, §61)
SIMPLIFIED_THRESHOLD = 104_000_000

# 간이과세 납부의무 면제: 해당 과세기간 공급대가 4,800만원 미만 (§69)
PAYMENT_EXEMPTION_THRESHOLD = 48_000_000

# 간이과세 매입세액공제율: 매입공급가액 × 0.5%
SIMPLIFIED_INPUT_CREDIT_RATE = 0.005

DISCLAIMER = (
    "2026년 기준 부가가치세법. "
    "2024.7.1 이후 간이과세 기준 1억 400만원 · 업종별 부가가치율 2021.7.1 기준. "
    "법 개정 주기 짧으니 홈택스 최신 안내 확인. "
    "매입세액 불공제·의제매입세액·가산세·과세기간 분할 반영 시 차이 발생. "
    "실제 신고는 세무 전문가 확인 권장."
)


# ─── 핵심 계산 함수 ────────────────────────────────────────────────────────────

def calc_general(
    sales_supply: int,
    purchase_supply: int,
    zero_rate_sales: int = 0,
    exempt_sales: int = 0,
) -> dict:
    """일반과세 납부세액 = 매출세액 - 매입세액."""
    if sales_supply < 0 or purchase_supply < 0:
        return {"error": "sales_supply / purchase_supply must be non-negative"}

    sales_vat = int(sales_supply * VAT_RATE)
    purchase_vat = int(purchase_supply * VAT_RATE)
    payable_vat = sales_vat - purchase_vat  # 환급(음수) 가능

    return {
        "mode": "general",
        "sales_supply": sales_supply,
        "sales_vat": sales_vat,
        "purchase_supply": purchase_supply,
        "purchase_vat": purchase_vat,
        "zero_rate_sales": zero_rate_sales,
        "exempt_sales": exempt_sales,
        "payable_vat": payable_vat,
        "formula": "납부세액 = 매출세액(공급가액×10%) - 매입세액(공급가액×10%)",
        "legal_basis": "부가가치세법 §30",
        "disclaimer": DISCLAIMER,
    }


def calc_simplified(
    supply_price: int,
    industry: str,
    purchase_supply: int = 0,
    prior_year_supply_price: int = 0,
) -> dict:
    """간이과세 납부세액 = 공급대가 × 부가가치율 × 10% - 매입세액공제."""
    if supply_price < 0:
        return {"error": "supply_price must be non-negative"}
    if industry not in INDUSTRY_RATES:
        return {
            "error": f"unknown industry '{industry}'. "
            f"choices: {list(INDUSTRY_RATES.keys())}"
        }

    info = INDUSTRY_RATES[industry]
    value_added_rate = info["rate"]
    industry_label = info["label"]

    output_tax_before_credits = int(supply_price * value_added_rate * VAT_RATE)
    input_tax_credit = int(purchase_supply * SIMPLIFIED_INPUT_CREDIT_RATE)

    # §69 납부의무 면제 (과세기간 공급대가 4,800만원 미만)
    exempt_from_payment = supply_price < PAYMENT_EXEMPTION_THRESHOLD
    if exempt_from_payment:
        payable_vat = 0
        exempt_reason = (
            f"해당 과세기간 공급대가 {supply_price:,}원이 "
            f"납부의무 면제 기준 {PAYMENT_EXEMPTION_THRESHOLD:,}원 미만 (§69)"
        )
    else:
        payable_vat = max(output_tax_before_credits - input_tax_credit, 0)
        exempt_reason = None

    return {
        "mode": "simplified",
        "supply_price": supply_price,
        "industry": industry,
        "industry_label": industry_label,
        "value_added_rate": value_added_rate,
        "tax_rate": VAT_RATE,
        "output_tax_before_credits": output_tax_before_credits,
        "input_tax_credit": input_tax_credit,
        "payable_vat": payable_vat,
        "prior_year_supply_price": prior_year_supply_price,
        "formula": "납부세액 = 공급대가 × 부가가치율 × 10% - 매입세액공제",
        "exempt_from_payment": exempt_from_payment,
        "exempt_reason": exempt_reason,
        "legal_basis": "부가가치세법 §63②",
        "disclaimer": DISCLAIMER,
    }


def calc_eligibility(
    prior_year_supply_price: int,
    is_corporate: bool = False,
    is_restricted_industry: bool = False,
) -> dict:
    """간이과세 적격 판정 (§61)."""
    if prior_year_supply_price < 0:
        return {"error": "prior_year_supply_price must be non-negative"}

    reasons = []
    eligible = True

    # 법인 체크
    if is_corporate:
        reasons.append("법인사업자 — 간이과세 불가 (개인사업자 전용)")
        eligible = False
    else:
        reasons.append("개인사업자")

    # 직전연도 공급대가 기준
    if prior_year_supply_price >= SIMPLIFIED_THRESHOLD:
        reasons.append(
            f"직전연도 공급대가 {prior_year_supply_price:,}원이 "
            f"간이과세 기준 1억 400만원({SIMPLIFIED_THRESHOLD:,}원) 이상"
        )
        eligible = False
    else:
        reasons.append("직전연도 공급대가 1억 400만원 미만")

    # 배제업종
    if is_restricted_industry:
        reasons.append("간이과세 배제업종 해당 — 부적격")
        eligible = False
    else:
        reasons.append("제외업종 해당 없음")

    return {
        "mode": "eligibility",
        "prior_year_supply_price": prior_year_supply_price,
        "is_corporate": is_corporate,
        "is_restricted_industry": is_restricted_industry,
        "threshold": SIMPLIFIED_THRESHOLD,
        "eligible": eligible,
        "reasons": reasons,
        "legal_basis": "부가가치세법 §61",
        "disclaimer": DISCLAIMER,
    }


def calc_compare(
    sales_supply: int,
    purchase_supply: int,
    supply_price: int,
    industry: str,
    zero_rate_sales: int = 0,
    exempt_sales: int = 0,
    simplified_purchase_supply: int = 0,
    prior_year_supply_price: int = 0,
) -> dict:
    """일반 vs 간이 비교."""
    gen = calc_general(
        sales_supply=sales_supply,
        purchase_supply=purchase_supply,
        zero_rate_sales=zero_rate_sales,
        exempt_sales=exempt_sales,
    )
    sim = calc_simplified(
        supply_price=supply_price,
        industry=industry,
        purchase_supply=simplified_purchase_supply,
        prior_year_supply_price=prior_year_supply_price,
    )

    gen_amt = gen.get("payable_vat", 0)
    sim_amt = sim.get("payable_vat", 0)
    difference = abs(gen_amt - sim_amt)

    if sim_amt < gen_amt:
        recommended = "simplified"
        rationale = (
            f"간이과세가 일반 대비 {difference:,}원 절감. "
            "단, 매입세액공제·환급 여부에 따라 실제 유리성 달라짐."
        )
    elif gen_amt < sim_amt:
        recommended = "general"
        rationale = (
            f"일반과세가 간이 대비 {difference:,}원 절감. "
            "매입 비중이 크거나 매입세액 환급이 가능한 경우 일반과세 유리."
        )
    else:
        recommended = "either"
        rationale = "두 방식 납부세액 동일. 환급 가능 여부 등 부가 요소로 선택."

    return {
        "mode": "compare",
        "general": gen,
        "simplified": sim,
        "difference": difference,
        "recommended": recommended,
        "rationale": rationale,
        "disclaimer": DISCLAIMER,
    }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="부가가치세 계산기 (부가가치세법 §30 / §61 / §63② / §69)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # general
    p_gen = sub.add_parser("general", help="일반과세 납부세액")
    p_gen.add_argument("--sales-supply", type=int, required=True,
                       help="매출 공급가액 (부가세 제외, 원)")
    p_gen.add_argument("--purchase-supply", type=int, required=True,
                       help="매입 공급가액 (부가세 제외, 원)")
    p_gen.add_argument("--zero-rate-sales", type=int, default=0,
                       help="영세율 매출 (원, default 0)")
    p_gen.add_argument("--exempt-sales", type=int, default=0,
                       help="면세 매출 (원, default 0)")

    # simplified
    p_sim = sub.add_parser("simplified", help="간이과세 납부세액")
    p_sim.add_argument("--supply-price", type=int, required=True,
                       help="공급대가 (부가세 포함 총액, 원)")
    p_sim.add_argument("--industry", type=str, required=True,
                       choices=list(INDUSTRY_RATES.keys()),
                       help="업종 코드 (retail/manufacturing/lodging/construction/service)")
    p_sim.add_argument("--purchase-supply", type=int, default=0,
                       help="매입 공급가액 (원, 매입세액공제 0.5%)")
    p_sim.add_argument("--prior-year-supply-price", type=int, default=0,
                       help="직전연도 공급대가 (원, 간이 적격 참고용)")

    # eligibility
    p_elig = sub.add_parser("eligibility", help="간이과세 적격 판정")
    p_elig.add_argument("--prior-year-supply-price", type=int, required=True,
                        help="직전연도 공급대가 (원)")
    p_elig.add_argument("--is-corporate", action="store_true",
                        help="법인사업자 여부 (flag, 법인은 간이과세 불가)")
    p_elig.add_argument("--is-restricted-industry", action="store_true",
                        help="간이과세 배제업종 여부 (flag)")

    # compare
    p_cmp = sub.add_parser("compare", help="일반 vs 간이 비교 + 권장안")
    p_cmp.add_argument("--sales-supply", type=int, required=True,
                       help="[일반] 매출 공급가액 (원)")
    p_cmp.add_argument("--purchase-supply", type=int, required=True,
                       help="[일반] 매입 공급가액 (원)")
    p_cmp.add_argument("--zero-rate-sales", type=int, default=0)
    p_cmp.add_argument("--exempt-sales", type=int, default=0)
    p_cmp.add_argument("--supply-price", type=int, required=True,
                       help="[간이] 공급대가 (원)")
    p_cmp.add_argument("--industry", type=str, required=True,
                       choices=list(INDUSTRY_RATES.keys()),
                       help="[간이] 업종 코드")
    p_cmp.add_argument("--simplified-purchase-supply", type=int, default=0,
                       help="[간이] 매입 공급가액 (원)")
    p_cmp.add_argument("--prior-year-supply-price", type=int, default=0)

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "general":
        result = calc_general(
            sales_supply=args.sales_supply,
            purchase_supply=args.purchase_supply,
            zero_rate_sales=args.zero_rate_sales,
            exempt_sales=args.exempt_sales,
        )
    elif args.cmd == "simplified":
        result = calc_simplified(
            supply_price=args.supply_price,
            industry=args.industry,
            purchase_supply=args.purchase_supply,
            prior_year_supply_price=args.prior_year_supply_price,
        )
    elif args.cmd == "eligibility":
        result = calc_eligibility(
            prior_year_supply_price=args.prior_year_supply_price,
            is_corporate=args.is_corporate,
            is_restricted_industry=args.is_restricted_industry,
        )
    elif args.cmd == "compare":
        result = calc_compare(
            sales_supply=args.sales_supply,
            purchase_supply=args.purchase_supply,
            supply_price=args.supply_price,
            industry=args.industry,
            zero_rate_sales=args.zero_rate_sales,
            exempt_sales=args.exempt_sales,
            simplified_purchase_supply=args.simplified_purchase_supply,
            prior_year_supply_price=args.prior_year_supply_price,
        )
    else:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
