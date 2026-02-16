"use client";

import { useEffect, useState } from "react";
import { backendGet, backendPost } from "@/lib/backend";

type DownloadedFile = {
  id: number;
  source_id: string;
  source_name: string;
  file_url: string;
  file_path: string | null;
  filename: string;
  file_sha256: string;
  file_type: string;
  file_size: number | null;
  report_period: string | null;
  download_status: string;
  downloaded_at: string;
  processed_at: string | null;
  run_id: string | null;
  bronze_loaded: boolean;
  bronze_table: string | null;
  bronze_rows: number;
  silver_loaded: boolean;
  silver_table: string | null;
  silver_rows: number;
  warehouse_loaded: boolean;
  warehouse_tables: string[] | null;
  warehouse_rows: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

type FilesResponse = {
  ok: boolean;
  total: number;
  limit: number;
  offset: number;
  files: DownloadedFile[];
};

type AvailableTable = {
  id: number;
  schema_name: string;
  table_name: string;
  full_name: string;
  table_type: string;
  source_id: string | null;
  description: string | null;
  row_count: number;
  last_updated: string | null;
  created_at: string;
};

type TablesResponse = {
  ok: boolean;
  tables: AvailableTable[];
};

type TableDetails = {
  ok: boolean;
  table: AvailableTable;
  actual_row_count: number;
  columns: Array<{
    column_name: string;
    data_type: string;
    is_nullable: string;
    column_default: string | null;
  }>;
};

type CatalogSummary = {
  ok: boolean;
  file_statistics: Array<{
    download_status: string;
    count: number;
    bronze_count: number;
    silver_count: number;
    warehouse_count: number;
  }>;
  source_statistics: Array<{
    source_id: string;
    source_name: string;
    total_files: number;
    downloaded: number;
    failed: number;
    duplicates: number;
    total_bronze_rows: number;
    total_silver_rows: number;
    total_warehouse_rows: number;
  }>;
  table_statistics: Array<{
    table_type: string;
    table_count: number;
    total_rows: number;
  }>;
};

export default function CatalogPage() {
  const [activeTab, setActiveTab] = useState<"summary" | "files" | "tables">("summary");
  const [summary, setSummary] = useState<CatalogSummary | null>(null);
  const [files, setFiles] = useState<FilesResponse | null>(null);
  const [tables, setTables] = useState<TablesResponse | null>(null);
  const [selectedTable, setSelectedTable] = useState<TableDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [tableTypeFilter, setTableTypeFilter] = useState<string>("");

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [activeTab, sourceFilter, statusFilter, tableTypeFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (activeTab === "summary") {
        const data = await backendGet<CatalogSummary>("/catalog/summary");
        setSummary(data);
      } else if (activeTab === "files") {
        let url = "/catalog/files?limit=100";
        if (sourceFilter) url += `&source_id=${sourceFilter}`;
        if (statusFilter) url += `&status=${statusFilter}`;
        const data = await backendGet<FilesResponse>(url);
        setFiles(data);
      } else if (activeTab === "tables") {
        let url = "/catalog/tables";
        if (tableTypeFilter) url += `?table_type=${tableTypeFilter}`;
        if (sourceFilter) url += `${tableTypeFilter ? "&" : "?"}source_id=${sourceFilter}`;
        const data = await backendGet<TablesResponse>(url);
        setTables(data);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const loadTableDetails = async (schema: string, table: string) => {
    try {
      const data = await backendGet<TableDetails>(`/catalog/tables/${schema}/${table}`);
      setSelectedTable(data);
    } catch (e) {
      setError(String(e));
    }
  };

  const refreshCatalog = async () => {
    try {
      await backendPost("/catalog/refresh");
      loadData();
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ marginTop: 0 }}>Data Catalog</h2>
        <button
          onClick={refreshCatalog}
          style={{
            padding: "8px 16px",
            fontSize: 14,
            fontWeight: 600,
            backgroundColor: "#f2a36b",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            cursor: "pointer",
          }}
        >
          🔄 Refresh Catalog
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24, borderBottom: "2px solid #eee" }}>
        {(["summary", "files", "tables"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab);
              setSelectedTable(null);
            }}
            style={{
              padding: "12px 24px",
              fontSize: 14,
              fontWeight: 600,
              backgroundColor: activeTab === tab ? "#f2a36b" : "transparent",
              color: activeTab === tab ? "#fff" : "#666",
              border: "none",
              borderBottom: activeTab === tab ? "3px solid #f2a36b" : "3px solid transparent",
              cursor: "pointer",
              textTransform: "capitalize",
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {error && (
        <div style={{ padding: 12, border: "1px solid #f00", borderRadius: 8, marginBottom: 16, backgroundColor: "#fee" }}>
          Error: {error}
        </div>
      )}

      {loading && <div>Loading...</div>}

      {/* Summary Tab */}
      {activeTab === "summary" && summary && (
        <div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: 16, marginBottom: 24 }}>
            {summary.file_statistics.map((stat) => (
              <div key={stat.download_status} style={{ padding: 16, border: "1px solid #eee", borderRadius: 12 }}>
                <div style={{ fontSize: 12, color: "#666", marginBottom: 8 }}>{stat.download_status.toUpperCase()}</div>
                <div style={{ fontSize: 32, fontWeight: 900 }}>{stat.count}</div>
                <div style={{ fontSize: 12, color: "#666", marginTop: 8 }}>
                  Bronze: {stat.bronze_count} | Silver: {stat.silver_count} | Warehouse: {stat.warehouse_count}
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginBottom: 24 }}>
            <h3>Source Statistics</h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ backgroundColor: "#f9f9f9" }}>
                    <th style={{ padding: 12, textAlign: "left", border: "1px solid #eee" }}>Source</th>
                    <th style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>Total Files</th>
                    <th style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>Downloaded</th>
                    <th style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>Failed</th>
                    <th style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>Duplicates</th>
                    <th style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>Bronze Rows</th>
                    <th style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>Silver Rows</th>
                    <th style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>Warehouse Rows</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.source_statistics.map((stat) => (
                    <tr key={stat.source_id}>
                      <td style={{ padding: 12, border: "1px solid #eee" }}>{stat.source_name}</td>
                      <td style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>{stat.total_files}</td>
                      <td style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>{stat.downloaded}</td>
                      <td style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>{stat.failed}</td>
                      <td style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>{stat.duplicates}</td>
                      <td style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>
                        {stat.total_bronze_rows.toLocaleString()}
                      </td>
                      <td style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>
                        {stat.total_silver_rows.toLocaleString()}
                      </td>
                      <td style={{ padding: 12, textAlign: "right", border: "1px solid #eee" }}>
                        {stat.total_warehouse_rows.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h3>Table Statistics</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
              {summary.table_statistics.map((stat) => (
                <div key={stat.table_type} style={{ padding: 16, border: "1px solid #eee", borderRadius: 12 }}>
                  <div style={{ fontSize: 12, color: "#666", marginBottom: 8 }}>{stat.table_type.toUpperCase()}</div>
                  <div style={{ fontSize: 24, fontWeight: 900 }}>{stat.table_count}</div>
                  <div style={{ fontSize: 12, color: "#666", marginTop: 8 }}>
                    {stat.total_rows.toLocaleString()} rows
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Files Tab */}
      {activeTab === "files" && (
        <div>
          <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #eee" }}
            >
              <option value="">All Sources</option>
              <option value="oil_production_status">Oil Production</option>
              <option value="gas_production_status">Gas Production</option>
              <option value="concession_situation">Concession</option>
              <option value="rig_disposition">Rig Disposition</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #eee" }}
            >
              <option value="">All Status</option>
              <option value="downloaded">Downloaded</option>
              <option value="failed">Failed</option>
              <option value="duplicate">Duplicate</option>
            </select>
          </div>

          {files && (
            <div>
              <div style={{ marginBottom: 16, fontSize: 14, color: "#666" }}>
                Showing {files.files.length} of {files.total} files
              </div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr style={{ backgroundColor: "#f9f9f9" }}>
                      <th style={{ padding: 8, textAlign: "left", border: "1px solid #eee" }}>Source</th>
                      <th style={{ padding: 8, textAlign: "left", border: "1px solid #eee" }}>Filename</th>
                      <th style={{ padding: 8, textAlign: "left", border: "1px solid #eee" }}>Status</th>
                      <th style={{ padding: 8, textAlign: "left", border: "1px solid #eee" }}>Bronze</th>
                      <th style={{ padding: 8, textAlign: "left", border: "1px solid #eee" }}>Silver</th>
                      <th style={{ padding: 8, textAlign: "left", border: "1px solid #eee" }}>Warehouse</th>
                      <th style={{ padding: 8, textAlign: "right", border: "1px solid #eee" }}>Rows</th>
                      <th style={{ padding: 8, textAlign: "left", border: "1px solid #eee" }}>Downloaded</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.files.map((file) => (
                      <tr key={file.id}>
                        <td style={{ padding: 8, border: "1px solid #eee" }}>{file.source_name}</td>
                        <td style={{ padding: 8, border: "1px solid #eee", maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis" }}>
                          {file.filename}
                        </td>
                        <td style={{ padding: 8, border: "1px solid #eee" }}>
                          <span
                            style={{
                              padding: "2px 8px",
                              borderRadius: 4,
                              fontSize: 10,
                              backgroundColor:
                                file.download_status === "downloaded"
                                  ? "#d4edda"
                                  : file.download_status === "failed"
                                  ? "#f8d7da"
                                  : "#fff3cd",
                              color:
                                file.download_status === "downloaded"
                                  ? "#155724"
                                  : file.download_status === "failed"
                                  ? "#721c24"
                                  : "#856404",
                            }}
                          >
                            {file.download_status}
                          </span>
                        </td>
                        <td style={{ padding: 8, border: "1px solid #eee", textAlign: "center" }}>
                          {file.bronze_loaded ? "✓" : "—"}
                        </td>
                        <td style={{ padding: 8, border: "1px solid #eee", textAlign: "center" }}>
                          {file.silver_loaded ? "✓" : "—"}
                        </td>
                        <td style={{ padding: 8, border: "1px solid #eee", textAlign: "center" }}>
                          {file.warehouse_loaded ? "✓" : "—"}
                        </td>
                        <td style={{ padding: 8, border: "1px solid #eee", textAlign: "right" }}>
                          {file.warehouse_rows > 0
                            ? file.warehouse_rows.toLocaleString()
                            : file.silver_rows > 0
                            ? file.silver_rows.toLocaleString()
                            : file.bronze_rows > 0
                            ? file.bronze_rows.toLocaleString()
                            : "—"}
                        </td>
                        <td style={{ padding: 8, border: "1px solid #eee", fontSize: 11 }}>
                          {new Date(file.downloaded_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tables Tab */}
      {activeTab === "tables" && (
        <div>
          <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
            <select
              value={tableTypeFilter}
              onChange={(e) => setTableTypeFilter(e.target.value)}
              style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #eee" }}
            >
              <option value="">All Types</option>
              <option value="bronze">Bronze</option>
              <option value="silver">Silver</option>
              <option value="warehouse">Warehouse</option>
              <option value="catalog">Catalog</option>
            </select>
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #eee" }}
            >
              <option value="">All Sources</option>
              <option value="oil_production_status">Oil Production</option>
              <option value="gas_production_status">Gas Production</option>
              <option value="concession_situation">Concession</option>
              <option value="rig_disposition">Rig Disposition</option>
            </select>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            <div>
              {tables && (
                <div>
                  <div style={{ marginBottom: 16, fontSize: 14, color: "#666" }}>
                    {tables.tables.length} tables
                  </div>
                  <div style={{ maxHeight: 600, overflowY: "auto" }}>
                    {tables.tables.map((table) => (
                      <div
                        key={table.id}
                        onClick={() => loadTableDetails(table.schema_name, table.table_name)}
                        style={{
                          padding: 12,
                          marginBottom: 8,
                          border: "1px solid #eee",
                          borderRadius: 8,
                          cursor: "pointer",
                          backgroundColor: selectedTable?.table.id === table.id ? "#f0f0f0" : "#fff",
                        }}
                      >
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>{table.full_name}</div>
                        <div style={{ fontSize: 12, color: "#666" }}>
                          {table.table_type} • {table.row_count.toLocaleString()} rows
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {selectedTable && (
              <div style={{ padding: 16, border: "1px solid #eee", borderRadius: 12, backgroundColor: "#f9f9f9" }}>
                <h3 style={{ marginTop: 0 }}>{selectedTable.table.full_name}</h3>
                <div style={{ marginBottom: 16, fontSize: 14 }}>
                  <div>Type: {selectedTable.table.table_type}</div>
                  <div>Rows: {selectedTable.actual_row_count.toLocaleString()}</div>
                  {selectedTable.table.source_id && <div>Source: {selectedTable.table.source_id}</div>}
                </div>
                <div>
                  <h4 style={{ fontSize: 14 }}>Columns ({selectedTable.columns.length})</h4>
                  <div style={{ maxHeight: 400, overflowY: "auto" }}>
                    <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                      <thead>
                        <tr style={{ backgroundColor: "#fff" }}>
                          <th style={{ padding: 8, textAlign: "left", border: "1px solid #ddd" }}>Column</th>
                          <th style={{ padding: 8, textAlign: "left", border: "1px solid #ddd" }}>Type</th>
                          <th style={{ padding: 8, textAlign: "left", border: "1px solid #ddd" }}>Nullable</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedTable.columns.map((col) => (
                          <tr key={col.column_name}>
                            <td style={{ padding: 8, border: "1px solid #ddd" }}>{col.column_name}</td>
                            <td style={{ padding: 8, border: "1px solid #ddd" }}>{col.data_type}</td>
                            <td style={{ padding: 8, border: "1px solid #ddd" }}>{col.is_nullable}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
