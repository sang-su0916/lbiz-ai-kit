---
name: omsc
description: Oh My Skill Super Creator — 한국어 도메인(세무·법무·노무·부동산) 전문 계산/판정/검토 스킬을 템플릿 기반으로 찍어내는 메타 스킬. 팩트체크 프로토콜 + scaffold.py CLI 포함.
when_to_use: 새 스킬 추가, 세무 계산기 만들기, 법무 체크리스트 스킬, "스킬 만들어줘"/"omsc" 요청, meta skill creation
---

# OMSC — Oh My Skill Super Creator (메타 스킬)

> **한줄 요약**: 도메인 전문 계산·판정·검토를 `SKILL.md` + `calculator.py`로 찍어내는 공장.

---

## ⚠️ 사용 원칙 (필독)

> 🛑 **절대 팩트체크 없이 스킬 작성 금지**
> — 법령 조문·요율·한도액·과표 구간은 반드시 `references/fact_check_protocol.md` 의 정부 원문 출처를 WebFetch 하여 확인한 뒤 하드코딩합니다. 제 기존 지식만으로 숫자를 쓰면 `hallucination` 으로 간주합니다.
>
> 🧑‍⚖️ **도메인 전문가(사용자)에게 최종 검증 요청 필수**
> — 상수·로직·엣지케이스는 최종적으로 상수님(또는 지정 노무사·세무사)의 확인을 받고 `SKILL.md` 하단 "검증 기록"에 `YYYY-MM-DD 확인자: XXX` 를 남깁니다.
>
> 🧩 **작은 스킬 원칙**
> — 한 도메인에 subcommand 3개를 넘기면 분리합니다. `severance-pay` (계산) / `wage-base` (기반 산정) 처럼 단일 책임을 유지합니다.

---

## 스킬이란 무엇인가

Claude Code 스킬은 **매뉴얼 + 검증 로직의 분리 설계** 입니다. `SKILL.md` 는 Claude 가 상황 판단에 쓰는 도메인 지식 (법령 근거, 되묻기 규칙, 한계, 응답 포맷) 이고, `references/calculator.py` 는 실제 숫자를 뽑는 결정적(deterministic) Python CLI 입니다.

이 분리는 `hallucination` 을 구조적으로 차단합니다. Claude 가 "퇴직금 얼마인가요?" 를 받으면 직접 계산하지 않고 CLI 를 호출하여 JSON 결과를 받아 포맷팅만 수행합니다. 따라서 **모든 수치 연산은 코드로 검증 가능** 해야 하고, 코드는 **외부 라이브러리 없이 표준 라이브러리로만** 작성해 어디서나 재현됩니다.

OMSC 는 이 두 축을 템플릿화해 새 스킬을 일관된 구조로 양산합니다. 패턴이 같으므로 에이전트가 스킬 간 교차 참조·검증도 쉬워집니다 (예: `severance-pay` 가 `wage-base` 의 평균임금을 입력으로 받는 구조).

---

## 6단계 프로세스 (핵심)

### STEP 1 — 도메인 인터뷰

**DO**

- 사용자(도메인 전문가)에게 아래 8가지 질문을 차례로 던집니다.
- 답변을 `.omc/notepads/omsc/{skill-name}-intake.md` 에 기록합니다.

**DON'T**

- 답변 없이 추정으로 진행 금지.
- "대충 이럴 겁니다" 로 넘어가지 않기.

**인터뷰 질문 8개**

1. 스킬 이름 (kebab-case 영문) 및 도메인 (세무/법무/노무/부동산/기타)?
2. 이 스킬이 답하는 **핵심 질문 1문장**은? (예: "퇴직금 얼마인가요?")
3. **법령 근거** (조문 단위): 법률명 §조항, 시행령·시행규칙·고시 포함?
4. **계산 모드**: amount / eligibility / comparison / breakdown / checklist / limit 중 어느 것? (아래 카탈로그 참조)
5. **필수 입력 파라미터** 리스트 (이름·단위·기본값)?
6. **엣지케이스**: 적용 제외 대상, 특례, 개정 전후 이력 (예: "5인 미만 사업장은 §56 제외")?
7. **상수 요율·한도·구간**: 연도별 값 (2026년 기준이면 언제 개정되는지)?
8. **검증 시나리오**: 대표 예제 입력·기대 출력 4건 이상?

