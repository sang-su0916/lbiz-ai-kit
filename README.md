# lbiz-ai-kit

**엘비즈파트너스 AI 컨설팅 키트** — 한국 비즈니스 도메인 전문 Claude Code 스킬 모음

> 운영: [엘비즈파트너스](https://lbiz-partners.com) · 노무·세무·법무·경영 컨설팅

## 무엇인가

한국 중소·소상공인을 위한 노무·세무·법무·경영 도메인의 **계산·판정·검토 작업**을 Claude AI가 hallucination 없이 수행하도록 만든 스킬 패키지.

```
질문 → Claude → SKILL.md (도메인 매뉴얼) + calculator.py (검증 로직) → 정확한 답
```

## 스킬 카테고리 (총 11종)

### 🏭 메타 (1)

| 스킬                                 | 설명                                        |
| ------------------------------------ | ------------------------------------------- |
| **omsc** (Oh My Skill Super Creator) | 새 도메인 스킬을 10분에 스캐폴딩하는 팩토리 |

### 💼 노무 (9)

| 스킬                      | 설명                                   |
| ------------------------- | -------------------------------------- |
| **severance-pay**         | 퇴직금 (평균임금 기반 정확 산정)       |
| **annual-leave**          | 연차수당 (발생일수·미사용수당)         |
| **four-insurances**       | 4대보험료 (2026년 요율)                |
| **unemployment-benefit**  | 실업급여 (자격·일액·소정급여일수)      |
| **wage-base**             | 통상임금·평균임금                      |
| **labor-contract-review** | 근로계약서 검토 체크리스트             |
| **minimum-wage**          | 최저임금 위반 체크 (2026년 10,320원)   |
| **weekly-holiday-pay**    | 주휴수당 (주15H + 개근)                |
| **overtime-pay**          | 연장·야간·휴일근로 가산수당 (50%/100%) |

### 🏛 세무 (1)

| 스킬           | 설명                                     |
| -------------- | ---------------------------------------- |
| **income-tax** | 종합소득세 (8단계 누진세율 + 지방소득세) |

### ⚖️ 법무 / 📈 경영 (계획 중)

OMSC로 순차 추가 예정. `/omsc 상속세`, `/omsc 취득세` 등.

## 빠른 시작

```bash
cp .env.local.example .env.local
# .env.local 수정 (Supabase 또는 더미값)
npm install
npm run dev

# 스킬 단독 테스트 (Python)
python3 skills/severance-pay/references/calculator.py calculate \
  --avg-monthly-wage 3500000 \
  --years-of-service 5 \
  --months-of-service 3
```

## 스킬 만들기

```bash
python3 skills/omsc/references/scaffold.py new \
  --name acquisition-tax --domain 세무 --law "지방세법 §11"
```

## 라이브

- 🌐 홈: https://lbiz-ai-kit.vercel.app (변경 예정)
- 📦 GitHub: https://github.com/sang-su0916/lbiz-ai-kit

## License

MIT (운영: 엘비즈파트너스)
