import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "엘비즈 AI 키트 · 컨설팅 스킬 패키지",
  description:
    "한국 비즈니스 도메인(노무·세무·법무·경영) 전문 Claude Code 스킬 패키지. 퇴직금·연차수당·4대보험·실업급여·종합소득세 등 11개 스킬의 트리거 키워드와 사용 방법을 안내합니다.",
};

export default function SkillsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
