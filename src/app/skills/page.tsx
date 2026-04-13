"use client";

const SKILLS = [
  {
    id: "severance-pay",
    emoji: "💼",
    title: "퇴직금 계산",
    subtitle: "평균임금 기반 정확 산정",
    description:
      "재직기간·평균임금을 기반으로 퇴직금을 정확히 산정합니다. 중간정산 이력 공제, 1년 미만 비례 계산까지 지원합니다.",
    triggers: ["퇴직금", "퇴직급여", "severance"],
    triggerExample:
      "입사일 2021년 3월 1일, 퇴사일 2026년 3월 31일, 월급 280만원인 경우 퇴직금을 계산해줘",
    resultExample:
      "평균임금 92,308원 × 30일 × 재직연수 5.08년 → 퇴직금 약 14,065,200원 (원 단위 절사)",
    source:
      "https://github.com/sang-su0916/nomu-oneQ-skill.V/tree/main/skills/severance-pay",
    accentColor: "#dbeafe",
    accentText: "#1d4ed8",
  },
  {
    id: "annual-leave",
    emoji: "📅",
    title: "연차수당 계산",
    subtitle: "발생일수 및 미사용수당 산정",
    description:
      "1년 미만 월차(11개), 1년 이상 15일+α, 회계연도 기준/입사일 기준 모두 지원합니다. 미사용 연차수당까지 자동 계산합니다.",
    triggers: ["연차", "연차수당", "미사용연차"],
    triggerExample:
      "입사일 2024년 7월 1일 기준으로 2026년 4월까지 발생한 연차일수와 미사용수당을 알려줘",
    resultExample:
      "회계연도 기준 2025년 발생 15일, 2026년 발생 10일(비례) — 미사용 5일 × 통상임금 = 수당 약 500,000원",
    source:
      "https://github.com/sang-su0916/nomu-oneQ-skill.V/tree/main/skills/annual-leave",
    accentColor: "#d1fae5",
    accentText: "#065f46",
  },
  {
    id: "four-insurances",
    emoji: "🛡️",
    title: "4대보험료 계산",
    subtitle: "2026년 확정 요율 적용",
    description:
      "국민연금·건강보험·고용보험·산재보험의 2026년 확정 요율로 사업주·근로자 부담분을 분리하여 정확히 산출합니다.",
    triggers: ["4대보험", "사회보험", "보험료"],
    triggerExample:
      "월 급여 320만원 근로자의 4대보험료 사업주·근로자 부담분을 각각 계산해줘",
    resultExample:
      "근로자: 국민연금 144,000원 + 건강보험 113,490원 + 고용보험 25,600원 = 합계 283,090원",
    source:
      "https://github.com/sang-su0916/nomu-oneQ-skill.V/tree/main/skills/four-insurances",
    accentColor: "#fef3c7",
    accentText: "#92400e",
  },
  {
    id: "unemployment-benefit",
    emoji: "🔍",
    title: "실업급여 계산",
    subtitle: "자격·일액·소정급여일수 판정",
    description:
      "이직 사유·피보험 기간·연령으로 수급 자격을 판정하고, 구직급여 일액과 소정급여일수를 고용보험법 기준으로 산출합니다.",
    triggers: ["실업급여", "구직급여"],
    triggerExample:
      "만 42세, 피보험 기간 3년 2개월, 이직 전 3개월 평균임금 일 85,000원인 경우 실업급여를 계산해줘",
    resultExample:
      "구직급여 일액 60,350원 (상한 66,000원 미만) × 소정급여일수 180일 = 총 10,863,000원",
    source:
      "https://github.com/sang-su0916/nomu-oneQ-skill.V/tree/main/skills/unemployment-benefit",
    accentColor: "#ede9fe",
    accentText: "#4c1d95",
  },
  {
    id: "wage-base",
    emoji: "⚖️",
    title: "통상임금 / 평균임금",
    subtitle: "환산·산정 — 다른 계산의 베이스",
    description:
      "정기적·일률적·고정적 임금 항목을 구분해 통상임금을 산출하고, 3개월 총임금÷총일수로 평균임금을 계산합니다. 시급 환산도 지원합니다.",
    triggers: ["통상임금", "평균임금", "시급 환산"],
    triggerExample:
      "기본급 230만원, 직책수당 20만원, 식대 10만원, 상여금(600%) 있을 때 통상임금을 구해줘",
    resultExample:
      "통상임금: 기본급 230만원 + 직책수당 20만원 = 250만원 (식대 비과세·상여금 비정기 제외) → 시급 11,905원",
    source:
      "https://github.com/sang-su0916/nomu-oneQ-skill.V/tree/main/skills/wage-base",
    accentColor: "#fee2e2",
    accentText: "#991b1b",
  },
  {
    id: "labor-contract-review",
    emoji: "📝",
    title: "근로계약서 검토",
    subtitle: "매뉴얼 체크리스트 (근기법 §17)",
    description:
      "근로기준법 제17조 필수 명시사항 9개 항목을 체크리스트로 검토합니다. 계산 없이 Claude가 계약서를 읽고 누락·위반 사항을 짚어 드립니다.",
    triggers: ["근로계약서", "근로계약 검토"],
    triggerExample:
      "첨부한 근로계약서에 근기법 §17 필수 사항이 모두 포함되어 있는지 검토해줘",
    resultExample:
      "✅ 임금·소정근로시간·휴일·연차 명시 확인 / ⚠️ 취업 장소·종사 업무 기재 미흡 / ❌ 근로계약서 교부 문구 누락",
    source:
      "https://github.com/sang-su0916/nomu-oneQ-skill.V/tree/main/skills/labor-contract-review",
    accentColor: "#f0fdf4",
    accentText: "#166534",
  },
];

