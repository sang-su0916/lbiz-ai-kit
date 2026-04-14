#!/usr/bin/env python3
"""
현금흐름표 분석 계산기

목적:
  - 영업·투자·재무 현금흐름 입력 → 8가지 CF 패턴 분류
  - 영업CF 품질지표 (OCF/순이익, OCF/매출)
  - 잉여현금흐름 (FCF = OCF - CapEx)
  - 위험 플래그 + 권고사항 자동 생성

모드: analyze

CLI:
  python3 calculator.py analyze \
    --operating-cf 80000000 \
    --investing-cf -50000000 \
    --financing-cf -20000000 \
    --net-income 70000000 \
    --capex 50000000 \
    --revenue 500000000

주의:
  - 표준 라이브러리만 사용 (argparse, json, sys)
  - 일반기업회계기준 제5장 / K-IFRS 제1007호 기준
  - JSON 출력: ensure_ascii=False, indent=2
"""

import argparse
import json
import sys

DISCLAIMER = (
    "본 분석은 현금흐름표 단년 참고치이며, 업종·회계기준(K-IFRS vs. "
    "일반기업회계기준)·이자배당 분류 방침에 따라 해석이 달라집니다. "
    "실제 투자·대출·M&A 판단은 회계사·재무전문가 검토가 필요합니다."
)


# ─── 패턴 분류 ─────────────────────────────────────────────────────────────────

def _sign(x: float) -> str:
    """부호를 '+' / '-' / '0' 으로 반환 (0은 +로 취급)."""
    if x > 0:
        return "+"
    if x < 0:
        return "-"
    return "+"  # 0은 양수로 분류 (관례)


# (O, I, F) → (패턴 키워드, 설명)
_PATTERN_MAP = {
    ("+", "-", "-"): ("안정형", "영업 +, 투자 -, 재무 - : 성숙기 우량기업 전형 — 영업이익으로 투자·배당/차입금 상환"),
    ("+", "-", "+"): ("성장형", "영업 +, 투자 -, 재무 + : 성장기 기업 — 영업흑자 + 추가 자본조달로 투자 확대"),
    ("+", "+", "-"): ("구조조정형", "영업 +, 투자 +, 재무 - : 구조조정기 — 영업흑자 + 자산매각으로 부채 상환"),
    ("+", "+", "+"): ("유동성비축형", "영업 +, 투자 +, 재무 + : 드물게 좋음 — 자산매각·조달 동시, 대규모 M&A 준비 가능성"),
    ("-", "-", "+"): ("확장형", "영업 -, 투자 -, 재무 + : 초기창업·확장기 — 영업적자를 외부자금으로 보전"),
    ("-", "+", "-"): ("쇠퇴형", "영업 -, 투자 +, 재무 - : 쇠퇴기 — 영업적자를 자산매각으로 충당하며 부채 상환, 위험"),
    ("-", "-", "-"): ("재무위기형", "영업 -, 투자 -, 재무 - : 재무위기 — 현금유출만, 즉시 위기 대응 필요"),
    ("-", "+", "+"): ("심각형", "영업 -, 투자 +, 재무 + : 심각한 위기 — 영업적자 + 자산매각 + 외부조달, 한계기업 징후"),
}


def classify_pattern(ocf: int, icf: int, fcf_fin: int) -> tuple:
    """(O, I, F) 부호 조합 → (패턴명, 설명) 반환."""
    key = (_sign(ocf), _sign(icf), _sign(fcf_fin))
    return _PATTERN_MAP.get(key, ("미분류", f"패턴 {key} — 분류 불가"))


# ─── 품질 지표 ─────────────────────────────────────────────────────────────────

def calc_quality_indicators(ocf: int, net_income: int = None, revenue: int = None) -> dict:
    """OCF 대비 순이익·매출 품질지표 계산."""
    result = {}
    interpretation_bits = []

    if net_income is not None and net_income != 0:
        ratio = round(ocf / net_income, 2)
        result["ocf_to_net_income_ratio"] = ratio
        if net_income > 0:
            if ratio >= 1.0:
                interpretation_bits.append("영업CF가 순이익을 초과 — 현금창출력 양호")
            elif ratio >= 0.5:
                interpretation_bits.append("영업CF가 순이익 대비 양호하나 개선 여지")
            elif ratio >= 0:
                interpretation_bits.append("영업CF가 순이익의 절반 미만 — 분식 징후 점검 필요")
            else:
                interpretation_bits.append("영업CF가 음수 — 장부이익과 현금 괴리 심각")
        else:
            interpretation_bits.append("당기순이익 음수 — OCF/순이익 비율 해석 주의")
    else:
        result["ocf_to_net_income_ratio"] = None

    if revenue is not None and revenue > 0:
        ratio_rev = round(ocf / revenue, 2)
        result["ocf_to_revenue_ratio"] = ratio_rev
        if ratio_rev >= 0.10:
            interpretation_bits.append(f"OCF/매출 {ratio_rev} — 업종 평균 이상 추정")
        elif ratio_rev >= 0:
            interpretation_bits.append(f"OCF/매출 {ratio_rev} — 낮음, 업종 평균 비교 필요")
        else:
            interpretation_bits.append(f"OCF/매출 {ratio_rev} — 영업활동 현금유출")
    else:
        result["ocf_to_revenue_ratio"] = None

    result["quality_interpretation"] = (
        " / ".join(interpretation_bits) if interpretation_bits else "품질지표 해석 불가 (입력 부족)"
    )
    return result


# ─── 위험 플래그 ────────────────────────────────────────────────────────────────

