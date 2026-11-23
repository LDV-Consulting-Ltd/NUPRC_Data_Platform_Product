"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useSourcesHealth } from "@/hooks/useSourcesHealth";
import { errorMessage, permissionDenied } from "@/lib/page-error";
import { NUPRC_REPORTS, sourceByKey } from "@/lib/public-sources";
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

export default function SourceHealthPage() {
  const params = useSearchParams();
  const initial = params.get("source");
  const [selectedKey, setSelectedKey] = useState<string | null>(initial);
  const [query, setQuery] = useState(params.get("q") ?? "");
  const health = useSourcesHealth();

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (health.data ?? []).filter((source) => {
      if (!needle) return true;
      const meta = sourceByKey(source.source_key);
      return `${source.label} ${source.source_key} ${meta?.commodity ?? ""}`.toLowerCase().includes(needle);
    });
  }, [health.data, query]);

  const selected = (health.data ?? []).find((row) => row.source_key === selectedKey) ?? null;

  return (
    <>
      <PageHeader
        title="Source Reports"
        description="Source availability for the publications this console ingests. Latency, failure rate, and schema drift are not in this payload, so they are not shown as measurements."
        actions={
          <a className="pc-btn" href={NUPRC_REPORTS} target="_blank" rel="noopener noreferrer">
            NUPRC reports
          </a>
        }
      />
      {health.isLoading && <LoadingRows />}
      {health.isError &&
        (permissionDenied(health.error) ? (
          <PermissionState />
        ) : (
          <StateBlock tone="error" title="Source health could not be loaded">
            {errorMessage(health.error)}
          </StateBlock>
        ))}
      {!health.isLoading && !health.isError && (
        <div className="pc-work">
          <div className="pc-work-main">
            <div className="pc-toolbar">
              <label>
                Filter sources
                <input className="pc-field" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Oil, gas, rig, concession" />
              </label>
              <CountLabel shown={rows.length} total={health.data?.length ?? 0} />
            </div>
            <SortTable
              rows={rows}
              caption="NUPRC source health"
              rowKey={(row) => row.source_key}
              selectedKey={selected?.source_key}
              onRow={(row) => setSelectedKey(row.source_key)}
              empty={<StateBlock tone="empty" title="No sources match this filter" />}
              columns={[
                { id: "source", header: "Source", sticky: true, sortValue: (row) => row.label, cell: (row) => row.label },
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
                  id: "report",
                  header: "Published report",
                  cell: (row) => {
                    const meta = sourceByKey(row.source_key);
                    return meta ? (
                      <a href={meta.href} target="_blank" rel="noopener noreferrer">
                        Open source
                      </a>
                    ) : (
                      "—"
                    );
                  },
                },
              ]}
            />
            <GapNote>
              Page or table references are not returned by the health feed. Use the published report link for the source document.
            </GapNote>
            <p>
              <Link href="/showcase/health">Open the isolated legacy source health fixture</Link>
            </p>
          </div>
          {selected && <SourceDetail source={selected} onClose={() => setSelectedKey(null)} />}
        </div>
      )}
    </>
  );
}

function SourceDetail({ source, onClose }: { source: SourceHealthItem; onClose: () => void }) {
  const meta = sourceByKey(source.source_key);
  return (
    <aside className="pc-detail" aria-label="Source detail">
      <div className="pc-detail-bar">
        <h2>{source.label}</h2>
        <button type="button" className="pc-btn" onClick={onClose}>
          Close
        </button>
      </div>
      <dl className="pc-detail-list">
        <div>
          <dt>Commodity</dt>
          <dd>{meta?.commodity ?? "—"}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{source.status}</dd>
        </div>
        <div>
          <dt>Last update</dt>
          <dd>{source.last_update ? new Date(source.last_update).toLocaleString("en-GB") : "Not supplied"}</dd>
        </div>
        <div>
          <dt>Unit</dt>
          <dd>{meta?.unit ?? "Not supplied"}</dd>
        </div>
        <div>
          <dt>Expected interval</dt>
          <dd>{source.expected_interval_minutes >= 1440 ? "Daily" : `${source.expected_interval_minutes} minutes`}</dd>
        </div>
        <div>
          <dt>Last error</dt>
          <dd>{source.last_error ?? "None reported"}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>
            {meta ? (
              <a href={meta.href} target="_blank" rel="noopener noreferrer">
                Published report
              </a>
            ) : (
              "—"
            )}
          </dd>
        </div>
      </dl>
    </aside>
  );
}