### STEP 2 — 팩트체크

**DO**

- `references/fact_check_protocol.md` 의 정부 원문 소스 표를 열어 해당 법령·고시를 WebFetch.
- 발췌문은 ≤125자로 인용하고 URL + 조회일자를 기록.
- SPA(React 등) 로 WebFetch 실패 시 2차 출처 (언론·학술) 명시 + 사용자 확인 요청.

**DON'T**

- 제 기존 지식만으로 숫자 작성 금지 (2026-04-13 기준 knowledge cutoff 이전 값은 모두 stale 가능).
- `wikipedia` 단일 출처 금지 (반드시 정부 원문과 교차 확인).

**Claude 수행 행동**

```
1) WebFetch https://www.law.go.kr/법령/{법명} → 해당 조문 발췌
2) WebFetch https://www.nts.go.kr 또는 https://www.moel.go.kr → 고시·별표
3) 수치는 3곳 이상 교차 확인 (원문 + 공식 해설 + 실무서)
4) SKILL.md 의 "법령 근거" 표에 [조문·출처·조회일자] 기록
```

### STEP 3 — SKILL.md 작성

**DO**

- `references/templates/skill_template.md` 를 복사해 치환 변수 채우기.
- 표·체크리스트·되묻기 규칙은 템플릿 구조 그대로 유지 (사용자가 스킬 간 일관성을 기대합니다).
- 600줄 이내로 유지 (과하면 `references/{subtopic}.md` 로 분리).

**DON'T**

- 템플릿 헤더 순서 변경 금지 (frontmatter → 경고 → 법령 근거 → 공식 → CLI → 입력 파싱 → 되묻기 → 응답 포맷 → 한계 → 관련 스킬).

### STEP 4 — calculator.py 구현

**DO**

- `references/templates/calculator_template.py` 를 복사.
- argparse subcommand 2~3개 (`calculate`, `simple`, `breakdown` 등).
- 모든 금액은 `int` (원 단위 절사) 로 반환.
- JSON 출력: `print(json.dumps(result, ensure_ascii=False, indent=2))`.

**DON'T**

- `requirements.txt` 추가 금지 — 표준 라이브러리만 (`argparse`, `json`, `sys`, `datetime`, `decimal`, `math`, `dataclasses`).
- 전역 상태·파일 쓰기 금지 (stateless CLI).
- `print()` 으로 디버그 흘리기 금지 (JSON 이외는 `sys.stderr`).

### STEP 5 — 검증 시나리오 추가

**DO**

- 대표 케이스 4건을 `tests/test_{skill_name}.py` 또는 `tests/test_skill_validation.py` 에 추가.
- 각 케이스는 `(인자, 기대_total, 허용_오차)` 튜플 형태.
- 엣지케이스 최소 1건 포함 (예: 0원, 법정 한도, 5인 미만 사업장).

**DON'T**

- 검증 시나리오 0건으로 배포 금지.
- 기대값을 코드에서 역산하여 맞추지 말 것 — 반드시 정부 예시·공식 계산기 결과와 대조.

### STEP 6 — 등록

**DO**

- `AGENTS.md` 의 "스킬 목록" 표에 행 추가 (이름·설명·트리거 키워드).
- `README.md` 루트에 한 줄 추가 (있으면).
- 관련 웹 앱 `/skills` 페이지 (노무원큐 프로젝트) 카드 추가 (있으면).
- `tests/` 검증 통과 확인: `python3 -m pytest tests/`.

**DON'T**

- AGENTS.md 업데이트 없이 커밋 금지.
- 검증 실패 상태로 push 금지.

---

## 계산 모드 카탈로그 (재사용 패턴)

| 모드            | 아이콘 | 설명                             | 예시 스킬                                | subcommand 예     |
| --------------- | ------ | -------------------------------- | ---------------------------------------- | ----------------- |
| **amount**      | 🧮     | 금액 산정 (수식 1~2개)           | severance-pay, income-tax                | `calculate`       |
| **eligibility** | ✅     | 자격 판정 (pass/fail + 사유)     | unemployment-benefit, weekly-holiday-pay | `check`           |
| **comparison**  | ⚖️     | 두 가지 임금 비교 (통상 vs 평균) | wage-base                                | `compare`         |
| **breakdown**   | ⏱      | 시간·금액 분해 (출퇴근→유형별)   | overtime-pay                             | `breakdown`       |
| **checklist**   | 📋     | 문서 검토 (필수 항목 7개 스캔)   | labor-contract-review                    | (계산기 없음)     |
| **limit**       | 📊     | 한도·공제 계산 (입력→최대치)     | 대출한도, 공제한도                       | `calculate-limit` |

