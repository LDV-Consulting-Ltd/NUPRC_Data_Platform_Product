"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { backendGet } from "@/lib/backend";

type PipelineStatus = {
  ok: boolean;
  latest_run: {
    run_id: string;
    status: string;
    started_at: string;
    ended_at: string | null;
    rows_loaded?: number;
    message?: string | null;
  } | null;
  bronze_counts?: Record<string, number>;
  warehouse_counts?: Record<string, number>;
};

function normalizeRunStatus(status?: string | null): "success" | "failed" | "running" | "cancelled" | "unknown" {
  const s = (status || "").toLowerCase();
  if (s === "success") return "success";
  if (s === "failed") return "failed";
  if (s === "running") return "running";
  if (s === "cancelled") return "cancelled";
  return "unknown";
}

function statusBadgeStyle(status: ReturnType<typeof normalizeRunStatus>) {
  if (status === "success") return { backgroundColor: "#d4edda", color: "#155724" };
  if (status === "failed") return { backgroundColor: "#f8d7da", color: "#721c24" };
  if (status === "cancelled") return { backgroundColor: "#fff3cd", color: "#856404" };
  return { backgroundColor: "#fff3cd", color: "#856404" };
}

export default function ShowcaseHome() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const data = await backendGet<PipelineStatus>("/pipeline/status");
      setStatus(data);
    } catch (e) {
      console.error("Failed to load status:", e);
    }
  };

  const latestStatus = normalizeRunStatus(status?.latest_run?.status);
  const badgeStyle = statusBadgeStyle(latestStatus);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Pipeline Overview</h2>
      <p style={{ color: "#444", marginBottom: 24 }}>
        View pipeline status and navigate to detailed views. To run the pipeline, go to the{" "}
        <Link href="/" style={{ color: "#f2a36b", textDecoration: "underline" }}>
          Home page
        </Link>
        .
      </p>

      {status && (
        <div style={{ marginTop: 24, padding: 16, border: "1px solid #eee", borderRadius: 8, backgroundColor: "#f9f9f9" }}>
          <h3 style={{ marginTop: 0 }}>Pipeline Status</h3>

          {status.latest_run ? (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 14, marginBottom: 8 }}>
                <strong>Latest Run:</strong>{" "}
                <span
                  style={{
                    padding: "4px 8px",
                    borderRadius: 4,
                    fontSize: 12,
                    fontWeight: 600,
                    ...badgeStyle,
                  }}
                >
                  {status.latest_run.status || "unknown"}
                </span>
                {(status.latest_run.rows_loaded ?? 0) > 0 && (
                  <span style={{ marginLeft: 12, color: "#0a0" }}>
                    ({status.latest_run.rows_loaded!.toLocaleString()} rows loaded)
                  </span>
                )}
              </div>
              {status.latest_run.message && (
                <div style={{ fontSize: 12, color: "#666", fontStyle: "italic" }}>
                  {status.latest_run.message}
                </div>
              )}
              {latestStatus === "running" && (
                <div style={{ marginTop: 12 }}>
                  <Link
                    href={`/showcase/runs?run_id=${status.latest_run.run_id}`}
                    style={{ color: "#0a0", textDecoration: "underline" }}
                  >
                    View detailed logs and progress →
                  </Link>
                </div>
              )}
            </div>
          ) : (
            <div style={{ fontSize: 14, color: "#666", marginBottom: 16 }}>
              No pipeline runs yet. Go to the{" "}
              <Link href="/" style={{ color: "#f2a36b", textDecoration: "underline" }}>
                Home page
              </Link>{" "}
              to start a pipeline run.
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div>
              <h4 style={{ marginTop: 0, fontSize: 14 }}>Bronze Layer</h4>
              <div style={{ fontSize: 12 }}>
                {Object.entries(status.bronze_counts ?? {}).map(([table, count]) => (
                  <div key={table} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>{table.split(".").pop()}:</span>
                    <strong>{count.toLocaleString()}</strong>
                  </div>
                ))}
                {Object.keys(status.bronze_counts ?? {}).length === 0 && (
                  <div style={{ color: "#666" }}>No bronze table counts available.</div>
                )}
              </div>
            </div>
            <div>
              <h4 style={{ marginTop: 0, fontSize: 14 }}>Warehouse Layer</h4>
              <div style={{ fontSize: 12 }}>
                {Object.entries(status.warehouse_counts ?? {}).map(([table, count]) => (
                  <div key={table} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>{table.split(".").pop()}:</span>
                    <strong>{count.toLocaleString()}</strong>
                  </div>
                ))}
                {Object.keys(status.warehouse_counts ?? {}).length === 0 && (
                  <div style={{ color: "#666" }}>No warehouse table counts available.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <div style={{ marginTop: 32, padding: 16, border: "1px solid #eee", borderRadius: 8 }}>
        <h3 style={{ marginTop: 0 }}>Pipeline Steps</h3>
        <ol style={{ margin: 0, paddingLeft: 20 }}>
          <li>Scrape 4 NUPRC sources (Concession, Oil, Gas, Rig)</li>
          <li>Download all available files (PDF/Excel)</li>
          <li>Extract tables and load into Bronze layer</li>
          <li>Transform to Silver with fuzzy column matching</li>
          <li>Load Warehouse dimensional model</li>
          <li>Generate data model diagrams</li>
        </ol>
      </div>
    </div>
  );
}
