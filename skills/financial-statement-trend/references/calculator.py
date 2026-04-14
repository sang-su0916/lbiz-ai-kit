#!/usr/bin/env python3
"""
재무제표 추세·수평·수직 분석기 — 일반기업회계기준 / K-IFRS 재무제표 표시

모드:
  horizontal : 수평분석 (전기 대비 증감액·증감율)
  vertical   : 수직분석 (구성비 — 손익 = 매출 100%, 재무상태 = 총자산 100%)
  trend      : 추세분석 (3~5개년 지수화 + YoY + CAGR)

CLI:
  python3 calculator.py horizontal --revenue-current 500000000 --revenue-prior 450000000 ...
  python3 calculator.py vertical --statement is --revenue 500000000 --cogs 325000000 ...
  python3 calculator.py trend --years "2022,2023,2024,2025,2026" --values "400000000,420000000,450000000,480000000,500000000" --label "매출"

주의:
  - 표준 라이브러리만 사용 (argparse, json, sys)
  - 모든 비율은 percent(%) 소수점 2자리
  - JSON 출력: ensure_ascii=False, indent=2
  - 비율 분석이 아니라 "증감·구성비·추세"에 집중 (financial-ratio와 차별)
"""

import argparse
import json
import sys

DISCLAIMER = (
    "본 분석은 일반기업회계기준·K-IFRS 재무제표 표시 원칙에 따른 참고치입니다. "
    "업종·회계정책·특별손익 여부에 따라 해석이 달라질 수 있으며, "
    "실제 경영 판단은 회계사·재무전문가 검토가 필요합니다."
)


# ─── 내부 유틸 ─────────────────────────────────────────────────────────────────

def _change_rate(current: float, prior: float) -> float | None:
    """전년 대비 증감률(%). 전기 0 또는 음수면 None."""
    if prior is None or prior == 0:
        return None
    return round((current - prior) / abs(prior) * 100, 2)


def _pct(num: float, den: float) -> float | None:
    if den is None or den == 0:
        return None
    return round(num / den * 100, 2)


def _parse_json_or_none(s: str | None) -> dict | None:
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        raise SystemExit(f"JSON 파싱 실패: {e}")


# ─── horizontal (수평분석) ─────────────────────────────────────────────────────

_SIMPLE_ITEM_ARGS = [
    # (key, label)
    ("revenue", "매출"),
    ("cogs", "매출원가"),
    ("gross_profit", "매출총이익"),
    ("sga", "판관비"),
    ("operating_income", "영업이익"),
    ("net_income", "당기순이익"),
    ("total_assets", "총자산"),
    ("total_liabilities", "총부채"),
    ("total_equity", "자기자본"),
    ("accounts_receivable", "매출채권"),
    ("inventory", "재고자산"),
]


