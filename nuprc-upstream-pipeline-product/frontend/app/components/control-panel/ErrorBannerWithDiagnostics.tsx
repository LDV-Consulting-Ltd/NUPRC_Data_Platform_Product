"use client";

import { useState } from "react";
import { useRunDiagnostics } from "@/hooks/useRunDiagnostics";

interface ErrorBannerWithDiagnosticsProps {
  runId: string | null;
  userMessage?: string;
  onRetry?: () => void;
  show: boolean;
}

export default function ErrorBannerWithDiagnostics({ runId, userMessage, onRetry, show }: ErrorBannerWithDiagnosticsProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const { data: diagnostics, isLoading } = useRunDiagnostics(runId, detailsOpen);

  if (!show) return null;

  return (
    <section className="pc-state pc-state-error" role="alert">
      <h2>Source connection issue</h2>
      <div className="pc-state-body">
        <p>{userMessage ?? "One or more NUPRC sources could not be reached. No data has been lost."}</p>
        <div className="pc-actions">
          <button type="button" className="pc-btn pc-btn-primary" onClick={onRetry}>
            Retry failed sources
          </button>
          <button type="button" className="pc-btn" onClick={() => setDetailsOpen((open) => !open)}>
            {detailsOpen ? "Hide details" : "View details"}
          </button>
        </div>
      </div>
      {detailsOpen && (
        <div className="pc-state-body">
          {isLoading && <p>Loading diagnostics…</p>}
          {!isLoading && !diagnostics && <p>No diagnostics available.</p>}
          {diagnostics && (
            <dl className="pc-detail-list">
              <div>
                <dt>Failing source</dt>
                <dd>{diagnostics.failing_source ?? "—"}</dd>
              </div>
              <div>
                <dt>Error</dt>
                <dd>{diagnostics.error_message ?? diagnostics.error_type ?? "—"}</dd>
              </div>
              <div>
                <dt>Last successful sync</dt>
                <dd>{diagnostics.last_successful_sync ?? "—"}</dd>
              </div>
            </dl>
          )}
          {diagnostics?.suggestion && <p>{diagnostics.suggestion}</p>}
        </div>
      )}
    </section>
  );
}
