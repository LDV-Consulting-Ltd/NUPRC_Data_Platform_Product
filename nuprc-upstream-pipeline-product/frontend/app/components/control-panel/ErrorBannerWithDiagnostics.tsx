"use client";

import { useState } from "react";
import { useRunDiagnostics } from "@/hooks/useRunDiagnostics";

interface ErrorBannerWithDiagnosticsProps {
  runId: string | null;
  userMessage?: string;
  onRetry?: () => void;
  show: boolean;
  variant?: "critical" | "advisory";
  title?: string;
}

export default function ErrorBannerWithDiagnostics({
  runId,
  userMessage,
  onRetry,
  show,
  variant = "critical",
  title,
}: ErrorBannerWithDiagnosticsProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const { data: diagnostics, isLoading } = useRunDiagnostics(runId, detailsOpen);

  if (!show) return null;

  const isAdvisory = variant === "advisory";

  return (
    <section className={`bg-white rounded-2xl border overflow-hidden ${isAdvisory ? "border-amber-200" : "border-slate-200"}`}>
      <div className="p-4 sm:p-5 border-b border-slate-200 flex items-start justify-between gap-3">
        <div>
          <div className="font-bold flex items-center gap-2">
            <span className={`inline-flex h-8 w-8 rounded-lg items-center justify-center ${isAdvisory ? "bg-amber-50 text-amber-600" : "bg-red-50 text-red-600"}`}>⚠</span>
            {title ?? (isAdvisory ? "Source freshness advisory" : "Source connection issue")}
          </div>
          <div className="text-sm text-slate-600 mt-1">
            {userMessage ?? (isAdvisory
              ? "Some sources have lower freshness or row-count scores, but data is available."
              : "One or more NUPRC sources could not be reached. No data has been lost.")}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {onRetry && !isAdvisory && (
          <button
            type="button"
            onClick={onRetry}
            className="px-3 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold"
          >
            Retry
          </button>
          )}
          <button
            type="button"
            onClick={() => setDetailsOpen((o) => !o)}
            className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-sm font-semibold"
          >
            View Details
          </button>
        </div>
      </div>

      {detailsOpen && (
        <div className="p-4 sm:p-5 bg-slate-50">
          <div className="text-xs font-semibold text-slate-600 uppercase">Diagnostics</div>
          {isLoading ? (
            <div className="mt-3 h-24 rounded-xl bg-slate-200 animate-pulse" />
          ) : diagnostics ? (
            <>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="bg-white border border-slate-200 rounded-xl p-4">
                  <div className="text-xs text-slate-500">Failing Source</div>
                  <div className="font-semibold mt-1">{diagnostics.failing_source ?? "—"}</div>
                </div>
                <div className="bg-white border border-slate-200 rounded-xl p-4">
                  <div className="text-xs text-slate-500">Error</div>
                  <div className="font-semibold mt-1 text-red-600">{diagnostics.error_message ?? diagnostics.error_type ?? "—"}</div>
                </div>
                <div className="bg-white border border-slate-200 rounded-xl p-4">
                  <div className="text-xs text-slate-500">Last Successful Sync</div>
                  <div className="font-semibold mt-1">{diagnostics.last_successful_sync ?? "—"}</div>
                </div>
              </div>
              {diagnostics.suggestion && (
                <div className="mt-3 text-xs text-slate-500">{diagnostics.suggestion}</div>
              )}
            </>
          ) : (
            <div className="mt-3 text-sm text-slate-500">No diagnostics available.</div>
          )}
        </div>
      )}
    </section>
  );
}
