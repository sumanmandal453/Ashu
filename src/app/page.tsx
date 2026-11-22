"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, Radar, FileSearch, PenLine, UserCheck, Send, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

const steps = [
  { icon: Radar, title: "Assignment detected", note: "Clustering Algorithms · Data Mining · 20 marks" },
  { icon: FileSearch, title: "Ashu reads the brief", note: "3 questions found. Deadline: 12 Nov, 6:00 pm" },
  { icon: PenLine, title: "Draft answers written", note: "Grounded in your lecture notes (demo)" },
  { icon: UserCheck, title: "You review and approve", note: "Nothing leaves without your confirmation", gate: true },
  { icon: Send, title: "Submitted through your portal", note: "Marked done only when the college confirms" },
];

export default function Landing() {
  const [active, setActive] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setActive((a) => (a + 1) % (steps.length + 1)), 1800);
    return () => clearInterval(t);
  }, []);

  return (
    <main className="min-h-screen bg-ink text-white">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <span className="font-display text-2xl font-bold tracking-tight">Ashu</span>
        <Link href="/dashboard" className="rounded-full bg-white px-5 py-2 text-sm font-medium text-ink hover:bg-indigo-100">Open dashboard</Link>
      </nav>

      <section className="mx-auto grid max-w-6xl items-center gap-14 px-6 pb-24 pt-10 lg:grid-cols-[1.05fr_1fr]">
        <div>
          <h1 className="font-display text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
            Assignments arrive. Ashu gets them ready. You press approve.
          </h1>
          <p className="mt-6 max-w-md text-lg text-indigo-100/75">
            Detect new work from your college portal, understand the brief, draft answers from your own notes and track every deadline.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/dashboard" className="rounded-full bg-signal px-6 py-3 font-medium hover:bg-indigo-500">Try the demo</Link>
            <Link href="/integrations/college" className="rounded-full border border-white/20 px-6 py-3 font-medium hover:bg-white/10">Connect college portal</Link>
          </div>
          <p className="mt-6 flex items-center gap-2 text-sm text-indigo-100/60">
            <ShieldCheck size={16} /> Demo build: sample data only, no real portal connected yet.
          </p>
        </div>

        {/* The lifecycle, lit step by step */}
        <ol className="relative space-y-3" aria-label="Assignment lifecycle">
          <span className="absolute bottom-6 left-[27px] top-6 w-px bg-white/10" aria-hidden />
          {steps.map((s, i) => {
            const on = i < active, now = i === active - 1;
            return (
              <motion.li key={s.title} animate={{ opacity: on ? 1 : 0.45 }} className={cn(
                "relative flex items-center gap-4 rounded-2xl border p-4 transition-colors",
                s.gate ? "border-amber-300/50 bg-amber-300/10" : "border-white/10 bg-white/5",
                now && "border-signal bg-signal/15")}>
                <span className="relative grid h-11 w-11 shrink-0 place-items-center rounded-full bg-ink ring-1 ring-white/20">
                  {now && <span className="absolute inset-0 animate-ring rounded-full bg-signal/60" />}
                  {on && !now ? <Check size={18} className="text-emerald-400" /> : <s.icon size={18} />}
                </span>
                <div>
                  <p className="font-medium">{s.title}</p>
                  <p className="text-sm text-indigo-100/65">{s.note}</p>
                </div>
              </motion.li>
            );
          })}
        </ol>
      </section>
    </main>
  );
}
