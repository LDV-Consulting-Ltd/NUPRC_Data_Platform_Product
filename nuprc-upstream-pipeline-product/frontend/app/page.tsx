"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Shield, Database } from "lucide-react";
import { backendGet } from "@/lib/backend";
import { fetchPlatformStatus } from "@/lib/api";
import { useStartPgPipelineRun } from "@/hooks/usePipelineRun";
import type { SourceHealthItem } from "@/lib/types";
import MarketingShell from "@/components/marketing/MarketingShell";
import PetroCoreHero from "@/components/marketing/PetroCoreHero";
import DataFabricFlow from "@/components/marketing/DataFabricFlow";
import FeatureCard from "@/components/marketing/FeatureCard";
import CTASection from "@/components/marketing/CTASection";
import GovernanceCard from "@/components/marketing/GovernanceCard";

type SourcesResponse = { ok: boolean; sources: SourceHealthItem[] };

export default function LandingPage() {
  const [sources, setSources] = useState<SourceHealthItem[]>([]);
  const [platform, setPlatform] = useState<Awaited<ReturnType<typeof fetchPlatformStatus>> | null>(null);
  const startPg = useStartPgPipelineRun();

  useEffect(() => {
    backendGet<SourcesResponse>("/v1/pipeline/sources/health")
      .then((d) => setSources(d.sources || []))
      .catch(() => {});
    fetchPlatformStatus().then(setPlatform).catch(() => {});
  }, []);

  return (
    <MarketingShell>
      <PetroCoreHero onRunPipeline={() => startPg.mutate("incremental")} runPending={startPg.isPending} />
      <DataFabricFlow />

      <section className="w-full px-6 lg:px-14 py-16 border-t border-cyan-500/10">
        <p className="text-cyan-400 text-xs font-bold uppercase tracking-widest mb-3">Live telemetry</p>
        <h2 className="text-2xl font-bold text-white">Operational intelligence at a glance</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <GovernanceCard
            icon={Activity}
            label="System health"
            value={platform?.system_health ?? "—"}
            hint={platform?.last_run ? `Last run ${new Date(platform.last_run.at).toLocaleString()}` : "Awaiting first successful run"}
          />
          <GovernanceCard icon={Database} label="Records today" value={platform?.records_today?.toLocaleString() ?? "—"} tone="gold" />
          <GovernanceCard
            icon={Shield}
            label="Sources monitored"
            value={sources.length || "—"}
            hint={sources.length ? `${sources.filter((s) => s.status === "fresh" || s.status === "healthy").length} healthy` : "Loading source health"}
          />
          <GovernanceCard
            icon={Activity}
            label="Pipeline duration"
            value={platform?.last_run ? `${platform.last_run.duration_seconds}s` : "—"}
            tone="emerald"
          />
        </div>
      </section>

      <section className="w-full px-6 lg:px-14 py-16">
        <h2 className="text-2xl font-bold text-white mb-8">Source coverage</h2>
        <motion.div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 w-full"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
        >
          {sources.length === 0 ? (
            <p className="text-slate-500 col-span-full">Loading source health…</p>
          ) : (
            sources.map((s) => (
              <motion.div key={s.source_key} variants={{ hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } }}>
                <FeatureCard
                  title={s.label}
                  description={`Status: ${s.status} · Freshness ${s.freshness_score}%${s.row_count != null ? ` · ${s.row_count.toLocaleString()} rows` : ""}`}
                  href="/source-health"
                />
              </motion.div>
            ))
          )}
        </motion.div>
      </section>

      <section className="w-full px-6 lg:px-14 py-16 border-t border-cyan-500/10">
        <h2 className="text-2xl font-bold text-white mb-8">Enterprise capabilities</h2>
        <motion.div
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
        >
          {[
            { title: "Governance automation", desc: "Metadata registry, lineage, schema drift, and audit exports.", href: "/governance" },
            { title: "Pipeline orchestration", desc: "Incremental and full-rebuild runs with live diagnostics.", href: "/console/pipeline" },
            { title: "Regulatory intelligence", desc: "Oil, gas, rig, and concession datasets in one fabric.", href: "/solutions" },
          ].map((c) => (
            <motion.div key={c.title} variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}>
              <FeatureCard title={c.title} description={c.desc} href={c.href} />
            </motion.div>
          ))}
        </motion.div>
      </section>

      <CTASection onRunPipeline={() => startPg.mutate("incremental")} runPending={startPg.isPending} />
    </MarketingShell>
  );
}