### 예시

- 🧮 **amount**: 퇴직금 = 1일 평균임금 × 30 × (재직일수/365)
- ✅ **eligibility**: 주휴수당 = (주 15H 이상) AND (개근) → 지급/미지급
- ⚖️ **comparison**: 평균임금과 통상임금 중 큰 값 선택 (근기법 §2②)
- ⏱ **breakdown**: 09:00~23:30, 휴게 60분 → 정규 8H + 연장 5.5H + 야간 1.5H
- 📋 **checklist**: 근로계약서 필수 명시사항 7개 → ✅/⚠️/❌ 매핑
- 📊 **limit**: 퇴직소득공제 한도 = f(근속연수)

---

## 팩트체크 프로토콜 (요약)

> 전체 문서: [`references/fact_check_protocol.md`](references/fact_check_protocol.md)

**권장 정부 소스**

| 도메인    | 원문 URL                      | 용도                           |
| --------- | ----------------------------- | ------------------------------ |
| 법령 전체 | https://www.law.go.kr         | 법률·시행령·시행규칙·별표      |
| 국세      | https://www.nts.go.kr         | 소득세·법인세·부가세 요율·과표 |
| 최저임금  | https://www.minimumwage.go.kr | 연도별 최저임금 고시           |
| 노동      | https://www.moel.go.kr        | 고용노동부 고시·지침·서식      |
| 복지      | https://www.4insure.or.kr     | 4대보험 요율                   |
| 부동산    | https://www.molit.go.kr       | 국토부 고시·시행령             |

**기본 흐름**

1. `WebFetch {정부원문_URL}` — 법령 조문·고시 확인
2. SPA 실패 시 `WebSearch "법령명 조항 site:law.go.kr"` → 정적 미러 페이지 찾기
3. 그래도 실패 시 상수님(도메인 전문가)에게 "아래 수치를 확인 부탁드립니다" 요청
4. `SKILL.md` 하단 "검증 기록" 섹션에 `YYYY-MM-DD 확인자: XXX · 출처: URL` 기록

**출처 인용 형식**

```markdown
> 근기법 §56① "사용자는 연장근로에 대하여 통상임금의 100분의 50 이상을 가산하여 지급하여야 한다"
> — 출처: https://www.law.go.kr/법령/근로기준법 (2026-04-13 조회)
```

---

## 도메인 팀장 매핑 (자동 호출 게이트)

OMSC 는 도메인 분류 결과에 따라 다음 팀장을 **자동 호출** 해 팩트체크·검수 정확도를 높입니다. 게이트 동작 상세는 `/omsc` 명령어 파일 STEP 2·6 참조.

| 팀장          | 트리거 도메인       | 활용 자산                                                              | 책임 단계                  | 차단권                           |
| ------------- | ------------------- | ---------------------------------------------------------------------- | -------------------------- | -------------------------------- |
| 🏛 법무팀장    | 세무 · 법무 · 노무 | `korean-law` MCP (`search_law` / `get_law_text` / `verify_citations`)  | STEP 2 팩트체크 (병렬 A)   | 없음 — 실패 시 사용자 확인 요청  |
| 💼 재무팀장    | 세무               | WebFetch `nts.go.kr` + `세무조정계산서분석` 스킬 (필요 시)             | STEP 2 팩트체크 (병렬 B)   | 없음                             |
| ⚖️ 노무팀장    | 노무               | WebFetch `moel.go.kr` · `minimumwage.go.kr` · `4insure.or.kr`          | STEP 2 팩트체크 (병렬 B)   | 없음                             |
| 🔍 검수팀장    | 전체               | `verifier` 에이전트 (SKILL.md 조문 ↔ calculator.py 상수 1:1 대조)      | STEP 6 검증 후 재검사      | **인터랙티브 게이트 (1/2/3)**    |

**원칙**