def calc_horizontal(items_current: dict, items_prior: dict) -> dict:
    """수평분석 — 전기 대비 증감액·증감율."""
    items_result: dict = {}
    keys = sorted(set(items_current.keys()) | set(items_prior.keys()))
    for k in keys:
        cur = items_current.get(k)
        pri = items_prior.get(k)
        if cur is None or pri is None:
            continue
        diff = cur - pri
        rate = _change_rate(cur, pri)
        items_result[k] = {
            "current": cur,
            "prior": pri,
            "change_amount": diff,
            "change_rate": rate,
        }

    flags: list[str] = []
    summary_parts: list[str] = []

    rev = items_result.get("revenue")
    op = items_result.get("operating_income")
    ni = items_result.get("net_income")
    cogs = items_result.get("cogs")
    assets = items_result.get("total_assets")
    liabs = items_result.get("total_liabilities")
    equity = items_result.get("total_equity")
    ar = items_result.get("accounts_receivable")

    if rev and rev["change_rate"] is not None:
        summary_parts.append(f"매출 {rev['change_rate']:+.2f}%")
    if op and op["change_rate"] is not None:
        summary_parts.append(f"영업이익 {op['change_rate']:+.2f}%")
    if ni and ni["change_rate"] is not None:
        summary_parts.append(f"당기순이익 {ni['change_rate']:+.2f}%")

    # flag: 성장성 대비 수익성 저하
    if rev and op and rev["change_rate"] is not None and op["change_rate"] is not None:
        if rev["change_rate"] > 0 and op["change_rate"] < rev["change_rate"]:
            if op["change_rate"] < 0:
                flags.append(
                    f"영업이익 {op['change_rate']:.2f}% 감소 — 매출 증가({rev['change_rate']:.2f}%)에도 수익성 악화, 비용구조 점검 필요"
                )
            else:
                flags.append(
                    f"성장성 대비 수익성 저하 — 매출 {rev['change_rate']:.2f}% 증가, 영업이익 {op['change_rate']:.2f}%만 증가"
                )

    # flag: 원가율 악화 (매출 대비 원가 비중 3%p 이상 증가)
    if rev and cogs and rev["current"] and rev["prior"] and cogs["current"] and cogs["prior"]:
        cogs_ratio_cur = cogs["current"] / rev["current"] * 100 if rev["current"] else None
        cogs_ratio_pri = cogs["prior"] / rev["prior"] * 100 if rev["prior"] else None
        if cogs_ratio_cur is not None and cogs_ratio_pri is not None:
            diff_pp = cogs_ratio_cur - cogs_ratio_pri
            if diff_pp >= 3.0:
                flags.append(
                    f"원가구조 악화 — 매출원가율 {cogs_ratio_pri:.2f}% → {cogs_ratio_cur:.2f}% ({diff_pp:+.2f}%p)"
                )

    # flag: 재무구조 악화 (부채 증가율 > 자산 증가율)
    if liabs and assets and liabs["change_rate"] is not None and assets["change_rate"] is not None:
        if liabs["change_rate"] > assets["change_rate"] and liabs["change_rate"] > 0:
            flags.append(
                f"재무구조 악화 — 부채 {liabs['change_rate']:+.2f}% 증가 > 자산 {assets['change_rate']:+.2f}% 증가"
            )

    # flag: 매출채권이 매출보다 빨리 증가 (회수 지연 우려)
    if ar and rev and ar["change_rate"] is not None and rev["change_rate"] is not None:
        if ar["change_rate"] > rev["change_rate"] + 5.0 and ar["change_rate"] > 0:
            flags.append(
                f"매출채권 회수 지연 우려 — 매출채권 {ar['change_rate']:+.2f}% 증가, 매출은 {rev['change_rate']:+.2f}%"
            )

    summary = (
        " · ".join(summary_parts) + (f" — 경보 {len(flags)}건" if flags else " — 특이 경보 없음")
        if summary_parts
        else ("경보 " + str(len(flags)) + "건" if flags else "분석 대상 항목 없음")
    )

    return {
        "mode": "horizontal",
        "items": items_result,
        "flags": flags,
        "summary": summary,
        "disclaimer": DISCLAIMER,
    }


# ─── vertical (수직분석) ───────────────────────────────────────────────────────

def calc_vertical_is(
    revenue: int,
    cogs: int | None,
    gross_profit: int | None,
    sga: int | None,
    operating_income: int | None,
    net_income: int | None,
) -> dict:
    """손익계산서 수직분석 — 매출 = 100% 기준."""
    if revenue is None or revenue <= 0:
        return {"error": "revenue must be > 0"}

    # 매출총이익 자동 보완 (입력 없고 cogs 있으면)
    if gross_profit is None and cogs is not None:
        gross_profit = revenue - cogs

    ratios: dict = {}
    if cogs is not None:
        ratios["cogs_ratio"] = _pct(cogs, revenue)
    if gross_profit is not None:
        ratios["gross_profit_margin"] = _pct(gross_profit, revenue)
    if sga is not None:
        ratios["sga_ratio"] = _pct(sga, revenue)
    if operating_income is not None:
        ratios["operating_margin"] = _pct(operating_income, revenue)
    if net_income is not None:
        ratios["net_profit_margin"] = _pct(net_income, revenue)

    flags: list[str] = []
    if ratios.get("cogs_ratio") is not None and ratios["cogs_ratio"] >= 80.0:
        flags.append(f"매출원가율 {ratios['cogs_ratio']}% — 원가 비중 과다")
    elif ratios.get("cogs_ratio") is not None:
        flags.append(f"매출원가율 {ratios['cogs_ratio']}% — 업종 평균 비교 필요")
    if ratios.get("operating_margin") is not None and ratios["operating_margin"] < 0:
        flags.append(f"영업이익률 {ratios['operating_margin']}% — 영업적자")
    if ratios.get("net_profit_margin") is not None and ratios["net_profit_margin"] < 0:
        flags.append(f"매출순이익률 {ratios['net_profit_margin']}% — 당기순손실")

    return {
        "mode": "vertical",
        "statement": "is",
        "base": {"label": "매출", "value": revenue},
        "ratios": ratios,
        "flags": flags,
        "disclaimer": DISCLAIMER,
    }


