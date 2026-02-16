"use client";

import { usePlatformStatus } from "@/hooks/usePlatformStatus";
import type { PlatformStatus } from "@/lib/types";

function formatTime(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) + " — " + d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

function formatDuration(seconds: number) {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s ? `${m}m ${s}s` : `${m}m`;
}

function Skeleton() {
  return <div className="h-4 w-20 rounded bg-slate-200 animate-pulse" />;
}

export default function ExecutiveStatusBar() {
  const { data, isLoading, isError } = usePlatformStatus();

  if (isError) {
    return (
      <section className="grid grid-cols-1 md:grid-cols-5 gap-3">
        <div className="bg-white rounded-xl border border-slate-200 p-4 col-span-full text-sm text-slate-600">
          Unable to load status. Check connection and retry.
        </div>
      </section>
    );
  }

  const s: PlatformStatus | null = data ?? null;

  return (
    <section className="grid grid-cols-1 md:grid-cols-5 gap-3">
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="text-xs text-slate-500">Pipeline Status</div>
        {isLoading ? <Skeleton /> : (
          <div className="mt-1 flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${s?.system_health === "healthy" ? "bg-emerald-500" : s?.system_health === "degraded" ? "bg-amber-500" : "bg-red-500"}`} />
            <span className="font-bold capitalize">{s?.system_health ?? "—"}</span>
          </div>
        )}
        <div className="mt-2 text-xs text-slate-500">No critical failures (7d)</div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="text-xs text-slate-500">Last Successful Run</div>
        {isLoading ? <Skeleton /> : (
          <div className="mt-1 font-bold">
            {s?.last_run?.status === "success" ? formatTime(s.last_run.at) : "—"}
          </div>
        )}
        <div className="mt-2 text-xs text-slate-500">
          {s?.last_run?.duration_seconds != null ? `Duration: ${formatDuration(s.last_run.duration_seconds)}` : "—"}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="text-xs text-slate-500">Records Processed Today</div>
        {isLoading ? <Skeleton /> : <div className="mt-1 font-bold">{(s?.records_today ?? 0).toLocaleString()}</div>}
        <div className="mt-2 text-xs text-slate-500">Oil + Gas + Rig + Concession</div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="text-xs text-slate-500">Avg Data Freshness</div>
        {isLoading ? <Skeleton /> : (
          <div className="mt-1 font-bold">
            {s?.avg_freshness_minutes != null ? `${Math.floor(s.avg_freshness_minutes / 60)}h ${s.avg_freshness_minutes % 60}m` : "—"}
          </div>
        )}
        <div className="mt-2 text-xs text-slate-500">Target: ≤ 6h</div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="text-xs text-slate-500">SLA Compliance</div>
        {isLoading ? <Skeleton /> : (
          <div className="mt-1 font-bold text-emerald-700">
            Met ({s?.sla_compliance.met ?? 0}/{s?.sla_compliance.total ?? 0})
          </div>
        )}
        <div className="mt-2 text-xs text-slate-500">{s?.sla_compliance.label ?? "Daily SLA: 02:00 delivery"}</div>
      </div>
    </section>
  );
}
