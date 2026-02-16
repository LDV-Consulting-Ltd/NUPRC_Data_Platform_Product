"use client";

import { useEffect, useState, useRef } from "react";
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

export default function Diagrams() {
  const [data, setData] = useState<DiagramResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const mermaidRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    backendGet<DiagramResponse>("/diagrams/latest")
      .then(setData)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (data?.diagram?.diagram_content && mermaidRef.current) {
      const loadMermaid = async () => {
        try {
          // Load Mermaid from CDN if not already loaded
          if (typeof window !== 'undefined' && !(window as any).mermaid) {
            await new Promise((resolve, reject) => {
              const script = document.createElement('script');
              script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
              script.onload = resolve;
              script.onerror = reject;
              document.head.appendChild(script);
            });
          }

          // Initialize Mermaid
          if ((window as any).mermaid) {
            (window as any).mermaid.initialize({ 
              startOnLoad: false,
              theme: 'default',
              securityLevel: 'loose'
            });

            // Clear previous content
            if (mermaidRef.current) {
              mermaidRef.current.innerHTML = '';
              
              // Create a unique ID for this diagram
              const diagramId = `mermaid-diagram-${Date.now()}`;
              mermaidRef.current.id = diagramId;
              
              // Render the diagram
              (window as any).mermaid.render(diagramId, data.diagram.diagram_content)
                .then((result: { svg: string }) => {
                  if (mermaidRef.current) {
                    mermaidRef.current.innerHTML = result.svg;
                  }
                })
                .catch((error: Error) => {
                  console.error('Mermaid rendering error:', error);
                  if (mermaidRef.current) {
                    mermaidRef.current.innerHTML = `<div style="color: red;">Error rendering diagram: ${error.message}</div>`;
                  }
                });
            }
          }
        } catch (error) {
          console.error('Failed to load Mermaid:', error);
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = '<div style="color: red;">Failed to load Mermaid library</div>';
          }
        }
      };

      loadMermaid();
    }
  }, [data]);

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
            ref={mermaidRef}
            style={{
              padding: 24,
              border: "1px solid #eee",
              borderRadius: 8,
              backgroundColor: "#fff",
              overflow: "auto",
              minHeight: 400,
            }}
          >
            {!mermaidRef.current?.innerHTML && (
              <div style={{ textAlign: "center", color: "#666", padding: 40 }}>
                Rendering diagram...
              </div>
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