def calc_vertical_bs(
    total_assets: int,
    current_assets: int | None,
    non_current_assets: int | None,
    current_liabilities: int | None,
    non_current_liabilities: int | None,
    total_equity: int | None,
) -> dict:
    """재무상태표 수직분석 — 총자산 = 100% 기준."""
    if total_assets is None or total_assets <= 0:
        return {"error": "total_assets must be > 0"}

    ratios: dict = {}
    if current_assets is not None:
        ratios["current_assets_ratio"] = _pct(current_assets, total_assets)
    if non_current_assets is not None:
        ratios["non_current_assets_ratio"] = _pct(non_current_assets, total_assets)
    if current_liabilities is not None:
        ratios["current_liabilities_ratio"] = _pct(current_liabilities, total_assets)
    if non_current_liabilities is not None:
        ratios["non_current_liabilities_ratio"] = _pct(non_current_liabilities, total_assets)
    if total_equity is not None:
        ratios["equity_ratio"] = _pct(total_equity, total_assets)

    # 총부채 = 유동부채 + 비유동부채 (입력된 것만 합산)
    total_liabs = None
    if current_liabilities is not None and non_current_liabilities is not None:
        total_liabs = current_liabilities + non_current_liabilities
        ratios["total_liabilities_ratio"] = _pct(total_liabs, total_assets)

    flags: list[str] = []
    if ratios.get("equity_ratio") is not None and ratios["equity_ratio"] < 30.0:
        flags.append(f"자기자본비율 {ratios['equity_ratio']}% — 자본 취약 (30% 미만)")
    if ratios.get("current_liabilities_ratio") is not None and ratios["current_liabilities_ratio"] >= 50.0:
        flags.append(f"유동부채 비중 {ratios['current_liabilities_ratio']}% — 단기상환 부담 과다")
    if total_liabs is not None and total_assets and total_liabs > total_equity_or_zero(total_equity) * 2:
        flags.append("부채 총액이 자기자본의 2배 초과 — 부채비율 200% 초과")

    return {
        "mode": "vertical",
        "statement": "bs",
        "base": {"label": "총자산", "value": total_assets},
        "ratios": ratios,
        "flags": flags,
        "disclaimer": DISCLAIMER,
    }


def total_equity_or_zero(v):
    return v if v is not None else 0


# ─── trend (추세분석) ──────────────────────────────────────────────────────────

