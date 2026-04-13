import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(
          cookiesToSet: {
            name: string;
            value: string;
            options?: CookieOptions;
          }[],
        ) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(
              name,
              value,
              options as Record<string, unknown>,
            ),
          );
        },
      },
    },
  );

  const {
    data: { user },
  } = await supabase.auth.getUser();

  // 인증 불필요 경로
  const guestPaths = [
    "/contract",
    "/documents",
    "/payslip",
    "/employees",
    "/wage-ledger",
    "/work-rules",
    "/archive",
    "/insurance",
    "/severance",
    "/terminate",
    "/guide",
    "/convert",
  ];
  const publicPaths = [
    "/login",
    "/signup",
    "/auth/callback",
    "/about",
    "/membership",
    "/terms",
    "/privacy",
    "/reset-password",
    "/forgot-password",
    "/contact",
    "/consult",
    "/shutdown-allowance",
    "/opengraph-image",
    "/sitemap.xml",
    "/robots.txt",
    "/offline",
    "/join",
    "/auto-login",
    "/api/auto-login",
    "/skills",
    ...guestPaths,
  ];
  const isPublicPath = publicPaths.some((p) =>
    request.nextUrl.pathname.startsWith(p),
  );

  if (!user && !isPublicPath && request.nextUrl.pathname !== "/") {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("redirect", request.nextUrl.pathname);
    return NextResponse.redirect(url);
  }

  return supabaseResponse;
}
