"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { listPipelineRuns } from "@/lib/api";
import { errorMessage, permissionDenied } from "@/lib/page-error";
import {
  CountLabel,
  GapNote,
  LoadingRows,
  PageHeader,
  PermissionState,
  SortTable,
  StateBlock,
  StatusPill,
  toneForStatus,
} from "../components/console/ui";

type RunRow = {
  run_id: string;
  mode: string;
  status: string;
  started_at: string;
  ended_at?: string | null;
};

export default function RunHistoryPage() {
  const params = useSearchParams();
  const router = useRouter();
  const status = params.get("status") ?? "";
  const [result, setResult] = useState<{ status: string; rows: RunRow[]; total: number; error: unknown } | null>(null);
  const [selected, setSelected] = useState<string | null>(params.get("run_id"));

  useEffect(() => {
    let cancelled = false;
    listPipelineRuns({ limit: 50, status: status || undefined })
      .then((res) => {
        if (!cancelled) setResult({ status, rows: res.runs, total: res.total, error: null });
      })
      .catch((err) => {
        if (!cancelled) setResult({ status, rows: [], total: 0, error: err });
      });
    return () => {
      cancelled = true;
    };
  }, [status]);

  const loading = result?.status !== status;
  const rows = result?.status === status ? result.rows : [];
  const total = result?.status === status ? result.total : 0;
  const error = result?.status === status ? result.error : null;

  const setStatus = (next: string) => {
    const query = new URLSearchParams(params.toString());
    if (next) query.set("status", next);
    else query.delete("status");
    const qs = query.toString();
    router.replace(qs ? `/run-history?${qs}` : "/run-history");
  };

  const current = rows.find((row) => row.run_id === selected) ?? null;

  return (
    <>
      <PageHeader
        title="Ingestion Runs"
        description="Pipeline attempts returned by the operations API. This list is the attempt history. It is not the published warehouse snapshot."
        actions={
          <label>
            Status
            <select className="pc-field" value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">All</option>
              <option value="running">Running</option>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </label>
        }
      />
      {loading && <LoadingRows />}
      {!loading && error != null &&
        (permissionDenied(error) ? (
          <PermissionState />
        ) : (
          <StateBlock tone="error" title="Ingestion runs could not be loaded">
            {errorMessage(error)}
          </StateBlock>
        ))}
      {!loading && error == null && (
        <div className="pc-work">
          <div className="pc-work-main">
            <CountLabel shown={rows.length} total={total} />
            <SortTable
              rows={rows}
              caption="Pipeline runs"
              rowKey={(row) => row.run_id}
              selectedKey={current?.run_id}
              onRow={(row) => setSelected(row.run_id)}
              empty={<StateBlock tone="empty" title="No ingestion runs match this filter" />}
              columns={[
                { id: "id", header: "Run", sticky: true, sortValue: (row) => row.run_id, cell: (row) => row.run_id },
                { id: "mode", header: "Mode", sortValue: (row) => row.mode, cell: (row) => row.mode },
                {
                  id: "status",
                  header: "Result",
                  sortValue: (row) => row.status,
                  cell: (row) => <StatusPill tone={toneForStatus(row.status)}>{row.status}</StatusPill>,
                },
                {
                  id: "started",
                  header: "Started",
                  sortValue: (row) => row.started_at,
                  cell: (row) => new Date(row.started_at).toLocaleString("en-GB"),
                },
                {
                  id: "ended",
                  header: "Ended",
                  sortValue: (row) => row.ended_at ?? null,
                  cell: (row) => (row.ended_at ? new Date(row.ended_at).toLocaleString("en-GB") : "—"),
                },
              ]}
            />
            <GapNote>Cost, data volume, and SLA impact are not on this runs payload, so they are omitted rather than filled in.</GapNote>
          </div>
          {current && (
            <aside className="pc-detail" aria-label="Run detail">
              <div className="pc-detail-bar">
                <h2>Attempt</h2>
                <button type="button" className="pc-btn" onClick={() => setSelected(null)}>
                  Close
                </button>
              </div>
              <dl className="pc-detail-list">
                <div>
                  <dt>Run</dt>
                  <dd>{current.run_id}</dd>
                </div>
                <div>
                  <dt>Mode</dt>
                  <dd>{current.mode}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{current.status}</dd>
                </div>
                <div>
                  <dt>Started</dt>
                  <dd>{new Date(current.started_at).toLocaleString("en-GB")}</dd>
                </div>
                <div>
                  <dt>Ended</dt>
                  <dd>{current.ended_at ? new Date(current.ended_at).toLocaleString("en-GB") : "Still open or not supplied"}</dd>
                </div>
              </dl>
              <p className="pc-detail-note">
                Re-running is done from the <Link href="/control-panel">Control Panel</Link>. This page does not start a pipeline.
              </p>
            </aside>
          )}
        </div>
      )}
    </>
  );
}