- 팩트체크 단계는 **A·B 두 경로 모두 성공** 해야 통과 (병렬 + 교차 검증)
- 검수팀장 불일치 발견 시 **차단 없이 인터랙티브 게이트** — 상수님이 1(진행) / 2(수정 후 재검증) / 3(중단) 중 선택
- 모든 팀장 호출 결과 (자동검증 + 사용자 선택) 는 본 문서의 "검증 기록" 표에 자동 기록
- 1차 운영 4주 후 검수팀장 false positive 율 < 10% 달성 시 **차단권 승격 검토**

---

## scaffold.py 사용법

새 스킬의 뼈대를 1분 안에 만드는 CLI. 템플릿 치환 + 디렉토리 생성을 자동화합니다.

### 예시 1 — 종합소득세 계산기 (amount 모드)

```bash
python3 skills/omsc/references/scaffold.py new \
  --name income-tax \
  --domain 세무 \
  --law "소득세법 §55" \
  --calc-mode amount
```

### 예시 2 — 취득세 한도 계산기 (limit 모드, dry-run 으로 미리보기)

```bash
python3 skills/omsc/references/scaffold.py new \
  --name acquisition-tax \
  --domain 법무 \
  --law "지방세법 §11" \
  --calc-mode limit \
  --dry-run
```

### 예시 3 — 근로계약서 검토 (checklist 모드, calculator.py 생성 안 함)

```bash
python3 skills/omsc/references/scaffold.py new \
  --name contract-checklist \
  --domain 노무 \
  --law "근로기준법 §17" \
  --calc-mode checklist
```

### 부가 명령어

- `python3 scaffold.py list-templates` — 사용 가능한 템플릿 목록 표시
- `python3 scaffold.py validate --skill-dir skills/income-tax` — frontmatter · CLI 실행 검증

---

## 도메인 예시 카탈로그 (20+)

### 세무 (8개)

| 스킬                 | 도메인 | 법령                        | 모드   |
| -------------------- | ------ | --------------------------- | ------ |
| income-tax           | 세무   | 소득세법 §55                | amount |
| capital-gains-tax    | 세무   | 소득세법 §104 (양도소득세)  | amount |
| inheritance-gift-tax | 세무   | 상속세및증여세법 §26·56     | amount |
| corporate-tax        | 세무   | 법인세법 §55                | amount |
| vat                  | 세무   | 부가가치세법 §30            | amount |
| withholding-tax      | 세무   | 소득세법 §129 (원천징수)    | amount |
| year-end-settlement  | 세무   | 소득세법 §137 (연말정산)    | amount |
| rental-income-tax    | 세무   | 소득세법 §12 (주택임대소득) | amount |

### 법무 (6개)

| 스킬              | 도메인 | 법령                                       | 모드        |
| ----------------- | ------ | ------------------------------------------ | ----------- |
| inheritance-share | 법무   | 민법 §1009 (상속분)                        | amount      |
| stamp-filing-fee  | 법무   | 인지법 §2, 민사소송법 §116 (인지액·송달료) | amount      |
| acquisition-tax   | 법무   | 지방세법 §11                               | amount      |
| registration-tax  | 법무   | 지방세법 §28 (등록면허세)                  | amount      |
| notary-fee        | 법무   | 공증인수수료규칙                           | amount      |
| deposit-return    | 법무   | 주택임대차보호법 §3의3 (보증금반환)        | eligibility |

### 부동산 (3개)

| 스킬                          | 도메인 | 법령                              | 모드   |
| ----------------------------- | ------ | --------------------------------- | ------ |
| property-tax                  | 부동산 | 지방세법 §107 (재산세)            | amount |
| comprehensive-real-estate-tax | 부동산 | 종합부동산세법 §7                 | amount |
| housing-subscription-score    | 부동산 | 주택공급에관한규칙 §28 (청약가점) | amount |

### 노무 (기존 9개 외 확장 예시 3+)

| 스킬                   | 도메인 | 법령                              | 모드   |
| ---------------------- | ------ | --------------------------------- | ------ |
| dismissal-notice-pay   | 노무   | 근기법 §26 (해고예고수당)         | amount |
| wage-arrear            | 노무   | 근기법 §36·37 (임금체불 지연이자) | amount |
| parental-leave-benefit | 노무   | 고용보험법 §70 (육아휴직급여)     | amount |

