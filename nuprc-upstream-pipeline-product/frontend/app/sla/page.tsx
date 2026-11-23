"use client";

import { GapNote, PageHeader, SortTable, StateBlock, StatusPill, toneForStatus } from "../components/console/ui";

const deadlines = [
  { label: "Daily pipeline delivery", date: "08 Feb 2026", time: "02:00", status: "Met" },
  { label: "Monthly submission", date: "15 Feb 2026", time: "", status: "On track" },
  { label: "Quarterly audit export", date: "31 Mar 2026", time: "", status: "Upcoming" },
];

const breaches = [{ run: "RUN-2026-02-06-0200", target: "02:00", actual: "—", impact: "Daily delivery missed" }];

export default function SLAPage() {
  return (
    <>
      <PageHeader
        title="SLA & Compliance"
        description="Submission deadlines and the breach note stored with this screen."
      />
      <GapNote>These dates are workspace reminders. They are not calculated from ingestion runs and are not a published NUPRC calendar.</GapNote>
      <div className="pc-metrics">
        {deadlines.map((item) => (
          <article key={item.label} className="pc-metric">
            <p className="pc-metric-label">{item.status}</p>
            <p className="pc-metric-value" style={{ fontSize: 16 }}>{item.label}</p>
            <p className="pc-metric-detail">
              {item.date}
              {item.time ? ` — ${item.time}` : ""}
            </p>
            <StatusPill tone={toneForStatus(item.status)}>{item.status}</StatusPill>
          </article>
        ))}
      </div>
      <section className="pc-card">
        <div className="pc-card-h">
          <h2>Breach notes</h2>
          <StatusPill tone="danger">{breaches.length} noted</StatusPill>
        </div>
        <div className="pc-card-b">
          <SortTable
            rows={breaches}
            caption="Breach notes"
            rowKey={(row) => row.run}
            columns={[
              { id: "run", header: "Run", cell: (row) => row.run },
              { id: "target", header: "Target", cell: (row) => row.target },
              { id: "actual", header: "Actual", cell: (row) => row.actual },
              { id: "impact", header: "Impact", cell: (row) => row.impact },
            ]}
          />
        </div>
      </section>
      <StateBlock tone="awaiting" title="Calendar view is not connected">
        Submission windows are listed in the cards above. A calendar component is not part of this console yet.
      </StateBlock>
    </>
  );
}
