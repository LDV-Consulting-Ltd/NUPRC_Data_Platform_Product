"use client";

import { useEffect, useState } from "react";
import { backendGet } from "@/lib/backend";

type DiagramPayload = {
  id?: number;
  diagram_type: string;
  diagram_content: string;
  created_at: string | null;
};

type DiagramResponse = {
  ok: boolean;
  status?: "available" | "empty" | "unavailable";
  message?: string | null;
  diagram: DiagramPayload | null;
  fallback_diagram?: DiagramPayload | null;
  source?: string;
  is_fallback?: boolean;
  suggested_action?: string;
};

type MermaidApi = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, code: string) => Promise<{ svg: string }>;
};

declare global {
  interface Window {
    mermaid?: MermaidApi;
  }
}

let mermaidLoadPromise: Promise<void> | null = null;

function loadMermaidLibrary(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (window.mermaid) return Promise.resolve();
  if (mermaidLoadPromise) return mermaidLoadPromise;

  mermaidLoadPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
    script.async = true;
    script.onload = () => {
      window.mermaid?.initialize({
        startOnLoad: false,
        theme: "default",
        securityLevel: "loose",
      });
      resolve();
    };
    script.onerror = () => reject(new Error("Failed to load Mermaid library"));
    document.head.appendChild(script);
  });

  return mermaidLoadPromise;
}

export default function Diagrams() {
  const [data, setData] = useState<DiagramResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [svgHtml, setSvgHtml] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);

  const activeDiagram = data?.diagram ?? data?.fallback_diagram ?? null;
  const isFallback = !data?.diagram && !!data?.fallback_diagram;

  useEffect(() => {
    backendGet<DiagramResponse>("/diagrams/latest")
      .then(setData)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const content = activeDiagram?.diagram_content;
    if (!content) {
      setSvgHtml(null);
      setRenderError(null);
      setRendering(false);
      return;
    }

    let cancelled = false;
    setRendering(true);
    setRenderError(null);
    setSvgHtml(null);

    (async () => {
      try {
        await loadMermaidLibrary();
        if (cancelled || !window.mermaid) return;

        const diagramId = `mermaid-diagram-${Date.now()}`;
        const result = await window.mermaid.render(diagramId, content);
        if (!cancelled) {
          setSvgHtml(result.svg);
        }
      } catch (error) {
        if (!cancelled) {
          setRenderError(error instanceof Error ? error.message : String(error));
        }
      } finally {
        if (!cancelled) {
          setRendering(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [activeDiagram?.diagram_content]);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Data Model and ETL Diagram</h2>

      {loading && <div>Loading diagram...</div>}

      {err && (
        <div style={{ padding: 12, border: "1px solid #f00", borderRadius: 8, marginBottom: 16 }}>
          Error: {err}
        </div>
      )}

      {data && data.status && data.status !== "available" && (
        <div
          style={{
            padding: 12,
            marginBottom: 16,
            border: "1px solid #eee",
            borderRadius: 8,
            backgroundColor: "#f9f9f9",
            fontSize: 14,
            color: "#444",
          }}
        >
          {data.message}
          {data.suggested_action && (
            <div style={{ marginTop: 8, fontSize: 12, color: "#666" }}>{data.suggested_action}</div>
          )}
        </div>
      )}

      {activeDiagram && (
        <>
          <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#f5f5f5", borderRadius: 8 }}>
            <div style={{ fontSize: 12, color: "#666" }}>
              Diagram Type: {activeDiagram.diagram_type}
              {isFallback && (
                <>
                  <br />
                  <strong>Fallback structural diagram</strong> (source: {data?.source ?? "generated_fallback"})
                </>
              )}
              {activeDiagram.created_at && (
                <>
                  <br />
                  Generated: {new Date(activeDiagram.created_at).toLocaleString()}
                </>
              )}
            </div>
          </div>

          <div
            style={{
              padding: 24,
              border: "1px solid #eee",
              borderRadius: 8,
              backgroundColor: "#fff",
              overflow: "auto",
              minHeight: 400,
            }}
          >
            {rendering && (
              <div style={{ textAlign: "center", color: "#666", padding: 40 }}>Rendering diagram...</div>
            )}
            {renderError && (
              <div style={{ color: "#c00", padding: 16 }}>
                Error rendering diagram: {renderError}
              </div>
            )}
            {svgHtml && !rendering && (
              <div
                key={activeDiagram.diagram_content.slice(0, 40)}
                dangerouslySetInnerHTML={{ __html: svgHtml }}
              />
            )}
          </div>

          <div style={{ marginTop: 16, padding: 12, backgroundColor: "#f9f9f9", borderRadius: 8 }}>
            <details>
              <summary style={{ cursor: "pointer", fontWeight: 600 }}>View Mermaid Source Code</summary>
              <pre
                style={{
                  marginTop: 12,
                  padding: 12,
                  backgroundColor: "#fff",
                  border: "1px solid #ddd",
                  borderRadius: 4,
                  overflow: "auto",
                  fontSize: 12,
                }}
              >
                {activeDiagram.diagram_content}
              </pre>
            </details>
          </div>
        </>
      )}

      {!loading && !err && !activeDiagram && (
        <div style={{ padding: 16, color: "#666" }}>No diagram content available.</div>
      )}
    </div>
  );
}
