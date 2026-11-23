"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { GapNote, PageHeader, SortTable, StatusPill } from "../components/console/ui";

const scores = [
  { name: "Oil Production", commodity: "Oil", completeness: 98, freshness: 92, schemaStability: 100, anomalyRate: 0.2, overall: 92 },
  { name: "Gas Production", commodity: "Gas", completeness: 85, freshness: 54, schemaStability: 95, anomalyRate: 1.1, overall: 72 },
  { name: "Rig Disposition", commodity: "Rig activity", completeness: 96, freshness: 88, schemaStability: 100, anomalyRate: 0.5, overall: 88 },
  { name: "Concession Status", commodity: "Concession", completeness: 100, freshness: 79, schemaStability: 100, anomalyRate: 0, overall: 85 },
];

const drills = ["bronze.oil_production_status_raw", "bronze.gas_production_status_raw", "silver.oil_production", "warehouse.fact_oil_production"];

export default function DataQualityPage() {
  const [commodity, setCommodity] = useState("All");
  const [selected, setSelected] = useState<string | null>(null);
  const rows = useMemo(
    () => scores.filter((row) => commodity === "All" || row.commodity === commodity),
    [commodity]
  );
  const current = rows.find((row) => row.name === selected) ?? null;

  return (
    <>
      <PageHeader
        title="Data Quality"
        description="Workspace trust illustrations for oil, gas, rig activity, and concession. These scores are not loaded from a published NUPRC snapshot."
        actions={
          <label>
            Commodity
            <select className="pc-field" value={commodity} onChange={(event) => setCommodity(event.target.value)}>
              <option>All</option>
              <option>Oil</option>
              <option>Gas</option>
              <option>Rig activity</option>
              <option>Concession</option>
            </select>
          </label>
        }
      />
      <GapNote>
        Completeness, freshness, schema stability, and anomaly rate below are stored with the screen. The quality API is still a placeholder, so they are labeled as illustrations.
      </GapNote>
      <div className="pc-work">
        <div className="pc-work-main">
          <SortTable
            rows={rows}
            caption="Illustrated trust scores"
            rowKey={(row) => row.name}
            selectedKey={current?.name}
            onRow={(row) => setSelected(row.name)}
            columns={[
              { id: "name", header: "Dataset", sticky: true, sortValue: (row) => row.name, cell: (row) => row.name },
              { id: "commodity", header: "Commodity", sortValue: (row) => row.commodity, cell: (row) => row.commodity },
              { id: "completeness", header: "Completeness", align: "right", sortValue: (row) => row.completeness, cell: (row) => <span className="pc-num">{row.completeness}%</span> },
              { id: "freshness", header: "Freshness", align: "right", sortValue: (row) => row.freshness, cell: (row) => <span className="pc-num">{row.freshness}</span> },
              { id: "schema", header: "Schema", align: "right", sortValue: (row) => row.schemaStability, cell: (row) => <span className="pc-num">{row.schemaStability}%</span> },
              { id: "anomaly", header: "Anomaly", align: "right", sortValue: (row) => row.anomalyRate, cell: (row) => <span className="pc-num">{row.anomalyRate}%</span> },
              {
                id: "overall",
                header: "Overall",
                align: "right",
                sortValue: (row) => row.overall,
                cell: (row) => <StatusPill tone={row.overall >= 85 ? "ok" : row.overall >= 70 ? "warn" : "danger"}>{row.overall}/100</StatusPill>,
              },
            ]}
          />
          <section className="pc-card">
            <div className="pc-card-h">
              <h2>Column-level drill</h2>
            </div>
            <div className="pc-card-b">
              <p className="pc-lede">Select a dataset name to keep the existing drill list. Per-column null rate, format, and outliers are not returned yet.</p>
              <div className="pc-actions">
                {drills.map((dataset) => (
                  <button key={dataset} type="button" className="pc-btn" onClick={() => setSelected(dataset)}>
                    {dataset}
                  </button>
                ))}
              </div>
            </div>
          </section>
          <p>
            <Link href="/showcase/quality">Open the isolated legacy quality fixture</Link>
          </p>
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
                <dt>Commodity</dt>
                <dd>{current.commodity}</dd>
              </div>
              <div>
                <dt>Overall</dt>
                <dd className="pc-num">{current.overall}/100</dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>Workspace illustration. No page or table reference is attached.</dd>
              </div>
            </dl>
          </aside>
        )}
      </div>
    </>
  );
}
