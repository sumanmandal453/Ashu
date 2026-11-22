"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { formatDistanceToNowStrict, isPast } from "date-fns";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ClipboardList, Sparkles, Clock, UserCheck, CheckCircle2, AlertTriangle, Upload, CalendarDays, Plug } from "lucide-react";
import { assignments, subjects, subjectName, weeklyCompletion, activity, user } from "@/lib/mock-data";
import { StatusBadge } from "@/components/shared/status-badge";
import { cn } from "@/lib/utils";

const count = (f: (s: string) => boolean) => assignments.filter((a) => f(a.status)).length;
const stats = [
  { label: "Total", value: assignments.length, icon: ClipboardList, note: "This semester", tone: "text-signal bg-signal/10" },
  { label: "New", value: count((s) => s === "new"), icon: Sparkles, note: "Detected, not started", tone: "text-sky-600 bg-sky-500/10" },
  { label: "Pending", value: count((s) => ["pending", "in_progress", "ai_generated"].includes(s)), icon: Clock, note: "Work in progress", tone: "text-slate-600 bg-slate-500/10" },
  { label: "Awaiting approval", value: count((s) => s === "awaiting_approval"), icon: UserCheck, note: "Needs your review", tone: "text-warn bg-warn/10" },
  { label: "Submitted", value: count((s) => s === "submitted"), icon: CheckCircle2, note: "Confirmed by portal", tone: "text-ok bg-ok/10" },
  { label: "Overdue", value: count((s) => s === "overdue"), icon: AlertTriangle, note: "Submit manually", tone: "text-bad bg-bad/10" },
];
const COLORS = ["#4F46E5", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"];

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const upcoming = [...assignments].filter((a) => a.status !== "submitted").sort((a, b) => +new Date(a.deadline) - +new Date(b.deadline));
  const bySubject = subjects.map((s) => ({ name: s.name.split(" ")[0], value: assignments.filter((a) => a.subjectId === s.id).length }));
  const hour = mounted ? new Date().getHours() : 12;
  const greet = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="rounded-3xl bg-ink p-6 text-white sm:p-8">
        <p className="font-display text-2xl font-semibold sm:text-3xl">{greet}, {user.name.split(" ")[0]}.</p>
        <p className="mt-2 max-w-xl text-indigo-100/80">
          {stats[2].value} assignments are in progress and {stats[3].value} is waiting for your approval. Clustering Algorithms (Data Mining) is due soonest.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          {[
            { l: "Upload assignment", i: Upload, a: () => toast.info("Upload needs the backend. Not connected in this demo.") },
            { l: "Generate answer", i: Sparkles, a: () => toast.info("AI service not configured. Demo drafts only.") },
            { l: "Connect college portal", i: Plug, href: "/integrations/college" },
            { l: "View calendar", i: CalendarDays, href: "/calendar" },
          ].map((q) => q.href ? (
            <Link key={q.l} href={q.href} className="flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm hover:bg-white/20"><q.i size={15} />{q.l}</Link>
          ) : (
            <button key={q.l} onClick={q.a} className="flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm hover:bg-white/20"><q.i size={15} />{q.l}</button>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        {stats.map((s) => (
          <div key={s.label} className="card !p-4">
            <span className={cn("grid h-9 w-9 place-items-center rounded-lg", s.tone)}><s.icon size={18} /></span>
            <p className="mt-3 font-display text-3xl font-bold">{s.value}</p>
            <p className="text-sm font-medium">{s.label}</p>
            <p className="text-xs text-slate-500">{s.note}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-lg font-semibold">Upcoming deadlines</h2>
            <Link href="/assignments" className="text-sm text-signal hover:underline">All assignments</Link>
          </div>
          <ul className="divide-y divide-slate-100 dark:divide-white/10">
            {upcoming.slice(0, 5).map((a) => {
              const late = mounted && isPast(new Date(a.deadline));
              const urgent = mounted && !late && +new Date(a.deadline) - Date.now() < 48 * 3600_000;
              return (
                <li key={a.id}>
                  <Link href={`/assignments/${a.id}`} className="flex flex-wrap items-center gap-3 py-3 hover:opacity-80">
                    <span className={cn("h-10 w-1 rounded-full", late ? "bg-bad" : urgent ? "bg-warn" : "bg-slate-200 dark:bg-white/20")} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">{a.title}</p>
                      <p className="text-xs text-slate-500">{subjectName(a.subjectId)} · {a.totalMarks} marks · {a.priority} priority</p>
                    </div>
                    <span className={cn("text-sm tabular-nums", late ? "text-bad" : urgent ? "text-warn" : "text-slate-500")}>
                      {mounted ? `${late ? "overdue by" : "in"} ${formatDistanceToNowStrict(new Date(a.deadline))}` : "…"}
                    </span>
                    <StatusBadge status={a.status} />
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="card">
          <h2 className="mb-4 font-display text-lg font-semibold">Recent activity</h2>
          <ol className="space-y-4">
            {activity.map((e) => (
              <li key={e.id} className="flex gap-3">
                <span className={cn("mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full", e.tone === "warn" ? "bg-warn" : "bg-signal")} />
                <div><p className="text-sm">{e.text}</p><p className="text-xs text-slate-500">{e.when}</p></div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 font-display text-lg font-semibold">Completed per week</h2>
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={weeklyCompletion}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#94a3b833" />
                <XAxis dataKey="week" tickLine={false} axisLine={false} /><YAxis allowDecimals={false} tickLine={false} axisLine={false} width={24} />
                <Tooltip cursor={{ fill: "#4F46E510" }} />
                <Bar dataKey="done" fill="#4F46E5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card">
          <h2 className="mb-4 font-display text-lg font-semibold">Assignments by subject</h2>
          <div className="flex h-56 items-center">
            <ResponsiveContainer width="55%" height="100%">
              <PieChart><Pie data={bySubject} dataKey="value" innerRadius={45} outerRadius={80} paddingAngle={3}>
                {bySubject.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip /></PieChart>
            </ResponsiveContainer>
            <ul className="space-y-2 text-sm">
              {bySubject.map((s, i) => <li key={s.name} className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />{s.name} · {s.value}</li>)}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
