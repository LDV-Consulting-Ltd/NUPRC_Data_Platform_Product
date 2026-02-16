"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/", label: "🏠 Home" },
  { href: "/showcase/runs", label: "Number of Runs" },
  { href: "/showcase/quality", label: "Data Quality Metrics" },
  { href: "/showcase/diagrams", label: "Data Model and ETL Diagram" },
  { href: "/showcase/warehouse", label: "Datawarehouse Tables" },
  { href: "/showcase/catalog", label: "📚 Data Catalog" },
  { href: "/showcase/health", label: "Pipeline Health" },
];

export default function ShowcaseLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#fff" }}>
      {/* Sidebar */}
      <div style={{ width: 300, padding: 24, borderRight: "1px solid #eee" }}>
        <Link href="/" style={{ textDecoration: "none", color: "inherit" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18, cursor: "pointer" }}>
            <div style={{ width: 44, height: 44, borderRadius: 12, overflow: "hidden", border: "1px solid #eee", backgroundColor: "#fff", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Image
                src="/logo.png"
                alt="LDV Consulting Ltd"
                width={44}
                height={44}
                style={{ objectFit: "contain" }}
                onError={(e) => {
                  // If logo missing, show text fallback
                  const parent = (e.currentTarget as any).parentElement;
                  if (parent) {
                    parent.innerHTML = '<div style="color: #f2a36b; fontWeight: 700; fontSize: 18">LDV</div>';
                  }
                }}
              />
            </div>
            <div>
              <div style={{ fontWeight: 900, fontSize: 16 }}>Energy Regulator Tenant Data Fabric</div>
              <div style={{ fontSize: 12, color: "#666" }}>by LDV Consulting Ltd</div>
            </div>
          </div>
        </Link>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {items.map((i) => {
            const active = pathname === i.href || (i.href === "/" && pathname === "/");
            return (
              <Link
                key={i.href}
                href={i.href}
                style={{
                  textDecoration: "none",
                  border: active ? "2px solid #f2a36b" : "1px solid #eee",
                  borderRadius: 18,
                  padding: 16,
                  fontWeight: 800,
                  textAlign: "center",
                  color: "#111",
                  background: active ? "rgba(242,163,107,0.10)" : "#fff",
                }}
              >
                {i.label}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Main Pane */}
      <div style={{ flex: 1, padding: 24 }}>
        <div
          style={{
            border: "3px solid #f2a36b",
            borderRadius: 40,
            padding: 24,
            minHeight: "calc(100vh - 48px)",
            background: "white",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}