---

## 네이밍 규칙

- **형식**: kebab-case 영문 (소문자 + 하이픈)
- **길이**: 3~30자
- **복수형 금지**: `severance-pays` ❌ → `severance-pay` ✅
- **한글·카멜케이스 금지**: `퇴직금계산기`, `calcSeverance` ❌

| 좋음              | 나쁨             | 이유            |
| ----------------- | ---------------- | --------------- |
| `severance-pay`   | `severance_pay`  | snake_case 금지 |
| `income-tax`      | `incomeTax`      | camelCase 금지  |
| `acquisition-tax` | `acquisitiontax` | 단어 구분 필요  |
| `overtime-pay`    | `overtime-pays`  | 복수형 금지     |
| `wage-base`       | `wage`           | 너무 짧고 모호  |

---

## 안티패턴 — 절대 하지 말 것

1. ❌ **팩트체크 없이 숫자 하드코딩**
   - 예: `MIN_WAGE_2026 = 10320` 을 언론 기사만 보고 기입. 반드시 `minimumwage.go.kr` 고시 원문 확인.

2. ❌ **너무 큰 단일 스킬**
   - 한 도메인에 subcommand 3개 이상이면 분리. 예: `tax-all` 안에 소득세·법인세·부가세를 함께 넣지 말고 각각 독립.

3. ❌ **calculator.py 가 SKILL.md 없이 혼자 존재**
   - Claude 가 언제·왜 호출할지 판단 못함. `SKILL.md` 가 "되묻기 규칙" 과 "입력 파싱" 을 제공해야 사용 가능.

4. ❌ **검증 시나리오 0건**
   - 리팩터링 시 회귀 감지 불가. 최소 4건 (정상 2, 경계 1, 예외 1).

5. ❌ **Python 외부 라이브러리 import**
   - `pandas`, `numpy`, `requests` 금지. 표준 라이브러리 + 순수 Python 만. (배포 환경 단순성 유지)

---

## 최종 체크리스트 (배포 전 10개)

- [ ] `SKILL.md` frontmatter `name`, `description`, `when_to_use` 3개 필드 채워짐
- [ ] 법령 근거 표에 조문·출처·조회일자 기록됨
- [ ] `calculator.py` 가 `--help` 로 subcommand 목록을 출력함
- [ ] 각 subcommand 가 JSON 출력 (`indent=2, ensure_ascii=False`)
- [ ] 표준 라이브러리만 사용 (`import` 문 검토)
- [ ] 검증 시나리오 4건 이상 `tests/` 에 존재
- [ ] `AGENTS.md` 스킬 목록 표 업데이트
- [ ] "알려진 한계" 섹션 3개 이상 명시
- [ ] "관련 스킬" 섹션 1개 이상 명시
- [ ] "검증 기록" 섹션에 도메인 전문가 확인 날짜·이름 기록

---

## 관련 스킬 (OMSC 로 만들어진 것들)

- `severance-pay` — amount 모드 레퍼런스
- `overtime-pay` — breakdown 모드 레퍼런스
- `wage-base` — comparison 모드 레퍼런스
- `unemployment-benefit` — eligibility 모드 레퍼런스
- `labor-contract-review` — checklist 모드 레퍼런스
- `minimum-wage` — eligibility + comparison 하이브리드 레퍼런스

---

## 면책

> ⚠️ OMSC 로 생성된 스킬은 **스캐폴딩(시작점)** 일 뿐입니다. 실제 운영 (고객 상담·법적 판단) 전에 **반드시 도메인 전문가 (상수님·공인노무사·세무사·변호사) 의 최종 검증** 을 받으세요. 법령·요율은 개정되며, 본 메타 스킬은 최신성을 자동 보장하지 않습니다.

## 검증 기록

| 날짜       | 확인자 | 내용                                                                                            |
| ---------- | ------ | ----------------------------------------------------------------------------------------------- |
| 2026-04-13 | 이상수 | 초기 작성 (템플릿 + scaffold CLI 검증)                                                          |
| 2026-05-04 | 이상수 | 도메인 팀장 게이트 추가 (법무·재무·노무 자동 호출 + 검수팀장 인터랙티브 게이트). `/omsc` STEP 2·6 동기화 |
