"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
import { format } from "date-fns";
import { Search, SearchX } from "lucide-react";
import { assignments, subjects, subjectName } from "@/lib/mock-data";
import { StatusBadge } from "@/components/shared/status-badge";
import { cn } from "@/lib/utils";
import type { AssignmentStatus } from "@/types";

const TABS: { id: string; label: string; match: (s: AssignmentStatus) => boolean }[] = [
  { id: "all", label: "All", match: () => true },
  { id: "new", label: "New", match: (s) => s === "new" },
  { id: "pending", label: "Pending", match: (s) => s === "pending" },
  { id: "in_progress", label: "In progress", match: (s) => s === "in_progress" },
  { id: "ai", label: "AI generated", match: (s) => s === "ai_generated" },
  { id: "approval", label: "Awaiting approval", match: (s) => s === "awaiting_approval" },
  { id: "submitted", label: "Submitted", match: (s) => s === "submitted" },
  { id: "overdue", label: "Overdue", match: (s) => s === "overdue" },
];

export default function AssignmentsPage() {
  const [tab, setTab] = useState("all");
  const [q, setQ] = useState("");
  const [subject, setSubject] = useState("all");
  const [sort, setSort] = useState<"deadline" | "created">("deadline");

  const rows = useMemo(() => {
    const t = TABS.find((x) => x.id === tab)!;
    return assignments
      .filter((a) => t.match(a.status) && (subject === "all" || a.subjectId === subject))
      .filter((a) => `${a.title} ${subjectName(a.subjectId)}`.toLowerCase().includes(q.toLowerCase()))
      .sort((a, b) => +new Date(sort === "deadline" ? a.deadline : b.createdAt) - +new Date(sort === "deadline" ? b.deadline : a.createdAt));
  }, [tab, q, subject, sort]);

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <div className="flex gap-2 overflow-x-auto pb-1">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={cn("whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium", tab === t.id ? "bg-ink text-white dark:bg-signal" : "bg-white text-slate-600 hover:bg-slate-100 dark:bg-white/5 dark:text-slate-300")}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <label className="flex min-w-[220px] flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-white/10 dark:bg-white/5">
          <Search size={16} className="text-slate-400" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by title or subject" className="w-full bg-transparent text-sm outline-none" />
        </label>
        <select value={subject} onChange={(e) => setSubject(e.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#15152E]">
          <option value="all">All subjects</option>
          {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value as "deadline" | "created")} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#15152E]">
          <option value="deadline">Sort by deadline</option><option value="created">Sort by newest</option>
        </select>
      </div>

      {rows.length === 0 ? (
        <div className="card py-14 text-center">
          <SearchX className="mx-auto text-slate-400" />
          <p className="mt-3 font-medium">No assignments match</p>
          <p className="text-sm text-slate-500">Clear the search or pick another tab.</p>
        </div>
      ) : (
        <div className="card overflow-x-auto !p-0">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-slate-100 text-slate-500 dark:border-white/10">
              <tr>{["Assignment", "Subject", "Deadline", "Marks", "Priority", "Status"].map((h) => <th key={h} className="px-5 py-3 font-medium">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-white/10">
              {rows.map((a) => (
                <tr key={a.id} className="hover:bg-slate-50 dark:hover:bg-white/5">
                  <td className="px-5 py-3 font-medium"><Link href={`/assignments/${a.id}`} className="hover:text-signal">{a.title}</Link></td>
                  <td className="px-5 py-3">{subjectName(a.subjectId)}</td>
                  <td className="px-5 py-3 tabular-nums">{format(new Date(a.deadline), "d MMM, h:mm a")}</td>
                  <td className="px-5 py-3">{a.totalMarks}</td>
                  <td className="px-5 py-3 capitalize">{a.priority}</td>
                  <td className="px-5 py-3"><StatusBadge status={a.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
