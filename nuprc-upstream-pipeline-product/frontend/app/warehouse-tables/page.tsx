"use client";

import { useEffect, useState } from "react";
import { fetchCatalogTables, type CatalogTable } from "@/lib/api";
import { errorMessage, permissionDenied } from "@/lib/page-error";
import { CountLabel, GapNote, LoadingRows, PageHeader, PermissionState, SortTable, StateBlock } from "../components/console/ui";

export default function WarehouseTablesPage() {
  const [tables, setTables] = useState<CatalogTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCatalogTables("gold")
      .then((res) => {
        if (!cancelled) setTables(res.tables);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const current = tables.find((table) => table.physical_name === selected) ?? null;

  return (
    <>
      <PageHeader
        title="Warehouse"
        description="Gold warehouse tables from the catalog. This production view does not open the isolated showcase fixture."
      />
      {loading && <LoadingRows />}
      {!loading && error != null &&
        (permissionDenied(error) ? (
          <PermissionState />
        ) : (
          <StateBlock tone="error" title="Warehouse tables could not be loaded">
            {errorMessage(error)}
          </StateBlock>
        ))}
      {!loading && error == null && (
        <div className="pc-work">
          <div className="pc-work-main">
            <CountLabel shown={tables.length} total={tables.length} />
            <SortTable
              rows={tables}
              caption="Gold warehouse tables"
              rowKey={(row) => row.physical_name}
              selectedKey={current?.physical_name}
              onRow={(row) => setSelected(row.physical_name)}
              empty={<StateBlock tone="empty" title="No gold warehouse tables are registered" />}
              columns={[
                { id: "name", header: "Table", sticky: true, sortValue: (row) => row.display_name, cell: (row) => row.display_name },
                { id: "physical", header: "Physical name", sortValue: (row) => row.physical_name, cell: (row) => row.physical_name },
                {
                  id: "rows",
                  header: "Rows",
                  align: "right",
                  sortValue: (row) => row.row_count ?? 0,
                  cell: (row) => <span className="pc-num">{(row.row_count ?? 0).toLocaleString("en-GB")}</span>,
                },
                { id: "updated", header: "Updated", sortValue: (row) => row.last_updated, cell: (row) => row.last_updated ?? "—" },
              ]}
            />
            <GapNote>The legacy warehouse screen remains at /showcase/warehouse and is not linked from production navigation.</GapNote>
          </div>
          {current && (
            <aside className="pc-detail">
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
                  <dt>Description</dt>
                  <dd>{current.description || "Not supplied"}</dd>
                </div>
                <div>
                  <dt>Grain</dt>
                  <dd>{current.grain ?? "Not supplied"}</dd>
                </div>
              </dl>
            </aside>
          )}
        </div>
      )}
    </>
  );
}
