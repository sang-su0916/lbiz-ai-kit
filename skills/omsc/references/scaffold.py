#!/usr/bin/env python3
"""
OMSC Scaffold — 새 Claude Code 스킬의 뼈대를 생성하는 CLI.

Usage:
    python3 scaffold.py new --name income-tax --domain 세무 [옵션]
    python3 scaffold.py list-templates
    python3 scaffold.py validate --skill-dir path/to/skills/new-skill

동작:
    new           : SKILL.md + calculator.py 를 템플릿 치환으로 생성
    list-templates: references/templates/ 내 파일 나열
    validate      : 작성된 스킬의 frontmatter · CLI 실행 여부 점검

중요:
    - 표준 라이브러리만 사용 (argparse, json, sys, os, shutil, re, pathlib, subprocess)
    - 파일 생성 실패 시 롤백 (ExitStack)
    - --dry-run 으로 실제 파일 생성 없이 내용 미리보기
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
DEFAULT_PARENT_DIR = Path("/Users/isangsu/lbiz-ai-kit/skills/")

CALC_MODES = ["amount", "eligibility", "comparison", "breakdown", "checklist", "limit"]

# ─── 헬퍼 ──────────────────────────────────────────────────────────────────────


def _validate_name(name: str) -> tuple[bool, str]:
    """kebab-case 검증: 3~30자, 소문자+하이픈, 복수형 금지."""
    if not name:
        return False, "이름이 비어있습니다."
    if len(name) < 3 or len(name) > 30:
        return False, f"이름 길이는 3~30자여야 합니다 (현재 {len(name)}자)."
    if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", name):
        return False, "kebab-case (소문자+하이픈) 만 허용됩니다. 예: income-tax"
    # 복수형 휴리스틱 (너무 공격적이지 않게)
    last = name.split("-")[-1]
    if last.endswith("ies") or (last.endswith("s") and not last.endswith("ss") and len(last) > 3):
        return False, f"복수형 금지: '{last}' → 단수로 변경하세요."
    return True, "ok"


def _snake_case(name: str) -> str:
    """kebab-case → snake_case (함수명용)."""
    return name.replace("-", "_")


def _domain_label(domain: str) -> str:
    """도메인 한국어 라벨."""
    mapping = {
        "세무": "세무 계산기",
        "법무": "법무 검토",
        "노무": "노무 계산기",
        "부동산": "부동산 계산기",
    }
    return mapping.get(domain, f"{domain} 계산기")


def _substitutions(
    name: str,
    domain: str,
    law: str,
    calc_mode: str,
) -> dict:
    """치환 변수 딕셔너리 생성."""
    main_command_map = {
        "amount": "calculate",
        "eligibility": "check",
        "comparison": "compare",
        "breakdown": "breakdown",
        "checklist": "review",
        "limit": "calculate-limit",
    }
    main_command = main_command_map.get(calc_mode, "calculate")
    main_function = _snake_case(name) + "_" + main_command.replace("-", "_")

    cli_example = (
        f"python3 skills/{name}/references/calculator.py {main_command} \\\n"
        f"  --input-a 1000000 \\\n"
        f"  --input-b 0.05"
    )

    interview_questions = (
        "1. **기본 입력 부족**: \"(필수 입력 A)를 알려주세요.\"\n"
        "2. **예외 조건 불명**: \"(적용 제외 여부)에 해당하시나요?\"\n"
        "3. **기준년도 불명**: \"(YYYY년) 기준으로 계산할까요?\""
    )

    law_basis = (
        f"| 조문 | 내용 | 출처 |\n"
        f"|------|------|------|\n"
        f"| {law} | (법령 본문 발췌) | [law.go.kr](https://www.law.go.kr) (YYYY-MM-DD 조회) |"
    )

    known_limitations = (
        "1. **(특수 대상 미지원)** — (예: 감시·단속적 근로자 §63 등)\n"
        "2. **(경과 규정 미반영)** — (법령 개정 전후 이력 확인 필요)\n"
        "3. **(판례·해석 쟁점)** — 분쟁 발생 시 도메인 전문가 자문 필수"
    )

    related_skills = (
        "- (관련 스킬 1) — 연계 계산 설명\n"
        "- (관련 스킬 2) — 베이스 값 제공"
    )

    domain_notes = (
        "- (적용 제외 대상 명시)\n"
        "- (특례 적용 요건 명시)"
    )

    core_formula = "(핵심 공식을 여기에 기재하세요. 예: 세액 = 과표 × 세율 - 누진공제)"

    return {
        "{{SKILL_NAME}}": name,
        "{{DESCRIPTION}}": f"{domain} 도메인 {_domain_label(domain)} — {law} 기반",
        "{{WHEN_TO_USE}}": f"{name.replace('-', ' ')}, {domain} 계산, {law}",
        "{{LAW_BASIS}}": law_basis,
        "{{LAW_BASIS_SHORT}}": law,
        "{{CORE_FORMULA}}": core_formula,
        "{{CLI_EXAMPLE}}": cli_example,
        "{{INTERVIEW_QUESTIONS}}": interview_questions,
        "{{DOMAIN_NOTES}}": domain_notes,
        "{{DOMAIN_LABEL}}": _domain_label(domain),
        "{{KNOWN_LIMITATIONS}}": known_limitations,
        "{{RELATED_SKILLS}}": related_skills,
        "{{MAIN_COMMAND}}": main_command,
        "{{MAIN_COMMAND_DESC}}": f"{calc_mode} 모드 계산 실행",
        "{{MAIN_FUNCTION}}": main_function,
        "{{CLI_COMMANDS}}": f"{main_command} | check",
    }


def _render_template(template_path: Path, subs: dict) -> str:
    """
    템플릿 파일을 읽어 치환 변수 대입.

    Markdown 포맷터 (Prettier 등) 가 {{VAR}} 를 { { VAR } } 로 변환하는 경우를
    대비해 두 형태 모두 매치합니다.
    """
    text = template_path.read_text(encoding="utf-8")

    # 정규식으로 {{ VAR }} · { { VAR } } · {{VAR}} 모든 형태 처리
    def _replace(match: re.Match) -> str:
        var_name = match.group(1).strip()
        key = "{{" + var_name + "}}"
        return str(subs.get(key, match.group(0)))

    # 패턴: `{` 1~2회 + 공백 + `{` 0~1회 + VAR_NAME + `}` 0~1회 + 공백 + `}` 1~2회
    pattern = re.compile(r"\{\s*\{\s*([A-Z_]+)\s*\}\s*\}")
    text = pattern.sub(_replace, text)

    return text


# ─── new subcommand ────────────────────────────────────────────────────────────


def cmd_new(args: argparse.Namespace) -> int:
    ok, msg = _validate_name(args.name)
    if not ok:
        print(f"[ERROR] 이름 검증 실패: {msg}", file=sys.stderr)
        return 1

    if args.calc_mode not in CALC_MODES:
        print(
            f"[ERROR] --calc-mode 는 {CALC_MODES} 중 하나여야 합니다.",
            file=sys.stderr,
        )
        return 1

    parent_dir = Path(args.parent_dir).expanduser().resolve()
    skill_dir = parent_dir / args.name
    references_dir = skill_dir / "references"

    if skill_dir.exists() and not args.force and not args.dry_run:
        print(
            f"[ERROR] 이미 존재합니다: {skill_dir}\n"
            f"  덮어쓰려면 --force, 미리보기는 --dry-run 사용.",
            file=sys.stderr,
        )
        return 1

    subs = _substitutions(
        name=args.name,
        domain=args.domain,
        law=args.law,
        calc_mode=args.calc_mode,
    )

    skill_tpl = TEMPLATES_DIR / "skill_template.md"
    calc_tpl = TEMPLATES_DIR / "calculator_template.py"

    if not skill_tpl.exists():
        print(f"[ERROR] 템플릿 없음: {skill_tpl}", file=sys.stderr)
        return 1

    skill_content = _render_template(skill_tpl, subs)

    # checklist 모드는 calculator.py 생성 안 함
    create_calc = args.calc_mode != "checklist"
    calc_content = ""
    if create_calc:
        if not calc_tpl.exists():
            print(f"[ERROR] 템플릿 없음: {calc_tpl}", file=sys.stderr)
            return 1
        calc_content = _render_template(calc_tpl, subs)

    # ── dry-run ────────────────────────────────────────────────────────────────
    if args.dry_run:
        if getattr(args, "output_json", False):
            files_to_create = [
                {"path": str(skill_dir / "SKILL.md"), "size": len(skill_content)},
            ]
            if create_calc:
                files_to_create.append(
                    {"path": str(references_dir / "calculator.py"), "size": len(calc_content)}
                )
            print(json.dumps(
                {
                    "dry_run": True,
                    "name": args.name,
                    "domain": args.domain,
                    "parent_dir": str(parent_dir) + "/",
                    "files_to_create": files_to_create,
                    "substitutions": {k: v[:80] + ("..." if len(str(v)) > 80 else "") for k, v in subs.items()},
                },
                ensure_ascii=False,
            ))
            return 0

        print("═" * 72)
        print(f"[DRY-RUN] 다음 파일이 생성될 예정입니다:")
        print("═" * 72)
        print(f"\n📁 {skill_dir}/")
        print(f"📄 {skill_dir / 'SKILL.md'}  ({len(skill_content)} bytes)")
        if create_calc:
            print(
                f"📄 {references_dir / 'calculator.py'}  "
                f"({len(calc_content)} bytes)"
            )
        else:
            print(f"(checklist 모드: calculator.py 생성 안 함)")

        print("\n" + "─" * 72)
        print("📄 SKILL.md (첫 40줄 미리보기)")
        print("─" * 72)
        for i, line in enumerate(skill_content.splitlines()[:40], 1):
            print(f"{i:3} | {line}")
        if create_calc:
            print("\n" + "─" * 72)
            print("📄 calculator.py (첫 30줄 미리보기)")
            print("─" * 72)
            for i, line in enumerate(calc_content.splitlines()[:30], 1):
                print(f"{i:3} | {line}")

        print("\n" + "═" * 72)
        print("치환 변수 요약:")
        print("═" * 72)
        print(json.dumps(
            {k: v[:80] + ("..." if len(str(v)) > 80 else "") for k, v in subs.items()},
            ensure_ascii=False,
            indent=2,
        ))
        return 0

    # ── 실제 파일 생성 (롤백 지원) ────────────────────────────────────────────
    created: list[Path] = []
    try:
        skill_dir.mkdir(parents=True, exist_ok=args.force)
        created.append(skill_dir)

        (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
        created.append(skill_dir / "SKILL.md")

        if create_calc:
            references_dir.mkdir(parents=True, exist_ok=True)
            created.append(references_dir)
            calc_path = references_dir / "calculator.py"
            calc_path.write_text(calc_content, encoding="utf-8")
            calc_path.chmod(0o755)
            created.append(calc_path)

    except Exception as e:
        print(f"[ERROR] 파일 생성 실패: {e}", file=sys.stderr)
        print(f"[ROLLBACK] 생성된 파일을 제거합니다...", file=sys.stderr)
        for p in reversed(created):
            try:
                if p.is_file():
                    p.unlink()
                elif p.is_dir() and not any(p.iterdir()):
                    p.rmdir()
            except Exception:
                pass
        return 1

    print(f"✅ 스킬 '{args.name}' 스캐폴드 완료")
    print(f"")
    print(f"생성된 파일:")
    print(f"  - {skill_dir / 'SKILL.md'}")
    if create_calc:
        print(f"  - {references_dir / 'calculator.py'}")
    print(f"")
    print(f"다음 단계:")
    print(f"  1) 팩트체크: references/fact_check_protocol.md 참조하여 법령 원문 확인")
    print(f"  2) SKILL.md 의 TODO·치환 잔여 섹션 채우기")
    if create_calc:
        print(f"  3) calculator.py 의 상수·로직 실제 구현")
        print(f"  4) 검증 시나리오 4건 이상 tests/ 에 추가")
    print(f"  5) AGENTS.md 스킬 목록 표 업데이트")
    print(f"  6) 도메인 전문가 (상수님) 검증 → 검증 기록 작성")
    return 0


# ─── list-templates subcommand ─────────────────────────────────────────────────


def cmd_list_templates(args: argparse.Namespace) -> int:
    if not TEMPLATES_DIR.exists():
        print(f"[ERROR] 템플릿 디렉토리 없음: {TEMPLATES_DIR}", file=sys.stderr)
        return 1

    files = sorted(TEMPLATES_DIR.iterdir())

    if getattr(args, "output_json", False):
        templates = [
            {"name": f.name, "size": f.stat().st_size}
            for f in files if f.is_file()
        ]
        print(json.dumps(
            {"templates": templates, "calc_modes": CALC_MODES},
            ensure_ascii=False,
        ))
        return 0

    if not files:
        print(f"(템플릿 없음: {TEMPLATES_DIR})")
        return 0

    print(f"📂 {TEMPLATES_DIR}")
    for f in files:
        if f.is_file():
            size = f.stat().st_size
            print(f"  - {f.name}  ({size:,} bytes)")
    print(f"")
    print(f"사용 가능한 calc 모드: {', '.join(CALC_MODES)}")
    return 0


# ─── validate subcommand ───────────────────────────────────────────────────────


def cmd_validate(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir).expanduser().resolve()
    if not skill_dir.exists():
        print(f"[ERROR] 디렉토리 없음: {skill_dir}", file=sys.stderr)
        return 1

    skill_md = skill_dir / "SKILL.md"
    calc_py = skill_dir / "references" / "calculator.py"

    issues: list[str] = []
    checks: list[tuple[str, bool, str]] = []

    # 1) SKILL.md 존재
    if not skill_md.exists():
        issues.append(f"SKILL.md 없음: {skill_md}")
        checks.append(("SKILL.md 존재", False, str(skill_md)))
    else:
        checks.append(("SKILL.md 존재", True, str(skill_md)))
        text = skill_md.read_text(encoding="utf-8")

        # 2) frontmatter 3개 필드
        front = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not front:
            issues.append("frontmatter (--- 블록) 없음")
            checks.append(("frontmatter 존재", False, ""))
        else:
            fm = front.group(1)
            for field in ["name", "description", "when_to_use"]:
                if re.search(rf"^{field}\s*:", fm, re.MULTILINE):
                    checks.append((f"frontmatter.{field}", True, ""))
                else:
                    issues.append(f"frontmatter.{field} 누락")
                    checks.append((f"frontmatter.{field}", False, ""))

        # 3) 치환 변수 잔여 확인
        leftover = re.findall(r"\{\{[A-Z_]+\}\}", text)
        if leftover:
            issues.append(f"치환 변수 잔여: {set(leftover)}")
            checks.append((f"치환 변수 모두 치환됨", False, str(set(leftover))))
        else:
            checks.append(("치환 변수 모두 치환됨", True, ""))

        # 4) 필수 섹션 존재
        for section in ["## 법령 근거", "## 알려진 한계", "## 검증 기록"]:
            if section in text:
                checks.append((f"섹션 '{section}'", True, ""))
            else:
                issues.append(f"섹션 누락: {section}")
                checks.append((f"섹션 '{section}'", False, ""))

    # 5) calculator.py 존재 + --help 실행
    if calc_py.exists():
        checks.append(("calculator.py 존재", True, str(calc_py)))
        try:
            result = subprocess.run(
                ["python3", str(calc_py), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                checks.append(("calculator.py --help 실행", True, ""))
            else:
                issues.append(f"calculator.py --help 실패: {result.stderr[:200]}")
                checks.append(("calculator.py --help 실행", False, result.stderr[:100]))
        except Exception as e:
            issues.append(f"calculator.py 실행 중 예외: {e}")
            checks.append(("calculator.py --help 실행", False, str(e)[:100]))
    else:
        # checklist 모드는 calculator.py 생성 안 함 → 경고 수준
        checks.append(
            ("calculator.py 존재",
             False,
             f"(없음 — checklist 모드라면 정상)")
        )

    # ── 결과 출력 ──────────────────────────────────────────────────────────────
    print(f"📋 Validation: {skill_dir}")
    print("─" * 72)
    for label, ok, note in checks:
        mark = "✅" if ok else "❌"
        line = f"  {mark} {label}"
        if note:
            line += f"  [{note[:60]}]"
        print(line)

    if issues:
        print("")
        print("❌ 발견된 문제:")
        for i in issues:
            print(f"  - {i}")
        return 1

    print("")
    print("✅ 모든 검증 통과")
    return 0


# ─── CLI 엔트리 ─────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scaffold.py",
        description="OMSC Scaffold — 새 Claude Code 스킬 뼈대 생성 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "예시:\n"
            "  python3 scaffold.py new --name income-tax --domain 세무 "
            "--law \"소득세법 §55\" --calc-mode amount\n"
            "  python3 scaffold.py list-templates\n"
            "  python3 scaffold.py validate --skill-dir skills/income-tax\n"
        ),
    )
    parser.add_argument(
        "--json", action="store_true", dest="output_json",
        help="stdout에 순수 JSON 출력 (파싱 용도)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── new ────────────────────────────────────────────────────────────────────
    p_new = sub.add_parser("new", help="새 스킬 스캐폴드 생성")
    p_new.add_argument(
        "--name", type=str, required=True,
        help="스킬 이름 (kebab-case 영문, 3~30자, 예: income-tax)",
    )
    p_new.add_argument(
        "--domain", type=str, required=True,
        help="도메인 (예: 세무, 법무, 노무, 부동산)",
    )
    p_new.add_argument(
        "--law", type=str, default="미지정",
        help='법령 근거 (예: "소득세법 §55")',
    )
    p_new.add_argument(
        "--calc-mode", type=str, default="amount",
        choices=CALC_MODES,
        help=f"계산 모드 {CALC_MODES} (기본 amount)",
    )
    p_new.add_argument(
        "--parent-dir", type=str, default=str(DEFAULT_PARENT_DIR),
        help=f"스킬이 생성될 부모 디렉토리 (기본 {DEFAULT_PARENT_DIR})",
    )
    p_new.add_argument(
        "--dry-run", action="store_true",
        help="파일 생성 없이 내용 미리보기만 출력",
    )
    p_new.add_argument(
        "--force", action="store_true",
        help="기존 디렉토리 덮어쓰기 허용",
    )
    p_new.set_defaults(func=cmd_new)

    # ── list-templates ─────────────────────────────────────────────────────────
    p_list = sub.add_parser("list-templates", help="사용 가능한 템플릿 나열")
    p_list.set_defaults(func=cmd_list_templates)

    # ── validate ───────────────────────────────────────────────────────────────
    p_val = sub.add_parser("validate", help="작성된 스킬 검증")
    p_val.add_argument(
        "--skill-dir", type=str, required=True,
        help="검증 대상 스킬 디렉토리 경로",
    )
    p_val.set_defaults(func=cmd_validate)

    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
