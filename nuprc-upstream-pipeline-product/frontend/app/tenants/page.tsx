"use client";

import { useState } from "react";
import { GapNote, PageHeader, StatusPill } from "../components/console/ui";

const tenants = [
  { name: "NUPRC Regulator", org: "Gov", activePipelines: 2, dataTrustAvg: 88, costUsage: "—", slaCompliance: "30/30" },
  { name: "LDV Internal", org: "LDV", activePipelines: 1, dataTrustAvg: 92, costUsage: "—", slaCompliance: "30/30" },
];

export default function TenantsPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const current = tenants.find((tenant) => tenant.name === selected) ?? null;

  return (
    <>
      <PageHeader
        title="Tenants"
        description="Workspace tenant cards. There is no authentication gate in this application, so these cards are configuration notes rather than a permissioned directory."
      />
      <GapNote>Tenant counts are stored with this screen. They are not loaded from a published NUPRC snapshot.</GapNote>
      <div className="pc-work">
        <div className="pc-work-main">
          <div className="pc-metrics">
            {tenants.map((tenant) => (
              <button key={tenant.name} type="button" className="pc-metric" onClick={() => setSelected(tenant.name)} style={{ textAlign: "left" }}>
                <p className="pc-metric-label">{tenant.org}</p>
                <p className="pc-metric-value">{tenant.name}</p>
                <p className="pc-metric-detail">{tenant.activePipelines} active pipelines · trust {tenant.dataTrustAvg}/100</p>
              </button>
            ))}
          </div>
        </div>
        {current && (
          <aside className="pc-detail">
            <div className="pc-detail-bar">
              <h2>{current.name}</h2>
              <button type="button" className="pc-btn" onClick={() => setSelected(null)}>
                Close
              </button>
            </div>
            <dl className="pc-detail-list">
              <div>
                <dt>Organisation</dt>
                <dd>{current.org}</dd>
              </div>
              <div>
                <dt>Active pipelines</dt>
                <dd className="pc-num">{current.activePipelines}</dd>
              </div>
              <div>
                <dt>Data trust average</dt>
                <dd className="pc-num">{current.dataTrustAvg}/100</dd>
              </div>
              <div>
                <dt>Cost usage</dt>
                <dd>{current.costUsage}</dd>
              </div>
              <div>
                <dt>SLA compliance</dt>
                <dd>
                  <StatusPill tone="ok">{current.slaCompliance}</StatusPill>
                </dd>
              </div>
            </dl>
            <p className="pc-detail-note">Settings and open actions are not wired to an admin API.</p>
          </aside>
        )}
      </div>
    </>
  );
}
