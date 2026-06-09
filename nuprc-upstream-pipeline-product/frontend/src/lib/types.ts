export type PipelineMode = "full" | "oil" | "gas" | "rig" | "concession" | "retry_failed_sources";

export interface PipelineStep {
  step_key: string;
  label: string;
  status: "done" | "running" | "waiting" | "failed" | "cancelled";
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds?: number | null;
  message?: string | null;
  /** When present, green (Done) should only show when rows_written > 0 or step was skipped for mode */
  metrics?: { rows_written?: number } | null;
}

export interface PlatformStatus {
  system_health: "healthy" | "degraded";
  last_run: { at: string; duration_seconds: number; status: "success" | "failed" | "cancelled" } | null;
  records_today: number;
  avg_freshness_minutes: number;
  sla_compliance: { met: number; total: number; label: string };
}

export interface PipelineRunStart {
  run_id: string;
}

export interface PipelineRunDetail {
  run_id: string;
  status: "running" | "success" | "failed" | "cancelled";
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  steps: PipelineStep[];
  message?: string | null;
  rows_loaded?: number;
}

export type SourceHealthItem = {
  source_key: string;
  label: string;
  status: "fresh" | "stable" | "degraded" | "down";
  last_update: string | null;
  expected_interval_minutes: number;
  freshness_score: number;
  last_error: string | null;
  row_count?: number;
  reachability_status?: "reachable" | "unavailable";
  data_presence_status?: "available" | "missing";
  freshness_status?: string;
  health_status?: string;
  explanation?: string;
};

export interface RunDiagnostics {
  failing_source: string | null;
  error_type: string;
  error_message: string;
  last_successful_sync: string | null;
  suggestion: string;
  raw?: unknown;
}
