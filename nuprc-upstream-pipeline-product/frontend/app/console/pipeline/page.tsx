"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  Globe,
  Download,
  Database,
  Sparkles,
  Building2,
  Package,
  RefreshCw,
  Play,
  RotateCcw,
  Square,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import SectionHeader from "@/components/enterprise/SectionHeader";
import PipelineStepCard, { type StepUiStatus } from "@/components/enterprise/PipelineStepCard";
import { usePipelineRun, useStartPgPipelineRun } from "@/hooks/usePipelineRun";
import { cancelPipelineRun } from "@/lib/api";
import type { PipelineStep } from "@/lib/types";

const RUN_ID_STORAGE_KEY = "nuprc:lastRunId";

const STEP_META: Record<string, { title: string; description: string; icon: LucideIcon }> = {
  source_scraping: { title: "Source Scraping", description: "Discover NUPRC publication URLs", icon: Globe },
  file_acquisition: { title: "File Acquisition", description: "Download and register raw files", icon: Download },
  bronze_load: { title: "Bronze Load", description: "Land raw JSONB in bronze tables", icon: Database },
  silver_transformation: { title: "Silver Transform", description: "Standardize facts and dimensions", icon: Sparkles },
  warehouse_modeling: { title: "Warehouse Model", description: "Load dims and facts", icon: Building2 },
  data_product_generation: { title: "Data Products", description: "Catalog, diagrams, insights", icon: Package },
};

function toUiStatus(s: PipelineStep["status"]): StepUiStatus {
  if (s === "done") return "done";
  if (s === "failed" || s === "cancelled") return "failed";
  if (s === "running") return "running";
  return "waiting";
}

function PipelineControlInner() {
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const [runId, setRunId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const startPg = useStartPgPipelineRun();
  const { data: run, refetch, isFetching } = usePipelineRun(runId, { enabled: !!runId && hydrated });

  useEffect(() => {
    const fromUrl = searchParams.get("run_id");
    const fromStorage = typeof window !== "undefined" ? sessionStorage.getItem(RUN_ID_STORAGE_KEY) : null;
    setRunId(fromUrl || fromStorage || null);
    setHydrated(true);
  }, [searchParams]);

  useEffect(() => {
    if (!hydrated) return;
    if (runId) sessionStorage.setItem(RUN_ID_STORAGE_KEY, runId);
    else sessionStorage.removeItem(RUN_ID_STORAGE_KEY);
  }, [runId, hydrated]);

  const running = run?.status === "running";
  const steps = run?.steps ?? [];

  const handleStart = (mode: "incremental" | "full_rebuild") => {
    startPg.mutate(mode, {
      onSuccess: (d) => setRunId(d.run_id),
    });
  };

  const handleStop = async () => {
    if (!runId) return;
    setCancelling(true);
    try {
      await cancelPipelineRun(runId);
      await queryClient.invalidateQueries({ queryKey: ["pipeline", "run", runId] });
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div className="w-full space-y-6">
      <SectionHeader
        icon={Play}
        title="Pipeline Control"
        description="Orchestrate NUPRC source ingestion through bronze, silver, warehouse, and data products."
      />

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="font-bold text-[#0f2744] mb-1">Orchestration</h3>
        <p className="text-sm text-slate-500 mb-4">Start or stop the Postgres-first full pipeline.</p>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => handleStart("incremental")}
            disabled={running || startPg.isPending}
            className="px-5 py-2.5 rounded-xl bg-teal-600 text-white font-semibold hover:bg-teal-700 disabled:opacity-50 flex items-center gap-2"
          >
            <Play className="h-4 w-4" /> Run Incremental
          </button>
          <button
            type="button"
            onClick={() => handleStart("full_rebuild")}
            disabled={running || startPg.isPending}
            className="px-5 py-2.5 rounded-xl border border-amber-300 bg-amber-50 text-amber-900 font-semibold hover:bg-amber-100 disabled:opacity-50 flex items-center gap-2"
          >
            <RotateCcw className="h-4 w-4" /> Full Rebuild
          </button>
          {running && runId && (
            <button
              type="button"
              onClick={handleStop}
              disabled={cancelling}
              className="px-5 py-2.5 rounded-xl border border-red-200 bg-red-50 text-red-700 font-semibold hover:bg-red-100 disabled:opacity-50 flex items-center gap-2"
            >
              <Square className="h-4 w-4" /> Stop
            </button>
          )}
          <button
            type="button"
            onClick={() => refetch()}
            disabled={!runId || isFetching}
            className="px-5 py-2.5 rounded-xl border border-slate-200 bg-white font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>
        {startPg.isError && (
          <p className="mt-3 text-sm text-red-600">{String(startPg.error?.message ?? "Failed to start")}</p>
        )}
      </div>

      {runId && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="font-bold text-[#0f2744] mb-3">Current run</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-slate-500 text-xs uppercase font-semibold">Run ID</div>
              <div className="font-mono text-xs mt-1 truncate" title={runId}>
                {runId}
              </div>
            </div>
            <div>
              <div className="text-slate-500 text-xs uppercase font-semibold">Status</div>
              <div className="font-bold capitalize mt-1">{run?.status ?? "loading…"}</div>
            </div>
            <div>
              <div className="text-slate-500 text-xs uppercase font-semibold">Duration</div>
              <div className="font-bold mt-1">{run?.duration_seconds != null ? `${run.duration_seconds}s` : "—"}</div>
            </div>
            <div>
              <div className="text-slate-500 text-xs uppercase font-semibold">Rows loaded</div>
              <div className="font-bold mt-1">{(run?.rows_loaded ?? 0).toLocaleString()}</div>
            </div>
          </div>
          {run?.message && <p className="mt-3 text-sm text-red-600">{run.message}</p>}
        </div>
      )}

      {steps.length > 0 && (
        <section>
          <h3 className="font-bold text-[#0f2744] mb-3">Pipeline steps</h3>
          <div className="pipeline-flow-scroll w-full">
            {steps.map((step, i) => {
              const meta = STEP_META[step.step_key] ?? {
                title: step.label,
                description: step.step_key,
                icon: Package,
              };
              return (
                <PipelineStepCard
                  key={step.step_key}
                  index={i + 1}
                  title={meta.title}
                  description={meta.description}
                  icon={meta.icon}
                  status={toUiStatus(step.status)}
                  durationSeconds={step.duration_seconds}
                  rowsProcessed={step.metrics?.rows_written}
                  logMessage={step.message}
                />
              );
            })}
          </div>
        </section>
      )}

      {!runId && (
        <p className="text-slate-500 text-sm">Start an incremental or full rebuild run to see live step progress.</p>
      )}
    </div>
  );
}

export default function PipelineControlPage() {
  return (
    <Suspense fallback={<p className="text-slate-500 p-6">Loading pipeline control…</p>}>
      <PipelineControlInner />
    </Suspense>
  );
}
