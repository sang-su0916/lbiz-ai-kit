# AGENTS.md — Claude Code 스킬 인덱스

이 프로젝트는 한국 노무 도메인의 계산·판정·검토 작업을 위한 **Claude Code 스킬 패키지**입니다.

## 스킬 사용 원칙

⚠️ **중요**: 노무 관련 질문(퇴직금·연차수당·4대보험·실업급여·통상임금·근로계약서)을 받으면 반드시:

1. `skills/<해당스킬>/SKILL.md` 를 먼저 읽고 도메인 규칙 파악
2. 계산이 필요하면 `python3 skills/<해당스킬>/references/calculator.py` CLI 실행
3. 직접 머릿속 계산 금지 — hallucination 위험

## 스킬 목록

### 🏭 메타 스킬 (스킬을 만드는 스킬)

| 스킬     | 설명                                                                              | 트리거 키워드                                |
| -------- | --------------------------------------------------------------------------------- | -------------------------------------------- |
| **omsc** | Oh My Skill Super Creator — 세무·법무·노무·부동산 도메인 스킬을 템플릿으로 찍어냄 | omsc, 스킬 만들기, skill creator, meta skill |

### 계산 스킬 (Python CLI)

| 스킬                     | 설명                                                            | 트리거 키워드                      |
| ------------------------ | --------------------------------------------------------------- | ---------------------------------- |
| **severance-pay**        | 퇴직금 계산 (평균임금×재직년수, 중간정산 공제)                  | 퇴직금, 퇴직급여, severance        |
| **annual-leave**         | 연차수당 (1년 미만 월차, 1년 이상 15일+, 회계연도/입사일)       | 연차, 연차수당, 미사용연차         |
| **four-insurances**      | 4대보험료 (국민·건강·고용·산재, 2026년 요율)                    | 4대보험, 사회보험, 보험료          |
| **unemployment-benefit** | 실업급여 (자격, 일액, 소정급여일수)                             | 실업급여, 구직급여                 |
| **wage-base**            | 통상임금/평균임금 산정 (다른 계산의 베이스)                     | 통상임금, 평균임금, 시급 환산      |
| **minimum-wage**         | 최저임금 위반 체크 (2026년 시급 10,320원, 월환산 2,156,880)     | 최저임금, 시급, 위반, 체불         |
| **weekly-holiday-pay**   | 주휴수당 (주15H+개근 요건, 1일 통상임금)                        | 주휴, 주휴수당, 개근               |
| **overtime-pay**         | 연장·야간·휴일 가산수당 (50%/100%, 22~06시 야간, 5인 미만 제외) | 연장근로, 야간, 휴일근로, 가산수당 |

### 매뉴얼 스킬 (계산 없음)

| 스킬                      | 설명                                             | 트리거 키워드             |
| ------------------------- | ------------------------------------------------ | ------------------------- |
| **labor-contract-review** | 근로계약서 필수 명시사항 체크리스트 (근기법 §17) | 근로계약서, 근로계약 검토 |

## 디렉토리 구조

```
skills/
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
├── labor-contract-review/
│   └── SKILL.md
└── omsc/
    ├── SKILL.md
    └── references/scaffold.py
```

## 도메인 컨텍스트

- **법령 베이스**: 근로기준법, 근로자퇴직급여보장법, 고용보험법, 국민건강보험법, 국민연금법, 산업재해보상보험법
- **요율 기준일**: 2026년 (법령 개정 시 `references/calculator.py` 상수 업데이트)
- **통화 단위**: 원(KRW) — 입력은 만원 단위 또는 원 단위 모두 지원 (스킬별 명시)
- **반올림**: 원 단위 절사(법정 산정 관행) — 계산기에서 처리

## 공통 면책

⚠️ 본 스킬 결과는 일반적 산정 기준에 따른 참고치입니다. 실제 적용은 단체협약·취업규칙·고용센터·공인노무사 자문에 따라 달라질 수 있습니다.

## 기여

- 법령 개정 시 SKILL.md 본문 + calculator.py 상수 동시 업데이트
- 새 스킬 추가 시 본 인덱스 업데이트
- 검증 시나리오는 `tests/test_skill_validation.py`에 추가
