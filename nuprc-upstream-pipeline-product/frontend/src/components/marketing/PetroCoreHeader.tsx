"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

type NavItem = { label: string; href: string; short?: string; external?: boolean };

const NAV: NavItem[] = [
  { label: "Platform", href: "/" },
  { label: "Solutions", href: "/solutions" },
  { label: "Product Features & API Docs", href: "/docs", short: "Docs" },
  { label: "Governance", href: "/governance" },
  { label: "Company", href: "https://www.ldvconsultingltd.ng/", external: true },
  { label: "Contact Us", href: "https://www.ldvconsultingltd.ng/contact-us", external: true },
];

export default function PetroCoreHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-cyan-500/10 bg-[#050d1a]/90 backdrop-blur-xl">
      <div className="w-full px-6 lg:px-14 py-3.5 flex items-center justify-between gap-4 flex-wrap">
        <Link href="/" className="flex items-center gap-3 min-w-0 group">
          <img src="/ldv-logo.png" alt="LDV Consulting Ltd" className="h-10 w-10 object-contain shrink-0" />
          <img
            src="/petrocore-hero.png"
            alt=""
            className="h-9 w-[4.5rem] object-cover object-center rounded-md border border-cyan-500/20 hidden sm:block shrink-0"
            aria-hidden
          />
          <motion.div className="min-w-0" whileHover={{ x: 2 }} transition={{ type: "spring", stiffness: 400, damping: 28 }}>
            <motion.div className="font-bold text-white leading-tight tracking-tight">PetroCore</motion.div>
            <motion.div
              className="text-[10px] sm:text-[11px] text-cyan-200/70 leading-snug max-w-[11rem] sm:max-w-none"
              animate={{ opacity: [0.65, 1, 0.65] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
            >
              Upstream Governance &amp; Intelligence Platform
            </motion.div>
          </motion.div>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2 lg:gap-4 text-xs sm:text-sm font-medium flex-wrap justify-end">
          {NAV.map((item) => {
            const active = !item.external && pathname === item.href;
            const cls = active
              ? "text-cyan-300"
              : "text-slate-300 hover:text-cyan-200 transition-colors";
            const label = item.short ? (
              <>
                <span className="hidden xl:inline">{item.label}</span>
                <span className="xl:hidden">{item.short}</span>
              </>
            ) : (
              item.label
            );
            if (item.external) {
              return (
                <a key={item.href} href={item.href} target="_blank" rel="noopener noreferrer" className={`px-2 py-1.5 ${cls}`}>
                  {label}
                </a>
              );
            }
            return (
              <Link key={item.href} href={item.href} className={`px-2 py-1.5 rounded-lg ${active ? "bg-cyan-500/10" : ""} ${cls}`}>
                {label}
              </Link>
            );
          })}
          <Link
            href="/console"
            className="ml-1 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-500 text-[#050d1a] font-bold shadow-[0_0_24px_rgba(34,211,238,0.35)] hover:shadow-[0_0_32px_rgba(34,211,238,0.5)] transition-shadow"
          >
            Admin Console
          </Link>
        </nav>
      </div>
    </header>
  );
}
