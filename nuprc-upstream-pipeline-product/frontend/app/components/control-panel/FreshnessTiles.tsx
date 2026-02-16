"use client";

import { useGoldFreshness } from "@/hooks/useGoldFreshness";
import type { SourceHealthItem } from "@/lib/types";

const sourceIcons: Record<string, string> = {
  oil_production_status: "🛢",
  gas_production_status: "🔥",
  rig_disposition: "🏗",
  concession_situation: "📜",
};

function statusBadge(status: SourceHealthItem["status"]) {
  switch (status) {
    case "fresh":
    case "healthy":
      return "bg-emerald-50 text-emerald-700";
    case "degraded":
      return "bg-amber-50 text-amber-700";
    case "down":
      return "bg-red-50 text-red-700";
    default:
      return "bg-slate-100 text-slate-700";
  }
}

function statusLabel(status: SourceHealthItem["status"]) {
  switch (status) {
    case "fresh":
    case "healthy":
      return "Fresh";
    case "degraded":
      return "Degraded";
    case "down":
      return "Down";
    default:
      return "Stable";
  }
}

export default function FreshnessTiles() {
  const { data: sources, isLoading } = useGoldFreshness();

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <div className="flex items-center justify-between">
        <div className="font-bold">Data Freshness</div>
        <span className="text-xs px-2 py-1 rounded-full bg-slate-100 chip">Target: ≤ 6h</span>
      </div>

      <div className="mt-4 space-y-3">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-slate-200 p-4">
                <div className="h-4 w-24 rounded bg-slate-200 animate-pulse" />
                <div className="mt-2 h-3 w-32 rounded bg-slate-100 animate-pulse" />
              </div>
            ))
          : (sources ?? []).map((s) => (
              <div key={s.source_key} className="rounded-xl border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <div className="font-semibold">{sourceIcons[s.source_key] ?? ""} {s.label}</div>
                  <span className={`text-xs px-2 py-1 rounded-full font-semibold ${statusBadge(s.status)}`}>
                    {statusLabel(s.status)}
                  </span>
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Last update: {s.last_update ? new Date(s.last_update).toLocaleString() : "—"} • Expected: {s.expected_interval_minutes >= 1440 ? "Daily" : `${s.expected_interval_minutes}m`}
                </div>
                <div className="mt-2 text-xs">
                  Freshness score: <b>{s.freshness_score}</b>/100
                </div>
              </div>
            ))}
      </div>
    </div>
  );
}
