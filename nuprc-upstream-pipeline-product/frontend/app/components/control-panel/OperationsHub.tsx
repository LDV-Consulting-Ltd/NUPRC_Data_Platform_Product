"use client";

import Link from "next/link";
import { NUPRC_REPORTS } from "@/lib/public-sources";

const links: { section: string; items: { href: string; label: string; external?: boolean }[] }[] = [
  {
    section: "Upstream Intelligence",
    items: [
      { href: "/regulatory", label: "Production, rigs, and concessions" },
      { href: "/data-quality", label: "Data quality" },
    ],
  },
  {
    section: "Source evidence",
    items: [
      { href: "/source-health", label: "Source reports" },
      { href: NUPRC_REPORTS, label: "NUPRC reports", external: true },
    ],
  },
  {
    section: "Governance",
    items: [
      { href: "/catalog", label: "Published datasets" },
      { href: "/warehouse-tables", label: "Warehouse" },
      { href: "/lineage", label: "Lineage" },
    ],
  },
  {
    section: "Operations",
    items: [
      { href: "/run-history", label: "Ingestion runs" },
      { href: "/sla", label: "SLA & compliance" },
    ],
  },
];

export default function OperationsHub() {
  return (
    <section className="pc-card">
      <div className="pc-card-h">
        <h2>Operations hub</h2>
        <Link className="pc-btn" href="/run-history">
          Ingestion runs
        </Link>
      </div>
      <div className="pc-card-b">
        <div className="pc-flow">
          {links.map((group) => (
            <div key={group.section} className="pc-step">
              <div className="pc-step-k">{group.section}</div>
              <div className="pc-actions" style={{ marginTop: 8, flexDirection: "column", alignItems: "flex-start" }}>
                {group.items.map((item) =>
                  item.external ? (
                    <a key={item.href} href={item.href} target="_blank" rel="noopener noreferrer">
                      {item.label}
                    </a>
                  ) : (
                    <Link key={item.href} href={item.href}>
                      {item.label}
                    </Link>
                  )
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
