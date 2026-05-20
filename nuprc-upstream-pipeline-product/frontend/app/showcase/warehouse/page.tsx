"use client";

import { useEffect, useState } from "react";
import { backendGet } from "@/lib/backend";

type TableInfo = {
  schema: string;
  table_name: string;
  full_name: string;
  row_count: number;
  layer: string;
  error?: string;
};

type WarehouseResponse = {
  ok: boolean;
  tables: TableInfo[];
};

function TableSection({ title, tables, accent }: { title: string; tables: TableInfo[]; accent: string }) {
  return (
    <div style={{ marginBottom: 32 }}>
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <div style={{ display: "grid", gap: 12 }}>
        {tables.length === 0 ? (
          <div style={{ color: "#666", fontSize: 14 }}>No tables yet.</div>
        ) : (
          tables.map((table) => (
            <div
              key={table.full_name}
              style={{
                padding: 16,
                border: "1px solid #eee",
                borderRadius: 8,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <div style={{ fontWeight: 600 }}>{table.table_name}</div>
                <div style={{ fontSize: 12, color: "#666" }}>{table.full_name}</div>
              </div>
              <div style={{ fontSize: 24, fontWeight: 900, color: accent }}>{table.row_count.toLocaleString()}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default function Warehouse() {
  const [data, setData] = useState<WarehouseResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [showEmpty, setShowEmpty] = useState(false);

  useEffect(() => {
    const q = showEmpty ? "?non_empty=false" : "";
    backendGet<WarehouseResponse>(`/warehouse/tables${q}`)
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, [showEmpty]);

  const metaTables = data?.tables.filter((t) => t.layer === "meta") || [];
  const bronzeTables = data?.tables.filter((t) => t.layer === "bronze") || [];
  const silverTables = data?.tables.filter((t) => t.layer === "silver") || [];
  const warehouseTables = data?.tables.filter((t) => t.layer === "warehouse") || [];

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Datawarehouse Tables</h2>
      <p style={{ color: "#666", fontSize: 14 }}>
        PostgreSQL schemas: meta, bronze, silver, warehouse. Showing tables with data only (legacy{" "}
        <code>etl_*</code> bronze tables and silver facts). Empty Postgres-first placeholders are hidden.
      </p>
      <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16, fontSize: 14 }}>
        <input type="checkbox" checked={showEmpty} onChange={(e) => setShowEmpty(e.target.checked)} />
        Show empty tables
      </label>

      {err && <div style={{ padding: 12, border: "1px solid #f00", borderRadius: 8, marginBottom: 16 }}>Error: {err}</div>}
      {!data && !err && <div>Loading…</div>}

      {data && (
        <>
          <TableSection title="Meta (Pipeline & Registry)" tables={metaTables} accent="#6366f1" />
          <TableSection title="Bronze (Raw JSONB)" tables={bronzeTables} accent="#f2a36b" />
          <TableSection title="Silver (Standardized)" tables={silverTables} accent="#2563eb" />
          <TableSection title="Warehouse (Reporting)" tables={warehouseTables} accent="#0a0" />
        </>
      )}
    </div>
  );
}
