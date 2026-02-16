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

export default function Warehouse() {
  const [data, setData] = useState<WarehouseResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    backendGet<WarehouseResponse>("/warehouse/tables")
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  const bronzeTables = data?.tables.filter((t) => t.layer === "bronze") || [];
  const warehouseTables = data?.tables.filter((t) => t.layer === "warehouse") || [];

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Datawarehouse Tables</h2>

      {err && <div style={{ padding: 12, border: "1px solid #f00", borderRadius: 8, marginBottom: 16 }}>Error: {err}</div>}
      {!data && !err && <div>Loading…</div>}

      {data && (
        <>
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ marginTop: 0 }}>Bronze Layer (Raw Data)</h3>
            <div style={{ display: "grid", gap: 12 }}>
              {bronzeTables.map((table) => (
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
                  <div style={{ fontSize: 24, fontWeight: 900, color: "#f2a36b" }}>
                    {table.row_count.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3>Warehouse Layer (Dimensional Model)</h3>
            <div style={{ display: "grid", gap: 12 }}>
              {warehouseTables.map((table) => (
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
                  <div style={{ fontSize: 24, fontWeight: 900, color: "#0a0" }}>
                    {table.row_count.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
