import Link from "next/link";
import type { ReactNode } from "react";

// Shared shell for /sign-in and /sign-up. Reuses the Ashu navy look.
export function AuthCard({ children, title }: { children: ReactNode; title: string }) {
  return (
    <main className="grid min-h-screen place-items-center bg-ink px-4 py-10 text-white">
      <div className="flex w-full max-w-md flex-col items-center">
        <Link href="/" className="mb-2 text-3xl font-bold tracking-tight" style={{ fontFamily: "var(--font-hero, var(--font-display))" }}>Ashu</Link>
        <p className="mb-1 text-lg font-medium">{title}</p>
        <p className="mb-6 text-sm text-indigo-100/70">Your Personal AI Academic Assistant</p>
        {children}
      </div>
    </main>
  );
}

export const clerkAppearance = {
  variables: { colorPrimary: "#4F46E5", borderRadius: "0.75rem" },
  elements: { footerAction: "hidden" }, // Google is the only method; no email/password switch
};
