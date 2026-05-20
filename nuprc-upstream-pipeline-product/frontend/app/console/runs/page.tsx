"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { History } from "lucide-react";
import { listPipelineRuns } from "@/lib/api";
import SectionHeader from "@/components/enterprise/SectionHeader";

type RunRow = {
  run_id: string;
  mode?: string;
  status: string;
  started_at: string;
  ended_at?: string | null;
  rows_loaded?: number;
};

function formatDuration(started: string, ended: string | null | undefined): string {
  if (!ended) return "—";
  const sec = Math.round((new Date(ended).getTime() - new Date(started).getTime()) / 1000);
  if (sec < 60) return `${sec}s`;
  return `${Math.floor(sec / 60)}m ${sec % 60}s`;
}

export default function RunsPage() {
  const [runs, setRuns] = useState<RunRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listPipelineRuns({ limit: 50 })
      .then(({ runs: list, total: t }) => {
        setRuns(list as RunRow[]);
        setTotal(t);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="w-full space-y-6">
      <SectionHeader
        icon={History}
        title="Pipeline Runs"
        description={`${total} runs in registry (admin.etl_runs + meta.pipeline_run).`}
      />
      {loading && <p className="text-slate-500">Loading…</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <section className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-sm w-full">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left p-4 font-semibold">Run ID</th>
                <th className="text-left p-4 font-semibold">Mode</th>
                <th className="text-left p-4 font-semibold">Started</th>
                <th className="text-left p-4 font-semibold">Duration</th>
                <th className="text-left p-4 font-semibold">Rows</th>
                <th className="text-left p-4 font-semibold">Status</th>
                <th className="text-left p-4 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.run_id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="p-4 font-mono text-xs max-w-[180px] truncate" title={run.run_id}>
                    {run.run_id}
                  </td>
                  <td className="p-4 capitalize">{run.mode ?? "—"}</td>
                  <td className="p-4 whitespace-nowrap">{new Date(run.started_at).toLocaleString()}</td>
                  <td className="p-4">{formatDuration(run.started_at, run.ended_at)}</td>
                  <td className="p-4">{run.rows_loaded?.toLocaleString() ?? "—"}</td>
                  <td className="p-4 capitalize">{run.status}</td>
                  <td className="p-4">
                    <Link
                      href={`/console/pipeline?run_id=${encodeURIComponent(run.run_id)}`}
                      className="text-teal-700 font-semibold hover:underline"
                    >
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
