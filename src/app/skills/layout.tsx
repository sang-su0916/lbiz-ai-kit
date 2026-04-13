import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Claude 스킬 카탈로그 — nomu-oneQ-skill.V",
  description:
    "한국 노무 도메인 전용 Claude Code 스킬 패키지. 퇴직금·연차수당·4대보험·실업급여·통상임금·근로계약서 6개 스킬의 트리거 키워드와 사용 방법을 안내합니다.",
};

export default function SkillsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
