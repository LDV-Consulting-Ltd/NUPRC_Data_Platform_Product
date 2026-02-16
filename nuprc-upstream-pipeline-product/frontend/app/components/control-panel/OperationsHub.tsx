"use client";

import Link from "next/link";

const links = [
  { section: "Analytics", items: [{ href: "/run-history", label: "Run History" }, { href: "/data-quality", label: "Data Quality Dashboard" }] },
  { section: "Architecture", items: [{ href: "/lineage-explorer", label: "Data Model Explorer" }, { href: "/warehouse-tables", label: "Warehouse Tables" }] },
  { section: "Governance", items: [{ href: "/catalog", label: "Data Catalog" }, { href: "/lineage-explorer", label: "Lineage Explorer" }, { href: "/regulatory-views", label: "Regulatory Views" }] },
  { section: "Platform Health", items: [{ href: "/run-history", label: "Pipeline Health" }, { href: "/source-health", label: "Source Availability" }, { href: "/source-health", label: "Error Trends" }] },
];

export default function OperationsHub() {
  return (
    <section className="bg-white rounded-2xl border border-slate-200 p-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-slate-500">Operations Hub</div>
          <div className="text-xl font-bold">Monitoring, Governance & Architecture</div>
        </div>
        <Link href="/run-history" className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-sm font-semibold">
          Open All
        </Link>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {links.map((group) => (
          <div key={group.section} className="rounded-2xl border border-slate-200 p-4">
            <div className="font-bold">{group.section}</div>
            <div className="mt-3 space-y-2">
              {group.items.map((item) => (
                <Link
                  key={item.href + item.label}
                  href={item.href}
                  className="block px-3 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-sm"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
