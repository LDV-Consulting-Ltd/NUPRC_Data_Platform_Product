"use client";

import Link from "next/link";
import {
  Activity,
  Database,
  PlayCircle,
  Shield,
  Warehouse,
  GitCompare,
  Network,
} from "lucide-react";
import StatusCard from "@/components/enterprise/StatusCard";
import SectionHeader from "@/components/enterprise/SectionHeader";
import { usePlatformStatus } from "@/hooks/usePlatformStatus";
import { useSourcesHealth } from "@/hooks/useSourcesHealth";

const SECTIONS = [
  { href: "/console/pipeline", label: "Pipeline Control", icon: PlayCircle, desc: "Run and monitor ETL" },
  { href: "/console/runs", label: "Runs", icon: Activity, desc: "History and timelines" },
  { href: "/console/bronze", label: "Bronze", icon: Database, desc: "Raw ingestion tables" },
  { href: "/console/warehouse", label: "Warehouse", icon: Warehouse, desc: "Reporting layer" },
  { href: "/console/governance", label: "Governance", icon: Shield, desc: "Lineage and registry" },
  { href: "/console/schema-drift", label: "Schema Drift", icon: GitCompare, desc: "Column mapping alerts" },
  { href: "/console/diagrams", label: "Diagrams", icon: Network, desc: "Mermaid architecture" },
];

export default function ConsoleOverviewPage() {
  const { data: platform } = usePlatformStatus();
  const { data: sources } = useSourcesHealth();

  const freshCount = (sources ?? []).filter((s) => s.status === "fresh" || s.status === "stable").length;
  const healthTone =
    platform?.system_health === "healthy" ? "success" : platform?.system_health === "degraded" ? "warning" : "danger";

  return (
    <div className="w-full space-y-8">
      <SectionHeader
        icon={Activity}
        title="Console Overview"
        description="Operational snapshot of the NUPRC upstream data fabric."
      />

      <div className="enterprise-grid">
        <StatusCard
          icon={Activity}
          label="System health"
          value={platform?.system_health ?? "—"}
          tone={healthTone}
        />
        <StatusCard
          icon={Database}
          label="Records today"
          value={(platform?.records_today ?? 0).toLocaleString()}
          hint="Rows loaded in latest successful run"
        />
        <StatusCard
          icon={PlayCircle}
          label="Last run"
          value={
            platform?.last_run
              ? `${platform.last_run.duration_seconds}s · ${platform.last_run.status}`
              : "No runs yet"
          }
          hint={platform?.last_run?.at ? new Date(platform.last_run.at).toLocaleString() : undefined}
        />
        <StatusCard
          icon={Shield}
          label="Sources healthy"
          value={`${freshCount} / ${(sources ?? []).length || "—"}`}
          tone="teal"
        />
      </div>

      <section>
        <h3 className="text-sm font-bold uppercase tracking-wide text-slate-500 mb-4">Navigate</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 w-full">
          {SECTIONS.map(({ href, label, icon: Icon, desc }) => (
            <Link
              key={href}
              href={href}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:border-teal-400 hover:shadow-md transition-all group"
            >
              <div className="h-10 w-10 rounded-xl bg-[#0f2744] text-teal-300 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <Icon className="h-5 w-5" />
              </div>
              <div className="font-bold text-[#0f2744]">{label}</div>
              <p className="text-xs text-slate-500 mt-1">{desc}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
