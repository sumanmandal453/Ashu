"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  AnimatePresence, motion, useMotionTemplate, useMotionValue, useReducedMotion, useSpring,
} from "framer-motion";
import { Check, Radar, FileSearch, PenLine, UserCheck, Send, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

const HERO = { fontFamily: "var(--font-hero)" };
const BODY = { fontFamily: "var(--font-hero-body)" };

const steps = [
  { icon: Radar, title: "Assignment detected", note: "Clustering Algorithms · Data Mining · 20 marks" },
  { icon: FileSearch, title: "Ashu reads the brief", note: "3 questions found. Deadline: 12 Nov, 6:00 pm" },
  { icon: PenLine, title: "Draft answers written", note: "Grounded in your lecture notes (demo)" },
  { icon: UserCheck, title: "You review and approve", note: "Nothing leaves without your confirmation", gate: true },
  { icon: Send, title: "Submitted through your portal", note: "Marked done only when the college confirms" },
];

const live = [
  "Watching your portal", "Reading the brief", "Drafting answers",
  "Waiting for your approval", "Submitting to portal", "Verified by college (demo)",
];

const subjects = ["Data Mining", "Machine Learning", "Statistics", "Database Management Systems", "Big Data Analytics"];

function Brand({ reduce }: { reduce: boolean | null }) {
  return (
    <Link href="/" aria-label="Ashu home" style={HERO} className="flex items-center text-2xl font-bold tracking-tight">
      {"Ashu".split("").map((c, i) => (
        <motion.span
          key={i}
          className="inline-block cursor-default"
          initial={reduce ? false : { opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 + i * 0.12, type: "spring", stiffness: 260, damping: 14 }}
          whileHover={reduce ? undefined : { y: -6, scale: 1.2, rotate: -4 }}
        >
          <motion.span
            className="inline-block bg-clip-text text-transparent"
            style={{
              backgroundImage: "linear-gradient(90deg, #ffffff 0%, #a5b4fc 35%, #818cf8 50%, #ffffff 100%)",
              backgroundSize: "200% 100%",
            }}
            animate={reduce ? undefined : { backgroundPosition: ["0% 50%", "200% 50%"] }}
            transition={{ duration: 3.5, repeat: Infinity, ease: "linear", delay: i * 0.15 }}
          >
            {c}
          </motion.span>
        </motion.span>
      ))}
      <span className="relative ml-1.5 mt-2 flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ring rounded-full bg-signal" />
        <span className="relative h-2 w-2 rounded-full bg-signal" />
      </span>
    </Link>
  );
}

export default function Landing() {
  const reduce = useReducedMotion();
  const [active, setActive] = useState(0);

  const mx = useMotionValue(700);
  const my = useMotionValue(300);
  const spot = useMotionTemplate`radial-gradient(560px circle at ${mx}px ${my}px, rgba(99,102,241,.24), transparent 65%)`;

  const rx = useSpring(0, { stiffness: 110, damping: 14 });
  const ry = useSpring(0, { stiffness: 110, damping: 14 });
  const onTilt = (e: React.MouseEvent<HTMLElement>) => {
    if (reduce) return;
    const r = e.currentTarget.getBoundingClientRect();
    ry.set(((e.clientX - r.left) / r.width - 0.5) * 12);
    rx.set(-((e.clientY - r.top) / r.height - 0.5) * 12);
  };

  useEffect(() => {
    const t = setInterval(() => setActive((a) => (a + 1) % (steps.length + 1)), 2000);
    return () => clearInterval(t);
  }, []);

  const words = "Assignments arrive. Ashu gets them ready. You press approve.".split(" ");

  return (
    <main
      style={BODY}
      onMouseMove={(e) => { mx.set(e.clientX); my.set(e.clientY); }}
      className="relative min-h-screen overflow-hidden bg-ink text-white"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,.07) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
          maskImage: "radial-gradient(ellipse at 50% 30%, black 30%, transparent 75%)",
          WebkitMaskImage: "radial-gradient(ellipse at 50% 30%, black 30%, transparent 75%)",
        }}
      />
      {!reduce && (
        <>
          <motion.div aria-hidden className="pointer-events-none absolute -left-32 top-10 h-96 w-96 rounded-full bg-indigo-500/25 blur-[110px]"
            animate={{ x: [0, 120, 0], y: [0, 60, 0] }} transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }} />
          <motion.div aria-hidden className="pointer-events-none absolute -right-24 bottom-0 h-96 w-96 rounded-full bg-fuchsia-500/15 blur-[120px]"
            animate={{ x: [0, -100, 0], y: [0, -70, 0] }} transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }} />
        </>
      )}
      <motion.div aria-hidden className="pointer-events-none absolute inset-0" style={{ background: spot }} />

      <div className="relative">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
          <Brand reduce={reduce} />
          <Link href="/dashboard" className="rounded-full border border-white/25 px-5 py-2 text-sm font-medium transition hover:bg-white hover:text-ink">
            Open dashboard
          </Link>
        </nav>

        <section className="mx-auto grid max-w-6xl items-center gap-14 px-6 pb-16 pt-8 lg:grid-cols-[1.1fr_1fr]">
          <div>
            <h1 style={HERO} className="text-4xl font-bold leading-[1.12] tracking-tight sm:text-5xl">
              {words.map((w, i) => (
                <motion.span key={i} className="mr-[0.28em] inline-block"
                  initial={reduce ? false : { opacity: 0, y: 28, filter: "blur(10px)" }}
                  animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                  transition={{ delay: 0.15 + i * 0.09, duration: 0.6, ease: "easeOut" }}>
                  {w}
                </motion.span>
              ))}
            </h1>
            <motion.p initial={reduce ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.3 }}
              className="mt-6 max-w-md text-lg leading-relaxed text-indigo-100/75">
              Detect new work from your college portal, understand the brief, draft answers from your own notes and track every deadline.
            </motion.p>
            <motion.div initial={reduce ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }} className="mt-8 flex flex-wrap gap-3">
              <Link href="/dashboard" className="group relative overflow-hidden rounded-full bg-signal px-7 py-3 font-semibold shadow-[0_0_40px_-8px_rgba(99,102,241,.9)] transition hover:bg-indigo-500">
                <span className="relative z-10">Try the demo</span>
                <span aria-hidden className="absolute inset-y-0 -left-full w-1/2 -skew-x-12 bg-white/30 transition-all duration-700 group-hover:left-[150%]" />
              </Link>
              <Link href="/integrations/college" className="rounded-full border border-white/20 px-7 py-3 font-semibold transition hover:bg-white/10">
                Connect college portal
              </Link>
            </motion.div>
            <p className="mt-6 flex items-center gap-2 text-sm text-indigo-100/60">
              <ShieldCheck size={16} /> Demo build: sample data only, no real portal connected yet.
            </p>
          </div>

          <div className="relative">
            <div className="mb-4 flex justify-end">
              <div className="flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-1.5 text-sm backdrop-blur">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ring rounded-full bg-emerald-400" />
                  <span className="relative h-2 w-2 rounded-full bg-emerald-400" />
                </span>
                <AnimatePresence mode="wait">
                  <motion.span key={active} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.2 }}>
                    {live[active]}
                  </motion.span>
                </AnimatePresence>
              </div>
            </div>

            <motion.ol
              aria-label="Assignment lifecycle"
              onMouseMove={onTilt}
              onMouseLeave={() => { rx.set(0); ry.set(0); }}
              style={{ rotateX: rx, rotateY: ry, transformPerspective: 1100 }}
              className="relative space-y-3"
            >
              <span className="absolute bottom-8 left-[27px] top-8 w-px bg-white/10" aria-hidden>
                <motion.span className="absolute left-0 top-0 w-px bg-gradient-to-b from-indigo-400 via-signal to-emerald-400 shadow-[0_0_12px_2px_rgba(99,102,241,.8)]"
                  animate={{ height: `${(Math.min(active, steps.length) / steps.length) * 100}%` }} transition={{ duration: 0.8, ease: "easeInOut" }} />
              </span>
              {steps.map((s, i) => {
                const on = i < active, now = i === active - 1;
                return (
                  <motion.li key={s.title}
                    animate={{ opacity: on ? 1 : 0.4, scale: now ? 1.02 : 1 }}
                    transition={{ type: "spring", stiffness: 200, damping: 20 }}
                    className={cn(
                      "relative flex items-center gap-4 rounded-2xl border p-4 backdrop-blur-sm transition-colors",
                      s.gate ? "border-amber-300/50 bg-amber-300/10" : "border-white/10 bg-white/5",
                      now && !s.gate && "border-signal bg-signal/15 shadow-[0_0_30px_-6px_rgba(99,102,241,.7)]",
                      now && s.gate && "shadow-[0_0_30px_-6px_rgba(252,211,77,.6)]",
                    )}>
                    <span className="relative grid h-11 w-11 shrink-0 place-items-center rounded-full bg-ink ring-1 ring-white/20">
                      {now && <span className="absolute inset-0 animate-ring rounded-full bg-signal/60" />}
                      {on && !now ? <Check size={18} className="text-emerald-400" /> : <s.icon size={18} />}
                    </span>
                    <div>
                      <p className="font-semibold">{s.title}</p>
                      <p className="text-sm text-indigo-100/65">{s.note}</p>
                    </div>
                  </motion.li>
                );
              })}
            </motion.ol>
          </div>
        </section>

        <div className="border-y border-white/10 bg-white/[0.03] py-4" aria-hidden>
          <div className="overflow-hidden [mask-image:linear-gradient(90deg,transparent,black_12%,black_88%,transparent)]">
            <motion.div className="flex w-max gap-12 whitespace-nowrap text-sm text-indigo-100/60"
              animate={reduce ? undefined : { x: ["0%", "-50%"] }} transition={{ duration: 28, repeat: Infinity, ease: "linear" }}>
              {[...subjects, ...subjects, ...subjects, ...subjects].map((s, i) => (
                <span key={i} className="flex items-center gap-12">{s}<span className="h-1 w-1 rounded-full bg-signal" /></span>
              ))}
            </motion.div>
          </div>
        </div>
      </div>
    </main>
  );
}
