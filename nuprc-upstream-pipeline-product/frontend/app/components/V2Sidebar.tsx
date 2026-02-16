"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { label: "Operations", links: [
    { href: "/control-panel", label: "Control Panel" },
    { href: "/run-history", label: "Run History" },
    { href: "/data-quality", label: "Data Quality" },
    { href: "/source-health", label: "Source Health" },
  ]},
  { label: "Governance", links: [
    { href: "/data-catalog", label: "Data Catalog" },
    { href: "/lineage-explorer", label: "Lineage Explorer" },
    { href: "/regulatory-views", label: "Regulatory Views" },
  ]},
  { label: "Admin (SaaS)", links: [
    { href: "/tenants", label: "Tenants & Orgs" },
    { href: "/pipeline-config", label: "Pipeline Config" },
    { href: "/sla-compliance", label: "SLA & Compliance" },
    { href: "/cost-usage", label: "Cost & Usage" },
    { href: "/trust-scoring", label: "Trust Scoring" },
  ]},
];

export default function V2Sidebar() {
  const pathname = usePathname() ?? "";

  return (
    <aside className="w-72 bg-white border-r border-slate-200 hidden lg:flex flex-col shrink-0">
      <div className="p-5 border-b border-slate-200">
        <Link href="/control-panel" className="flex items-center gap-3">
          <img src="/ldv-logo.png" alt="LDV Consulting Ltd" className="h-10 w-10 rounded-xl object-contain shrink-0" />
          <div>
            <div className="text-sm font-semibold">LDV Data Console</div>
            <div className="text-xs text-slate-500">Energy Regulator Tenant Data Fabric</div>
          </div>
        </Link>
        <div className="mt-4 flex items-center justify-between text-xs gap-2 flex-wrap">
          <span className="px-2 py-1 rounded-full bg-slate-100 text-slate-700 chip">Environment: <b>PROD</b></span>
          <span className="px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 chip">● Healthy</span>
        </div>
      </div>
      <nav className="p-3 flex-1 overflow-auto">
        {nav.map((group) => (
          <div key={group.label}>
            <div className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase">{group.label}</div>
            {group.links.map((link) => {
              const isActive =
  pathname === link.href ||
  (pathname === "/" && link.href === "/control-panel") ||
  (link.href !== "/control-panel" && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                    isActive ? "bg-slate-100 font-semibold" : "hover:bg-slate-100"
                  } text-slate-800`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-slate-200" />
          <div className="min-w-0">
            <div className="text-sm font-semibold truncate">Platform Admin</div>
            <div className="text-xs text-slate-500 truncate">LDV</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
