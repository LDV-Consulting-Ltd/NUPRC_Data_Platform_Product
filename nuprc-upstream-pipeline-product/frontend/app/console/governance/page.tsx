"use client";

import { useEffect, useState } from "react";
import { Shield } from "lucide-react";
import { backendGet } from "@/lib/backend";
import SectionHeader from "@/components/enterprise/SectionHeader";
import StatusCard from "@/components/enterprise/StatusCard";
import { FileStack, GitBranch, Table2 } from "lucide-react";

type GovernanceSummary = {
  ok: boolean;
  metadata: {
    file_registry_count: number;
    pipeline_runs: number;
    tables_with_data: number;
  };
  lineage_coverage_pct: number;
  schema_drift: Array<Record<string, unknown>>;
  schema_drift_high_count: number;
  table_health: Array<{ schema: string; table: string; row_count: number }>;
  last_run?: { run_id: string; status: string; started_at: string } | null;
};

export default function GovernancePage() {
  const [data, setData] = useState<GovernanceSummary | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    backendGet<GovernanceSummary>("/v1/governance/summary")
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="w-full space-y-6">
      <SectionHeader
        icon={Shield}
        title="Governance"
        description="Metadata registry, lineage coverage, and table health across layers."
      />
      {err && <p className="text-red-600 text-sm">{err}</p>}
      {data && (
        <>
          <div className="enterprise-grid">
            <StatusCard icon={FileStack} label="Files registered" value={data.metadata.file_registry_count} />
            <StatusCard icon={GitBranch} label="Pipeline runs" value={data.metadata.pipeline_runs} tone="teal" />
            <StatusCard icon={Table2} label="Tables with data" value={data.metadata.tables_with_data} />
            <StatusCard
              icon={Shield}
              label="Lineage coverage"
              value={`${data.lineage_coverage_pct}%`}
              hint={`${data.schema_drift_high_count} high-severity drift`}
              tone={data.schema_drift_high_count > 0 ? "warning" : "success"}
            />
          </div>

          {data.last_run && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
              <span className="font-semibold text-[#0f2744]">Last ETL run: </span>
              <span className="font-mono">{data.last_run.run_id}</span>
              <span className="mx-2 text-slate-300">·</span>
              <span className="capitalize">{data.last_run.status}</span>
              <span className="mx-2 text-slate-300">·</span>
              {data.last_run.started_at && new Date(data.last_run.started_at).toLocaleString()}
            </div>
          )}

          <section className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-sm">
            <h3 className="p-4 font-bold text-[#0f2744] border-b border-slate-100">Table health (top)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="text-left p-3 font-semibold">Schema</th>
                    <th className="text-left p-3 font-semibold">Table</th>
                    <th className="text-right p-3 font-semibold">Rows</th>
                  </tr>
                </thead>
                <tbody>
                  {data.table_health.map((t) => (
                    <tr key={`${t.schema}.${t.table}`} className="border-b border-slate-100">
                      <td className="p-3">{t.schema}</td>
                      <td className="p-3 font-mono text-xs">{t.table}</td>
                      <td className="p-3 text-right font-semibold">{t.row_count.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-sm">
            <h3 className="p-4 font-bold text-[#0f2744] border-b border-slate-100">
              Recent schema drift ({data.schema_drift.length})
            </h3>
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="text-left p-3 font-semibold">Source</th>
                    <th className="text-left p-3 font-semibold">Original</th>
                    <th className="text-left p-3 font-semibold">Mapped</th>
                    <th className="text-left p-3 font-semibold">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {data.schema_drift.slice(0, 20).map((d, i) => (
                    <tr key={i} className="border-b border-slate-100">
                      <td className="p-3">{String(d.source_key ?? "—")}</td>
                      <td className="p-3 font-mono text-xs">{String(d.original_column ?? "—")}</td>
                      <td className="p-3 font-mono text-xs">{String(d.mapped_column ?? "—")}</td>
                      <td className="p-3 capitalize">{String(d.severity ?? "—")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
