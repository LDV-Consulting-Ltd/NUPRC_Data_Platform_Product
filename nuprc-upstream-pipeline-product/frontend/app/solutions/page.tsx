"use client";

import { motion } from "framer-motion";
import {
  Building2,
  GitBranch,
  Map,
  Droplets,
  Flame,
  Drill,
  Database,
  LineChart,
  Shield,
  Briefcase,
} from "lucide-react";
import MarketingShell from "@/components/marketing/MarketingShell";
import FeatureCard from "@/components/marketing/FeatureCard";
import CTASection from "@/components/marketing/CTASection";
import { SOLUTION_PILLARS } from "@/lib/productDocs";

const CAPABILITY_GRID = [
  { icon: Shield, title: "Upstream regulatory intelligence", desc: "NUPRC-aligned datasets unified for executive and operational stakeholders.", href: "/docs" },
  { icon: GitBranch, title: "Metadata & lineage", desc: "Trace every dataset from publication through warehouse products.", href: "/lineage-explorer" },
  { icon: Map, title: "Concession intelligence", desc: "Concession register snapshots and status intelligence.", href: "/catalog" },
  { icon: Droplets, title: "Oil production intelligence", desc: "Operator-level production facts with conformed dimensions.", href: "/console/warehouse" },
  { icon: Flame, title: "Gas production intelligence", desc: "Gas production standardized for regulatory and analytics use.", href: "/console/warehouse" },
  { icon: Drill, title: "Rig intelligence", desc: "Rig disposition and activity facts for operational oversight.", href: "/console/warehouse" },
  { icon: Database, title: "Data product strategy", desc: "Medallion layers designed for governed downstream consumption.", href: "/docs" },
  { icon: LineChart, title: "Operational oversight", desc: "Pipeline health, diagnostics, freshness, and SLA views.", href: "/console" },
  { icon: Briefcase, title: "Business value", desc: "Investor-ready intelligence platform for sovereign energy operations.", href: "/governance" },
];

export default function SolutionsPage() {
  return (
    <MarketingShell>
      <section className="w-full px-6 lg:px-14 py-16 lg:py-20">
        <motion.p
          className="text-cyan-400 text-xs font-bold uppercase tracking-[0.2em]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          Solutions
        </motion.p>
        <motion.h1
          className="mt-4 text-[clamp(2rem,4vw,3rem)] font-bold text-white max-w-4xl leading-tight"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
        >
          Executive-grade upstream governance and intelligence for Nigeria&apos;s regulatory data fabric
        </motion.h1>
        <motion.p
          className="mt-5 text-slate-400 max-w-3xl text-lg leading-relaxed"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          PetroCore by LDV Consulting Ltd transforms fragmented NUPRC publications into a governed operating system —
          acquisition, standardization, warehousing, lineage, and analytics in one platform.
        </motion.p>
      </section>

      <section className="w-full px-6 lg:px-14 pb-12">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {CAPABILITY_GRID.map((c) => (
            <FeatureCard key={c.title} icon={c.icon} title={c.title} description={c.desc} href={c.href} />
          ))}
        </div>
      </section>

      <section className="w-full px-6 lg:px-14 py-16 border-t border-cyan-500/10">
        <div className="flex items-center gap-3 mb-8">
          <Building2 className="h-8 w-8 text-amber-400" />
          <h2 className="text-2xl font-bold text-white">Strategic alignment &amp; outcomes</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {SOLUTION_PILLARS.map((p) => (
            <motion.div
              key={p.title}
              whileHover={{ borderColor: "rgba(201,162,39,0.4)" }}
              className="rounded-2xl border border-amber-500/15 bg-white/5 backdrop-blur p-6"
            >
              <h3 className="font-bold text-amber-100">{p.title}</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">{p.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <CTASection />
    </MarketingShell>
  );
}
