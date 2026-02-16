"use client";

import type { PipelineStep } from "@/lib/types";

interface PipelineLifecycleTrackerProps {
  runId: string | null;
  steps: PipelineStep[];
  isLoading?: boolean;
}

function getStepBadge(step: PipelineStep): { className: string; label: string } {
  if (step.status === "done") {
    const rw = step.metrics?.rows_written;
    if (rw !== undefined && rw === 0) {
      return { className: "bg-slate-100 text-slate-600", label: "Done (skipped)" };
    }
    return { className: "bg-emerald-50 text-emerald-700", label: "✅ Done" };
  }
  const map: Record<PipelineStep["status"], { className: string; label: string }> = {
    running: { className: "bg-blue-50 text-blue-700", label: "🔄 Running" },
    waiting: { className: "bg-slate-200 text-slate-700", label: "⏳ Waiting" },
    failed: { className: "bg-red-50 text-red-700", label: "❌ Failed" },
    cancelled: { className: "bg-slate-200 text-slate-600", label: "Cancelled" },
    done: { className: "bg-emerald-50 text-emerald-700", label: "✅ Done" },
  };
  return map[step.status] ?? map.waiting;
}

export default function PipelineLifecycleTracker({ runId, steps, isLoading }: PipelineLifecycleTrackerProps) {
  return (
    <div className="mt-6">
      <div className="flex items-center justify-between">
        <div className="font-semibold">Pipeline Lifecycle</div>
        <div className="text-xs text-slate-500">
          Run ID: <span className="font-mono">{runId ? runId.slice(0, 8) + "…" : "—"}</span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-between">
              <div className="h-4 w-32 rounded bg-slate-200 animate-pulse" />
              <div className="h-6 w-16 rounded bg-slate-200 animate-pulse" />
            </div>
          ))
        ) : (
          steps.map((step) => {
            const badge = getStepBadge(step);
            const sub = step.duration_seconds != null ? `Duration: ${Math.floor(step.duration_seconds / 60)}m ${step.duration_seconds % 60}s` : step.status === "waiting" ? "Queued" : step.status === "running" ? "In progress" : step.status === "cancelled" ? "Cancelled" : "";
            return (
              <div
                key={step.step_key}
                className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-between"
              >
                <div>
                  <div className="text-sm font-semibold">{step.label}</div>
                  <div className="text-xs text-slate-500 mt-1">{sub}</div>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${badge.className}`}>
                  {badge.label}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
