import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// Only these are public. Everything else (pages AND /api routes) requires a Clerk session.
const isAuthPage = createRouteMatcher(["/sign-in(.*)", "/sign-up(.*)"]);
const isLanding = createRouteMatcher(["/"]);

export default clerkMiddleware(async (auth, req) => {
  const { userId } = await auth();

  if (isAuthPage(req)) {
    // Signed-in students never need the sign-in screen
    if (userId) return NextResponse.redirect(new URL("/dashboard", req.url));
    return;
  }
  if (isLanding(req)) return;
  await auth.protect(); // unauthenticated -> redirected to /sign-in
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
