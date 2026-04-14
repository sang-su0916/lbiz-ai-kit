# nomu-oneQ-skill.V

노무원큐 본 서비스(`nomu-oneq`)에 **Claude Code 스킬 패턴**을 적용한 실험 프로젝트(Lab).

> ⚠️ **Lab 프로젝트** — 운영 서비스(`nomu-oneq.vercel.app`)와 분리된 실험·교육용입니다.

## 무엇이 다른가?

기존 노무원큐는 Next.js 웹 UI만 제공합니다. 이 lab은 동일한 UI 위에 **Claude Code 스킬**(`skills/` 디렉토리)을 추가해, **AI 에이전트가 노무 계산을 hallucination 없이 수행**할 수 있게 합니다.

```
[질문] → Claude → ① skills/<name>/SKILL.md (도메인 매뉴얼)
                → ② skills/<name>/references/calculator.py (검증된 계산기)
                → [정확한 답]
```

참고: [한국 부동산대출 Claude 스킬 패키지](https://github.com/BancaKim/korean-loan-claude-skills)

## 스킬 구성 (11종 — 계산 스킬 10 + 메타 1)

### 🏭 메타 스킬

| 스킬     | 설명                                                  |
| -------- | ----------------------------------------------------- |
| **omsc** | 새 도메인 스킬을 템플릿·scaffold.py로 찍어내는 팩토리 |

### 계산·검토 스킬

| 스킬                      | 설명                                              | 계산   |
| ------------------------- | ------------------------------------------------- | ------ |
| **income-tax**            | 종합소득세 — 소득세법 §55 8단계 누진세율 + 지방세 | ✅     |
| **severance-pay**         | 퇴직금 — 평균임금×재직년수, 중간정산 공제         | ✅     |
| **annual-leave**          | 연차수당 — 1년 미만/이상, 회계연도/입사일 분기    | ✅     |
| **four-insurances**       | 4대보험 — 2026년 요율, 사업주/근로자 분담         | ✅     |
| **unemployment-benefit**  | 실업급여 — 자격·금액·소정급여일수                 | ✅     |
| **wage-base**             | 통상임금/평균임금 — 다른 계산의 베이스            | ✅     |
| **minimum-wage**          | 최저임금 위반 체크 — 2026년 시급 10,320원 기준    | ✅     |
| **weekly-holiday-pay**    | 주휴수당 — 주 15H 이상+개근, 단시간 비례 계산     | ✅     |
| **overtime-pay**          | 가산수당 — 연장·야간·휴일 50%/100%, 5인 미만 제외 | ✅     |
| **labor-contract-review** | 근로계약서 검토 — 필수 명시사항 체크              | 매뉴얼 |

## 기존 노무원큐와의 관계

| 항목      | nomu-oneq (운영)     | nomu-oneQ-skill.V (Lab)                    |
| --------- | -------------------- | ------------------------------------------ |
| 도메인    | nomu-oneq.vercel.app | nomu-oneq-skill-v.vercel.app (예정)        |
| 분리 수준 | —                    | 별도 GitHub + 별도 Vercel + 별도 Supabase  |
| 스킬      | 없음                 | `skills/` 디렉토리 11종 (계산 10 + 메타 1) |
| UI        | 풀 SaaS              | 동일 UI + `/skills` 카탈로그 페이지 추가   |

## 빠른 시작

```bash
cp .env.local.example .env.local
# .env.local 수정 (lab 전용 Supabase 또는 더미값)
npm install
npm run dev

# 스킬 단독 테스트 (Python)
python3 skills/severance-pay/references/calculator.py calculate \
  --avg-monthly-wage 3500000 \
  --years-of-service 5 \
  --months-of-service 3
```

## License

MIT
