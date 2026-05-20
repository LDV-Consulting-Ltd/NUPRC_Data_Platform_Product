"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Shield, FileStack, GitBranch, Table2, AlertTriangle, Activity, BookOpen } from "lucide-react";
import { backendGet } from "@/lib/backend";
import MarketingShell from "@/components/marketing/MarketingShell";
import GovernanceCard from "@/components/marketing/GovernanceCard";
import FeatureCard from "@/components/marketing/FeatureCard";
import CTASection from "@/components/marketing/CTASection";

type GovernanceSummary = {
  ok: boolean;
  metadata: { file_registry_count: number; pipeline_runs: number; tables_with_data: number };
  lineage_coverage_pct: number;
  schema_drift_high_count: number;
  table_health: Array<{ schema: string; table: string; row_count: number }>;
  last_run?: { run_id: string; status: string; started_at: string } | null;
};

const SHOWCASE = [
  { title: "Metadata coverage", desc: "File registry, catalog, and table health across layers.", href: "/console/metadata", icon: BookOpen },
  { title: "Lineage", desc: "Source-to-product lineage explorer and coverage metrics.", href: "/lineage-explorer", icon: GitBranch },
  { title: "DQ & schema monitoring", desc: "Quality views and silver-layer schema drift detection.", href: "/console/schema-drift", icon: AlertTriangle },
  { title: "Auditability", desc: "Regulatory exports, snapshots, and audit bundles.", href: "/regulatory", icon: Shield },
  { title: "Run diagnostics", desc: "Per-run failure analysis and remediation guidance.", href: "/console/diagnostics", icon: Activity },
  { title: "Observability", desc: "Pipeline health, runs, and platform status dashboards.", href: "/console", icon: Activity },
];

export default function PublicGovernancePage() {
  const [data, setData] = useState<GovernanceSummary | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    backendGet<GovernanceSummary>("/v1/governance/summary")
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  return (
    <MarketingShell>
      <section className="w-full px-6 lg:px-14 py-16 lg:py-20">
        <p className="text-cyan-400 text-xs font-bold uppercase tracking-[0.2em]">Governance</p>
        <h1 className="mt-4 text-[clamp(2rem,4vw,3rem)] font-bold text-white max-w-4xl">
          Operational governance, lineage, and observability for upstream intelligence
        </h1>
        <p className="mt-5 text-slate-400 max-w-3xl text-lg">
          PetroCore embeds DAMA-aligned cataloging, lineage coverage, schema drift monitoring, and audit-ready exports —
          with live metrics from your connected PostgreSQL fabric.
        </p>
        <Link
          href="/console/governance"
          className="inline-block mt-6 px-5 py-2.5 rounded-xl border border-cyan-400/35 text-cyan-200 font-semibold hover:bg-cyan-500/10"
        >
          Open operational governance console →
        </Link>
      </section>

      {err && (
        <div className="mx-6 lg:mx-14 mb-6 p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-100 text-sm">
          Live metrics unavailable — start the backend to populate governance telemetry. ({err})
        </div>
      )}

      {data && (
        <section className="w-full px-6 lg:px-14 pb-12">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <GovernanceCard icon={FileStack} label="Files registered" value={data.metadata.file_registry_count} />
            <GovernanceCard icon={GitBranch} label="Pipeline runs" value={data.metadata.pipeline_runs} tone="gold" />
            <GovernanceCard icon={Table2} label="Tables with data" value={data.metadata.tables_with_data} tone="emerald" />
            <GovernanceCard
              icon={Shield}
              label="Lineage coverage"
              value={`${data.lineage_coverage_pct}%`}
              hint={`${data.schema_drift_high_count} high-severity drift signals`}
              tone={data.schema_drift_high_count > 0 ? "amber" : "cyan"}
            />
          </div>
          {data.last_run && (
            <motion.p className="mt-4 text-sm text-slate-400" animate={{ opacity: [0.7, 1, 0.7] }} transition={{ duration: 2.8, repeat: Infinity }}>
              Last ETL run: <span className="font-mono text-cyan-300">{data.last_run.run_id}</span> ·{" "}
              <span className="capitalize">{data.last_run.status}</span>
              {data.last_run.started_at && ` · ${new Date(data.last_run.started_at).toLocaleString()}`}
            </motion.p>
          )}
        </section>
      )}

      <section className="w-full px-6 lg:px-14 py-16 border-t border-cyan-500/10">
        <h2 className="text-xl font-bold text-white mb-8">Governance capabilities</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {SHOWCASE.map((s) => (
            <FeatureCard key={s.title} icon={s.icon} title={s.title} description={s.desc} href={s.href} />
          ))}
        </div>
      </section>

      {data && data.table_health.length > 0 && (
        <section className="w-full px-6 lg:px-14 py-12 border-t border-cyan-500/10">
          <h2 className="text-lg font-bold text-white mb-4">Table health (live)</h2>
          <div className="rounded-2xl border border-cyan-500/15 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 text-slate-400">
                  <th className="text-left p-3 font-semibold">Schema</th>
                  <th className="text-left p-3 font-semibold">Table</th>
                  <th className="text-right p-3 font-semibold">Rows</th>
                </tr>
              </thead>
              <tbody>
                {data.table_health.slice(0, 12).map((t) => (
                  <tr key={`${t.schema}.${t.table}`} className="border-t border-cyan-500/5">
                    <td className="p-3 font-mono text-cyan-200/80">{t.schema}</td>
                    <td className="p-3 font-mono">{t.table}</td>
                    <td className="p-3 text-right text-white font-semibold">{t.row_count.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <CTASection />
    </MarketingShell>
  );
}
