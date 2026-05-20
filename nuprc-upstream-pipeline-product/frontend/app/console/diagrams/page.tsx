"use client";

import { useEffect, useState } from "react";
import { Network } from "lucide-react";
import { backendGet } from "@/lib/backend";
import SectionHeader from "@/components/enterprise/SectionHeader";

type DiagramLatest = {
  ok: boolean;
  conceptual?: { mermaid?: string; created_at?: string | null };
  logical?: { mermaid?: string; created_at?: string | null };
  physical?: { mermaid?: string; created_at?: string | null };
  lineage?: { mermaid?: string; created_at?: string | null };
  diagram?: { diagram_type?: string; diagram_content?: string };
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
  if (typeof window === "undefined") return Promise.reject(new Error("Browser only"));
  if (window.mermaid) return Promise.resolve(window.mermaid);
  return new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-mermaid="true"]');
    if (existing) {
      existing.addEventListener("load", () => (window.mermaid ? resolve(window.mermaid) : reject()));
      return;
    }
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
    script.async = true;
    script.dataset.mermaid = "true";
    script.onload = () => (window.mermaid ? resolve(window.mermaid) : reject(new Error("Mermaid load failed")));
    script.onerror = () => reject(new Error("Mermaid script error"));
    document.head.appendChild(script);
  });
}

const TABS = ["lineage", "conceptual", "logical", "physical"] as const;

export default function DiagramsPage() {
  const [data, setData] = useState<DiagramLatest | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]>("lineage");
  const [svgMarkup, setSvgMarkup] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);

  useEffect(() => {
    backendGet<DiagramLatest>("/diagrams/latest")
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  const content =
    tab === "lineage"
      ? data?.lineage?.mermaid ?? data?.diagram?.diagram_content
      : data?.[tab]?.mermaid;

  useEffect(() => {
    if (!content) {
      setSvgMarkup(null);
      return;
    }
    let cancelled = false;
    (async () => {
      setRendering(true);
      setRenderError(null);
      setSvgMarkup(null);
      try {
        const mermaid = await loadMermaidScript();
        if (cancelled) return;
        mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "loose" });
        const { svg } = await mermaid.render(`diagram-${tab}-${Date.now()}`, content);
        if (!cancelled) setSvgMarkup(svg);
      } catch (e) {
        if (!cancelled) setRenderError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setRendering(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [content, tab]);

  return (
    <div className="w-full space-y-6">
      <SectionHeader
        icon={Network}
        title="Architecture Diagrams"
        description="Mermaid diagrams generated after pipeline runs (conceptual, logical, physical, lineage)."
      />
      {err && <p className="text-red-600 text-sm">{err}</p>}
      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-xl text-sm font-semibold capitalize ${
              tab === t ? "bg-[#0f2744] text-teal-300" : "bg-white border border-slate-200 text-slate-700"
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-6 min-h-[400px] overflow-auto w-full">
        {rendering && <p className="text-slate-500 text-center py-12">Rendering diagram…</p>}
        {renderError && <p className="text-red-600">{renderError}</p>}
        {svgMarkup && !rendering && (
          <div className="mermaid-diagram" dangerouslySetInnerHTML={{ __html: svgMarkup }} />
        )}
        {!content && !rendering && !err && (
          <p className="text-slate-500 text-center py-12">Run the pipeline to generate diagrams.</p>
        )}
      </div>
      {content && (
        <details className="rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer font-semibold text-sm text-[#0f2744]">Mermaid source</summary>
          <pre className="mt-3 text-xs overflow-auto p-3 bg-slate-50 rounded-lg">{content}</pre>
        </details>
      )}
    </div>
  );
}
