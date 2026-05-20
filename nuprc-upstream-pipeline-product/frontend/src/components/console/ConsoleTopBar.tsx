"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { usePlatformStatus } from "@/hooks/usePlatformStatus";

const LABELS: Record<string, string> = {
  console: "Console",
  pipeline: "Pipeline Control",
  runs: "Runs",
  diagnostics: "Diagnostics",
  bronze: "Bronze",
  silver: "Silver",
  warehouse: "Warehouse",
  governance: "Governance",
  "schema-drift": "Schema Drift",
  metadata: "Metadata Registry",
  diagrams: "Diagrams",
  analytics: "Analytics",
};

export default function ConsoleTopBar() {
  const pathname = usePathname();
  const { data: platform } = usePlatformStatus();
  const health = platform?.system_health ?? "healthy";
  const env = process.env.NEXT_PUBLIC_APP_ENV ?? "Development";

  const segments = pathname.split("/").filter(Boolean);
  const crumbs = segments.map((seg, i) => ({
    label: LABELS[seg] ?? seg.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    href: "/" + segments.slice(0, i + 1).join("/"),
  }));

  const healthColor =
    health === "healthy" ? "bg-emerald-500" : health === "degraded" ? "bg-amber-500" : "bg-red-500";

  return (
    <header className="h-14 shrink-0 border-b border-slate-200 bg-white flex items-center justify-between px-6 gap-4">
      <nav className="flex items-center gap-1 text-sm text-slate-600 min-w-0 overflow-hidden">
        {crumbs.map((c, i) => (
          <span key={c.href} className="flex items-center gap-1 shrink-0">
            {i > 0 && <ChevronRight className="h-3.5 w-3.5 text-slate-400" />}
            {i < crumbs.length - 1 ? (
              <Link href={c.href} className="hover:text-[#0f2744] font-medium truncate">
                {c.label}
              </Link>
            ) : (
              <span className="font-semibold text-[#0f2744] truncate">{c.label}</span>
            )}
          </span>
        ))}
      </nav>

      <div className="flex items-center gap-4 shrink-0">
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <span className={`h-2.5 w-2.5 rounded-full ${healthColor}`} title={`System: ${health}`} />
          <span className="capitalize">{health}</span>
        </div>
        <span className="text-xs font-semibold uppercase tracking-wide px-2.5 py-1 rounded-full bg-[#0f2744] text-teal-300">
          {env}
        </span>
      </div>
    </header>
  );
}
