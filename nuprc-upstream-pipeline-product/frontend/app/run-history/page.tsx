"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import V2Header from "../components/V2Header";
import { backendGet } from "@/lib/backend";

type RunHistoryItem = {
  run_id: string;
  status: string;
  mode?: string;
  triggered_by?: string;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
  rows_bronze: number | null;
  error_summary?: string | null;
};

type RunHistoryResponse = {
  ok: boolean;
  source: string;
  total: number;
  runs: RunHistoryItem[];
};

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function formatVolume(rows: number | null): string {
  if (rows == null || rows === 0) return "—";
  if (rows >= 1_000_000) return `${(rows / 1_000_000).toFixed(2)}M`;
  if (rows >= 1_000) return `${(rows / 1_000).toFixed(1)}K`;
  return rows.toLocaleString();
}

function normalizeStatus(status?: string | null): string {
  return (status || "unknown").toLowerCase();
}

function statusLabel(status: string): string {
  const s = normalizeStatus(status);
  if (s === "success") return "Success";
  if (s === "failed") return "Failed";
  if (s === "running") return "Running";
  return s;
}

export default function RunHistoryPage() {
  const [data, setData] = useState<RunHistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    backendGet<RunHistoryResponse>("/v1/pipeline/runs/history?limit=50")
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const runs = data?.runs ?? [];

  return (
    <>
      <V2Header
        title="Run History"
        subtitle="Live v1 ETL runs from admin.etl_runs — trigger, duration, volume, and result"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {loading && <div className="text-sm text-slate-500">Loading run history…</div>}
        {error && (
          <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-red-700 text-sm">
            Failed to load run history: {error}
          </div>
        )}

        <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="p-4 sm:p-5 border-b border-slate-200">
            <div className="text-sm text-slate-500">
              Run Timeline ({data?.total ?? 0} v1 runs from {data?.source ?? "admin.etl_runs"})
            </div>
            <div className="mt-3 flex gap-2 overflow-x-auto pb-2">
              {runs.slice(0, 7).map((run, i) => (
                <button
                  key={run.run_id}
                  type="button"
                  className={`shrink-0 px-4 py-2 rounded-xl text-sm font-semibold ${
                    i === 0 ? "bg-ldv-green text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  {run.started_at
                    ? new Date(run.started_at).toLocaleString(undefined, {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : run.run_id.slice(0, 8)}
                </button>
              ))}
              {runs.length === 0 && !loading && (
                <span className="text-sm text-slate-500">No v1 runs recorded yet.</span>
              )}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="text-left p-4 font-semibold">Run ID</th>
                  <th className="text-left p-4 font-semibold">Trigger</th>
                  <th className="text-left p-4 font-semibold">Duration</th>
                  <th className="text-left p-4 font-semibold">Data Volume</th>
                  <th className="text-left p-4 font-semibold">Result</th>
                  <th className="text-left p-4 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => {
                  const result = statusLabel(run.status);
                  const isSuccess = normalizeStatus(run.status) === "success";
                  return (
                    <tr key={run.run_id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="p-4 font-mono text-xs">{run.run_id}</td>
                      <td className="p-4">{run.triggered_by || run.mode || "—"}</td>
                      <td className="p-4">{formatDuration(run.duration_seconds)}</td>
                      <td className="p-4">{formatVolume(run.rows_bronze)}</td>
                      <td className="p-4">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            isSuccess ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                          }`}
                        >
                          {result}
                        </span>
                        {run.error_summary && (
                          <div className="text-xs text-slate-500 mt-1 max-w-xs truncate" title={run.error_summary}>
                            {run.error_summary}
                          </div>
                        )}
                      </td>
                      <td className="p-4">
                        <Link
                          href={`/showcase/runs?run_id=${run.run_id}`}
                          className="text-ldv-blue font-semibold hover:underline"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        <p className="text-xs text-slate-500">
          Data source: admin.etl_runs (v1 ETL). Cost and SLA columns are not tracked in v1 observability yet.
        </p>
      </div>
    </>
  );
}
