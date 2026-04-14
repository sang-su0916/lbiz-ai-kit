---
name: financial-statement-trend
description: 재무제표 수평·수직·추세 분석 (horizontal·vertical·trend). 비율이 아닌 전기 대비 증감·구성비·3~5개년 지수화·CAGR에 집중. Financial statement trend analysis.
when_to_use: 전기 대비 증감액·증감율 분석, 매출·자산 구성비(100% 기준) 산출, 3~5개년 추세·CAGR·지수화, 재무제표 기간 비교, 성장성·수익성 추세 점검
---

# 재무제표 추세·수평·수직 분석기 (financial-statement-trend)

⚠️ **반드시 계산기 CLI를 실행하세요. 직접 계산 금지** — hallucination 방지.

## 언제 사용

- **수평분석**: 전기 대비 당기 증감액·증감율 — "매출 11% 증가, 영업이익 17% 감소" 같은 비교
- **수직분석**: 매출(손익) 또는 총자산(재무상태) = 100% 기준 구성비 — 원가율·마진율·자산구성
- **추세분석**: 3~5개년 지수화(기준연도=100) + YoY 증감율 + CAGR — 장기 성장성 평가
- `financial-ratio` 와의 차이: 본 스킬은 **비율이 아닌 증감·구성비·추세**를 다룸. 비율(부채비율·ROE 등)은 `financial-ratio` 사용.

## 법령·근거

| 근거                 | 내용                                   | 출처                      |
| -------------------- | -------------------------------------- | ------------------------- |
| 일반기업회계기준     | 재무제표 표시·비교표시 원칙            | K-IFRS / 일반기업회계기준 |
| 전통적 재무분석 기법 | horizontal / vertical / trend analysis | 재무분석 교과서 표준      |
| CAGR 공식            | `(end/start)^(1/(n-1)) - 1`            | 재무관리 표준 공식        |

## 핵심 공식

```
─ 수평분석 ───────────────────────────────────────────────
증감액      = 당기 − 전기
증감율 (%)  = (당기 − 전기) / |전기| × 100

─ 수직분석 ───────────────────────────────────────────────
손익계산서: 각 항목 / 매출 × 100 (매출 = 100%)
재무상태표: 각 항목 / 총자산 × 100 (총자산 = 100%)

─ 추세분석 ───────────────────────────────────────────────
지수(index)  = 당해 값 / 기준연도 값 × 100
YoY          = (당해 − 전년) / |전년| × 100
CAGR (%)     = ((end / start)^(1/(n−1)) − 1) × 100
```

## CLI 사용법

### `horizontal` — 수평분석 (전년 대비 증감)

간편 모드 (개별 플래그):

```bash
python3 skills/financial-statement-trend/references/calculator.py horizontal \
  --revenue-current 500000000 --revenue-prior 450000000 \
  --cogs-current 325000000 --cogs-prior 270000000 \
  --operating-income-current 50000000 --operating-income-prior 60000000 \
  --net-income-current 40000000 --net-income-prior 48000000
```

일괄 모드 (JSON):

```bash
python3 skills/financial-statement-trend/references/calculator.py horizontal \
  --items-current '{"revenue": 500000000, "operating_income": 50000000}' \
  --items-prior   '{"revenue": 450000000, "operating_income": 60000000}'
```

출력: `items`(항목별 `current`/`prior`/`change_amount`/`change_rate`), `flags`(경보), `summary`(요약 문장).

지원 항목: `revenue`, `cogs`, `gross_profit`, `sga`, `operating_income`, `net_income`, `total_assets`, `total_liabilities`, `total_equity`, `accounts_receivable`, `inventory`.

### `vertical` — 수직분석 (구성비)

손익계산서(`is`) — 매출 = 100% 기준:

```bash
python3 skills/financial-statement-trend/references/calculator.py vertical \
  --statement is \
  --revenue 500000000 --cogs 325000000 --sga 100000000 \
  --operating-income 50000000 --net-income 40000000
```

재무상태표(`bs`) — 총자산 = 100% 기준:

```bash
python3 skills/financial-statement-trend/references/calculator.py vertical \
  --statement bs \
  --total-assets 500000000 --current-assets 200000000 --non-current-assets 300000000 \
  --current-liabilities 100000000 --non-current-liabilities 150000000 --total-equity 250000000
```

### `trend` — 추세분석 (3~5개년)

```bash
python3 skills/financial-statement-trend/references/calculator.py trend \
  --years "2022,2023,2024,2025,2026" \
  --values "400000000,420000000,450000000,480000000,500000000" \
  --label "매출"
```

출력: `index`(기준=100 지수), `yoy_change_rate`(전년 대비 %), `cagr`(연평균 성장율 %), `interpretation`(해석 문장).

## 해석 플래그 규칙

| 규칙                                  | 경보                    |
| ------------------------------------- | ----------------------- |
| 매출 증가율 > 영업이익 증가율         | 성장성 대비 수익성 저하 |
| 매출원가율(당기/전기) 3%p 이상 증가   | 원가구조 악화           |
| 부채 증가율 > 자산 증가율             | 재무구조 악화           |
| 매출채권 증가율 > 매출 증가율 + 5%p   | 회수 지연 우려          |
| CAGR 음수                             | 장기 마이너스 성장      |
| trend 최근 추세 반전 (전년 +, 당해 −) | 최근 추세 반전          |
| vertical 영업이익률 < 0               | 영업적자                |
| vertical 자기자본비율 < 30%           | 자본 취약               |

