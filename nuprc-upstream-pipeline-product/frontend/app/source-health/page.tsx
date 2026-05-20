"use client";

import Link from "next/link";
import V2Header from "../components/V2Header";
import { useSourcesHealth } from "@/hooks/useSourcesHealth";

function statusLabel(status: string): string {
  switch (status) {
    case "fresh":
      return "Healthy";
    case "stable":
      return "Healthy";
    case "degraded":
      return "Degraded";
    case "down":
      return "Down";
    default:
      return status;
  }
}

function statusClass(status: string): string {
  if (status === "fresh" || status === "stable") return "bg-emerald-50 text-emerald-700";
  if (status === "degraded") return "bg-amber-50 text-amber-700";
  return "bg-red-50 text-red-700";
}

export default function SourceHealthPage() {
  const { data: sources, isLoading, isError, error } = useSourcesHealth();

  return (
    <>
      <V2Header
        title="Source Health"
        subtitle="Bronze-layer data volume and freshness (from loaded tables, not live scrape latency)"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="p-4 sm:p-5 border-b border-slate-200">
            <div className="text-sm text-slate-500">Source Reliability Dashboard</div>
            <div className="text-xl font-bold mt-1">NUPRC source endpoints</div>
            <p className="text-xs text-slate-500 mt-2">
              Status is derived from bronze row counts (<code>etl_*</code> legacy tables). Degraded means low or
              stale loaded data, not necessarily that the public website is unreachable.
            </p>
          </div>

          {isLoading && <div className="p-6 text-sm text-slate-500">Loading source health…</div>}
          {isError && (
            <div className="p-6 text-sm text-red-600">
              Could not load source health. {error instanceof Error ? error.message : String(error)}
            </div>
          )}

          {!isLoading && !isError && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <th className="text-left p-4 font-semibold">Source</th>
                    <th className="text-left p-4 font-semibold">Bronze rows</th>
                    <th className="text-left p-4 font-semibold">Freshness score</th>
                    <th className="text-left p-4 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(sources ?? []).map((s) => (
                    <tr key={s.source_key} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="p-4 font-semibold">{s.label}</td>
                      <td className="p-4">{s.row_count != null ? s.row_count.toLocaleString() : "—"}</td>
                      <td className="p-4">{s.freshness_score}</td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${statusClass(s.status)}`}>
                          {statusLabel(s.status)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <div className="font-bold">Latency trends (7d)</div>
            <div className="mt-3 h-32 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500 text-sm">
              Chart placeholder
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <div className="font-bold">Failure frequency</div>
            <div className="mt-3 h-32 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500 text-sm">
              Chart placeholder
            </div>
          </div>
        </section>

        <p className="text-sm text-slate-600">
          <Link href="/showcase/health" className="text-ldv-blue font-semibold hover:underline">
            Open legacy Source Health
          </Link>
        </p>
      </div>
    </>
  );
}
