"use client";

import { useEffect, useState } from "react";
import { backendGet } from "@/lib/backend";

type DiagramResponse = {
  ok: boolean;
  diagram: {
    id: number;
    diagram_type: string;
    diagram_content: string;
    created_at: string;
  };
};

type MermaidAPI = {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, definition: string) => Promise<{ svg: string }>;
};

declare global {
  interface Window {
    mermaid?: MermaidAPI;
  }
}

function loadMermaidScript(): Promise<MermaidAPI> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Mermaid requires a browser"));
  }
  if (window.mermaid) {
    return Promise.resolve(window.mermaid);
  }
  return new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-mermaid="true"]');
    if (existing) {
      existing.addEventListener("load", () => {
        if (window.mermaid) resolve(window.mermaid);
        else reject(new Error("Mermaid failed to load"));
      });
      existing.addEventListener("error", () => reject(new Error("Mermaid script error")));
      return;
    }
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
    script.async = true;
    script.dataset.mermaid = "true";
    script.onload = () => {
      if (window.mermaid) resolve(window.mermaid);
      else reject(new Error("Mermaid failed to load"));
    };
    script.onerror = () => reject(new Error("Failed to load Mermaid library"));
    document.head.appendChild(script);
  });
}

export default function Diagrams() {
  const [data, setData] = useState<DiagramResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [svgMarkup, setSvgMarkup] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);

  useEffect(() => {
    backendGet<DiagramResponse>("/diagrams/latest")
      .then(setData)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const content = data?.diagram?.diagram_content;
    if (!content) {
      setSvgMarkup(null);
      setRenderError(null);
      return;
    }

    let cancelled = false;

    const renderDiagram = async () => {
      setRendering(true);
      setRenderError(null);
      setSvgMarkup(null);

      try {
        const mermaid = await loadMermaidScript();
        if (cancelled) return;

        mermaid.initialize({
          startOnLoad: false,
          theme: "default",
          securityLevel: "loose",
        });

        const renderId = `mermaid-diagram-${Date.now()}`;
        const { svg } = await mermaid.render(renderId, content);
        if (!cancelled) {
          setSvgMarkup(svg);
        }
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : String(error);
          setRenderError(message);
        }
      } finally {
        if (!cancelled) {
          setRendering(false);
        }
      }
    };

    renderDiagram();
    return () => {
      cancelled = true;
    };
  }, [data?.diagram?.diagram_content]);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Data Model and ETL Diagram</h2>

      {loading && <div>Loading diagram...</div>}

      {err && (
        <div style={{ padding: 12, border: "1px solid #f00", borderRadius: 8, marginBottom: 16 }}>
          Error: {err}
          <br />
          <small>Run the pipeline first to generate diagrams.</small>
        </div>
      )}

      {data?.diagram && (
        <>
          <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#f5f5f5", borderRadius: 8 }}>
            <div style={{ fontSize: 12, color: "#666" }}>
              Diagram Type: {data.diagram.diagram_type}
              <br />
              Generated: {new Date(data.diagram.created_at).toLocaleString()}
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
              <div style={{ color: "red", padding: 16 }}>Error rendering diagram: {renderError}</div>
            )}
            {svgMarkup && !rendering && (
              <div
                className="mermaid-diagram"
                dangerouslySetInnerHTML={{ __html: svgMarkup }}
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
                {data.diagram.diagram_content}
              </pre>
            </details>
          </div>
        </>
      )}
    </div>
  );
}
