"use client";

import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

export default function GovernanceCard({
  icon: Icon,
  label,
  value,
  hint,
  tone = "cyan",
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  hint?: string;
  tone?: "cyan" | "gold" | "emerald" | "amber";
}) {
  const ring =
    tone === "gold"
      ? "border-amber-400/25 text-amber-200"
      : tone === "emerald"
        ? "border-emerald-400/25 text-emerald-200"
        : tone === "amber"
          ? "border-amber-400/25 text-amber-200"
          : "border-cyan-400/25 text-cyan-200";

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`rounded-2xl border bg-white/5 backdrop-blur-md p-5 ${ring.split(" ")[0]} shadow-lg shadow-black/25`}
    >
      <div className="flex items-start gap-3">
        <div className={`h-11 w-11 rounded-xl bg-[#0f2744] flex items-center justify-center shrink-0 border ${ring}`}>
          <Icon className="h-5 w-5" />
        </div>
        <motion.div className="min-w-0 flex-1" animate={{ opacity: [0.88, 1, 0.88] }} transition={{ duration: 2.8, repeat: Infinity }}>
          <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{label}</div>
          <div className="text-2xl font-bold mt-1 text-white">{value}</div>
          {hint && <div className="text-xs mt-1 text-slate-400">{hint}</div>}
        </motion.div>
      </div>
    </motion.div>
  );
}
