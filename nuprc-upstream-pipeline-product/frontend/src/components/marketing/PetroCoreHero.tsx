"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";

export default function PetroCoreHero({
  onRunPipeline,
  runPending,
}: {
  onRunPipeline: () => void;
  runPending?: boolean;
}) {
  return (
    <section className="w-full min-h-[calc(100vh-64px)] grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-14 px-6 lg:px-14 py-14 lg:py-20 items-center">
      <div>
        <motion.p
          className="text-cyan-400 text-xs font-bold uppercase tracking-[0.18em] mb-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
        >
          LDV Consulting Ltd × PetroCore
        </motion.p>
        <motion.h1
          className="text-[clamp(2rem,4.5vw,3.25rem)] font-bold text-white leading-[1.12] tracking-tight"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        >
          Nigerian upstream regulatory data, orchestrated into governed intelligence.
        </motion.h1>
        <motion.p
          className="mt-5 text-[clamp(1rem,1.6vw,1.125rem)] text-slate-400 max-w-xl leading-relaxed"
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          Automated acquisition, standardization, warehousing, governance, lineage, and analytics across concession, oil
          production, gas production, and rig intelligence datasets.
        </motion.p>
        <motion.div
          className="mt-9 flex flex-wrap gap-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <button
            type="button"
            onClick={onRunPipeline}
            disabled={runPending}
            className="px-7 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-400 text-[#050d1a] font-bold shadow-[0_0_28px_rgba(34,211,238,0.35)] hover:shadow-[0_0_40px_rgba(34,211,238,0.45)] disabled:opacity-50 transition-shadow"
          >
            {runPending ? "Starting pipeline…" : "Run Pipeline"}
          </button>
          <Link
            href="/console"
            className="px-7 py-3.5 rounded-xl border border-cyan-400/35 text-cyan-100 font-semibold hover:bg-cyan-500/10 transition-colors"
          >
            Open Admin Console
          </Link>
        </motion.div>
      </div>

      <motion.div
        className="relative w-full h-[260px] sm:h-[340px] md:h-[400px] lg:h-[480px] xl:h-[560px] rounded-[2rem] overflow-hidden border border-cyan-500/25 shadow-[0_0_80px_rgba(34,211,238,0.12)] bg-[#0a1628]"
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
      >
        <Image
          src="/petrocore-hero.png"
          alt="LDV Consulting Ltd and PetroCore Upstream Governance and Intelligence Platform"
          fill
          priority
          className="object-cover object-center"
          sizes="(max-width: 1024px) 100vw, 50vw"
        />
        <div className="absolute inset-0 bg-gradient-to-tr from-[#050d1a]/55 via-transparent to-cyan-500/15 pointer-events-none" />
        <div className="absolute inset-0 ring-1 ring-inset ring-cyan-400/20 pointer-events-none" />
      </motion.div>
    </section>
  );
}