export default function SkillsPage() {
  return (
    <>
      <style jsx global>{`
        @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;800&display=swap");

        .skills-page * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        .skills-page {
          font-family:
            "Noto Sans KR",
            -apple-system,
            BlinkMacSystemFont,
            sans-serif;
          color: #1e293b;
          line-height: 1.7;
          background: #ffffff;
        }

        /* Hero */
        .skills-hero {
          background: linear-gradient(
            135deg,
            #1e3a5f 0%,
            #2563eb 50%,
            #3b82f6 100%
          );
          color: white;
          padding: 72px 24px 88px;
          text-align: center;
          position: relative;
          overflow: hidden;
        }
        .skills-hero::before {
          content: "";
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background:
            radial-gradient(
              circle at 25% 25%,
              rgba(255, 255, 255, 0.08) 0%,
              transparent 50%
            ),
            radial-gradient(
              circle at 75% 75%,
              rgba(255, 255, 255, 0.04) 0%,
              transparent 50%
            );
        }
        .skills-hero-content {
          position: relative;
          max-width: 760px;
          margin: 0 auto;
        }
        .skills-hero-badge {
          display: inline-block;
          background: rgba(255, 255, 255, 0.15);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          padding: 5px 14px;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 500;
          margin-bottom: 22px;
          letter-spacing: 0.2px;
        }
        .skills-hero h1 {
          font-size: clamp(32px, 5.5vw, 52px);
          font-weight: 800;
          letter-spacing: -1px;
          margin-bottom: 14px;
        }
        .skills-hero p {
          font-size: clamp(15px, 2.2vw, 18px);
          opacity: 0.88;
          max-width: 580px;
          margin: 0 auto;
          line-height: 1.8;
        }

        /* How-it-works */
        .skills-how {
          background: #f8fafc;
          padding: 60px 24px;
        }
        .skills-how-inner {
          max-width: 860px;
          margin: 0 auto;
        }
        .skills-how h2 {
          font-size: 22px;
          font-weight: 800;
          color: #1e293b;
          margin-bottom: 6px;
        }
        .skills-how-desc {
          font-size: 14px;
          color: #64748b;
          margin-bottom: 28px;
        }
        .skills-flow {
          display: flex;
          align-items: stretch;
          gap: 0;
          flex-wrap: wrap;
        }
        .skills-flow-step {
          flex: 1;
          min-width: 180px;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px 18px;
          position: relative;
        }
        .skills-flow-step + .skills-flow-step {
          margin-left: 0;
        }
        .skills-flow-arrow {
          display: flex;
          align-items: center;
          padding: 0 10px;
          color: #94a3b8;
          font-size: 20px;
          flex-shrink: 0;
        }
        .skills-flow-num {
          width: 26px;
          height: 26px;
          background: #2563eb;
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 700;
          margin-bottom: 10px;
        }
        .skills-flow-step h4 {
          font-size: 14px;
          font-weight: 700;
          color: #1e293b;
          margin-bottom: 4px;
        }
        .skills-flow-step p {
          font-size: 12px;
          color: #64748b;
          line-height: 1.6;
        }
        .skills-flow-code {
          display: inline-block;
          background: #f1f5f9;
          color: #0f172a;
          font-family: "SF Mono", "Fira Code", monospace;
          font-size: 11px;
          padding: 2px 6px;
          border-radius: 4px;
          margin-top: 4px;
        }

        /* Grid */
        .skills-grid-section {
          padding: 64px 24px;
          max-width: 1160px;
          margin: 0 auto;
        }
        .skills-grid-title {
          font-size: clamp(24px, 3.5vw, 32px);
          font-weight: 800;
          text-align: center;
          margin-bottom: 8px;
          letter-spacing: -0.5px;
        }
        .skills-grid-subtitle {
          text-align: center;
          color: #64748b;
          font-size: 15px;
          margin-bottom: 44px;
        }
        .skills-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 20px;
        }
        @media (min-width: 768px) {
          .skills-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
        @media (min-width: 1024px) {
          .skills-grid {
            grid-template-columns: repeat(3, 1fr);
          }
        }

        /* Card */
        .skill-card {
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          overflow: hidden;
          background: white;
          transition:
            box-shadow 0.2s,
            transform 0.2s;
          display: flex;
          flex-direction: column;
        }
        .skill-card:hover {
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
          transform: translateY(-3px);
        }
        .skill-card-header {
          padding: 24px 24px 16px;
          display: flex;
          align-items: flex-start;
          gap: 14px;
        }
        .skill-card-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 22px;
          flex-shrink: 0;
        }
        .skill-card-titles {
          flex: 1;
          min-width: 0;
        }
        .skill-card-titles h3 {
          font-size: 17px;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 3px;
        }
        .skill-card-titles span {
          font-size: 13px;
          color: #64748b;
        }
        .skill-card-body {
          padding: 0 24px 20px;
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .skill-card-desc {
          font-size: 14px;
          color: #475569;
          line-height: 1.7;
        }
        .skill-card-triggers {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .skill-card-trigger-chip {
          font-size: 12px;
          font-weight: 500;
          padding: 3px 9px;
          border-radius: 999px;
          border: 1px solid;
        }
        .skill-card-qa {
          background: #f8fafc;
          border-radius: 10px;
          padding: 14px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .skill-card-q,
        .skill-card-a {
          display: flex;
          gap: 8px;
          align-items: flex-start;
          font-size: 13px;
          line-height: 1.6;
          color: #334155;
        }
        .skill-card-q-label {
          font-weight: 700;
          color: #2563eb;
          flex-shrink: 0;
          margin-top: 1px;
        }
        .skill-card-a-label {
          font-weight: 700;
          color: #059669;
          flex-shrink: 0;
          margin-top: 1px;
        }
        .skill-card-footer {
          padding: 14px 24px;
          border-top: 1px solid #f1f5f9;
        }
        .skill-card-source {
          font-size: 12px;
          color: #94a3b8;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 4px;
          transition: color 0.15s;
        }
        .skill-card-source:hover {
          color: #2563eb;
        }

        /* Disclaimer */
        .skills-disclaimer {
          background: #fffbeb;
          border-top: 1px solid #fde68a;
          padding: 28px 24px;
        }
        .skills-disclaimer-inner {
          max-width: 860px;
          margin: 0 auto;
          display: flex;
          gap: 12px;
          align-items: flex-start;
        }
        .skills-disclaimer-icon {
          font-size: 20px;
          flex-shrink: 0;
          margin-top: 2px;
        }
        .skills-disclaimer p {
          font-size: 13px;
          color: #78350f;
          line-height: 1.7;
        }
        .skills-disclaimer strong {
          font-weight: 700;
        }

        /* GitHub CTA */
        .skills-cta {
          padding: 48px 24px;
          text-align: center;
          border-top: 1px solid #e2e8f0;
        }
        .skills-cta p {
          font-size: 14px;
          color: #64748b;
          margin-bottom: 14px;
        }
        .skills-cta-link {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: #0f172a;
          color: white;
          padding: 11px 24px;
          border-radius: 10px;
          font-size: 14px;
          font-weight: 600;
          text-decoration: none;
          transition:
            background 0.2s,
            transform 0.15s;
        }
        .skills-cta-link:hover {
          background: #1e293b;
          transform: translateY(-1px);
        }

        @media (max-width: 640px) {
          .skills-hero {
            padding: 52px 20px 68px;
          }
          .skills-flow {
            flex-direction: column;
          }
          .skills-flow-arrow {
            transform: rotate(90deg);
            justify-content: center;
            padding: 4px 0;
          }
          .skills-grid-section {
            padding: 48px 16px;
          }
        }
      `}</style>

      <div className="skills-page">
        {/* Hero */}
        <section className="skills-hero">
          <div className="skills-hero-content">
            <span className="skills-hero-badge">
              노무원큐 lab · Claude Code 스킬 패키지
            </span>
            <h1>Claude Code 스킬 패키지</h1>
            <p>
              한국 노무 도메인의 계산·판정·검토 작업을
              <br />
              Claude가 정확하게 수행하도록 훈련된 6개 스킬 모음입니다.
            </p>
          </div>
        </section>

        {/* How it works */}
        <section className="skills-how">
          <div className="skills-how-inner">
            <h2>스킬 패턴이란?</h2>
            <p className="skills-how-desc">
              트리거 키워드가 감지되면 Claude가 SKILL.md를 읽고 calculator.py를
              실행하는 3단계 흐름입니다.
            </p>
            <div className="skills-flow">
              <div className="skills-flow-step">
                <div className="skills-flow-num">1</div>
                <h4>트리거 감지</h4>
                <p>
                  사용자 질문에서 키워드(예: "퇴직금", "연차수당")를 인식합니다.
                </p>
              </div>
              <div className="skills-flow-arrow">→</div>
              <div className="skills-flow-step">
                <div className="skills-flow-num">2</div>
                <h4>SKILL.md 읽기</h4>
                <p>
                  해당 스킬의 도메인 규칙·공식·법령 근거를 파악합니다.
                  <span className="skills-flow-code">
                    skills/&lt;스킬&gt;/SKILL.md
                  </span>
                </p>
              </div>
              <div className="skills-flow-arrow">→</div>
              <div className="skills-flow-step">
                <div className="skills-flow-num">3</div>
                <h4>calculator.py 실행</h4>
                <p>
                  머릿속 계산(hallucination) 대신 Python CLI로 정확한 수치를
                  산출합니다.
                  <span className="skills-flow-code">
                    python3 skills/&lt;스킬&gt;/references/calculator.py
                  </span>
                </p>
              </div>
              <div className="skills-flow-arrow">→</div>
              <div className="skills-flow-step">
                <div className="skills-flow-num">4</div>
                <h4>결과 응답</h4>
                <p>
                  계산 근거·법령 조문과 함께 최종 결과를 사용자에게 전달합니다.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Skill Cards */}
        <section className="skills-grid-section">
          <h2 className="skills-grid-title">6개 스킬 카탈로그</h2>
          <p className="skills-grid-subtitle">
            키워드를 포함한 질문을 입력하면 해당 스킬이 자동으로 활성화됩니다.
          </p>

          <div className="skills-grid">
            {SKILLS.map((skill) => (
              <div key={skill.id} className="skill-card">
                <div className="skill-card-header">
                  <div
                    className="skill-card-icon"
                    style={{ background: skill.accentColor }}
                  >
                    {skill.emoji}
                  </div>
                  <div className="skill-card-titles">
                    <h3>{skill.title}</h3>
                    <span>{skill.subtitle}</span>
                  </div>
                </div>

                <div className="skill-card-body">
                  <p className="skill-card-desc">{skill.description}</p>

                  {/* Trigger chips */}
                  <div>
                    <p
                      style={{
                        fontSize: "11px",
                        fontWeight: 600,
                        color: "#94a3b8",
                        textTransform: "uppercase",
                        letterSpacing: "0.5px",
                        marginBottom: "6px",
                      }}
                    >
                      트리거 키워드
                    </p>
                    <div className="skill-card-triggers">
                      {skill.triggers.map((t) => (
                        <span
                          key={t}
                          className="skill-card-trigger-chip"
                          style={{
                            background: skill.accentColor,
                            borderColor: skill.accentColor,
                            color: skill.accentText,
                          }}
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Q&A example */}
                  <div className="skill-card-qa">
                    <div className="skill-card-q">
                      <span className="skill-card-q-label">Q</span>
                      <span>{skill.triggerExample}</span>
                    </div>
                    <div className="skill-card-a">
                      <span className="skill-card-a-label">A</span>
                      <span>{skill.resultExample}</span>
                    </div>
                  </div>
                </div>

                <div className="skill-card-footer">
                  <a
                    href={skill.source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="skill-card-source"
                  >
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                    </svg>
                    GitHub 소스 보기
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Disclaimer */}
        <div className="skills-disclaimer">
          <div className="skills-disclaimer-inner">
            <span className="skills-disclaimer-icon">⚠️</span>
            <p>
              <strong>면책 안내</strong>: 본 스킬의 계산 결과는 일반적인 법령
              산정 기준에 따른 참고치입니다. 실제 적용은{" "}
              <strong>단체협약·취업규칙·고용센터·공인노무사 자문</strong>에 따라
              달라질 수 있으며, 법적 효력을 보증하지 않습니다. 중요한 노무
              판단은 반드시 전문가에게 확인하시기 바랍니다.
            </p>
          </div>
        </div>

        {/* GitHub CTA */}
        <div className="skills-cta">
          <p>
            스킬 전체 소스코드 · SKILL.md · calculator.py · 테스트는 GitHub에서
            확인하세요.
          </p>
          <a
            href="https://github.com/sang-su0916/nomu-oneQ-skill.V"
            target="_blank"
            rel="noopener noreferrer"
            className="skills-cta-link"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            sang-su0916/nomu-oneQ-skill.V
          </a>
        </div>
      </div>
    </>
  );
}
