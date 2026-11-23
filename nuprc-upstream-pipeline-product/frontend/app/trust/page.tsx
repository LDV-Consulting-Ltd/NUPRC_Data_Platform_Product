"use client";

import { GapNote, PageHeader, SortTable, StatusPill } from "../components/console/ui";

const heatmap = [
  { dataset: "bronze.oil_production_status_raw", commodity: "Oil", score: 92, trend: "up" },
  { dataset: "bronze.gas_production_status_raw", commodity: "Gas", score: 72, trend: "down" },
  { dataset: "silver.oil_production", commodity: "Oil", score: 95, trend: "up" },
  { dataset: "warehouse.fact_oil_production", commodity: "Oil", score: 98, trend: "stable" },
];

export default function TrustPage() {
  return (
    <>
      <PageHeader
        title="Trust Scoring"
        description="Illustrated trust scores by dataset. Oil and gas tables are listed separately."
      />
      <GapNote>Scores are workspace illustrations on a 0–100 scale. They are not a published NUPRC quality result, and no page or table reference is attached.</GapNote>
      <div className="pc-legend">
        <span><i className="pc-swatch" style={{ background: "#146c43" }} /> High, 85 and above</span>
        <span><i className="pc-swatch" style={{ background: "#c4a35a" }} /> Medium, 70–84</span>
        <span><i className="pc-swatch" style={{ background: "#8f2d2d" }} /> Low, under 70</span>
      </div>
      <SortTable
        rows={heatmap}
        caption="Trust illustrations"
        rowKey={(row) => row.dataset}
        columns={[
          { id: "dataset", header: "Dataset", sticky: true, sortValue: (row) => row.dataset, cell: (row) => row.dataset },
          { id: "commodity", header: "Commodity", sortValue: (row) => row.commodity, cell: (row) => row.commodity },
          {
            id: "score",
            header: "Trust score",
            align: "right",
            sortValue: (row) => row.score,
            cell: (row) => (
              <StatusPill tone={row.score >= 85 ? "ok" : row.score >= 70 ? "warn" : "danger"}>{row.score}/100</StatusPill>
            ),
          },
          { id: "trend", header: "Trend", sortValue: (row) => row.trend, cell: (row) => row.trend },
        ]}
      />
    </>
  );
}
