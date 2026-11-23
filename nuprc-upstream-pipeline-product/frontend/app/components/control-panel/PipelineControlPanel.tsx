"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useStartPipelineRun } from "@/hooks/usePipelineRun";
import { cancelPipelineRun } from "@/lib/api";
import PipelineLifecycleTracker from "./PipelineLifecycleTracker";
import type { PipelineMode } from "@/lib/types";

interface PipelineControlPanelProps {
  runId: string | null;
  onRunIdChange: (id: string | null) => void;
  running: boolean;
  runDetail?: {
    status: string;
    steps?: Array<{ step_key: string; label: string; status: string; duration_seconds?: number | null; message?: string | null }>;
  } | null;
}

const LIFECYCLE_STEPS: { key: string; label: string }[] = [
  { key: "source_scraping", label: "1) Source Scraping" },
  { key: "file_acquisition", label: "2) File Acquisition" },
  { key: "bronze_load", label: "3) Bronze Load" },
  { key: "silver_transformation", label: "4) Silver Transformation" },
  { key: "warehouse_modeling", label: "5) Warehouse Modeling" },
  { key: "data_product_generation", label: "6) Data Product Generation" },
];

function stepsFromRunDetail(runDetail: PipelineControlPanelProps["runDetail"]): Array<{ step_key: string; label: string; status: "done" | "running" | "waiting" | "failed"; duration_seconds?: number | null; message?: string | null }> {
  if (!runDetail?.steps?.length) {
    const status = runDetail?.status ?? "waiting";
    const lastDone = status === "success" ? 5 : status === "failed" ? 0 : status === "running" ? 0 : -1;
    return LIFECYCLE_STEPS.map((s, i) => ({
      step_key: s.key,
      label: s.label,
      status: i <= lastDone ? (i === lastDone && status === "running" ? "running" : "done") : "waiting" as const,
      duration_seconds: null,
      message: null,
    }));
  }
  return LIFECYCLE_STEPS.map((s, i) => {
    const fromApi = runDetail.steps?.find((st) => st.step_key === s.key || st.label === s.label);
    let status: "done" | "running" | "waiting" | "failed" = "waiting";
    if (fromApi) {
      if (fromApi.status === "success" || fromApi.status === "done") status = "done";
      else if (fromApi.status === "failed") status = "failed";
      else status = "running";
    } else if (runDetail.status === "running" && i === 0) status = "running";
    return {
      step_key: s.key,
      label: s.label,
      status,
      duration_seconds: fromApi?.duration_seconds ?? null,
      message: fromApi?.message ?? null,
    };
  });
}

const SOURCE_RUNS: { mode: PipelineMode; label: string }[] = [
  { mode: "oil", label: "Oil only" },
  { mode: "gas", label: "Gas only" },
  { mode: "rig", label: "Rig only" },
  { mode: "concession", label: "Concession only" },
];

export default function PipelineControlPanel({ runId, onRunIdChange, running, runDetail }: PipelineControlPanelProps) {
  const [confirmMode, setConfirmMode] = useState<PipelineMode | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const queryClient = useQueryClient();
  const startMutation = useStartPipelineRun();

  const runSingle = (mode: PipelineMode) => {
    startMutation.mutate(mode, {
      onSuccess: (data) => {
        onRunIdChange(data?.run_id ?? null);
      },
    });
  };

  const steps = stepsFromRunDetail(runDetail);

  return (
    <section className="pc-card">
      <div className="pc-card-h">
        <h2>Pipeline control</h2>
      </div>
      <div className="pc-card-b">
        <p className="pc-lede">
          Start an ingestion attempt for all sources, or for oil, gas, rig activity, or concession on its own. Starting a run does not by itself publish a new warehouse snapshot.
        </p>
        <div className="pc-actions" style={{ marginTop: 12 }}>
          <button type="button" className="pc-btn pc-btn-primary" onClick={() => setConfirmMode("full")} disabled={running}>
            Run full pipeline
          </button>
          {SOURCE_RUNS.map((item) => (
            <button key={item.mode} type="button" className="pc-btn" onClick={() => runSingle(item.mode)} disabled={running}>
              {item.label}
            </button>
          ))}
        </div>

        {runId && running && (
          <div className="pc-actions" style={{ marginTop: 12 }}>
            <button
              type="button"
              className="pc-btn pc-btn-danger"
              disabled={cancelling}
              onClick={async () => {
                if (!runId) return;
                setCancelling(true);
                try {
                  await cancelPipelineRun(runId);
                  await queryClient.invalidateQueries({ queryKey: ["pipeline", "run", runId] });
                } finally {
                  setCancelling(false);
                }
              }}
            >
              {cancelling ? "Cancelling…" : "Cancel run"}
            </button>
          </div>
        )}

        {runId && (
          <PipelineLifecycleTracker
            runId={runId}
            steps={steps}
            isLoading={running && steps.every((step) => step.status === "waiting")}
          />
        )}

        {startMutation.isError && (
          <p className="pc-state-body" role="alert">
            {String(startMutation.error?.message ?? "Failed to start run")}
          </p>
        )}
      </div>

      {confirmMode && (
        <div className="pc-modal-back" role="presentation">
          <div className="pc-modal" role="dialog" aria-modal="true" aria-labelledby="confirm-run-title">
            <h2 id="confirm-run-title">{confirmMode === "full" ? "Run full pipeline?" : `Run ${confirmMode} only?`}</h2>
            <p>
              {confirmMode === "full"
                ? "This starts an ingestion attempt for every configured NUPRC source."
                : `This starts an ingestion attempt for the ${confirmMode} source only.`}
            </p>
            <div className="pc-actions">
              <button type="button" className="pc-btn" onClick={() => setConfirmMode(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="pc-btn pc-btn-primary"
                disabled={startMutation.isPending}
                onClick={() => {
                  runSingle(confirmMode);
                  setConfirmMode(null);
                }}
              >
                {startMutation.isPending ? "Starting…" : "Run"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
