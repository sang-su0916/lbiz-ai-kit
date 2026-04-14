#!/usr/bin/env python3
"""lbiz-ai-kit — Skill Validation Test

검증 항목:
  1. SKILL.md frontmatter (name/description/when_to_use)
  2. calculator.py CLI 실행 가능
  3. 시나리오별 계산 정확도

Usage:
  python3 tests/test_skill_validation.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"


def check_frontmatter(skill_dir: Path) -> tuple[bool, str]:
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return False, f"SKILL.md missing in {skill_dir.name}"
    text = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return False, f"{skill_dir.name}: no frontmatter"
    fm = m.group(1)
    for key in ("name:", "description:", "when_to_use:"):
        if key not in fm:
            return False, f"{skill_dir.name}: missing {key}"
    return True, ""


def run_calculator(skill: str, args: list[str], cli_path: str = "references/calculator.py") -> dict:
    cli = SKILLS_DIR / skill / cli_path
    proc = subprocess.run(
        ["python3", str(cli)] + args,
        capture_output=True, text=True, timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{skill} CLI failed: {proc.stderr}")
    return json.loads(proc.stdout)


SCENARIOS = [
    {
        "id": "S-01",
        "skill": "severance-pay",
        "args": ["simple", "--avg-monthly-wage", "3500000", "--years", "5"],
        "assert": lambda r: r["eligible"] and r["final_severance"] == 17500000,
        "desc": "간이: 월350만 × 5년 = 1750만",
    },
    {
        "id": "S-02",
        "skill": "severance-pay",
        "args": ["simple", "--avg-monthly-wage", "3000000", "--years", "0", "--months", "11"],
        "assert": lambda r: not r["eligible"],
        "desc": "1년 미만 → 청구권 없음",
    },
    {
        "id": "S-03",
        "skill": "severance-pay",
        "args": [
            "calculate",
            "--avg-3month-wage-total", "10500000",
            "--days-in-3month", "92",
            "--total-service-days", "1825",
        ],
        "assert": lambda r: r["eligible"] and 16500000 < r["final_severance"] < 17500000,
        "desc": "정확: 3개월 1050만/92일 × 5년 ≈ 17백만",
    },
    {
        "id": "S-04",
        "skill": "severance-pay",
        "args": [
            "calculate",
            "--avg-3month-wage-total", "12000000",
            "--days-in-3month", "90",
            "--annual-bonus", "8000000",
            "--total-service-days", "3650",
            "--prior-settlement", "20000000",
        ],
        "assert": lambda r: r["eligible"] and r["prior_settlement"] == 20000000,
        "desc": "중간정산 공제 적용",
    },
    # annual-leave
    {
        "id": "AL-01",
        "skill": "annual-leave",
        "args": ["entitlement", "--hire-date", "2020-04-13", "--base-date", "2026-04-13", "--base-type", "hire"],
        "assert": lambda r: r.get("entitlement_days") == 17,
        "desc": "5년 근속 → 17일 (15 + 가산 2)",
    },
    {
        "id": "AL-02",
        "skill": "annual-leave",
        "args": ["entitlement", "--hire-date", "2001-04-13", "--base-date", "2026-04-13", "--base-type", "hire"],
        "assert": lambda r: r.get("entitlement_days") == 25,
        "desc": "25년 근속 → 25일 (한도)",
    },
    {
        "id": "AL-03",
        "skill": "annual-leave",
        "args": ["unused-pay", "--daily-ordinary-wage", "100000", "--unused-days", "5"],
        "assert": lambda r: r.get("unused_pay") == 500000,
        "desc": "미사용수당: 일급 10만 × 5일 = 50만",
    },
    # four-insurances
    {
        "id": "FI-01",
        "skill": "four-insurances",
        "args": ["calculate", "--monthly-wage", "3000000", "--company-size", "under_150", "--industry-rate", "0.0143"],
        "assert": lambda r: r["items"]["national_pension"]["employee"] == 135000,
        "desc": "국민연금 근로자 분담 (300만 × 4.5% = 135,000)",
    },
    {
        "id": "FI-02",
        "skill": "four-insurances",
        "args": ["calculate", "--monthly-wage", "7000000", "--company-size", "under_150", "--industry-rate", "0.0143"],
        "assert": lambda r: r["items"]["national_pension"]["employee"] == 277650,
        "desc": "상한 적용 (700만 → 6,170,000 × 4.5% = 277,650)",
    },
    # unemployment-benefit
    {
        "id": "UB-01",
        "skill": "unemployment-benefit",
        "args": [
            "calculate", "--avg-daily-wage", "200000", "--insured-days", "1825",
            "--insured-years", "5", "--age", "45", "--voluntary", "no", "--has-disability", "no",
        ],
        "assert": lambda r: r.get("eligible") and r.get("daily_benefit") == 66000,
        "desc": "5년 가입, 평균임금 일20만 → 일액 66,000 (상한)",
    },
    {
        "id": "UB-02",
        "skill": "unemployment-benefit",
        "args": [
            "calculate", "--avg-daily-wage", "100000", "--insured-days", "100",
            "--insured-years", "0", "--age", "30", "--voluntary", "no", "--has-disability", "no",
        ],
        "assert": lambda r: not r.get("eligible"),
        "desc": "피보험단위기간 100일 → 자격 없음",
    },
    # wage-base
    {
        "id": "WB-01",
        "skill": "wage-base",
        "args": ["ordinary", "--base-wage", "3000000", "--base-type", "monthly"],
        "assert": lambda r: r.get("hourly") in (14354, 14353) or 14350 <= r.get("hourly", 0) <= 14360,
        "desc": "월 300만 통상임금 → 시급 약 14,354",
    },
    # minimum-wage
    {
        "id": "MW-01",
        "skill": "minimum-wage",
        "args": ["check", "--monthly-wage", "2000000", "--weekly-hours", "40"],
        "assert": lambda r: r.get("violation") is True and r.get("hourly_rate_actual") == 9569,
        "desc": "월 200만/40H → 시급 9,569 위반",
    },
    {
        "id": "MW-02",
        "skill": "minimum-wage",
        "args": ["check", "--monthly-wage", "2156880", "--weekly-hours", "40"],
        "assert": lambda r: r.get("violation") is False,
        "desc": "월 2,156,880 = 시급 10,320 정확히 최저임금",
    },
    # weekly-holiday-pay
    {
        "id": "WH-01",
        "skill": "weekly-holiday-pay",
        "args": ["calculate", "--weekly-hours", "40", "--hourly-wage", "10320", "--worked-all-days"],
        "assert": lambda r: r.get("amount") == 82560,
        "desc": "주 40H/시급 10,320/개근 → 주휴수당 82,560",
    },
    {
        "id": "WH-02",
        "skill": "weekly-holiday-pay",
        "args": ["calculate", "--weekly-hours", "14", "--hourly-wage", "10320", "--worked-all-days"],
        "assert": lambda r: not r.get("eligible"),
        "desc": "주 14H → 15H 미만 미발생",
    },
    # overtime-pay
    {
        "id": "OT-01",
        "skill": "overtime-pay",
        "args": ["calculate", "--hourly-wage", "10320", "--overtime-hours", "2", "--company-size-ge-5"],
        "assert": lambda r: r.get("grand_total") == 30960,
        "desc": "시급 10,320 연장 2H → 기본 20,640 + 가산 10,320 = 30,960",
    },
    {
        "id": "OT-02",
        "skill": "overtime-pay",
        "args": ["calculate", "--hourly-wage", "10320", "--overtime-hours", "2", "--no-company-size-ge-5"],
        "assert": lambda r: r.get("grand_total") == 20640,
        "desc": "5인 미만 사업장 연장 2H → 가산 없음 원금만",
    },
    # omsc (meta)
    {
        "id": "OMSC-01",
        "skill": "omsc",
        "args": ["--json", "list-templates"],
        "_cli_path": "references/scaffold.py",
        "assert": lambda r: "templates" in r and len(r.get("templates", [])) >= 2,
        "desc": "omsc scaffold.py list-templates (json) — 최소 2개 템플릿 존재",
    },
    {
        "id": "OMSC-02",
        "skill": "omsc",
        "args": ["--json", "new", "--name", "tmp-test-scaffold", "--domain", "테스트", "--law", "없음", "--dry-run"],
        "_cli_path": "references/scaffold.py",
        "assert": lambda r: r.get("dry_run") is True and r.get("name") == "tmp-test-scaffold",
        "desc": "omsc scaffold.py new dry-run (json) — 실제 생성 없이 미리보기",
    },
    # income-tax (세무)
    {
        "id": "IT-01",
        "skill": "income-tax",
        "args": ["calculate", "--taxable-income", "10000000"],
        "assert": lambda r: r["national_income_tax"] == 600000,
        "desc": "과표 1천만 (구간1 6%) → 60만",
    },
    {
        "id": "IT-02",
        "skill": "income-tax",
        "args": ["calculate", "--taxable-income", "30000000"],
        "assert": lambda r: r["national_income_tax"] == 3240000,
        "desc": "과표 3천만 → 3천만×15% - 126만 = 324만",
    },
    {
        "id": "IT-03",
        "skill": "income-tax",
        "args": ["calculate", "--taxable-income", "50000000"],
        "assert": lambda r: r["national_income_tax"] == 6240000,
        "desc": "과표 5천만 (구간2 끝) → 5천만×15% - 126만 = 624만",
    },
    {
        "id": "IT-04",
        "skill": "income-tax",
        "args": ["calculate", "--taxable-income", "100000000"],
        "assert": lambda r: r["national_income_tax"] == 19560000,
        "desc": "과표 1억 (구간4 35%) → 1억×35% - 1544만 = 1,956만",
    },
    {
        "id": "IT-05",
        "skill": "income-tax",
        "args": ["calculate", "--taxable-income", "1500000000"],
        "assert": lambda r: r["national_income_tax"] == 609060000,
        "desc": "과표 15억 (최고구간 45%) → 15억×45% - 6594만 = 6억 906만",
    },
    {
        "id": "IT-06",
        "skill": "income-tax",
        "args": ["effective-rate", "--taxable-income", "50000000"],
        "assert": lambda r: r["marginal_rate_pct"] == 15 and 12 < r["national_effective_rate_pct"] < 13,
        "desc": "과표 5천만 실효세율 약 12.48%",
    },
    # break-even (경영)
    {
        "id": "BE-01",
        "skill": "break-even",
        "args": [
            "calculate",
            "--fixed-cost", "100000000",
            "--unit-price", "10000",
            "--unit-variable-cost", "6000",
        ],
        "assert": lambda r: r["bep_units"] == 25000 and r["bep_revenue"] == 250000000,
        "desc": "고정비 1억·단가 1만·변동비 6천 → BEP 25,000개·2.5억",
    },
    {
        "id": "BE-02",
        "skill": "break-even",
        "args": [
            "calculate",
            "--fixed-cost", "100000000",
            "--unit-price", "10000",
            "--unit-variable-cost", "6000",
            "--target-profit", "20000000",
        ],
        "assert": lambda r: r["target_units"] == 30000,
        "desc": "위 + 목표이익 2천만 → 목표수량 30,000개",
    },
    {
        "id": "BE-03",
        "skill": "break-even",
        "args": [
            "margin-of-safety",
            "--actual-revenue", "300000000",
            "--bep-revenue", "250000000",
        ],
        "assert": lambda r: 0.166 < r["margin_of_safety_ratio"] < 0.168,
        "desc": "실제매출 3억·BEP 2.5억 → 안전한계율 ≈ 0.1667",
    },
    # depreciation (경영·세무)
    {
        "id": "DEP-01",
        "skill": "depreciation",
        "args": ["straight-line", "--acquisition-cost", "10000000", "--useful-life", "5"],
        "assert": lambda r: r["annual_depreciation"] == 2000000,
        "desc": "정액법 취득 1천만·잔존 0·5년 → 연 200만",
    },
    {
        "id": "DEP-02",
        "skill": "depreciation",
        "args": ["straight-line", "--acquisition-cost", "100000000",
                 "--salvage-value", "10000000", "--useful-life", "10"],
        "assert": lambda r: r["annual_depreciation"] == 9000000,
        "desc": "정액법 취득 1억·잔존 1천만·10년 → 연 900만",
    },
    {
        "id": "DEP-03",
        "skill": "depreciation",
        "args": ["estimate-useful-life", "--asset-category", "computer"],
        "assert": lambda r: r["useful_life_years"] == 4,
        "desc": "기준내용연수: 컴퓨터 → 4년",
    },
    {
        "id": "DEP-04",
        "skill": "depreciation",
        "args": ["production", "--acquisition-cost", "10000000", "--salvage-value", "0",
                 "--total-production", "100000", "--actual-production", "20000"],
        "assert": lambda r: r["current_depreciation"] == 2000000,
        "desc": "생산량비례법 1천만/10만×2만 → 200만",
    },
    # financial-ratio (경영)
    {
        "id": "FR-01",
        "skill": "financial-ratio",
        "args": ["liquidity", "--current-assets", "15000000", "--current-liabilities", "10000000"],
        "assert": lambda r: r["current_ratio"] == 150.0,
        "desc": "유동자산 1500만/유동부채 1000만 → 유동비율 150.0%",
    },
    {
        "id": "FR-02",
        "skill": "financial-ratio",
        "args": [
            "leverage", "--total-debt", "300000000", "--total-equity", "200000000",
            "--total-assets", "500000000", "--ebit", "30000000", "--interest-expense", "10000000",
        ],
        "assert": lambda r: r["debt_to_equity"] == 150.0,
        "desc": "부채 3억/자본 2억 → 부채비율 150.0%",
    },
    {
        "id": "FR-03",
        "skill": "financial-ratio",
        "args": [
            "profitability", "--net-income", "10000000", "--revenue", "100000000",
            "--total-assets", "500000000", "--total-equity", "500000000",
        ],
        "assert": lambda r: r["net_profit_margin"] == 10.0,
        "desc": "당기순이익 1천만/매출 1억 → 매출순이익률 10.0%",
    },
    {
        "id": "FR-04",
        "skill": "financial-ratio",
        "args": [
            "profitability", "--net-income", "50000000", "--revenue", "500000000",
            "--total-assets", "1000000000", "--total-equity", "500000000",
        ],
        "assert": lambda r: r["roe"] == 10.0,
        "desc": "당기순이익 5천만/자본 5억 → ROE 10.0%",
    },
    # financial-diagnosis (경영 — 메타 종합진단)
    {
        "id": "FD-01",
        "skill": "financial-diagnosis",
        "args": [
            "diagnose",
            "--current-assets", "200000000", "--current-liabilities", "100000000",
            "--inventory", "40000000", "--accounts-receivable", "50000000",
            "--total-debt", "160000000", "--total-equity", "200000000", "--total-assets", "360000000",
            "--revenue", "500000000", "--net-income", "24000000",
            "--operating-income", "50000000", "--cogs", "300000000",
            "--ebit", "50000000", "--interest-expense", "10000000",
        ],
        "assert": lambda r: r["grade"][0] in ("A", "S") and r["overall_score"] >= 75,
        "desc": "건전 기업 (유동 200/부채 80/ROE 12/이자보상 5) → A 또는 S",
    },
    {
        "id": "FD-02",
        "skill": "financial-diagnosis",
        "args": [
            "diagnose",
            "--current-assets", "80000000", "--current-liabilities", "100000000",
            "--inventory", "30000000", "--accounts-receivable", "50000000",
            "--total-debt", "450000000", "--total-equity", "150000000", "--total-assets", "600000000",
            "--revenue", "500000000", "--net-income", "-7500000",
            "--operating-income", "5000000", "--cogs", "400000000",
            "--ebit", "5000000", "--interest-expense", "10000000",
        ],
        "assert": lambda r: r["grade"][0] == "D" and r["overall_score"] < 45,
        "desc": "위험 기업 (유동 80/부채 300/ROE -5/이자보상 0.5) → D",
    },
    {
        "id": "FD-03",
        "skill": "financial-diagnosis",
        "args": [
            "diagnose",
            "--current-assets", "80000000", "--current-liabilities", "100000000",
            "--inventory", "30000000", "--accounts-receivable", "50000000",
            "--total-debt", "450000000", "--total-equity", "150000000", "--total-assets", "600000000",
            "--revenue", "500000000", "--net-income", "-7500000",
            "--operating-income", "5000000", "--cogs", "400000000",
            "--ebit", "5000000", "--interest-expense", "10000000",
        ],
        "assert": lambda r: any("한계기업" in f for f in r.get("risk_flags", [])),
        "desc": "이자보상배율 1배 미만 → risk_flags에 '한계기업' 포함",
    },
    # cash-flow-analysis (경영 — 현금흐름표)
    {
        "id": "CFA-01",
        "skill": "cash-flow-analysis",
        "args": [
            "analyze",
            "--operating-cf", "80000000",
            "--investing-cf", "-50000000",
            "--financing-cf", "-20000000",
        ],
        "assert": lambda r: r["cf_pattern"].startswith("안정"),
        "desc": "OCF +8천만/IFCF -5천만/FCF -2천만 → 안정형",
    },
    {
        "id": "CFA-02",
        "skill": "cash-flow-analysis",
        "args": [
            "analyze",
            "--operating-cf", "-30000000",
            "--investing-cf", "20000000",
            "--financing-cf", "10000000",
        ],
        "assert": lambda r: r["cf_pattern"].startswith("심각"),
        "desc": "OCF -3천만/IFCF +2천만/FCF +1천만 → 심각형",
    },
    {
        "id": "CFA-03",
        "skill": "cash-flow-analysis",
        "args": [
            "analyze",
            "--operating-cf", "100000000",
            "--investing-cf", "-10000000",
            "--financing-cf", "-10000000",
            "--net-income", "80000000",
        ],
        "assert": lambda r: r["quality_indicators"]["ocf_to_net_income_ratio"] == 1.25,
        "desc": "OCF 1억/순이익 8천만 → ocf_to_net_income_ratio = 1.25",
    },
    {
        "id": "CFA-04",
        "skill": "cash-flow-analysis",
        "args": [
            "analyze",
            "--operating-cf", "50000000",
            "--investing-cf", "-20000000",
            "--financing-cf", "0",
            "--capex", "20000000",
        ],
        "assert": lambda r: r["free_cash_flow"] == 30000000,
        "desc": "OCF 5천만 - CapEx 2천만 → FCF 3천만",
    },
    # financial-statement-trend (경영 — 수평·수직·추세)
    {
        "id": "FST-01",
        "skill": "financial-statement-trend",
        "args": [
            "horizontal",
            "--revenue-current", "500000000", "--revenue-prior", "450000000",
        ],
        "assert": lambda r: r["items"]["revenue"]["change_rate"] == 11.11,
        "desc": "수평: 매출 5억/4.5억 → change_rate 11.11%",
    },
    {
        "id": "FST-02",
        "skill": "financial-statement-trend",
        "args": [
            "vertical", "--statement", "is",
            "--revenue", "500000000", "--cogs", "325000000",
        ],
        "assert": lambda r: r["ratios"]["cogs_ratio"] == 65.00,
        "desc": "수직: 매출 5억·원가 3.25억 → cogs_ratio 65.00%",
    },
    {
        "id": "FST-03",
        "skill": "financial-statement-trend",
        "args": [
            "trend",
            "--years", "2025,2026",
            "--values", "100000000,121000000",
            "--label", "매출",
        ],
        "assert": lambda r: r["cagr"] == 21.00,
        "desc": "추세: 1억→1.21억 2년 → CAGR 21.00%",
    },
    {
        "id": "FST-04",
        "skill": "financial-statement-trend",
        "args": [
            "trend",
            "--years", "2022,2023,2024,2025,2026",
            "--values", "400000000,420000000,450000000,480000000,500000000",
            "--label", "매출",
        ],
        "assert": lambda r: (
            r["index"][0] == 100.00
            and r["index"][-1] == 125.00
            and r["cagr"] == 5.74
        ),
        "desc": "추세 5개년: 기준 100, 종료 125, CAGR 5.74%",
    },
]


def main():
    print(f"\n{'='*60}\nlbiz-ai-kit — Skill Validation\n{'='*60}\n")
    pass_count = fail_count = 0

    print("[1] Frontmatter checks:")
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        ok, msg = check_frontmatter(skill_dir)
        if ok:
            print(f"  ✅ {skill_dir.name}")
            pass_count += 1
        else:
            print(f"  ❌ {msg}")
            fail_count += 1

    print(f"\n[2] Scenario tests ({len(SCENARIOS)}):")
    for sc in SCENARIOS:
        try:
            result = run_calculator(sc["skill"], sc["args"], sc.get("_cli_path", "references/calculator.py"))
            ok = sc["assert"](result)
        except Exception as e:
            ok = False
            result = {"error": str(e)}
        if ok:
            print(f"  ✅ {sc['id']} {sc['desc']}")
            pass_count += 1
        else:
            print(f"  ❌ {sc['id']} {sc['desc']}\n     → {result}")
            fail_count += 1

    total = pass_count + fail_count
    print(f"\n{'='*60}\nResult: {pass_count}/{total} PASS ({fail_count} FAIL)\n{'='*60}\n")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
