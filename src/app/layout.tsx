import type { Metadata } from "next";
import { Bricolage_Grotesque, DM_Sans, Unbounded, Figtree } from "next/font/google";
import { Toaster } from "sonner";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const display = Bricolage_Grotesque({ subsets: ["latin"], variable: "--font-display" });
const body = DM_Sans({ subsets: ["latin"], variable: "--font-body" });
const hero = Unbounded({ subsets: ["latin"], variable: "--font-hero" });
const heroBody = Figtree({ subsets: ["latin"], variable: "--font-hero-body" });

export const metadata: Metadata = { title: "Ashu — Your Personal AI Academic Assistant", description: "Detect assignments, draft answers, manage deadlines. You approve every submission." };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider afterSignOutUrl="/sign-in">
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `try{if(localStorage.getItem("asu-theme")==="dark")document.documentElement.classList.add("dark")}catch(e){}` }} />
      </head>
      <body className={`${display.variable} ${body.variable} ${hero.variable} ${heroBody.variable} font-sans`}>
        {children}
        <Toaster richColors position="bottom-right" />
      </body>
    </html>
    </ClerkProvider>
  );
}
