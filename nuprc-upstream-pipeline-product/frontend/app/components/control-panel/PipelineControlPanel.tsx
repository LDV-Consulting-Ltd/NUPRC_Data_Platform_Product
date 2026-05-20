"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useStartPipelineRun, useStartPgPipelineRun } from "@/hooks/usePipelineRun";
import { cancelPipelineRun } from "@/lib/api";
import PipelineLifecycleTracker from "./PipelineLifecycleTracker";
import type { PipelineMode, PgPipelineMode } from "@/lib/types";

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
  const stepStatus = runDetail.status === "success" ? "done" : runDetail.status === "failed" ? "failed" : "running";
  return LIFECYCLE_STEPS.map((s, i) => {
    const fromApi = runDetail.steps?.find((st) => st.step_key === s.key || st.label === s.label);
    let status: "done" | "running" | "waiting" | "failed" = "waiting";
    if (fromApi) {
      if (fromApi.status === "success" || fromApi.status === "done") status = "done";
      else if (fromApi.status === "failed") status = "failed";
      else if (fromApi.status === "running") status = "running";
      else if (fromApi.status === "cancelled") status = "failed";
      else status = "waiting";
    }
    return {
      step_key: s.key,
      label: s.label,
      status,
      duration_seconds: fromApi?.duration_seconds ?? null,
      message: fromApi?.message ?? null,
    };
  });
}

export default function PipelineControlPanel({ runId, onRunIdChange, running, runDetail }: PipelineControlPanelProps) {
  const [confirmMode, setConfirmMode] = useState<PipelineMode | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const queryClient = useQueryClient();
  const startMutation = useStartPipelineRun();
  const startPgMutation = useStartPgPipelineRun();

  const handleOpenModal = (mode: PipelineMode) => setConfirmMode(mode);
  const handleCloseModal = () => setConfirmMode(null);

  const runSingle = (mode: PipelineMode) => {
    startMutation.mutate(mode, {
      onSuccess: (data) => {
        onRunIdChange(data?.run_id ?? null);
      },
    });
  };

  const runPg = (mode: PgPipelineMode) => {
    startPgMutation.mutate(mode, {
      onSuccess: (data) => {
        onRunIdChange(data?.run_id ?? null);
      },
    });
  };

  const handleConfirmRun = () => {
    if (confirmMode) {
      runSingle(confirmMode);
      handleCloseModal();
    }
  };

  const steps = stepsFromRunDetail(runDetail);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <div className="font-semibold text-lg">Pipeline Control</div>
      <p className="text-sm text-slate-500 mt-1">Run & Monitor the Full Data Fabric</p>
      <p className="text-xs text-slate-500 mt-0.5">Orchestrate NUPRC source ingestion into Bronze → Silver → Warehouse, with automated diagrams and audit logs.</p>

      <div className="mt-4 flex flex-col sm:flex-row flex-wrap gap-3 items-stretch">
        <button
          type="button"
          onClick={() => runPg("incremental")}
          disabled={running || startPgMutation.isPending}
          className="w-full sm:w-auto px-5 py-3 rounded-xl bg-emerald-600 text-white font-semibold shadow-sm hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-2"
        >
          <span aria-hidden>▶</span> Run Full Pipeline
        </button>
        <button type="button" onClick={() => runPg("incremental")} disabled={running || startPgMutation.isPending} className="px-4 py-2 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-800 text-sm font-semibold hover:bg-emerald-100 disabled:opacity-50">Incremental Run</button>
        <button type="button" onClick={() => runPg("full_rebuild")} disabled={running || startPgMutation.isPending} className="px-4 py-2 rounded-xl border border-amber-200 bg-amber-50 text-amber-900 text-sm font-semibold hover:bg-amber-100 disabled:opacity-50">Full Rebuild</button>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 w-full sm:w-auto">
          <button
            type="button"
            onClick={() => runSingle("oil")}
            disabled={running}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-sm font-semibold disabled:opacity-50"
          >
            🛢 Oil Only
          </button>
          <button
            type="button"
            onClick={() => runSingle("gas")}
            disabled={running}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-sm font-semibold disabled:opacity-50"
          >
            🔥 Gas Only
          </button>
          <button
            type="button"
            onClick={() => runSingle("rig")}
            disabled={running}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-sm font-semibold disabled:opacity-50"
          >
            🏗 Rig Only
          </button>
          <button
            type="button"
            onClick={() => runSingle("concession")}
            disabled={running}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-sm font-semibold disabled:opacity-50"
          >
            📜 Concession Only
          </button>
        </div>
      </div>

      {confirmMode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-modal="true">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full mx-4">
            <h3 className="font-bold text-lg">
              {confirmMode === "full" ? "Run Full Pipeline?" : `Run ${confirmMode.charAt(0).toUpperCase() + confirmMode.slice(1)} Only?`}
            </h3>
            <p className="text-sm text-slate-600 mt-2">
              {confirmMode === "full" ? "Run the full pipeline (all sources)." : `Run only the ${confirmMode} source.`}
            </p>
            <div className="mt-6 flex gap-3 justify-end">
              <button
                type="button"
                onClick={handleCloseModal}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmRun}
                disabled={startMutation.isPending}
                className="px-4 py-2 rounded-xl bg-ldv-green text-white font-semibold disabled:opacity-50"
              >
                {startMutation.isPending ? "Starting…" : "Run"}
              </button>
            </div>
          </div>
        </div>
      )}

      {runId && (
        <>
          {running && (
            <div className="mt-3 flex justify-end">
              <button
                type="button"
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
                disabled={cancelling}
                className="px-4 py-2 rounded-xl bg-red-50 text-red-700 font-semibold text-sm hover:bg-red-100 disabled:opacity-50"
              >
                {cancelling ? "Cancelling…" : "Cancel Run"}
              </button>
            </div>
          )}
          <PipelineLifecycleTracker
            runId={runId}
            steps={steps}
            isLoading={running && steps.every((s) => s.status === "waiting")}
          />
        </>
      )}

      {startMutation.isError && (
        <p className="mt-3 text-sm text-red-600">{String(startMutation.error?.message ?? "Failed to start run")}</p>
      )}
    </div>
  );
}
