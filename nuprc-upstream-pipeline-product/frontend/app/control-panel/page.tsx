"use client";

import { useState } from "react";
import { usePipelineRun, useRetryPipelineRun } from "@/hooks/usePipelineRun";
import { useSourcesHealth } from "@/hooks/useSourcesHealth";
import { NUPRC_REPORTS } from "@/lib/public-sources";
import { PageHeader } from "../components/console/ui";
import ExecutiveStatusBar from "../components/control-panel/ExecutiveStatusBar";
import ErrorBannerWithDiagnostics from "../components/control-panel/ErrorBannerWithDiagnostics";
import PipelineControlPanel from "../components/control-panel/PipelineControlPanel";
import FreshnessTiles from "../components/control-panel/FreshnessTiles";
import OperationsHub from "../components/control-panel/OperationsHub";

export default function ControlPanelPage() {
  const [runId, setRunId] = useState<string | null>(null);
  const { data: runDetail } = usePipelineRun(runId, { enabled: !!runId });
  const retryMutation = useRetryPipelineRun();
  const { data: sourcesHealth } = useSourcesHealth();

  const running = runDetail?.status === "running";
  const showRunError = runDetail?.status === "failed" || Boolean(runDetail?.message && runDetail.status !== "success");
  const hasSourceIssues = (sourcesHealth ?? []).some((source) => source.status === "down" || source.status === "degraded");

  const handleRetrySources = () => {
    retryMutation.mutate(undefined, {
      onSuccess: (data) => {
        if (data?.run_id) setRunId(data.run_id);
      },
    });
  };

  return (
    <>
      <PageHeader
        title="Control Panel"
        description="Source reports, ingestion attempts, data quality, and published datasets. The latest attempt is the platform run. The published snapshot is warehouse freshness."
        actions={
          <a className="pc-btn" href={NUPRC_REPORTS} target="_blank" rel="noopener noreferrer">
            NUPRC reports
          </a>
        }
      />
      <ExecutiveStatusBar />
      {hasSourceIssues && (
        <ErrorBannerWithDiagnostics
          runId={runId}
          userMessage="One or more NUPRC sources could not be reached. No data has been lost."
          onRetry={handleRetrySources}
          show
        />
      )}
      {showRunError && !hasSourceIssues && (
        <ErrorBannerWithDiagnostics
          runId={runId}
          userMessage={runDetail?.message ?? undefined}
          onRetry={handleRetrySources}
          show
        />
      )}
      <div className="pc-split pc-split-wide">
        <PipelineControlPanel runId={runId} onRunIdChange={setRunId} running={running} runDetail={runDetail ?? undefined} />
        <FreshnessTiles />
      </div>
      <OperationsHub />
    </>
  );
}
