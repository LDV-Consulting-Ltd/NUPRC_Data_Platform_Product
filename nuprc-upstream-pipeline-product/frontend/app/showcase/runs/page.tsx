"use client";

import { useEffect, useState } from "react";
import { backendGet } from "@/lib/backend";

type RunsSummary = {
  ok: boolean;
  total_runs: number;
  success: number;
  failed: number;
  running: number;
  last_run: any;
};

export default function RunsPane() {
  const [data, setData] = useState<RunsSummary | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    backendGet<RunsSummary>("/runs/summary")
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

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

          <div style={{ marginTop: 18, padding: 16, border: "1px solid #eee", borderRadius: 16 }}>
            <h3 style={{ marginTop: 0 }}>Last Run</h3>
            <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{JSON.stringify(data.last_run, null, 2)}</pre>
          </div>
        </>
      )}
    </div>
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
