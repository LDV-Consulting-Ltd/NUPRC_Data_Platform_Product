"use client";

import { Database, Search, Sparkles, Warehouse, LineChart } from "lucide-react";
import PipelineStage from "./PipelineStage";

const STAGES = [
  {
    icon: Search,
    label: "NUPRC Sources",
    subtitle: "Discover & Collect",
    description: "Publication discovery, acquisition, and source health telemetry.",
  },
  {
    icon: Database,
    label: "Bronze",
    subtitle: "Raw & Immutable",
    description: "Immutable raw landing with file registry and provenance.",
  },
  {
    icon: Sparkles,
    label: "Silver",
    subtitle: "Clean & Standardized",
    description: "Conformed dimensions and facts with fuzzy column matching.",
  },
  {
    icon: Warehouse,
    label: "Warehouse",
    subtitle: "Integrated & Governed",
    description: "Gold-layer marts integrated for analytics and oversight.",
  },
  {
    icon: LineChart,
    label: "Data Products",
    subtitle: "Analytics & Intelligence",
    description: "Regulatory exports, dashboards, and intelligence outputs.",
  },
];

export default function DataFabricFlow() {
  return (
    <section className="w-full py-16 lg:py-20 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a1628] via-[#0f2744] to-[#050d1a]" />
      <div className="absolute inset-0 opacity-30 bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.12),transparent_65%)]" />
      <div className="relative w-full px-6 lg:px-14">
        <p className="text-cyan-400 text-xs font-bold uppercase tracking-[0.2em] mb-3">Medallion architecture</p>
        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white max-w-3xl">
          Data fabric flow — from regulatory sources to governed intelligence
        </h2>
        <p className="mt-3 text-slate-400 max-w-2xl text-sm sm:text-base">
          PetroCore orchestrates upstream datasets through bronze, silver, and warehouse layers with enterprise governance
          baked into every stage.
        </p>
        <div className="mt-10 flex flex-wrap lg:flex-nowrap justify-center gap-3 lg:gap-0">
          {STAGES.map((s, i) => (
            <PipelineStage
              key={s.label}
              icon={s.icon}
              label={s.label}
              subtitle={s.subtitle}
              description={s.description}
              index={i}
              showConnector={i < STAGES.length - 1}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
