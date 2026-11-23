import type { Metadata } from "next";
import Link from "next/link";
import "./styles/landing.css";
import { COMPANY_SITE, NUPRC_REPORTS, PUBLIC_SOURCES } from "@/lib/public-sources";

export const metadata: Metadata = {
  title: "LDV Data Console · NUPRC",
  description:
    "LDV Consulting’s upstream petroleum data product, built from published NUPRC reports. Not an official NUPRC application.",
};

const WORKSPACE = [
  {
    href: "/control-panel",
    title: "Control Panel",
    text: "Latest ingestion attempt, published snapshot, source health, and pipeline controls.",
  },
  {
    href: "/regulatory",
    title: "Upstream Intelligence",
    text: "Oil, gas, rig activity, and concession datasets with units, periods, and sources.",
  },
  {
    href: "/source-health",
    title: "Source Reports",
    text: "Each monitored publication, with a link back to the NUPRC page that supplied it.",
  },
  {
    href: "/catalog",
    title: "Published Datasets",
    text: "Bronze, silver, and warehouse tables currently registered in the catalog.",
  },
  {
    href: "/run-history",
    title: "Ingestion Runs",
    text: "Pipeline runs returned by the operations API, including status and timing.",
  },
  {
    href: "/lineage",
    title: "Lineage",
    text: "How published reports move from source files through bronze, silver, and the warehouse.",
  },
];

export default function LandingPage() {
  return (
    <div className="ldv-landing">
      <a className="ldv-skip" href="#landing-main">
        Skip to content
      </a>
      <header className="ldv-head">
        <div className="ldv-head-inner">
          <Link href="/" className="ldv-brand">
            <span className="ldv-mark" aria-hidden="true">
              LDV
            </span>
            <div>
              <strong>LDV Consulting</strong>
              <span>LDV Data Console · NUPRC</span>
            </div>
          </Link>
          <nav className="ldv-nav" aria-label="Landing">
            <a href="#platform">Platform</a>
            <a href="#coverage">Upstream data</a>
            <a href="#workspace">Workspace</a>
            <a href={NUPRC_REPORTS} target="_blank" rel="noopener noreferrer">
              Source reports
            </a>
            <a className="ldv-company" href={COMPANY_SITE} target="_blank" rel="noopener noreferrer">
              Company Website
            </a>
            <Link className="ldv-open" href="/control-panel">
              Open NUPRC Data Console
            </Link>
          </nav>
        </div>
      </header>
      <main id="landing-main">
        <div className="ldv-wrap">
          <section className="ldv-hero" id="platform">
            <p className="ldv-kicker">Upstream petroleum data product</p>
            <h1>LDV Data Console · NUPRC</h1>
            <p className="ldv-lede">
              LDV Consulting’s workspace for upstream petroleum data, built from reports published by the Nigerian
              Upstream Petroleum Regulatory Commission.
            </p>
            <p className="ldv-note">
              Figures in the console are traced to those published reports. This site is an LDV Consulting product. It
              is not an official NUPRC application.
            </p>
            <div className="ldv-hero-actions">
              <Link className="ldv-open ldv-open-lg" href="/control-panel">
                Open NUPRC Data Console
              </Link>
              <a className="ldv-ghost" href={COMPANY_SITE} target="_blank" rel="noopener noreferrer">
                Company Website
              </a>
            </div>
          </section>

          <section className="ldv-section" id="coverage">
            <h2>What the console monitors</h2>
            <p>
              Published NUPRC production, rig, and concession reports are ingested separately so oil and gas stay
              distinct, and each record can point back to its source page.
            </p>
            <div className="ldv-grid">
              {PUBLIC_SOURCES.map((source) => (
                <a key={source.key} className="ldv-card" href={source.href} target="_blank" rel="noopener noreferrer">
                  <strong>{source.label}</strong>
                  <span>{source.commodity}</span>
                  <span>{source.unit}</span>
                </a>
              ))}
              <Link className="ldv-card" href="/data-quality">
                <strong>Data quality</strong>
                <span>Freshness and trust views for the same four source families.</span>
              </Link>
              <a className="ldv-card" href={NUPRC_REPORTS} target="_blank" rel="noopener noreferrer">
                <strong>NUPRC reports</strong>
                <span>The published report library this product is built from.</span>
              </a>
            </div>
          </section>

          <section className="ldv-section">
            <h2>From published reports to a data product</h2>
            <div className="ldv-flow" aria-label="Data path">
              <span>Published NUPRC reports</span>
              <span>Bronze extraction</span>
              <span>Silver normalization</span>
              <span>Warehouse datasets</span>
              <span>Console and catalog</span>
            </div>
            <p className="ldv-center">
              The console keeps the latest ingestion attempt separate from the latest published warehouse snapshot.
            </p>
          </section>

          <section className="ldv-section" id="workspace">
            <h2>Open a workspace view</h2>
            <p>These links open the production console. Fixture screens under /showcase stay out of this navigation.</p>
            <div className="ldv-grid">
              {WORKSPACE.map((entry) => (
                <Link key={entry.href} className="ldv-card" href={entry.href}>
                  <strong>{entry.title}</strong>
                  <span>{entry.text}</span>
                </Link>
              ))}
            </div>
          </section>

          <section className="ldv-section">
            <h2>Governance by design</h2>
            <ul className="ldv-list">
              <li>Source pages stay attached to oil, gas, rig activity, and concession records.</li>
              <li>Catalog, warehouse, and lineage views read the existing platform APIs.</li>
              <li>Pipeline runs are started only from the control panel, not from this page.</li>
              <li>
                Documentation for operators lives in the catalog, lineage, and control panel. There is no separate
                public docs route in this application.
              </li>
            </ul>
          </section>
        </div>
      </main>
      <footer className="ldv-foot">
        <div className="ldv-foot-inner">
          <div>
            <strong>LDV Consulting</strong>
            <p>
              LDV Data Console · NUPRC is built from published NUPRC reports. It is not an official NUPRC application.
            </p>
          </div>
          <nav aria-label="Sources and documentation">
            <a href={COMPANY_SITE} target="_blank" rel="noopener noreferrer">
              Company Website
            </a>
            <a href={NUPRC_REPORTS} target="_blank" rel="noopener noreferrer">
              NUPRC reports
            </a>
            <Link href="/control-panel">Open NUPRC Data Console</Link>
            <Link href="/catalog">Published datasets</Link>
            <Link href="/lineage">Lineage</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