def build_flags(ocf: int, icf: int, fcf_fin: int,
                fcf: int = None, ocf_to_ni: float = None,
                pattern: str = "") -> list:
    flags = []
    if ocf < 0:
        flags.append("영업활동 현금유출 — 수익구조 재점검 시급")
    if ocf_to_ni is not None and 0 < ocf_to_ni < 0.5:
        flags.append("OCF/순이익 < 0.5 — 장부이익 대비 현금 창출 부족, 매출채권·재고 급증 확인")
    if fcf is not None and fcf < 0:
        flags.append("잉여현금흐름(FCF) 음수 — 투자 대비 자체 현금 부족, 외부 의존도 확인")
    if fcf_fin > 0 and ocf < 0:
        flags.append("영업 현금유출을 재무활동으로 보전 — 외부 자본 의존 지속")
    if pattern == "재무위기형":
        flags.append("패턴 (-,-,-) 재무위기 — 긴급 유동성 대책 필요 (자산매각·차입·자본조달 검토)")
    if pattern == "심각형":
        flags.append("패턴 (-,+,+) 한계기업 징후 — 영업·재무 동시 악화")
    if pattern == "쇠퇴형":
        flags.append("패턴 (-,+,-) 쇠퇴기 — 자산매각 의존, 지속 가능성 점검")
    return flags


# ─── 권고사항 ──────────────────────────────────────────────────────────────────

def build_recommendations(ocf: int, icf: int, fcf_fin: int,
                          fcf: int = None, ocf_to_ni: float = None,
                          pattern: str = "") -> list:
    recs = []
    if ocf < 0:
        recs.append("영업활동 자체가 현금 유출 — 수익구조 재점검 시급 (마진·운전자본 관리·원가절감)")
    if ocf_to_ni is not None and 0 < ocf_to_ni < 0.5:
        recs.append("장부이익 대비 실제 현금 창출 부족 — 매출채권·재고 급증 여부 확인 및 회수 강화")
    if fcf is not None and fcf < 0:
        recs.append("투자 대비 자체 현금 부족 — 외부 의존도 확인, CapEx 우선순위 재검토")
    if fcf_fin > 0 and ocf >= 0 and pattern != "성장형":
        recs.append("재무활동 현금유입 지속 — 외부 자본 의존 구조 개선 검토")
    if pattern == "재무위기형":
        recs.append("긴급 유동성 대책 필요 — 자산매각·차입·자본조달 옵션 동시 검토")
    if pattern == "심각형":
        recs.append("한계기업 근접 — 영업개선 단기에 어려우면 구조조정·M&A 검토")
    if pattern == "쇠퇴형":
        recs.append("자산매각 의존 탈피 — 영업현금창출력 회복 또는 사업재편 필요")
    if pattern == "안정형" and not recs:
        recs.append("현 패턴 유지 — 우량 현금흐름, 투자·배당 정책 지속 가능")
    if pattern == "성장형" and not recs:
        recs.append("성장기 정상 패턴 — 단, 재무활동 유입 지속 시 부채비율 모니터링")
    return recs


# ─── 메인 분석 함수 ────────────────────────────────────────────────────────────

def analyze(
    operating_cf: int,
    investing_cf: int,
    financing_cf: int,
    net_income: int = None,
    capex: int = None,
    revenue: int = None,
) -> dict:
    """현금흐름 종합 분석."""

    net_cash_change = operating_cf + investing_cf + financing_cf

    pattern, pattern_desc = classify_pattern(operating_cf, investing_cf, financing_cf)

    free_cash_flow = None
    if capex is not None:
        free_cash_flow = operating_cf - capex

    quality = calc_quality_indicators(operating_cf, net_income, revenue)

    flags = build_flags(
        operating_cf, investing_cf, financing_cf,
        fcf=free_cash_flow,
        ocf_to_ni=quality.get("ocf_to_net_income_ratio"),
        pattern=pattern,
    )
    recommendations = build_recommendations(
        operating_cf, investing_cf, financing_cf,
        fcf=free_cash_flow,
        ocf_to_ni=quality.get("ocf_to_net_income_ratio"),
        pattern=pattern,
    )

    result = {
        "summary": {
            "operating_cf": operating_cf,
            "investing_cf": investing_cf,
            "financing_cf": financing_cf,
            "net_cash_change": net_cash_change,
        },
        "free_cash_flow": free_cash_flow,
        "cf_pattern": pattern,
        "pattern_description": pattern_desc,
        "quality_indicators": quality,
        "flags": flags,
        "recommendations": recommendations,
        "disclaimer": DISCLAIMER,
    }
    return result


# ─── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="현금흐름표 분석 (8패턴 분류 + OCF 품질지표 + FCF + 권고)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("analyze", help="현금흐름 종합 분석")
    p.add_argument("--operating-cf", type=int, required=True,
                   help="영업활동현금흐름 (원, 유출 시 음수)")
    p.add_argument("--investing-cf", type=int, required=True,
                   help="투자활동현금흐름 (원, 유출 시 음수)")
    p.add_argument("--financing-cf", type=int, required=True,
                   help="재무활동현금흐름 (원, 유출 시 음수)")
    p.add_argument("--net-income", type=int, default=None,
                   help="당기순이익 (선택 — 괴리 분석용)")
    p.add_argument("--capex", type=int, default=None,
                   help="자본적지출 (선택 — FCF 계산용)")
    p.add_argument("--revenue", type=int, default=None,
                   help="매출 (선택 — OCF/매출 비율용)")

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "analyze":
        result = analyze(
            operating_cf=args.operating_cf,
            investing_cf=args.investing_cf,
            financing_cf=args.financing_cf,
            net_income=args.net_income,
            capex=args.capex,
            revenue=args.revenue,
        )
    else:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
