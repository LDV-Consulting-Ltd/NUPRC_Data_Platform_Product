"use client";

import { motion } from "framer-motion";
import PetroCoreHeader from "./PetroCoreHeader";

export default function MarketingShell({
  children,
  footer,
}: {
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <div className="min-h-screen w-full flex flex-col bg-[#050d1a] text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-10%,rgba(34,211,238,0.08),transparent)]" />
      <PetroCoreHeader />
      <main className="relative flex-1 w-full">{children}</main>
      {footer ?? (
        <footer className="w-full px-6 lg:px-14 py-8 border-t border-cyan-500/10 text-sm text-slate-500">
          <motion.div className="flex flex-wrap justify-between gap-4">
            <span>© LDV Consulting Ltd — PetroCore Upstream Governance &amp; Intelligence Platform</span>
            <a
              href="https://www.ldvconsultingltd.ng/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400/80 hover:text-cyan-300 font-semibold"
            >
              ldvconsultingltd.ng
            </a>
          </motion.div>
        </footer>
      )}
    </div>
  );
}
