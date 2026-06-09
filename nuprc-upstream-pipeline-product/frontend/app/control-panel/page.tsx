"use client";

import { useState } from "react";
import V2Header from "../components/V2Header";
import ExecutiveStatusBar from "../components/control-panel/ExecutiveStatusBar";
import ErrorBannerWithDiagnostics from "../components/control-panel/ErrorBannerWithDiagnostics";
import PipelineControlPanel from "../components/control-panel/PipelineControlPanel";
import FreshnessTiles from "../components/control-panel/FreshnessTiles";
import OperationsHub from "../components/control-panel/OperationsHub";
import { usePipelineRun, useRetryPipelineRun } from "@/hooks/usePipelineRun";
import { useSourcesHealth } from "@/hooks/useSourcesHealth";

export default function ControlPanelPage() {
  const [runId, setRunId] = useState<string | null>(null);
  const { data: runDetail } = usePipelineRun(runId, { enabled: !!runId });
  const retryMutation = useRetryPipelineRun();
  const { data: sourcesHealth } = useSourcesHealth();

  const running = runDetail?.status === "running";
  const showRunError = runDetail?.status === "failed" || (runDetail?.message && runDetail.status !== "success");
  const hasSourceDown = (sourcesHealth ?? []).some((s) => s.status === "down");
  const hasSourceDegraded = (sourcesHealth ?? []).some((s) => s.status === "degraded");

  const handleRetrySources = () => {
    retryMutation.mutate(undefined, {
      onSuccess: (data) => {
        if (data?.run_id) setRunId(data.run_id);
      },
    });
  };

  return (
    <>
      <V2Header
        title="Control Panel"
        subtitle="Automated pipeline: Sources → Bronze → Silver → Warehouse → Data Products → Insights"
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <ExecutiveStatusBar />

        {hasSourceDown && (
          <ErrorBannerWithDiagnostics
            runId={runId}
            userMessage="One or more NUPRC sources could not be reached or have no data."
            onRetry={handleRetrySources}
            show={true}
            variant="critical"
          />
        )}

        {!hasSourceDown && hasSourceDegraded && (
          <ErrorBannerWithDiagnostics
            runId={runId}
            userMessage="Some sources have lower freshness or row-count scores, but data is available."
            show={true}
            variant="advisory"
          />
        )}

        {showRunError && !hasSourceDown && !hasSourceDegraded && (
          <ErrorBannerWithDiagnostics
            runId={runId}
            userMessage={runDetail?.message ?? undefined}
            onRetry={handleRetrySources}
            show={true}
          />
        )}

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <PipelineControlPanel runId={runId} onRunIdChange={setRunId} running={running} runDetail={runDetail ?? undefined} />
          <FreshnessTiles />
        </section>

        <OperationsHub />
      </div>
    </>
  );
}