def calc_trend(years: list[int], values: list[float], label: str = "값") -> dict:
    """추세분석 — 기준연도 = 100 지수화 + YoY + CAGR."""
    if len(years) != len(values):
        return {"error": "years and values length mismatch"}
    if len(years) < 2:
        return {"error": "at least 2 years required"}
    if values[0] == 0:
        return {"error": "base year value must not be 0"}

    base = values[0]
    index = [round(v / base * 100, 2) for v in values]

    yoy: list[float | None] = [None]
    for i in range(1, len(values)):
        prev = values[i - 1]
        if prev == 0:
            yoy.append(None)
        else:
            yoy.append(round((values[i] - prev) / abs(prev) * 100, 2))

    # CAGR = (end/start)^(1/(n-1)) - 1
    n = len(values)
    end, start = values[-1], values[0]
    try:
        if start > 0 and end > 0:
            cagr_decimal = (end / start) ** (1 / (n - 1)) - 1
            cagr = round(cagr_decimal * 100, 2)
        else:
            cagr = None
    except (ValueError, ZeroDivisionError):
        cagr = None

    # 해석
    total_pct = index[-1] - 100
    interpretation_parts = [f"{n}년간"]
    if cagr is not None:
        interpretation_parts.append(f"연평균 {cagr:+.2f}% 성장")
    interpretation_parts.append(f"기준 100→{index[-1]:.2f}로 {total_pct:+.2f}% 변동")
    interpretation = ". ".join(interpretation_parts) + "."

    flags: list[str] = []
    if cagr is not None and cagr < 0:
        flags.append(f"장기 마이너스 성장 — CAGR {cagr:+.2f}%")
    # 추세 역전 감지
    if len(yoy) >= 3 and yoy[-1] is not None and yoy[-2] is not None:
        if yoy[-2] > 0 and yoy[-1] < 0:
            flags.append(f"최근 추세 반전 — {years[-2]}→{years[-1]} 증가에서 감소 전환")

    return {
        "mode": "trend",
        "label": label,
        "years": years,
        "values": values,
        "base_year": years[0],
        "index": index,
        "yoy_change_rate": yoy,
        "cagr": cagr,
        "interpretation": interpretation,
        "flags": flags,
        "disclaimer": DISCLAIMER,
    }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="재무제표 수평·수직·추세 분석기",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # horizontal
    p_h = sub.add_parser("horizontal", help="수평분석 (전기 대비 증감)")
    p_h.add_argument("--items-current", type=str, default=None,
                     help='당기 JSON 예: \'{"revenue": 500000000, "operating_income": 50000000}\'')
    p_h.add_argument("--items-prior", type=str, default=None,
                     help="전기 JSON")
    # 간편 모드
    for k, label in _SIMPLE_ITEM_ARGS:
        p_h.add_argument(f"--{k.replace('_', '-')}-current", type=int, default=None, help=f"{label} 당기 (원)")
        p_h.add_argument(f"--{k.replace('_', '-')}-prior", type=int, default=None, help=f"{label} 전기 (원)")

    # vertical
    p_v = sub.add_parser("vertical", help="수직분석 (구성비)")
    p_v.add_argument("--statement", choices=["is", "bs"], required=True, help="is=손익, bs=재무상태")
    # IS
    p_v.add_argument("--revenue", type=int, default=None, help="매출액 (원) — is")
    p_v.add_argument("--cogs", type=int, default=None, help="매출원가 (원) — is")
    p_v.add_argument("--gross-profit", type=int, default=None, help="매출총이익 (원) — is")
    p_v.add_argument("--sga", type=int, default=None, help="판관비 (원) — is")
    p_v.add_argument("--operating-income", type=int, default=None, help="영업이익 (원) — is")
    p_v.add_argument("--net-income", type=int, default=None, help="당기순이익 (원) — is")
    # BS
    p_v.add_argument("--total-assets", type=int, default=None, help="총자산 (원) — bs")
    p_v.add_argument("--current-assets", type=int, default=None, help="유동자산 (원) — bs")
    p_v.add_argument("--non-current-assets", type=int, default=None, help="비유동자산 (원) — bs")
    p_v.add_argument("--current-liabilities", type=int, default=None, help="유동부채 (원) — bs")
    p_v.add_argument("--non-current-liabilities", type=int, default=None, help="비유동부채 (원) — bs")
    p_v.add_argument("--total-equity", type=int, default=None, help="자기자본 (원) — bs")

    # trend
    p_t = sub.add_parser("trend", help="추세분석 (3~5개년 지수+CAGR)")
    p_t.add_argument("--years", type=str, required=True, help='연도 콤마 구분 예: "2022,2023,2024,2025,2026"')
    p_t.add_argument("--values", type=str, required=True, help='값 콤마 구분 예: "400000000,420000000,..."')
    p_t.add_argument("--label", type=str, default="값", help="지표 이름 (예: 매출·영업이익)")

    return parser


def _collect_horizontal_items(args) -> tuple[dict, dict]:
    # items-current / items-prior JSON 우선
    cur = _parse_json_or_none(args.items_current) or {}
    pri = _parse_json_or_none(args.items_prior) or {}
    # 개별 플래그 병합
    for k, _label in _SIMPLE_ITEM_ARGS:
        cur_v = getattr(args, f"{k}_current", None)
        pri_v = getattr(args, f"{k}_prior", None)
        if cur_v is not None:
            cur[k] = cur_v
        if pri_v is not None:
            pri[k] = pri_v
    return cur, pri


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "horizontal":
        cur, pri = _collect_horizontal_items(args)
        if not cur or not pri:
            print("최소 한 항목 이상 --xxx-current / --xxx-prior 또는 --items-current/--items-prior 필요",
                  file=sys.stderr)
            return 2
        result = calc_horizontal(cur, pri)
    elif args.cmd == "vertical":
        if args.statement == "is":
            result = calc_vertical_is(
                revenue=args.revenue,
                cogs=args.cogs,
                gross_profit=args.gross_profit,
                sga=args.sga,
                operating_income=args.operating_income,
                net_income=args.net_income,
            )
        else:
            result = calc_vertical_bs(
                total_assets=args.total_assets,
                current_assets=args.current_assets,
                non_current_assets=args.non_current_assets,
                current_liabilities=args.current_liabilities,
                non_current_liabilities=args.non_current_liabilities,
                total_equity=args.total_equity,
            )
    elif args.cmd == "trend":
        try:
            years = [int(s.strip()) for s in args.years.split(",") if s.strip()]
            values = [float(s.strip()) for s in args.values.split(",") if s.strip()]
        except ValueError as e:
            print(f"years/values 파싱 실패: {e}", file=sys.stderr)
            return 2
        result = calc_trend(years=years, values=values, label=args.label)
    else:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
