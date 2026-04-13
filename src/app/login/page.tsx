"use client";

import { useEffect, useState, Suspense } from "react";
import { createClient } from "@/lib/supabase/client";
import { useRouter, useSearchParams } from "next/navigation";

const HOMEPAGE_LOGIN_URL =
  "https://lbiz-partners.com/api/app-redirect?app=labor";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin w-8 h-8 border-2 border-[var(--primary)] border-t-transparent rounded-full" />
        </div>
      }
    >
      <LoginHandler />
    </Suspense>
  );
}

function LoginHandler() {
  const [processing, setProcessing] = useState(true); // 기본 true: 항상 로딩부터
  const [error, setError] = useState("");
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/dashboard";
  const errorParam = searchParams.get("error");
  const supabase = createClient();

  useEffect(() => {
    if (typeof window === "undefined") return;

    // 1. URL 해시에 access_token이 있으면 세션 설정 (레거시 호환)
    const hash = window.location.hash;
    if (hash && hash.includes("access_token")) {
      const params = new URLSearchParams(hash.substring(1));
      const accessToken = params.get("access_token");
      const refreshToken = params.get("refresh_token");

      if (accessToken && refreshToken) {
        supabase.auth
          .setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          })
          .then(({ error: sessionError }) => {
            if (sessionError) {
              setProcessing(false);
              setError("인증에 실패했습니다. 홈페이지에서 다시 시도해주세요.");
              return;
            }
            window.history.replaceState(
              null,
              "",
              window.location.pathname + window.location.search,
            );
            router.push(redirect);
          });
        return;
      }
    }

    // 2. auto-login 실패로 돌아온 경우 → 에러 표시 (무한루프 방지)
    if (errorParam) {
      setProcessing(false);
      const errorMessages: Record<string, string> = {
        no_token: "인증 토큰이 없습니다.",
        invalid_token: "인증 토큰이 유효하지 않습니다.",
        token_expired: "인증 토큰이 만료되었습니다.",
        server_config: "서버 설정 오류입니다.",
        create_failed: "계정 생성에 실패했습니다.",
        link_failed: "로그인 링크 생성에 실패했습니다.",
        auth_failed: "인증에 실패했습니다.",
      };
      setError(
        errorMessages[errorParam] ||
          "인증에 실패했습니다. 홈페이지에서 다시 시도해주세요.",
      );
      return;
    }

    // 3. 이미 로그인된 경우 → 바로 이동
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        router.push(redirect);
      } else {
        // 4. 로그인 안 됨 → 홈페이지 자동 로그인 흐름으로 리다이렉트
        window.location.href = HOMEPAGE_LOGIN_URL;
      }
    });
  }, [supabase, router, redirect, errorParam]);

  if (processing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg)]">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-[var(--primary)] border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-[var(--text-muted)]">자동 로그인 중...</p>
        </div>
      </div>
    );
  }

  // 에러가 있거나 auto-login 실패 시 수동 안내
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg)] px-4">
      <div className="w-full max-w-md text-center">
        <a
          href="https://lbiz-partners.com"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img
            src="/gold-logo.png"
            alt="엘비즈파트너스"
            className="h-14 w-auto mx-auto mb-4 object-contain"
          />
        </a>
        <h1 className="text-2xl font-bold text-[var(--text)] mb-2">노무원큐</h1>
        <p className="text-[var(--text-muted)] mb-8 leading-relaxed">
          엘비즈파트너스 홈페이지 회원 전용 서비스입니다.
        </p>

        {error && (
          <div className="text-red-500 text-sm bg-red-50 px-4 py-2 rounded-lg mb-4">
            {error}
          </div>
        )}

        <a
          href={HOMEPAGE_LOGIN_URL}
          className="inline-block px-8 py-3 bg-[var(--primary)] text-white rounded-xl font-bold hover:opacity-90 transition-opacity shadow-lg"
        >
          홈페이지에서 로그인하고 시작하기
        </a>

        <p className="mt-6 text-sm text-[var(--text-muted)]">
          아직 회원이 아니신가요?{" "}
          <a
            href="https://lbiz-partners.com/signup"
            className="text-[var(--primary)] font-semibold"
          >
            회원가입
          </a>
        </p>

        <div className="mt-6 pt-4 border-t border-[var(--border)] text-xs text-[var(--text-muted)]">
          <a
            href="tel:010-3709-5785"
            className="text-[var(--text)] font-semibold"
          >
            &#128222; 010-3709-5785
          </a>
          {" · "}
          <span>sangsu0916@naver.com</span>
        </div>
      </div>
    </div>
  );
}
