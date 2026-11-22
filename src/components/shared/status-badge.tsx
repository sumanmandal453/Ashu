import { cn } from "@/lib/utils";
import type { AssignmentStatus } from "@/types";

export const STATUS: Record<AssignmentStatus, { label: string; cls: string }> = {
  new: { label: "New", cls: "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300" },
  pending: { label: "Pending", cls: "bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-300" },
  in_progress: { label: "In progress", cls: "bg-sky-50 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300" },
  ai_generated: { label: "AI generated", cls: "bg-violet-50 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300" },
  awaiting_approval: { label: "Awaiting your approval", cls: "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300" },
  verification_pending: { label: "Verification pending", cls: "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300" },
  submitted: { label: "Submitted", cls: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300" },
  overdue: { label: "Overdue", cls: "bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-300" },
};

export function StatusBadge({ status }: { status: AssignmentStatus }) {
  const s = STATUS[status];
  return <span className={cn("inline-flex whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium", s.cls)}>{s.label}</span>;
}
