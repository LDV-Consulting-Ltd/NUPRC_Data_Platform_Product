"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useGoldFreshness } from "@/hooks/useGoldFreshness";
import { PUBLIC_SOURCES, sourceByKey } from "@/lib/public-sources";
import type { SourceHealthItem } from "@/lib/types";
import {
  CountLabel,
  GapNote,
  LoadingRows,
  PageHeader,
  PermissionState,
  SortTable,
  StateBlock,
  StatusPill,
  toneForStatus,
} from "../components/console/ui";
import { errorMessage, permissionDenied } from "@/lib/page-error";

const FILTERS = [
  { id: "all", label: "All" },
  { id: "oil", label: "Oil" },
  { id: "gas", label: "Gas" },
  { id: "rig", label: "Rig activity" },
  { id: "concession", label: "Concession" },
];

function matchesFilter(source: SourceHealthItem, filter: string) {
  if (filter === "all") return true;
  const meta = sourceByKey(source.source_key);
  const haystack = `${source.source_key} ${source.label} ${meta?.commodity ?? ""}`.toLowerCase();
  if (filter === "oil") return haystack.includes("oil");
  if (filter === "gas") return haystack.includes("gas");
  if (filter === "rig") return haystack.includes("rig");
  return haystack.includes("concession");
}

