"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import "../../styles/console.css";
import { COMPANY_SITE } from "@/lib/public-sources";

const STORAGE_KEY = "ldv-nuprc-sidebar";

function subscribeSidebar(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  return () => window.removeEventListener("storage", onStoreChange);
}

function readCollapsed() {
  return window.localStorage.getItem(STORAGE_KEY) === "collapsed";
}

const NAV = [
  {
    id: "control",
    label: "Control",
    items: [
      { href: "/control-panel", label: "Control Panel", short: "CP" },
      { href: "/run-history", label: "Ingestion Runs", short: "RN" },
      { href: "/source-health", label: "Source Reports", short: "SR" },
    ],
  },
  {
    id: "intel",
    label: "Upstream Intelligence",
    items: [
      { href: "/regulatory", label: "Production & Concessions", short: "UP" },
      { href: "/data-quality", label: "Data Quality", short: "DQ" },
    ],
  },
  {
    id: "gov",
    label: "Governance",
    items: [
      { href: "/catalog", label: "Published Datasets", short: "DS" },
      { href: "/warehouse-tables", label: "Warehouse", short: "WH" },
      { href: "/lineage", label: "Lineage", short: "LN" },
    ],
  },
  {
    id: "admin",
    label: "Administration",
    items: [
      { href: "/tenants", label: "Tenants", short: "TN" },
      { href: "/pipeline-config", label: "Pipeline Config", short: "CF" },
      { href: "/sla", label: "SLA & Compliance", short: "SLA" },
      { href: "/cost", label: "Cost & Usage", short: "CU" },
      { href: "/trust", label: "Trust Scoring", short: "TS" },
    ],
  },
];

const ALIASES: Record<string, string[]> = {
  "/catalog": ["/data-catalog"],
  "/regulatory": ["/regulatory-views"],
  "/lineage": ["/lineage-explorer"],
  "/sla": ["/sla-compliance"],
  "/cost": ["/cost-usage"],
  "/trust": ["/trust-scoring"],
};

function isActive(href: string, pathname: string) {
  if (pathname === href || pathname.startsWith(`${href}/`)) return true;
  return (ALIASES[href] ?? []).some((alias) => pathname === alias || pathname.startsWith(`${alias}/`));
}

export default function ConsoleShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "/control-panel";
  const storedCollapsed = useSyncExternalStore(subscribeSidebar, readCollapsed, () => false);
  const [collapsedOverride, setCollapsedOverride] = useState<boolean | null>(null);
  const collapsed = collapsedOverride ?? storedCollapsed;
  const [menuPath, setMenuPath] = useState<string | null>(null);
  const mobileOpen = menuPath === pathname;

  const toggleCollapsed = () => {
    const next = !collapsed;
    window.localStorage.setItem(STORAGE_KEY, next ? "collapsed" : "open");
    setCollapsedOverride(next);
  };

  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuPath(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mobileOpen]);

  const className = ["ldv-console", collapsed ? "is-collapsed" : "", mobileOpen ? "is-mobile-open" : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className}>
      <a className="pc-skip" href="#console-main">
        Skip to content
      </a>
      <button type="button" className="pc-backdrop" aria-label="Close navigation" onClick={() => setMenuPath(null)} />
      <aside className="pc-sidebar" aria-label="LDV Data Console">
        <Link className="pc-brand" href="/control-panel">
          <span className="pc-mark" aria-hidden="true">
            LDV
          </span>
          <span className="pc-brand-text">
            <span className="pc-brand-name">LDV Data Console</span>
            <span className="pc-brand-sub">Upstream petroleum</span>
          </span>
        </Link>
        <nav className="pc-nav">
          {NAV.map((group) => (
            <div key={group.id} className="pc-nav-group">
              <p className="pc-nav-label">{group.label}</p>
              {group.items.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={isActive(item.href, pathname) ? "page" : undefined}
                  title={item.label}
                >
                  <span className="pc-nav-short" aria-hidden="true">
                    {item.short}
                  </span>
                  <span className="pc-nav-full">{item.label}</span>
                </Link>
              ))}
            </div>
          ))}
        </nav>
        <div className="pc-side-foot">
          <a className="pc-side-link" href={COMPANY_SITE} target="_blank" rel="noopener noreferrer">
            Company website
          </a>
          <Link className="pc-side-link" href="/">
            Landing page
          </Link>
          <p className="pc-side-extra">LDV Consulting · built from published NUPRC reports. Not an official NUPRC application.</p>
        </div>
      </aside>
      <div className="pc-workspace">
        <header className="pc-topbar">
          <button type="button" className="pc-icon-btn pc-menu" onClick={() => setMenuPath(pathname)} aria-expanded={mobileOpen}>
            Menu
          </button>
          <button
            type="button"
            className="pc-icon-btn"
            onClick={toggleCollapsed}
            aria-pressed={collapsed}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? "Expand" : "Collapse"}
          </button>
          <div className="pc-topbar-title">
            <div className="pc-topbar-kicker">LDV Data Console</div>
            <div className="pc-topbar-name">Upstream petroleum · NUPRC</div>
          </div>
          <div className="pc-topbar-actions">
            <a className="pc-btn pc-btn-ghost" href={COMPANY_SITE} target="_blank" rel="noopener noreferrer">
              Company website
            </a>
            <Link className="pc-btn pc-btn-ghost" href="/">
              Landing page
            </Link>
          </div>
        </header>
        <main id="console-main" className="pc-main" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
