import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Routes that require authentication
const PROTECTED_ROUTES = [
  "/dashboard",
  "/chat",
  "/memories",
  "/documents",
  "/insights",
  "/analytics",
  "/settings",
  "/discovery",
  "/workspaces",
];

// Routes that should redirect to dashboard if authenticated
const AUTH_ROUTES = [
  "/login",
  "/signup",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // The auth_state cookie mirrors "a session exists" (set/cleared by
  // AuthProvider via setTokens/clearTokens). It is a UX gate only, not a
  // credential — pages still verify the real token client-side via
  // useProtectedRoute, and the API validates the actual bearer token.
  const hasSession = !!request.cookies.get("auth_state")?.value;
  const isProtectedRoute = PROTECTED_ROUTES.some((route) => pathname.startsWith(route));
  const isAuthRoute = AUTH_ROUTES.some((route) => pathname.startsWith(route));

  // Redirect authenticated users away from auth pages
  if (hasSession && isAuthRoute) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // Redirect unauthenticated users to login
  if (!hasSession && isProtectedRoute) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!api|_next/static|_next/image|favicon.ico|public).*)",
  ],
};
