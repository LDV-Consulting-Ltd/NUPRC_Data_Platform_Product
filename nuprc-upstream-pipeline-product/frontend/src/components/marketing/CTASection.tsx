"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function CTASection({
  onRunPipeline,
  runPending,
}: {
  onRunPipeline?: () => void;
  runPending?: boolean;
}) {
  return (
    <section className="w-full px-6 lg:px-14 py-16">
      <motion.div
        className="w-full rounded-3xl border border-cyan-500/20 bg-gradient-to-br from-[#163a5f]/80 to-[#050d1a] p-8 lg:p-12 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8 shadow-[0_0_60px_rgba(34,211,238,0.08)]"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
      >
        <div>
          <p className="text-cyan-400 text-xs font-bold uppercase tracking-widest">LDV Consulting Ltd</p>
          <h2 className="mt-2 text-2xl lg:text-3xl font-bold text-white">Ready to operate upstream intelligence?</h2>
          <p className="mt-2 text-slate-400 max-w-xl">
            Launch the admin console for pipeline control, governance, lineage, and operational diagnostics — or run the
            pipeline directly from the platform.
          </p>
        </div>
        <div className="flex flex-wrap gap-3 shrink-0">
          {onRunPipeline && (
            <button
              type="button"
              onClick={onRunPipeline}
              disabled={runPending}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-400 text-[#050d1a] font-bold disabled:opacity-50 shadow-[0_0_24px_rgba(34,211,238,0.3)]"
            >
              {runPending ? "Starting…" : "Run Pipeline"}
            </button>
          )}
          <Link
            href="/console"
            className="px-6 py-3 rounded-xl border border-cyan-400/40 text-cyan-100 font-semibold hover:bg-cyan-500/10 transition-colors"
          >
            Open Admin Console
          </Link>
        </div>
      </motion.div>
    </section>
  );
}
