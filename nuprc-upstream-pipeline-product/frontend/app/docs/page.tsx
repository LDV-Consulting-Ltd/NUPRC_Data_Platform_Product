"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import MarketingShell from "@/components/marketing/MarketingShell";
import FeatureCard from "@/components/marketing/FeatureCard";
import DataFabricFlow from "@/components/marketing/DataFabricFlow";
import { API_GROUPS, FEATURES, JSON_EXAMPLES, PIPELINE_CAPABILITIES } from "@/lib/productDocs";
import {
  Search,
  Download,
  ScanText,
  Layers,
  Sparkles,
  Warehouse,
  Shield,
  BookOpen,
  GitBranch,
  AlertTriangle,
  Stethoscope,
  Radio,
  Code2,
  Workflow,
} from "lucide-react";

const CAP_ICONS: Record<string, typeof Search> = {
  "Source Discovery": Search,
  "File Acquisition": Download,
  "OCR & Extraction": ScanText,
  "Bronze Layer": Layers,
  "Silver Standardization": Sparkles,
  "Gold Warehouse": Warehouse,
  "Governance Engine": Shield,
  "Metadata Registry": BookOpen,
  "Data Lineage": GitBranch,
  "Schema Drift Detection": AlertTriangle,
  Diagnostics: Stethoscope,
  Monitoring: Radio,
  APIs: Code2,
  "Pipeline Orchestration": Workflow,
};

const PROXY_PREFIX = "/api/backend";
const BACKEND_DOCS = "http://127.0.0.1:8000/docs";

function MethodBadge({ method }: { method: "GET" | "POST" }) {
  const cls =
    method === "GET" ? "bg-cyan-500/15 text-cyan-300" : "bg-violet-500/15 text-violet-300";
  return <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-bold ${cls}`}>{method}</span>;
}

export default function DocsPage() {
  return (
    <MarketingShell>
      <section className="w-full px-6 lg:px-14 py-16 lg:py-20">
        <p className="text-cyan-400 text-xs font-bold uppercase tracking-[0.2em]">
          Product Features &amp; API Docs
        </p>
        <h1 className="mt-4 text-[clamp(1.75rem,3.5vw,2.75rem)] font-bold text-white max-w-4xl">
          Pipeline capabilities, REST APIs, and architecture reference
        </h1>
        <p className="mt-4 text-slate-400 max-w-3xl">
          PetroCore exposes a full upstream data fabric from NUPRC source discovery through governed warehouse
          products.
        </p>
        <motion.div className="mt-6 flex flex-wrap gap-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <a
            href={BACKEND_DOCS}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-lg bg-cyan-500 text-[#050d1a] text-sm font-bold"
          >
            Open Swagger UI
          </a>
          <Link
            href="/showcase/diagrams"
            className="px-4 py-2 rounded-lg border border-cyan-500/30 text-cyan-200 text-sm font-semibold"
          >
            ETL Diagrams
          </Link>
          <Link
            href="/test-connection"
            className="px-4 py-2 rounded-lg border border-cyan-500/30 text-cyan-200 text-sm font-semibold"
          >
            Test connection
          </Link>
        </motion.div>
      </section>

      <DataFabricFlow />

      <section className="w-full px-6 lg:px-14 py-16">
        <h2 className="text-xl font-bold text-white mb-6">Pipeline capabilities</h2>
        <motion.div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {PIPELINE_CAPABILITIES.map((c) => (
            <FeatureCard
              key={c.name}
              icon={CAP_ICONS[c.name] ?? Code2}
              title={c.name}
              description={c.description}
              href={c.href}
            />
          ))}
        </motion.div>
      </section>

      <section className="w-full px-6 lg:px-14 py-16 border-t border-cyan-500/10">
        <h2 className="text-xl font-bold text-white mb-6">JSON examples</h2>
        <motion.div
          className="grid gap-4 lg:grid-cols-3"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
        >
          {JSON_EXAMPLES.map((ex) => (
            <motion.div
              key={ex.title}
              variants={{ hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } }}
              className="rounded-2xl border border-cyan-500/15 bg-white/5 overflow-hidden"
            >
              <motion.div className="px-4 py-3 border-b border-cyan-500/10">
                <p className="font-semibold text-white text-sm">{ex.title}</p>
                <code className="text-xs text-cyan-400/80">{ex.path}</code>
              </motion.div>
              <pre className="p-4 text-xs text-slate-300 overflow-x-auto font-mono">{ex.body}</pre>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section className="w-full px-6 lg:px-14 py-16 border-t border-cyan-500/10">
        <h2 className="text-xl font-bold text-white mb-6">Console modules</h2>
        <motion.div className="space-y-8">
          {FEATURES.map((group) => (
            <motion.div key={group.section}>
              <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">{group.section}</h3>
              <motion.div className="grid gap-3 md:grid-cols-2">
                {group.items.map((f) => (
                  <FeatureCard
                    key={f.href}
                    title={f.name}
                    description={f.description}
                    href={f.href}
                    tag={f.tag}
                  />
                ))}
              </motion.div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section className="w-full px-6 lg:px-14 py-16 border-t border-cyan-500/10 pb-20">
        <h2 className="text-xl font-bold text-white mb-4">REST API reference</h2>
        <p className="text-sm text-slate-400 mb-6">
          Browser proxy: <code className="text-cyan-300">{PROXY_PREFIX}</code>
        </p>
        <motion.div className="space-y-6">
          {API_GROUPS.map((group) => (
            <motion.div
              key={group.title}
              className="rounded-2xl border border-cyan-500/15 bg-white/5 overflow-hidden"
            >
              <motion.div className="px-4 py-3 border-b border-cyan-500/10 font-semibold text-cyan-100">
                {group.title}
              </motion.div>
              <ul className="divide-y divide-cyan-500/5">
                {group.endpoints.map((ep) => (
                  <li key={ep.path + ep.method} className="px-4 py-3 flex gap-4">
                    <MethodBadge method={ep.method} />
                    <motion.div className="min-w-0 flex-1">
                      <code className="text-sm font-mono text-cyan-100 break-all">{ep.path}</code>
                      <p className="text-sm text-slate-400 mt-0.5">{ep.summary}</p>
                    </motion.div>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </motion.div>
      </section>
    </MarketingShell>
  );
}
