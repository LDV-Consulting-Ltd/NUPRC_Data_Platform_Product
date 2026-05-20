"use client";

import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

export default function FeatureCard({
  icon: Icon,
  title,
  description,
  href,
  tag,
}: {
  icon?: LucideIcon;
  title: string;
  description: string;
  href?: string;
  tag?: string;
}) {
  const inner = (
    <motion.div
      whileHover={{ y: -4, borderColor: "rgba(34,211,238,0.45)" }}
      className="h-full rounded-2xl border border-cyan-500/15 bg-white/5 backdrop-blur-md p-5 shadow-lg shadow-black/20"
    >
      <motion.div className="flex items-start justify-between gap-3" whileHover={{ opacity: 1 }}>
        {Icon && (
          <div className="h-11 w-11 rounded-xl bg-cyan-500/10 border border-cyan-400/25 flex items-center justify-center text-cyan-300 shrink-0">
            <Icon className="h-5 w-5" />
          </div>
        )}
        {tag && (
          <span className="text-[10px] uppercase tracking-wider font-bold px-2 py-1 rounded-full bg-amber-500/15 text-amber-200 border border-amber-400/20">
            {tag}
          </span>
        )}
      </motion.div>
      <h3 className="mt-4 font-bold text-white text-lg">{title}</h3>
      <p className="mt-2 text-sm text-slate-400 leading-relaxed">{description}</p>
      {href && (
        <div className="mt-4 flex items-center gap-1 text-xs font-semibold text-cyan-300">
          Explore <ArrowUpRight className="h-3.5 w-3.5" />
        </div>
      )}
    </motion.div>
  );

  if (href) {
    return (
      <Link href={href} className="block h-full">
        {inner}
      </Link>
    );
  }
  return inner;
}