## 입력 파싱 가이드

| 사용자 입력 예                        | 액션         | 비고                      |
| ------------------------------------- | ------------ | ------------------------- |
| "매출 5억(당기)/4.5억(전기) 증감율?"  | `horizontal` | `--revenue-*` 만으로 충분 |
| "매출 대비 원가율·영업이익률 구성비"  | `vertical`   | `--statement is`          |
| "자산 구성 — 유동자산 vs. 비유동자산" | `vertical`   | `--statement bs`          |
| "최근 5년 매출 추세·CAGR 보자"        | `trend`      | 연도·값 콤마 리스트       |
| "전기 대비 손익 전체 변화"            | `horizontal` | 여러 항목 한 번에         |

## 되묻기 규칙 (정보 부족 시)

1. **비교 기간 확인**: "당기(current)·전기(prior) 기준인가요? 아니면 3년 이상 추세가 필요하시면 `trend` 모드로 진행합니다."
2. **연결 vs. 별도**: "연결재무제표·별도재무제표 여부는 구성비와 증감율에 영향을 줍니다. 기준을 통일해서 넣어주세요."
3. **특별손익 유무**: "전기·당기 사이 자산처분이익·감액손실 등 일회성 요인은 증감율을 왜곡합니다. 정상화한 수치를 넣을지 확인해주세요."
4. **손익 vs. 재무상태**: "수직분석은 손익(`is`)과 재무상태(`bs`) 중 어느 쪽인가요? 기준치가 다릅니다."
5. **추세 기간**: "몇 개년을 보고 싶으신가요? 3년(초단기 추세)·5년(표준)·10년(장기) 중 선택 가능합니다."

## 도메인 특수 규칙

- **전기 0 또는 음수**: 증감율(%) 산출 불가 — JSON `change_rate: null`
- **기준연도 0**: trend 지수화 실패 — `error: "base year value must not be 0"`
- **CAGR는 시작·종료 모두 양수일 때만 의미 있음**: 적자→흑자, 흑자→적자 전환 구간에는 CAGR 미산출(`null`)
- **수평분석 `change_rate`는 전기 절대값 기준**: 전기 적자(-100) → 당기 +50 증가도 양수로 표시됨. 의미 해석은 별도 필요
- **구성비는 반올림 합 ≠ 100% 가능**: 예) cogs 65.01 + gross 34.99 → 100.00, 반올림 누적 오차 있음

## 응답 포맷

계산 결과에 다음 항목을 포함하세요.

- 입력 재무제표 요약
- 모드별 핵심 결과 (증감·구성비·지수+CAGR)
- 경보 플래그 (`flags` 배열)
- 해석 문장 (`summary` / `interpretation`)
- 면책 문구 (`disclaimer`)

**면책**: 본 분석은 일반기업회계기준·K-IFRS 재무제표 표시 원칙에 따른 참고치입니다. 업종·회계정책·특별손익 여부에 따라 해석이 달라질 수 있으며, 실제 경영 판단은 회계사·재무전문가 검토가 필요합니다.

## 알려진 한계

1. **비교 기간 단방향** — horizontal은 2개 기간만, trend는 n개 기간이지만 계절성(분기)·세그먼트(사업부) 분해 미지원.
2. **구성비 업종 비교 없음** — 제조업·서비스업·금융업 간 구성비는 본질적으로 다름. 업종 평균치 DB 미탑재.
3. **회계정책 변경 영향 미반영** — 수익인식 기준 변경(K-IFRS 1115 등), 리스회계 전환(K-IFRS 1116) 등은 전기·당기 직접 비교 불가. 입력 전 기준 통일 필요.
4. **CAGR은 시작·종료만 반영** — 중간 년도 변동성·표준편차 미고려. "CAGR 10% 안정 성장"과 "CAGR 10% 급락 후 반등" 구분 안 됨.
5. **연결범위·M&A 보정 없음** — 사업결합·사업분할로 범위가 달라진 해는 동일 범위로 직접 비교 불가. 본 계산기는 입력값을 그대로 사용.
6. **명목 금액 기준 (인플레이션 미조정)** — 장기 추세 해석 시 실질 증감율과 다를 수 있음.

## 관련 스킬

- `financial-ratio` — 재무비율 분석 (유동성·안정성·수익성·활동성). 본 스킬과 상호보완 (비율 vs. 증감·구성)
- `financial-diagnosis` — 재무비율 종합 점수·등급 진단. 본 스킬의 추세 결과를 입력 근거로 활용 가능
- `break-even` — 손익분기점 분석 (고정비·변동비 구조). vertical의 원가구조와 연계
- `depreciation` — 감가상각비 (재무제표 비용·자산 감액 항목)
- `omsc` — 본 스킬은 OMSC scaffold로 생성된 경영 도메인 스킬

## 검증 기록

| 날짜       | 확인자 | 내용                                                                                                                              |
| ---------- | ------ | --------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-14 | 상수님 | horizontal·vertical·trend 3개 CLI 정상 실행 확인. FST-01~04 검증 시나리오 (증감율 11.11%, 원가율 65.00%, CAGR 21.00%·5.74%) PASS. |
