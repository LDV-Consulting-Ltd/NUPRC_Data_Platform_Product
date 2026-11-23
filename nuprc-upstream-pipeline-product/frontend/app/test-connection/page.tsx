"use client";

import { useState } from "react";
import { backendGet } from "@/lib/backend";
import { PageHeader, StateBlock, StatusPill } from "../components/console/ui";

type TestResult = { success: boolean; data?: unknown; error?: string };

export default function TestConnection() {
  const [results, setResults] = useState<Record<string, TestResult> | null>(null);
  const [loading, setLoading] = useState(false);

  const testConnection = async () => {
    setLoading(true);
    setResults(null);
    const tests: Record<string, TestResult> = {};

    try {
      const response = await fetch("/api/backend/health/summary");
      const data = await response.json();
      tests.publicPath = { success: response.ok, data };
    } catch (error) {
      tests.publicPath = { success: false, error: error instanceof Error ? error.message : "Request failed" };
    }

    try {
      tests.rewritePath = { success: true, data: await backendGet("/health/summary") };
    } catch (error) {
      tests.rewritePath = { success: false, error: error instanceof Error ? error.message : "Request failed" };
    }

    try {
      tests.pipelineTest = { success: true, data: await backendGet("/v1/pipeline/test") };
    } catch (error) {
      tests.pipelineTest = { success: false, error: error instanceof Error ? error.message : "Request failed" };
    }

    try {
      tests.pipelineStatus = { success: true, data: await backendGet("/v1/pipeline/status") };
    } catch (error) {
      tests.pipelineStatus = { success: false, error: error instanceof Error ? error.message : "Request failed" };
    }

    setResults(tests);
    setLoading(false);
  };

  return (
    <>
      <PageHeader
        title="Connection test"
        description="Checks the local API proxy. This page does not start a pipeline run. It is not part of the production navigation."
        actions={
          <button type="button" className="pc-btn pc-btn-primary" onClick={testConnection} disabled={loading}>
            {loading ? "Testing…" : "Test connection"}
          </button>
        }
      />
      {loading && (
        <StateBlock tone="loading" title="Checking the API">
          Health and pipeline test endpoints are being read. No ingestion run is started.
        </StateBlock>
      )}
      {results &&
        Object.entries(results).map(([key, value]) => (
          <section key={key} className={value.success ? "pc-state pc-state-awaiting" : "pc-state pc-state-error"}>
            <h2>
              {key} <StatusPill tone={value.success ? "ok" : "danger"}>{value.success ? "Reached" : "Failed"}</StatusPill>
            </h2>
            <div className="pc-state-body">
              {value.success ? <pre>{JSON.stringify(value.data, null, 2)}</pre> : <p>{value.error}</p>}
            </div>
          </section>
        ))}
      <StateBlock tone="partial" title="Where this page looks">
        The console calls /api/backend on this site, and that route forwards to the backend service. The same API is also public at /backend, with the prefix removed before FastAPI sees the path.
      </StateBlock>
    </>
  );
}
