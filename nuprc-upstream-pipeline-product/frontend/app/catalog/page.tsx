"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { fetchCatalogTables, type CatalogTable } from "@/lib/api";
import { errorMessage, permissionDenied } from "@/lib/page-error";
import { PUBLIC_SOURCES } from "@/lib/public-sources";
import {
  CountLabel,
  GapNote,
  LoadingRows,
  PageHeader,
  PermissionState,
  SortTable,
  StateBlock,
} from "../components/console/ui";

type Layer = "bronze" | "silver" | "gold";

function readLayer(value: string | null): Layer {
  if (value === "silver" || value === "gold" || value === "bronze") return value;
  return "bronze";
}

export default function CatalogPage() {
  const params = useSearchParams();
  const router = useRouter();
  const layer = readLayer(params.get("layer"));
  const [result, setResult] = useState<{ layer: Layer; tables: CatalogTable[]; error: unknown } | null>(null);
  const [selected, setSelected] = useState<string | null>(params.get("table"));

  useEffect(() => {
    let cancelled = false;
    fetchCatalogTables(layer)
      .then((res) => {
        if (!cancelled) setResult({ layer, tables: res.tables, error: null });
      })
      .catch((err) => {
        if (!cancelled) setResult({ layer, tables: [], error: err });
      });
    return () => {
      cancelled = true;
    };
  }, [layer]);

  const loading = result?.layer !== layer;
  const tables = result?.layer === layer ? result.tables : [];
  const error = result?.layer === layer ? result.error : null;

  const setLayer = (next: Layer) => {
    const query = new URLSearchParams(params.toString());
    query.set("layer", next);
    router.replace(`/catalog?${query.toString()}`);
  };

  const current = tables.find((table) => table.physical_name === selected) ?? null;

  return (
    <>
      <PageHeader
        title="Published Datasets"
        description="Dataset profiles by layer. Bronze is the raw landing, silver is cleaned, and gold is the warehouse."
        actions={
          <div className="pc-actions">
            {(["bronze", "silver", "gold"] as const).map((item) => (
              <button key={item} type="button" className={layer === item ? "pc-btn pc-btn-primary" : "pc-btn"} onClick={() => setLayer(item)}>
                {item}
              </button>
            ))}
          </div>
        }
      />
      {loading && <LoadingRows />}
      {!loading && error != null &&
        (permissionDenied(error) ? (
          <PermissionState />
        ) : (
          <StateBlock tone="error" title="The catalog could not be loaded">
            {errorMessage(error)}
          </StateBlock>
        ))}
      {!loading && error == null && (
        <div className="pc-work">
          <div className="pc-work-main">
            <CountLabel shown={tables.length} total={tables.length} />
            <SortTable
              rows={tables}
              caption={`${layer} catalog tables`}
              rowKey={(row) => row.physical_name}
              selectedKey={current?.physical_name}
              onRow={(row) => setSelected(row.physical_name)}
              empty={<StateBlock tone="empty" title="No tables in this layer" />}
              columns={[
                { id: "name", header: "Dataset", sticky: true, sortValue: (row) => row.display_name, cell: (row) => row.display_name },
                { id: "physical", header: "Physical name", sortValue: (row) => row.physical_name, cell: (row) => row.physical_name },
                {
                  id: "rows",
                  header: "Rows",
                  align: "right",
                  sortValue: (row) => row.row_count ?? 0,
                  cell: (row) => <span className="pc-num">{(row.row_count ?? 0).toLocaleString("en-GB")}</span>,
                },
                {
                  id: "updated",
                  header: "Updated",
                  sortValue: (row) => row.last_updated,
                  cell: (row) => row.last_updated ?? "—",
                },
              ]}
            />
            <GapNote>Row counts are catalog records. They are not a substitute for the unit printed on the source report.</GapNote>
            <p>
              <Link href={`/showcase/catalog?schema=${layer}${selected ? `&table=${selected}` : ""}`}>
                Open the isolated legacy catalog fixture
              </Link>
            </p>
          </div>
          {current && (
            <aside className="pc-detail" aria-label="Dataset profile">
              <div className="pc-detail-bar">
                <h2>{current.display_name}</h2>
                <button type="button" className="pc-btn" onClick={() => setSelected(null)}>
                  Close
                </button>
              </div>
              <dl className="pc-detail-list">
                <div>
                  <dt>Physical name</dt>
                  <dd>{current.physical_name}</dd>
                </div>
                <div>
                  <dt>Layer</dt>
                  <dd>{layer}</dd>
                </div>
                <div>
                  <dt>Rows</dt>
                  <dd className="pc-num">{(current.row_count ?? 0).toLocaleString("en-GB")}</dd>
                </div>
                <div>
                  <dt>Updated</dt>
                  <dd>{current.last_updated ?? "Not supplied"}</dd>
                </div>
                <div>
                  <dt>Subject</dt>
                  <dd>{current.subject_area ?? "Not supplied"}</dd>
                </div>
                <div>
                  <dt>Grain</dt>
                  <dd>{current.grain ?? "Not supplied"}</dd>
                </div>
                <div>
                  <dt>Description</dt>
                  <dd>{current.description || "Not supplied"}</dd>
                </div>
              </dl>
              <p className="pc-detail-note">Data contract, owner, and a lineage drawing are not returned on this catalog payload.</p>
            </aside>
          )}
        </div>
      )}
      <section className="pc-card">
        <div className="pc-card-h">
          <h2>Source pages for these datasets</h2>
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
