"use client";

import type { PipelineStep } from "@/lib/types";
import { StatusPill, toneForStatus } from "../console/ui";

interface PipelineLifecycleTrackerProps {
  runId: string | null;
  steps: PipelineStep[];
  isLoading?: boolean;
}

function stepLabel(step: PipelineStep) {
  if (step.status === "done") {
    const rows = step.metrics?.rows_written;
    if (rows !== undefined && rows === 0) return "Done (skipped)";
    return "Done";
  }
  if (step.status === "running") return "Running";
  if (step.status === "failed") return "Failed";
  if (step.status === "cancelled") return "Cancelled";
  return "Waiting";
}

export default function PipelineLifecycleTracker({ runId, steps, isLoading }: PipelineLifecycleTrackerProps) {
  return (
    <div className="pc-card" style={{ marginTop: 14 }}>
      <div className="pc-card-h">
        <h2>Pipeline lifecycle</h2>
        <span className="pc-count">
          Run <span className="pc-num">{runId ? `${runId.slice(0, 8)}…` : "—"}</span>
        </span>
      </div>
      <div className="pc-card-b">
        <div className="pc-flow pc-flow-two">
          {isLoading
            ? Array.from({ length: 6 }).map((_, index) => <div key={index} className="pc-skel" />)
            : steps.map((step) => {
                const minutes = step.duration_seconds != null ? Math.floor(step.duration_seconds / 60) : null;
                const seconds = step.duration_seconds != null ? step.duration_seconds % 60 : null;
                const timing =
                  step.duration_seconds != null
                    ? `Duration ${minutes}m ${seconds}s`
                    : step.status === "waiting"
                      ? "Queued"
                      : step.status === "running"
                        ? "In progress"
                        : step.status === "cancelled"
                          ? "Cancelled"
                          : "";
                return (
                  <article key={step.step_key} className="pc-step">
                    <strong>{step.label}</strong>
                    <p>{timing}</p>
                    {step.message && <p>{step.message}</p>}
                    <StatusPill tone={toneForStatus(step.status === "done" ? "success" : step.status)}>{stepLabel(step)}</StatusPill>
                  </article>
                );
              })}
        </div>
      </div>
    </div>
  );
}
