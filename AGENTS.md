# AGENTS.md — lbiz-ai-kit Claude Code 스킬 인덱스

엘비즈파트너스 AI 컨설팅 키트 — 한국 비즈니스 도메인 (노무·세무·법무·경영) 전문 스킬 패키지.

## 스킬 사용 원칙

⚠️ 해당 도메인 질문을 받으면 반드시:

1. `skills/<스킬명>/SKILL.md` 읽고 도메인 규칙 파악
2. 계산 필요 시 `python3 skills/<스킬명>/references/calculator.py` CLI 실행
3. 직접 머릿속 계산 금지

## 🏭 메타 스킬 (스킬을 만드는 스킬)

| 스킬     | 설명                                                | 트리거                        |
| -------- | --------------------------------------------------- | ----------------------------- |
| **omsc** | Oh My Skill Super Creator — 새 도메인 스킬 스캐폴딩 | omsc, 스킬 만들기, meta skill |

## 💼 노무 스킬 (9)

| 스킬                      | 설명                    | 트리거                    |
| ------------------------- | ----------------------- | ------------------------- |
| **severance-pay**         | 퇴직금                  | 퇴직금, 퇴직급여          |
| **annual-leave**          | 연차수당                | 연차, 연차수당            |
| **four-insurances**       | 4대보험료 (2026 요율)   | 4대보험, 사회보험         |
| **unemployment-benefit**  | 실업급여                | 실업급여, 구직급여        |
| **wage-base**             | 통상임금·평균임금       | 통상임금, 평균임금, 시급  |
| **labor-contract-review** | 근로계약서 검토         | 근로계약서, 근로계약      |
| **minimum-wage**          | 최저임금 위반 체크      | 최저임금, 시급 위반, 체불 |
| **weekly-holiday-pay**    | 주휴수당                | 주휴, 주휴수당, 개근      |
| **overtime-pay**          | 연장·야간·휴일 가산수당 | 연장근로, 야간, 휴일근로  |

## 🏛 세무 스킬 (1)

| 스킬           | 설명                        | 트리거                   |
| -------------- | --------------------------- | ------------------------ |
| **income-tax** | 종합소득세 (누진세율 8단계) | 종합소득세, 소득세, 세율 |

## ⚖️ 법무 스킬 (계획)

OMSC로 추가 예정: 상속세, 취득세, 등록세, 공증료, 임대보증금 반환, 상속분 산정.

## 📈 경영 스킬 (계획)

OMSC로 추가 예정: ISO 심사 체크리스트, BCP 진단, 사업계획서 검토.

## 디렉토리 구조

```
skills/
├── omsc/
│   ├── SKILL.md
│   └── references/scaffold.py
├── income-tax/
│   ├── SKILL.md
│   └── references/calculator.py
├── severance-pay/
│   ├── SKILL.md
│   └── references/calculator.py
├── annual-leave/
│   ├── SKILL.md
│   └── references/calculator.py
├── four-insurances/
│   ├── SKILL.md
│   └── references/calculator.py
├── unemployment-benefit/
│   ├── SKILL.md
│   └── references/calculator.py
├── wage-base/
│   ├── SKILL.md
│   └── references/calculator.py
├── minimum-wage/
│   ├── SKILL.md
│   └── references/calculator.py
├── weekly-holiday-pay/
│   ├── SKILL.md
│   └── references/calculator.py
├── overtime-pay/
│   ├── SKILL.md
│   └── references/calculator.py
└── labor-contract-review/
    └── SKILL.md
```

## 도메인 컨텍스트

- **법령 베이스**: 근로기준법, 근로자퇴직급여보장법, 고용보험법, 국민건강보험법, 국민연금법, 산업재해보상보험법, 소득세법
- **요율 기준일**: 2026년 (법령 개정 시 `references/calculator.py` 상수 업데이트)
- **통화 단위**: 원(KRW) — 입력은 만원 단위 또는 원 단위 모두 지원 (스킬별 명시)
- **반올림**: 원 단위 절사(법정 산정 관행) — 계산기에서 처리

## 공통 면책

⚠️ 본 스킬 결과는 일반적 산정 기준에 따른 참고치입니다. 실제 적용은 단체협약·취업규칙·고용센터·공인노무사·세무사 자문에 따라 달라질 수 있습니다.

## 기여

- 법령 개정 시 SKILL.md 본문 + calculator.py 상수 동시 업데이트
- 새 스킬 추가 시 본 인덱스 업데이트
- 검증 시나리오는 `tests/test_skill_validation.py`에 추가
