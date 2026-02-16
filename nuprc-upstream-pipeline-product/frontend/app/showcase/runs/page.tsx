"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { backendGet, backendPost } from "@/lib/backend";

type RunsSummary = {
  ok: boolean;
  total_runs: number;
  success: number;
  failed: number;
  running: number;
  last_run: any;
};

type PipelineRun = {
  ok: boolean;
  run: {
    run_id: string;
    status: string;
    started_at: string;
    ended_at: string | null;
    rows_loaded: number;
    message: string | null;
  };
  logs: Array<{
    id: number;
    ts: string;
    level: string;
    message: string;
  }>;
};

function RunsPaneContent() {
  const [data, setData] = useState<RunsSummary | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [runDetails, setRunDetails] = useState<PipelineRun | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const searchParams = useSearchParams();
  const router = useRouter();
  const runId = searchParams?.get("run_id");

  useEffect(() => {
    backendGet<RunsSummary>("/runs/summary")
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    if (runId) {
      const loadRunDetails = () => {
        backendGet<{ ok: boolean; run_id: string; status: string; started_at: string | null; ended_at: string | null; steps: unknown[]; meta?: { rows_loaded?: number }; user_message?: string | null }>(`/v1/pipeline/runs/${runId}`)
          .then((v1) => ({
            ok: true,
            run: {
              run_id: v1.run_id,
              status: (v1.status || "").toUpperCase(),
              started_at: v1.started_at || "",
              ended_at: v1.ended_at,
              rows_loaded: v1.meta?.rows_loaded ?? 0,
              message: v1.user_message ?? null,
            },
            logs: [],
          }))
          .then(setRunDetails as (x: PipelineRun) => void)
          .catch((e) => console.error("Failed to load run details:", e));
      };
      loadRunDetails();
      const interval = setInterval(loadRunDetails, 3000);
      return () => clearInterval(interval);
    }
  }, [runId]);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Number of Runs</h2>

      {err && <div style={{ padding: 12, border: "1px solid #f00" }}>Error: {err}</div>}
      {!data && !err && <div>Loading…</div>}

      {data && (
        <>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Card title="Total Runs" value={data.total_runs} />
            <Card title="Success" value={data.success} />
            <Card title="Failed" value={data.failed} />
            <Card title="Running" value={data.running} />
          </div>

          {runDetails ? (
            <div style={{ marginTop: 24, padding: 16, border: "1px solid #eee", borderRadius: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <h3 style={{ marginTop: 0, marginBottom: 0 }}>
                  Run Details: {runDetails.run.run_id.substring(0, 8)}...
                  <span style={{ 
                    marginLeft: 12, 
                    padding: "4px 8px", 
                    borderRadius: 4,
                    backgroundColor: runDetails.run.status === "SUCCESS" ? "#d4edda" : 
                                     runDetails.run.status === "FAILED" ? "#f8d7da" : 
                                     runDetails.run.status === "CANCELLED" ? "#fff3cd" : "#fff3cd",
                    color: runDetails.run.status === "SUCCESS" ? "#155724" : 
                           runDetails.run.status === "FAILED" ? "#721c24" : 
                           runDetails.run.status === "CANCELLED" ? "#856404" : "#856404",
                    fontSize: 12
                  }}>
                    {runDetails.run.status}
                  </span>
                </h3>
                {runDetails.run.status === "RUNNING" && (
                  <button
                    onClick={async () => {
                      setCancelling(true);
                      try {
                        await backendPost(`/v1/pipeline/runs/${runDetails.run.run_id}/cancel`);
                        // Refresh the page to show updated status
                        setTimeout(() => {
                          router.refresh();
                          setCancelling(false);
                        }, 1000);
                      } catch (e) {
                        setErr(String(e));
                        setCancelling(false);
                      }
                    }}
                    disabled={cancelling}
                    style={{
                      padding: "8px 16px",
                      fontSize: 14,
                      fontWeight: 600,
                      backgroundColor: cancelling ? "#ccc" : "#dc3545",
                      color: "#fff",
                      border: "none",
                      borderRadius: 6,
                      cursor: cancelling ? "not-allowed" : "pointer",
                    }}
                  >
                    {cancelling ? "Cancelling..." : "Cancel Pipeline"}
                  </button>
                )}
              </div>
              
              <div style={{ marginBottom: 16, fontSize: 12, color: "#666" }}>
                Started: {new Date(runDetails.run.started_at).toLocaleString()}
                {runDetails.run.ended_at && (
                  <> | Ended: {new Date(runDetails.run.ended_at).toLocaleString()}</>
                )}
                {runDetails.run.rows_loaded > 0 && (
                  <> | Rows: {runDetails.run.rows_loaded.toLocaleString()}</>
                )}
              </div>

              {runDetails.run.message && (
                <div style={{ 
                  padding: 12, 
                  marginBottom: 16, 
                  backgroundColor: "#f8d7da", 
                  border: "1px solid #f5c6cb",
                  borderRadius: 4,
                  color: "#721c24"
                }}>
                  {runDetails.run.message}
                </div>
              )}

              <div style={{ maxHeight: 400, overflow: "auto", border: "1px solid #ddd", borderRadius: 4, padding: 12 }}>
                <h4 style={{ marginTop: 0, fontSize: 14 }}>Logs ({runDetails.logs.length})</h4>
                <div style={{ fontFamily: "monospace", fontSize: 11 }}>
                  {runDetails.logs.map((log) => (
                    <div 
                      key={log.id} 
                      style={{ 
                        marginBottom: 4,
                        padding: 4,
                        backgroundColor: log.level === "ERROR" ? "#fee" : 
                                        log.level === "WARN" ? "#ffeaa7" : "#f0f0f0"
                      }}
                    >
                      <span style={{ color: "#666" }}>
                        [{new Date(log.ts).toLocaleTimeString()}] 
                      </span>
                      <span style={{ 
                        fontWeight: 600,
                        color: log.level === "ERROR" ? "#c00" : 
                               log.level === "WARN" ? "#a60" : "#000"
                      }}>
                        {log.level}:
                      </span>
                      <span style={{ marginLeft: 8 }}>{log.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ marginTop: 18, padding: 16, border: "1px solid #eee", borderRadius: 16 }}>
              <h3 style={{ marginTop: 0 }}>Last Run</h3>
              <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{JSON.stringify(data.last_run, null, 2)}</pre>
              {data.last_run && (
                <div style={{ marginTop: 12 }}>
                  <a 
                    href={`/showcase/runs?run_id=${data.last_run.run_id}`}
                    style={{ color: "#0a0", textDecoration: "underline" }}
                  >
                    View detailed logs →
                  </a>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function RunsPane() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <RunsPaneContent />
    </Suspense>
  );
}

function Card({ title, value }: { title: string; value: any }) {
  return (
    <div style={{ width: 220, padding: 14, border: "1px solid #eee", borderRadius: 16 }}>
      <div style={{ fontSize: 12, color: "#444" }}>{title}</div>
      <div style={{ fontSize: 28, fontWeight: 900 }}>{String(value)}</div>
    </div>
  );
}
