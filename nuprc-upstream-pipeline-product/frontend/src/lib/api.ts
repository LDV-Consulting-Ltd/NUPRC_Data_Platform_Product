/**
 * Pipeline API client (v1): /v1/pipeline/*
 */
import { backendGet, backendPost } from "./backend";
import type {
  PlatformStatus,
  PipelineMode,
  PipelineRunStart,
  PipelineRunDetail,
  SourceHealthItem,
  RunDiagnostics,
} from "./types";

/** GET /v1/pipeline/platform/status → PlatformStatus */
export async function fetchPlatformStatus(): Promise<PlatformStatus> {
  const data = await backendGet<{ ok: boolean; latest_run?: { run_id: string; status: string; started_at: string; ended_at: string | null; meta_json?: unknown } | null }>("/v1/pipeline/platform/status");
  const latest = data.latest_run;
  let last_run: PlatformStatus["last_run"] = null;
  if (latest) {
    const end = latest.ended_at ? new Date(latest.ended_at).getTime() : null;
    const start = new Date(latest.started_at).getTime();
    const dur = end ? Math.round((end - start) / 1000) : 0;
    last_run = {
      at: latest.started_at,
      duration_seconds: dur,
      status: latest.status === "success" ? "success" : latest.status === "failed" ? "failed" : "cancelled",
    };
  }
  const meta = (latest as { meta_json?: { rows_loaded?: number } })?.meta_json;
  const rows = typeof meta === "object" && meta && "rows_loaded" in meta ? Number((meta as { rows_loaded?: number }).rows_loaded) : 0;
  return {
    system_health: latest?.status === "running" ? "healthy" : latest?.status === "failed" ? "degraded" : "healthy",
    last_run,
    records_today: rows,
    avg_freshness_minutes: 138,
    sla_compliance: { met: 30, total: 30, label: "Daily SLA: 02:00 delivery" },
  };
}

/** POST /v1/pipeline/runs { mode } → { run_id } */
export async function startPipelineRun(mode: PipelineMode): Promise<PipelineRunStart> {
  const data = await backendPost<{ ok: boolean; run_id: string }>("/v1/pipeline/runs", { mode });
  return { run_id: data.run_id };
}

/** GET /v1/pipeline/runs/:run_id → PipelineRunDetail (6 canonical steps) */
export async function fetchPipelineRun(runId: string): Promise<PipelineRunDetail> {
  const data = await backendGet<{
    ok: boolean;
    run_id: string;
    status: string;
    started_at: string | null;
    ended_at: string | null;
    steps: Array<{ step_key: string; label: string; status: string; started_at?: string | null; ended_at?: string | null; duration_seconds?: number | null; error?: string | null; metrics?: { rows_written?: number } }>;
    meta?: { rows_loaded?: number };
    user_message?: string | null;
  }>(`/v1/pipeline/runs/${runId}`);
  const start = data.started_at ? new Date(data.started_at).getTime() : 0;
  const end = data.ended_at ? new Date(data.ended_at).getTime() : null;
  const durationSeconds = end ? Math.round((end - start) / 1000) : null;
  const steps = (data.steps || []).map((s) => ({
    step_key: s.step_key,
    label: s.label || s.step_key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    status: (s.status === "done" ? "done" : s.status === "failed" ? "failed" : s.status === "cancelled" ? "cancelled" : s.status === "running" ? "running" : "waiting") as PipelineRunDetail["steps"][0]["status"],
    started_at: s.started_at ?? null,
    finished_at: s.ended_at ?? null,
    duration_seconds: s.duration_seconds ?? null,
    message: s.error ?? null,
    metrics: s.metrics ?? null,
  }));
  return {
    run_id: data.run_id,
    status: (data.status === "running" ? "running" : data.status === "success" ? "success" : data.status === "cancelled" ? "cancelled" : "failed") as PipelineRunDetail["status"],
    started_at: data.started_at ?? null,
    finished_at: data.ended_at ?? null,
    duration_seconds: durationSeconds,
    steps,
    message: data.user_message ?? null,
    rows_loaded: data.meta?.rows_loaded ?? 0,
  };
}

/** POST /v1/pipeline/runs { mode: "retry_failed_sources" } for source-issue retry */
export async function retryPipelineRun(_runId?: string): Promise<{ run_id: string }> {
  return startPipelineRun("retry_failed_sources");
}

/** GET /v1/pipeline/sources/health → SourceHealthItem[] (bronze-layer health) */
export async function fetchSourcesHealth(): Promise<SourceHealthItem[]> {
  const data = await backendGet<{ ok: boolean; sources: Array<{ source_key: string; label: string; status: string; freshness_score: number; row_count?: number }> }>("/v1/pipeline/sources/health");
  return (data.sources || []).map((s) => ({
    source_key: s.source_key,
    label: s.label,
    status: (s.status === "fresh" ? "fresh" : s.status === "down" ? "down" : s.status === "degraded" ? "degraded" : "stable") as SourceHealthItem["status"],
    last_update: null,
    expected_interval_minutes: 120,
    freshness_score: s.freshness_score ?? 50,
    last_error: null,
  }));
}

