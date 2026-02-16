"use client";

import { useState } from "react";
import { backendGet, backendPost } from "@/lib/backend";

export default function TestConnection() {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testConnection = async () => {
    setLoading(true);
    setResults(null);

    const tests: any = {};

    // Test 1: Direct backend health check
    try {
      const response = await fetch("http://127.0.0.1:8001/health/summary");
      const data = await response.json();
      tests.directBackend = { success: true, data };
    } catch (e: any) {
      tests.directBackend = { success: false, error: e.message };
    }

    // Test 2: Through Next.js rewrite
    try {
      const data = await backendGet("/health/summary");
      tests.rewritePath = { success: true, data };
    } catch (e: any) {
      tests.rewritePath = { success: false, error: e.message };
    }

    // Test 3: Pipeline test endpoint (v1)
    try {
      const data = await backendGet("/v1/pipeline/test");
      tests.pipelineTest = { success: true, data };
    } catch (e: any) {
      tests.pipelineTest = { success: false, error: e.message };
    }

    // Test 4: Pipeline status (v1)
    try {
      const data = await backendGet("/v1/pipeline/status");
      tests.pipelineStatus = { success: true, data };
    } catch (e: any) {
      tests.pipelineStatus = { success: false, error: e.message };
    }

    setResults(tests);
    setLoading(false);
  };

  return (
    <div style={{ padding: 24, maxWidth: 800, margin: "0 auto" }}>
      <h1>Backend Connection Test</h1>
      <button
        onClick={testConnection}
        disabled={loading}
        style={{
          padding: "12px 24px",
          fontSize: 16,
          backgroundColor: "#0070f3",
          color: "white",
          border: "none",
          borderRadius: 6,
          cursor: loading ? "not-allowed" : "pointer",
          marginBottom: 24,
        }}
      >
        {loading ? "Testing..." : "Test Connection"}
      </button>

      {results && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {Object.entries(results).map(([key, value]: [string, any]) => (
            <div
              key={key}
              style={{
                padding: 16,
                border: `2px solid ${value.success ? "#00ff00" : "#ff0000"}`,
                borderRadius: 8,
                backgroundColor: value.success ? "#f0fff0" : "#fff0f0",
              }}
            >
              <h3>{key}</h3>
              {value.success ? (
                <pre style={{ overflow: "auto", fontSize: 12 }}>
                  {JSON.stringify(value.data, null, 2)}
                </pre>
              ) : (
                <div style={{ color: "red" }}>Error: {value.error}</div>
              )}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 24, padding: 16, backgroundColor: "#f5f5f5", borderRadius: 8 }}>
        <h3>Configuration Info:</h3>
        <ul>
          <li>Backend URL (from config): http://127.0.0.1:8001</li>
          <li>Frontend rewrite path: /api/backend/* → http://127.0.0.1:8001/*</li>
          <li>Current page URL: {typeof window !== "undefined" ? window.location.href : "N/A"}</li>
        </ul>
      </div>
    </div>
  );
}
