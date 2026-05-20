"use client";

import { useEffect, useState } from "react";
import { GitCompare } from "lucide-react";
import { backendGet } from "@/lib/backend";
import SectionHeader from "@/components/enterprise/SectionHeader";
import StatusCard from "@/components/enterprise/StatusCard";
import { AlertTriangle } from "lucide-react";

type DriftRow = {
  source_key?: string;
  reporting_year?: number;
  original_column?: string;
  mapped_column?: string;
  confidence?: number;
  severity?: string;
  detected_at?: string;
};

type GovernanceSummary = {
  ok: boolean;
  schema_drift: DriftRow[];
  schema_drift_high_count: number;
};

export default function SchemaDriftPage() {
  const [rows, setRows] = useState<DriftRow[]>([]);
  const [highCount, setHighCount] = useState(0);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    backendGet<GovernanceSummary>("/v1/governance/summary")
      .then((d) => {
        setRows(d.schema_drift || []);
        setHighCount(d.schema_drift_high_count ?? 0);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="w-full space-y-6">
      <SectionHeader
        icon={GitCompare}
        title="Schema Drift"
        description="Fuzzy column mappings and severity from meta.schema_drift."
      />
      {err && <p className="text-red-600 text-sm">{err}</p>}
      <div className="enterprise-grid max-w-2xl">
        <StatusCard icon={GitCompare} label="Total drift events" value={rows.length} />
        <StatusCard
          icon={AlertTriangle}
          label="High severity"
          value={highCount}
          tone={highCount > 0 ? "warning" : "success"}
        />
      </div>
      <section className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-sm w-full">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left p-3 font-semibold">Source</th>
                <th className="text-left p-3 font-semibold">Year</th>
                <th className="text-left p-3 font-semibold">Original column</th>
                <th className="text-left p-3 font-semibold">Mapped column</th>
                <th className="text-left p-3 font-semibold">Confidence</th>
                <th className="text-left p-3 font-semibold">Severity</th>
                <th className="text-left p-3 font-semibold">Detected</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-6 text-slate-500 text-center">
                    No schema drift recorded.
                  </td>
                </tr>
              ) : (
                rows.map((d, i) => (
                  <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="p-3">{d.source_key ?? "—"}</td>
                    <td className="p-3">{d.reporting_year ?? "—"}</td>
                    <td className="p-3 font-mono text-xs">{d.original_column ?? "—"}</td>
                    <td className="p-3 font-mono text-xs">{d.mapped_column ?? "—"}</td>
                    <td className="p-3">{d.confidence != null ? `${Math.round(d.confidence * 100)}%` : "—"}</td>
                    <td className="p-3 capitalize">{d.severity ?? "—"}</td>
                    <td className="p-3 whitespace-nowrap">
                      {d.detected_at ? new Date(d.detected_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
