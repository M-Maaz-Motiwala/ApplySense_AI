import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("access_token")?.value;
  const isAuthPage = request.nextUrl.pathname.startsWith("/auth");
  const isProtectedPage = 
    request.nextUrl.pathname.startsWith("/applications") || 
    request.nextUrl.pathname.startsWith("/jobs") || 
    request.nextUrl.pathname.startsWith("/dashboard") ||
    request.nextUrl.pathname.startsWith("/onboarding");

  if (isProtectedPage && !token) {
    return NextResponse.redirect(new URL("/auth/login", request.url));
  }

  if (isAuthPage && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/applications/:path*",
    "/jobs/:path*",
    "/dashboard/:path*",
    "/onboarding/:path*",
    "/auth/:path*",
  ],
};