/** GET /v1/pipeline/freshness → Data freshness from Gold/Warehouse layer only (for Control Panel Data Freshness cards) */
export async function fetchGoldFreshness(): Promise<SourceHealthItem[]> {
  const data = await backendGet<{ ok: boolean; sources: Array<{ source_key: string; label: string; status: string; freshness_score: number; row_count?: number; last_updated?: string | null; expected_interval_minutes?: number }> }>("/v1/pipeline/freshness");
  return (data.sources || []).map((s) => ({
    source_key: s.source_key,
    label: s.label,
    status: (s.status === "fresh" ? "fresh" : s.status === "down" ? "down" : s.status === "degraded" ? "degraded" : "stable") as SourceHealthItem["status"],
    last_update: s.last_updated ?? null,
    expected_interval_minutes: s.expected_interval_minutes ?? 120,
    freshness_score: s.freshness_score ?? 50,
    last_error: null,
  }));
}

/** GET /v1/pipeline/runs/:run_id/diagnostics → RunDiagnostics */
export async function fetchRunDiagnostics(runId: string): Promise<RunDiagnostics> {
  const data = await backendGet<{ ok: boolean; user_message?: string; technical_details?: unknown; steps?: unknown[] }>(`/v1/pipeline/runs/${runId}/diagnostics`);
  return {
    failing_source: null,
    error_type: "PipelineError",
    error_message: data.user_message ?? "See technical_details",
    last_successful_sync: null,
    suggestion: "Check source URLs and network; run healthcheck.",
    raw: data.technical_details,
  };
}

/** POST /v1/pipeline/runs/:run_id/cancel */
export async function cancelPipelineRun(runId: string): Promise<{ ok: boolean; run_id: string; status: string }> {
  const data = await backendPost<{ ok: boolean; run_id: string; status: string }>(`/v1/pipeline/runs/${runId}/cancel`);
  return data;
}

/** GET /v1/pipeline/runs (list with pagination) */
export async function listPipelineRuns(params?: { limit?: number; offset?: number; status?: string; mode?: string }): Promise<{ runs: Array<{ run_id: string; mode: string; status: string; started_at: string; ended_at?: string | null }>; total: number }> {
  const q = new URLSearchParams();
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  if (params?.status) q.set("status", params.status);
  if (params?.mode) q.set("mode", params.mode);
  const data = await backendGet<{ ok: boolean; runs: unknown[]; total: number }>(`/v1/pipeline/runs?${q.toString()}`);
  return { runs: data.runs as Array<{ run_id: string; mode: string; status: string; started_at: string; ended_at?: string | null }>, total: data.total };
}

/** POST /v1/pipeline/runs/clear-stuck */
export async function clearStuckRuns(): Promise<{ ok: boolean; cleared: number; run_ids: string[] }> {
  return backendPost<{ ok: boolean; cleared: number; run_ids: string[] }>("/v1/pipeline/runs/clear-stuck");
}

/** GET /v1/pipeline/runs/blocking */
interface BlockingRunsResponse {
  ok: boolean;
  blocking_runs: Array<{
    run_id: string;
    mode: string;
    status: string;
    started_at: string | null;
  }>;
  blocking: boolean;
}

/** GET /v1/pipeline/runs/blocking */
export async function checkBlockingRuns(): Promise<BlockingRunsResponse> {
  return backendGet<BlockingRunsResponse>(
    "/v1/pipeline/runs/blocking"
  );
}

/** GET /v1/pipeline/test */
export async function fetchPipelineTest(): Promise<{ ok: boolean; timestamp: string; version: string }> {
  return backendGet<{ ok: boolean; timestamp: string; version: string }>("/v1/pipeline/test");
}

/** GET /catalog/tables?layer=bronze|silver|gold — current catalog (canonical tables only) */
export interface CatalogTable {
  physical_name: string;
  display_name: string;
  description: string;
  row_count: number;
  last_updated: string | null;
  subject_area?: string | null;
  grain?: string | null;
}
export async function fetchCatalogTables(layer: "bronze" | "silver" | "gold"): Promise<{ layer: string; schema: string; tables: CatalogTable[] }> {
  const data = await backendGet<{ ok: boolean; layer: string; schema: string; tables: CatalogTable[] }>(`/catalog/tables?layer=${encodeURIComponent(layer)}`);
  return { layer: data.layer, schema: data.schema, tables: data.tables };
}
