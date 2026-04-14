#!/usr/bin/env python3
"""
{{SKILL_NAME}} 계산기 — {{DESCRIPTION}}

법령 근거: {{LAW_BASIS_SHORT}}

모드: {{CLI_COMMANDS}}

CLI:
  python3 calculator.py {{MAIN_COMMAND}} --help

치환 변수:
  {{SKILL_NAME}}      : kebab-case 스킬 이름
  {{DESCRIPTION}}     : 한 문장 설명
  {{LAW_BASIS_SHORT}} : 법령 근거 요약 (예: 소득세법 §55)
  {{MAIN_FUNCTION}}   : 주 계산 함수 이름
  {{MAIN_COMMAND}}    : 메인 subcommand 이름 (예: calculate)
  {{CLI_COMMANDS}}    : subcommand 목록 (쉼표로)

주의:
  - 표준 라이브러리만 사용 (argparse, json, sys, datetime, decimal)
  - 모든 금액은 int (원 단위 절사)
  - JSON 출력: ensure_ascii=False, indent=2
"""

import argparse
import json
import sys
from decimal import ROUND_HALF_UP, Decimal

# ─── 상수 (법령 개정 시 SKILL.md 와 동시 업데이트) ───────────────────────────────
# 예시: 연도별 요율·한도·과표 구간
# MIN_WAGE_2026 = 10320  # 원/시, 고시 제XXX호 (YYYY-MM-DD 조회)

EXAMPLE_CONSTANT = 0  # TODO: 실제 상수로 교체


# ─── 핵심 계산 함수 ────────────────────────────────────────────────────────────

def {{MAIN_FUNCTION}}(
    input_a: float,
    input_b: float = 0.0,
) -> dict:
    """
    {{MAIN_FUNCTION}} — {{DESCRIPTION}}

    Args:
        input_a: (설명) 단위 (예: 원)
        input_b: (설명) 단위 (기본 0)

    Returns:
        dict: {
            "inputs": {...},
            "calculation": "산식 문자열",
            "total": int,
            "disclaimer": "면책 문구",
        }

    예시:
        >>> r = {{MAIN_FUNCTION}}(1000000, 0.05)
        >>> r["total"] == 50000
        True
    """
    a = Decimal(str(input_a))
    b = Decimal(str(input_b))

    # TODO: 실제 로직 구현
    raw = a * b
    total = int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    return {
        "inputs": {
            "input_a": float(a),
            "input_b": float(b),
        },
        "calculation": f"{float(a):,.0f} × {float(b)} = {total:,}원",
        "total": total,
        "disclaimer": (
            "본 계산은 일반적 산정 기준에 따른 참고치입니다. "
            "실제 적용은 도메인 전문가 자문에 따라 달라질 수 있습니다."
        ),
    }


def simple_check(
    flag_a: bool = False,
    amount: float = 0.0,
) -> dict:
    """
    간이 자격 판정 (eligibility 모드용 예시).

    Returns:
        {
            "eligible": bool,
            "reasons": [...],
            "recommendation": str,
        }
    """
    reasons = []
    eligible = True

    if not flag_a:
        eligible = False
        reasons.append("조건 A 미충족")
    if amount <= 0:
        eligible = False
        reasons.append("입력 금액이 0 이하")

    return {
        "eligible": eligible,
        "reasons": reasons or ["모든 조건 충족"],
        "recommendation": (
            "신청 가능합니다."
            if eligible
            else "요건 충족 후 재신청하세요."
        ),
    }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calculator.py",
        description="{{SKILL_NAME}} 계산기 ({{LAW_BASIS_SHORT}})",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── {{MAIN_COMMAND}} ──────────────────────────────────────────────────────
    p_main = sub.add_parser(
        "{{MAIN_COMMAND}}",
        help="주 계산 실행",
    )
    p_main.add_argument(
        "--input-a", type=float, required=True,
        help="입력 A (설명·단위)",
    )
    p_main.add_argument(
        "--input-b", type=float, default=0.0,
        help="입력 B (설명·단위, 기본 0)",
    )

    # ── check (eligibility 예시) ──────────────────────────────────────────────
    p_check = sub.add_parser(
        "check",
        help="자격 판정 (eligibility)",
    )
    p_check.add_argument(
        "--flag-a",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="조건 A 충족 여부 (기본 False)",
    )
    p_check.add_argument(
        "--amount", type=float, default=0.0,
        help="판정용 금액",
    )

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "{{MAIN_COMMAND}}":
        result = {{MAIN_FUNCTION}}(
            input_a=args.input_a,
            input_b=args.input_b,
        )
    elif args.cmd == "check":
        result = simple_check(
            flag_a=args.flag_a,
            amount=args.amount,
        )
    else:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
