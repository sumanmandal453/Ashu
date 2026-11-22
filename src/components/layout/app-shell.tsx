"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  LayoutDashboard, ClipboardList, Sparkles, BookOpen, CalendarDays, Send, Bell, Plug, BarChart3,
  Settings, Menu, X, Search, Moon, Sun, HelpCircle, PanelLeftClose, PanelLeftOpen, LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { user } from "@/lib/mock-data";

export const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/assignments", label: "Assignments", icon: ClipboardList },
  { href: "/ai-generator", label: "AI Generator", icon: Sparkles },
  { href: "/study-materials", label: "Study Materials", icon: BookOpen },
  { href: "/calendar", label: "Calendar & Deadlines", icon: CalendarDays },
  { href: "/submissions", label: "Submissions", icon: Send },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/integrations/college", label: "Integrations", icon: Plug },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

function NavList({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  const path = usePathname();
  return (
    <nav className="flex-1 space-y-1 px-3">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = path === href || path.startsWith("/" + href.split("/")[1]);
        return (
          <Link key={href} href={href} onClick={onNavigate} title={label}
            className={cn("relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
              active ? "bg-signal/10 text-signal dark:text-indigo-300" : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5")}>
            {active && <span className="absolute -left-3 h-5 w-1 rounded-r bg-signal" />}
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span>{label}</span>}
          </Link>
        );
      })}
    </nav>
  );
}

function Profile({ collapsed }: { collapsed: boolean }) {
  return (
    <div className="border-t border-slate-200 p-3 dark:border-white/10">
      <div className="flex items-center gap-3 rounded-xl p-2">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ink text-sm font-semibold text-white">AS</span>
        {!collapsed && (
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{user.name}</p>
            <p className="truncate text-xs text-slate-500">Sem {user.semester} · {user.department}</p>
          </div>
        )}
        {!collapsed && (
          <button aria-label="Log out" onClick={() => toast.info("Auth is not configured in this demo build.")} className="text-slate-400 hover:text-slate-700"><LogOut size={16} /></button>
        )}
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [dark, setDark] = useState(false);
  const path = usePathname();
  const title = NAV.find((n) => path.startsWith(n.href.split("/").slice(0, 2).join("/")))?.label ?? "Ashu";

  useEffect(() => { setDark(document.documentElement.classList.contains("dark")); }, []);
  const toggleTheme = () => {
    const next = !dark; setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try { localStorage.setItem("asu-theme", next ? "dark" : "light"); } catch {}
  };

  return (
    <div className="min-h-screen">
      <aside className={cn("fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-slate-200 bg-white pt-5 transition-[width] dark:border-white/10 dark:bg-[#11112A] lg:flex", collapsed ? "w-[76px]" : "w-64")}>
        <div className="mb-6 flex items-center justify-between px-5">
          <span className="font-display text-2xl font-bold tracking-tight text-ink dark:text-white">{collapsed ? "A" : "Ashu"}</span>
          <button aria-label="Toggle sidebar" onClick={() => setCollapsed(!collapsed)} className="text-slate-400 hover:text-slate-700">
            {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>
        </div>
        <NavList collapsed={collapsed} />
        <Profile collapsed={collapsed} />
      </aside>

      {drawer && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setDrawer(false)} />
          <aside className="absolute inset-y-0 left-0 flex w-72 flex-col bg-white pt-5 dark:bg-[#11112A]">
            <div className="mb-6 flex items-center justify-between px-5">
              <span className="font-display text-2xl font-bold">Ashu</span>
              <button aria-label="Close menu" onClick={() => setDrawer(false)}><X size={20} /></button>
            </div>
            <NavList collapsed={false} onNavigate={() => setDrawer(false)} />
            <Profile collapsed={false} />
          </aside>
        </div>
      )}

      <div className={cn("transition-[padding]", collapsed ? "lg:pl-[76px]" : "lg:pl-64")}>
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-200 bg-paper/85 px-4 py-3 backdrop-blur dark:border-white/10 dark:bg-[#0C0C1F]/85 sm:px-8">
          <button aria-label="Open menu" className="lg:hidden" onClick={() => setDrawer(true)}><Menu size={22} /></button>
          <div className="hidden sm:block">
            <p className="text-xs text-slate-500">Ashu / {title}</p>
            <h1 className="font-display text-lg font-semibold leading-tight">{title}</h1>
          </div>
          <label className="mx-auto flex w-full max-w-md items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-white/10 dark:bg-white/5">
            <Search size={16} className="text-slate-400" />
            <input placeholder="Search assignments, subjects, notes" className="w-full bg-transparent text-sm outline-none placeholder:text-slate-400"
              onKeyDown={(e) => e.key === "Enter" && toast.info("Global search arrives with the backend.")} />
          </label>
          <button aria-label="Notifications" onClick={() => toast("3 unread notifications (demo)")} className="relative rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-white/10">
            <Bell size={18} /><span className="absolute right-1 top-1 grid h-4 w-4 place-items-center rounded-full bg-bad text-[10px] font-semibold text-white">3</span>
          </button>
          <button aria-label="Toggle theme" onClick={toggleTheme} className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-white/10">{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
          <button aria-label="Help" className="hidden rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-white/10 sm:block" onClick={() => toast.info("Help centre is not configured yet.")}><HelpCircle size={18} /></button>
        </header>
        <main className="px-4 py-6 sm:px-8">{children}</main>
      </div>
    </div>
  );
}
