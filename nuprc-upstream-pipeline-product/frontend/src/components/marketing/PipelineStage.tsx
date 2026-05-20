"use client";

import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

export default function PipelineStage({
  icon: Icon,
  label,
  subtitle,
  description,
  index,
  showConnector,
}: {
  icon: LucideIcon;
  label: string;
  subtitle: string;
  description: string;
  index: number;
  showConnector?: boolean;
}) {
  return (
    <motion.div
      className="flex items-stretch flex-1 min-w-[150px] max-w-[220px]"
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1, duration: 0.45 }}
    >
      <motion.div
        whileHover={{ y: -6, boxShadow: "0 0 32px rgba(34,211,238,0.2)" }}
        className="flex-1 rounded-2xl border border-cyan-500/30 bg-gradient-to-b from-[#163a5f]/90 to-[#0a1628]/90 p-4 text-center backdrop-blur-sm"
      >
        <motion.div
          className="mx-auto mb-3 h-12 w-12 rounded-xl bg-cyan-500/10 border border-cyan-400/30 flex items-center justify-center text-cyan-300"
          animate={{ boxShadow: ["0 0 0 rgba(34,211,238,0)", "0 0 20px rgba(34,211,238,0.35)", "0 0 0 rgba(34,211,238,0)"] }}
          transition={{ duration: 2.6, repeat: Infinity, delay: index * 0.25 }}
        >
          <Icon className="h-6 w-6" />
        </motion.div>
        <div className="text-sm font-bold text-white">{label}</div>
        <div className="text-[11px] font-semibold text-cyan-300/90 mt-1 uppercase tracking-wide">{subtitle}</div>
        <p className="text-[11px] text-slate-400 mt-2 leading-snug">{description}</p>
      </motion.div>
      {showConnector && (
        <div className="hidden lg:flex items-center px-1">
          <motion.div
            className="w-6 h-px bg-gradient-to-r from-cyan-500/60 to-cyan-300/20"
            animate={{ opacity: [0.3, 1, 0.3], scaleX: [0.8, 1, 0.8] }}
            transition={{ duration: 2, repeat: Infinity, delay: index * 0.2 }}
          />
        </div>
      )}
    </motion.div>
  );
}
