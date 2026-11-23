"use client";

import { GapNote, MetricTile, PageHeader, SortTable, StateBlock } from "../components/console/ui";

const rows = [
  { run: "RUN-2026-02-07-2114", cost: "—", dataset: "Full pipeline" },
  { run: "RUN-2026-02-07-0200", cost: "—", dataset: "Full pipeline" },
];

export default function CostPage() {
  return (
    <>
      <PageHeader title="Cost & Usage" description="FinOps placeholders. No billing feed is connected, so costs stay blank." />
      <GapNote>Run identifiers below are the notes previously shown on this screen. They are not a live billing extract.</GapNote>
      <section className="pc-metrics">
        <MetricTile label="Cost this month" value="—" detail="No billing unit is configured" />
        <MetricTile label="Cost per run" value="—" detail="Average not supplied" />
        <MetricTile label="Cost per dataset" value="—" detail="Not supplied" />
        <MetricTile label="Forecast, next 30 days" value="—" detail="Not supplied" />
      </section>
      <SortTable
        rows={rows}
        caption="Cost notes"
        rowKey={(row) => row.run}
        columns={[
          { id: "run", header: "Run", cell: (row) => row.run },
          { id: "cost", header: "Cost", cell: (row) => row.cost },
          { id: "dataset", header: "Dataset / scope", cell: (row) => row.dataset },
        ]}
      />
      <StateBlock tone="awaiting" title="Billing is not connected">
        Cost per run, cost per dataset, and the forecast can be wired when a billing API exists. This screen does not invent amounts.
      </StateBlock>
    </>
  );
}