export default function RegulatoryPage() {
  const params = useSearchParams();
  const requested = params.get("source");
  const [filter, setFilter] = useState("all");
  const [selectedKey, setSelectedKey] = useState<string | null>(requested);
  const freshness = useGoldFreshness();

  const rows = useMemo(
    () => (freshness.data ?? []).filter((source) => matchesFilter(source, filter)),
    [freshness.data, filter]
  );
  const selected = rows.find((row) => row.source_key === selectedKey) ?? rows.find((row) => row.source_key === requested) ?? null;
  const selectedMeta = selected ? sourceByKey(selected.source_key) : undefined;

  return (
    <>
      <PageHeader
        title="Upstream Intelligence"
        description="Oil, gas, rig activity, and concession freshness from the published warehouse snapshot. Volumes are not invented here: this feed reports freshness, not barrels or standard cubic feet."
        period={selected?.last_update ? new Date(selected.last_update).toLocaleString("en-GB") : null}
      />
      <GapNote>
        Provisional versus final is shown only when a dataset supplies that status. The freshness feed does not include it.
        Oil and gas remain separate rows.
      </GapNote>
      {freshness.isLoading && <LoadingRows />}
      {freshness.isError &&
        (permissionDenied(freshness.error) ? (
          <PermissionState />
        ) : (
          <StateBlock tone="error" title="Published datasets could not be loaded">
            {errorMessage(freshness.error)}
          </StateBlock>
        ))}
      {!freshness.isLoading && !freshness.isError && (
        <div className="pc-work">
          <div className="pc-work-main">
            <div className="pc-filters" style={{ position: "static", marginBottom: 12, flexDirection: "row", flexWrap: "wrap" }}>
              {FILTERS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className="pc-btn"
                  aria-pressed={filter === item.id}
                  onClick={() => setFilter(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <CountLabel shown={rows.length} total={freshness.data?.length ?? null} />
            <div className="pc-card">
              <div className="pc-card-h">
                <h2>Freshness by dataset</h2>
              </div>
              <div className="pc-card-b">
                {rows.map((row) => (
                  <div key={row.source_key} style={{ marginBottom: 10 }}>
                    <div className="pc-toolbar">
                      <span>{row.label}</span>
                      <span className="pc-num">{row.freshness_score}/100</span>
                    </div>
                    <div className="pc-bar" aria-hidden="true">
                      <span style={{ width: `${Math.max(0, Math.min(100, row.freshness_score))}%` }} />
                    </div>
                  </div>
                ))}
                {rows.length === 0 && <StateBlock tone="empty" title="No datasets match this filter" />}
              </div>
            </div>
            <SortTable
              rows={rows}
              caption="Upstream datasets"
              rowKey={(row) => row.source_key}
              selectedKey={selected?.source_key}
              onRow={(row) => setSelectedKey(row.source_key)}
              columns={[
                {
                  id: "dataset",
                  header: "Dataset",
                  sticky: true,
                  sortValue: (row) => row.label,
                  cell: (row) => row.label,
                },
                {
                  id: "commodity",
                  header: "Commodity",
                  sortValue: (row) => sourceByKey(row.source_key)?.commodity ?? "",
                  cell: (row) => sourceByKey(row.source_key)?.commodity ?? "—",
                },
                {
                  id: "status",
                  header: "Status",
                  sortValue: (row) => row.status,
                  cell: (row) => <StatusPill tone={toneForStatus(row.status)}>{row.status}</StatusPill>,
                },
                {
                  id: "score",
                  header: "Freshness",
                  align: "right",
                  sortValue: (row) => row.freshness_score,
                  cell: (row) => <span className="pc-num">{row.freshness_score}/100</span>,
                },
                {
                  id: "updated",
                  header: "Published update",
                  sortValue: (row) => row.last_update,
                  cell: (row) => (row.last_update ? new Date(row.last_update).toLocaleString("en-GB") : "—"),
                },
                {
                  id: "unit",
                  header: "Unit",
                  cell: (row) => sourceByKey(row.source_key)?.unit ?? "Not supplied",
                },
              ]}
            />
          </div>
          {selected && (
            <aside className="pc-detail" aria-label="Dataset detail">
              <div className="pc-detail-bar">
                <h2>{selected.label}</h2>
                <button type="button" className="pc-btn" onClick={() => setSelectedKey(null)}>
                  Close
                </button>
              </div>
              <dl className="pc-detail-list">
                <div>
                  <dt>Commodity</dt>
                  <dd>{selectedMeta?.commodity ?? "—"}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{selected.status}</dd>
                </div>
                <div>
                  <dt>Reporting period</dt>
                  <dd>{selected.last_update ? new Date(selected.last_update).toLocaleString("en-GB") : "Not supplied"}</dd>
                </div>
                <div>
                  <dt>Unit</dt>
                  <dd>{selectedMeta?.unit ?? "Not supplied by this feed"}</dd>
                </div>
                <div>
                  <dt>Freshness score</dt>
                  <dd className="pc-num">{selected.freshness_score}/100</dd>
                </div>
                <div>
                  <dt>Expected interval</dt>
                  <dd>{selected.expected_interval_minutes >= 1440 ? "Daily" : `${selected.expected_interval_minutes} minutes`}</dd>
                </div>
                <div>
                  <dt>Source</dt>
                  <dd>
                    {selectedMeta ? (
                      <a href={selectedMeta.href} target="_blank" rel="noopener noreferrer">
                        Published NUPRC page
                      </a>
                    ) : (
                      "—"
                    )}
                  </dd>
                </div>
              </dl>
              {selectedMeta?.pageNote && <p className="pc-detail-note">{selectedMeta.pageNote}</p>}
            </aside>
          )}
        </div>
      )}

      <section className="pc-card">
        <div className="pc-card-h">
          <h2>Workspace submission notes</h2>
        </div>
        <div className="pc-card-b">
          <GapNote>These notes are workspace reminders. They are not a published NUPRC snapshot and have no page or table reference.</GapNote>
          <SortTable
            rows={[
              { name: "Monthly Oil & Gas Report", deadline: "15 Feb 2026", status: "On track", version: "v2026.1" },
              { name: "Quarterly Concession Snapshot", deadline: "31 Mar 2026", status: "On track", version: "v2026.Q1" },
            ]}
            caption="Workspace submission notes"
            rowKey={(row) => row.name}
            columns={[
              { id: "name", header: "Name", sortValue: (row) => row.name, cell: (row) => row.name },
              { id: "deadline", header: "Deadline", sortValue: (row) => row.deadline, cell: (row) => row.deadline },
              { id: "version", header: "Version", cell: (row) => row.version },
              { id: "status", header: "Status", cell: (row) => <StatusPill tone={toneForStatus(row.status)}>{row.status}</StatusPill> },
            ]}
          />
        </div>
      </section>

      <section className="pc-card">
        <div className="pc-card-h">
          <h2>Publication pages</h2>
        </div>
        <div className="pc-card-b">
          <ul>
            {PUBLIC_SOURCES.map((source) => (
              <li key={source.key}>
                <a href={source.href} target="_blank" rel="noopener noreferrer">
                  {source.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  );
}
