"use client";

import { useEffect, useState } from "react";
import { backendGet } from "@/lib/backend";

type QualitySummary = {
  ok: boolean;
  status?: string;
  source?: string;
  kpis: {
    sources_monitored?: number;
    sources_with_data?: number;
    sources_degraded?: number;
    sources_down?: number;
    avg_quality_score?: number;
    total_bronze_rows?: number;
    total_gold_rows?: number;
    rules_passed?: number;
    rules_failed?: number;
  };
  rule_checks: Array<{
    rule_id: string;
    label: string;
    source: string;
    status: string;
    detail: string;
  }>;
  issues: Array<{
    severity: string;
    source: string;
    message: string;
  }>;
  datasets: Array<{
    source_key: string;
    label: string;
    bronze_rows: number;
    bronze_score: number;
    bronze_status: string;
    gold_rows: number;
    gold_score: number;
    gold_status?: string;
    gold_last_updated?: string | null;
  }>;
};

function KpiCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div style={{ minWidth: 160, padding: 14, border: "1px solid #eee", borderRadius: 16 }}>
      <div style={{ fontSize: 12, color: "#666" }}>{title}</div>
      <div style={{ fontSize: 28, fontWeight: 900 }}>{value}</div>
    </div>
  );
}

export default function Quality() {
  const [data, setData] = useState<QualitySummary | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    backendGet<QualitySummary>("/quality/summary")
      .then(setData)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const kpis = data?.kpis ?? {};

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Data Quality Metrics</h2>
      <p style={{ color: "#444", marginBottom: 20 }}>
        Live KPIs and rule checks from v1 bronze source health and gold warehouse freshness.
      </p>

      {loading && <div>Loading quality metrics…</div>}
      {err && (
        <div style={{ padding: 12, border: "1px solid #f00", borderRadius: 8, marginBottom: 16 }}>
          Error loading quality summary: {err}
        </div>
      )}

      {data && (
        <>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
            <KpiCard title="Sources Monitored" value={kpis.sources_monitored ?? 0} />
            <KpiCard title="Sources With Data" value={kpis.sources_with_data ?? 0} />
            <KpiCard title="Avg Quality Score" value={kpis.avg_quality_score ?? 0} />
            <KpiCard title="Bronze Rows" value={(kpis.total_bronze_rows ?? 0).toLocaleString()} />
            <KpiCard title="Gold Rows" value={(kpis.total_gold_rows ?? 0).toLocaleString()} />
            <KpiCard title="Rules Passed" value={kpis.rules_passed ?? 0} />
          </div>

          {data.issues.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ marginTop: 0 }}>Issues</h3>
              {data.issues.map((issue, i) => (
                <div
                  key={`${issue.source}-${i}`}
                  style={{
                    padding: 12,
                    marginBottom: 8,
                    borderRadius: 8,
                    border: `1px solid ${issue.severity === "critical" ? "#f5c6cb" : "#ffeeba"}`,
                    backgroundColor: issue.severity === "critical" ? "#f8d7da" : "#fff3cd",
                    fontSize: 13,
                  }}
                >
                  <strong>{issue.source}</strong> ({issue.severity}): {issue.message}
                </div>
              ))}
            </div>
          )}

          <div style={{ marginBottom: 20 }}>
            <h3 style={{ marginTop: 0 }}>Rule Checks</h3>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ backgroundColor: "#f9f9f9" }}>
                  <th style={{ padding: 10, textAlign: "left", border: "1px solid #eee" }}>Rule</th>
                  <th style={{ padding: 10, textAlign: "left", border: "1px solid #eee" }}>Source</th>
                  <th style={{ padding: 10, textAlign: "left", border: "1px solid #eee" }}>Status</th>
                  <th style={{ padding: 10, textAlign: "left", border: "1px solid #eee" }}>Detail</th>
                </tr>
              </thead>
              <tbody>
                {data.rule_checks.map((rule) => (
                  <tr key={rule.rule_id}>
                    <td style={{ padding: 10, border: "1px solid #eee" }}>{rule.label}</td>
                    <td style={{ padding: 10, border: "1px solid #eee" }}>{rule.source}</td>
                    <td style={{ padding: 10, border: "1px solid #eee" }}>
                      <span
                        style={{
                          padding: "2px 8px",
                          borderRadius: 4,
                          fontSize: 11,
                          fontWeight: 600,
                          backgroundColor: rule.status === "pass" ? "#d4edda" : "#f8d7da",
                          color: rule.status === "pass" ? "#155724" : "#721c24",
                        }}
                      >
                        {rule.status}
                      </span>
                    </td>
                    <td style={{ padding: 10, border: "1px solid #eee" }}>{rule.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h3 style={{ marginTop: 0 }}>Dataset Scores</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 12 }}>
              {data.datasets.map((ds) => (
                <div key={ds.source_key} style={{ padding: 14, border: "1px solid #eee", borderRadius: 12 }}>
                  <div style={{ fontWeight: 700 }}>{ds.label}</div>
                  <div style={{ fontSize: 12, color: "#666", marginTop: 8 }}>
                    Bronze: {ds.bronze_rows.toLocaleString()} rows · score {ds.bronze_score} ({ds.bronze_status})
                  </div>
                  <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
                    Gold: {ds.gold_rows.toLocaleString()} rows · score {ds.gold_score}
                    {ds.gold_last_updated ? ` · updated ${new Date(ds.gold_last_updated).toLocaleDateString()}` : ""}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {data.source && (
            <p style={{ marginTop: 16, fontSize: 11, color: "#999" }}>Source: {data.source}</p>
          )}
        </>
      )}
    </div>
  );
}
