"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PlayCircle,
  History,
  Stethoscope,
  Database,
  Layers,
  Warehouse,
  Shield,
  GitCompare,
  FolderTree,
  Network,
  BarChart3,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const NAV: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/console", label: "Overview", icon: LayoutDashboard },
  { href: "/console/pipeline", label: "Pipeline Control", icon: PlayCircle },
  { href: "/console/runs", label: "Runs", icon: History },
  { href: "/console/diagnostics", label: "Diagnostics", icon: Stethoscope },
  { href: "/console/bronze", label: "Bronze", icon: Database },
  { href: "/console/silver", label: "Silver", icon: Layers },
  { href: "/console/warehouse", label: "Warehouse", icon: Warehouse },
  { href: "/console/governance", label: "Governance", icon: Shield },
  { href: "/console/schema-drift", label: "Schema Drift", icon: GitCompare },
  { href: "/console/metadata", label: "Metadata Registry", icon: FolderTree },
  { href: "/console/diagrams", label: "Diagrams", icon: Network },
  { href: "/console/analytics", label: "Analytics", icon: BarChart3 },
];

export default function ConsoleSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-[280px] shrink-0 min-h-screen bg-[#0f2744] text-slate-200 flex flex-col">
      <div className="p-5 border-b border-white/10">
        <Link href="/" className="flex items-center gap-3">
          <img src="/ldv-logo.png" alt="LDV" className="h-9 w-9 rounded-lg object-contain bg-white/10" />
          <div>
            <div className="font-bold text-white text-sm leading-tight">NUPRC Data Fabric</div>
            <div className="text-xs text-teal-300/90">Admin Console</div>
          </div>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/console" ? pathname === "/console" : pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                active
                  ? "bg-teal-500/20 text-teal-300 border border-teal-500/30"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/10 text-xs text-slate-400">
        <Link href="/" className="text-teal-400 hover:text-teal-300">
          ← Back to landing
        </Link>
      </div>
    </aside>
  );
}
