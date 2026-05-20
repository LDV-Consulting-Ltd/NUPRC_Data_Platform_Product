export type Feature = {
  name: string;
  description: string;
  href: string;
  tag?: string;
};

export type ApiEndpoint = {
  method: "GET" | "POST";
  path: string;
  summary: string;
};

export const PIPELINE_CAPABILITIES = [
  { name: "Source Discovery", description: "NUPRC publication discovery and health monitoring.", href: "/source-health" },
  { name: "File Acquisition", description: "Automated download and file registry tracking.", href: "/console/pipeline" },
  { name: "OCR & Extraction", description: "Structured extraction from regulatory publications.", href: "/console/bronze" },
  { name: "Bronze Layer", description: "Immutable raw landing zone with provenance.", href: "/console/bronze" },
  { name: "Silver Standardization", description: "Conformed facts and dimensions with fuzzy matching.", href: "/console/silver" },
  { name: "Gold Warehouse", description: "Integrated marts for oil, gas, rig, and concession.", href: "/console/warehouse" },
  { name: "Governance Engine", description: "Metadata registry, drift detection, and auditability.", href: "/governance" },
  { name: "Metadata Registry", description: "Canonical catalog across bronze, silver, and gold.", href: "/catalog" },
  { name: "Data Lineage", description: "End-to-end source-to-product lineage views.", href: "/lineage-explorer" },
  { name: "Schema Drift Detection", description: "Silver-layer drift signals and severity scoring.", href: "/console/schema-drift" },
  { name: "Diagnostics", description: "Run-level failure diagnostics and remediation hints.", href: "/console/diagnostics" },
  { name: "Monitoring", description: "Freshness, SLA, and platform health dashboards.", href: "/console" },
  { name: "APIs", description: "REST surface for pipeline, catalog, and exports.", href: "/docs" },
  { name: "Pipeline Orchestration", description: "Incremental and full-rebuild orchestration.", href: "/console/pipeline" },
] as const;

export const FEATURES: { section: string; items: Feature[] }[] = [
  {
    section: "Operations",
    items: [
      { name: "Pipeline Control", description: "Run incremental/full pipeline, track lifecycle steps.", href: "/console/pipeline", tag: "Primary" },
      { name: "Run History", description: "Timeline of pipeline runs from admin and meta stores.", href: "/console/runs" },
      { name: "Data Quality", description: "Quality rules and validation summary.", href: "/data-quality" },
      { name: "Source Health", description: "Bronze-layer volume and freshness per NUPRC source.", href: "/source-health" },
    ],
  },
  {
    section: "Governance & intelligence",
    items: [
      { name: "Data Catalog", description: "Browse bronze, silver, and gold tables with row counts.", href: "/catalog" },
      { name: "Lineage Explorer", description: "Source → bronze → silver → warehouse lineage.", href: "/lineage-explorer" },
      { name: "Regulatory Exports", description: "Submission datasets, audit bundles, snapshots.", href: "/regulatory" },
      { name: "ETL Diagrams", description: "Mermaid data-model and pipeline flow diagrams.", href: "/showcase/diagrams" },
    ],
  },
];

export const API_GROUPS: { title: string; endpoints: ApiEndpoint[] }[] = [
  {
    title: "Pipeline (v1)",
    endpoints: [
      { method: "GET", path: "/v1/pipeline/platform/status", summary: "Executive platform status" },
      { method: "POST", path: "/v1/pipeline/run?mode=incremental|full_rebuild", summary: "Postgres-first pipeline run" },
      { method: "GET", path: "/v1/pipeline/runs/{run_id}", summary: "Run detail with lifecycle steps" },
      { method: "GET", path: "/v1/pipeline/sources/health", summary: "Per-source bronze health" },
    ],
  },
  {
    title: "Governance",
    endpoints: [
      { method: "GET", path: "/v1/governance/summary", summary: "Metadata, lineage, drift, table health" },
    ],
  },
  {
    title: "Catalog & regulatory",
    endpoints: [
      { method: "GET", path: "/catalog/tables?layer=bronze|silver|gold", summary: "Canonical tables by layer" },
      { method: "GET", path: "/regulatory/exports", summary: "Regulatory export catalog" },
      { method: "GET", path: "/regulatory/download/{export_id}", summary: "CSV or ZIP download" },
    ],
  },
];

export const JSON_EXAMPLES = [
  {
    title: "Platform status",
    path: "GET /v1/pipeline/platform/status",
    body: `{
  "ok": true,
  "system_health": "healthy",
  "records_today": 12480,
  "last_successful_run": {
    "run_id": "pg-2026-05-18T08-12-00",
    "status": "success",
    "started_at": "2026-05-18T08:12:00Z"
  }
}`,
  },
  {
    title: "Start pipeline run",
    path: "POST /v1/pipeline/run?mode=incremental",
    body: `{
  "ok": true,
  "run_id": "pg-2026-05-18T09-00-00"
}`,
  },
  {
    title: "Governance summary",
    path: "GET /v1/governance/summary",
    body: `{
  "ok": true,
  "lineage_coverage_pct": 88,
  "schema_drift_high_count": 0,
  "metadata": {
    "file_registry_count": 42,
    "pipeline_runs": 156,
    "tables_with_data": 24
  }
}`,
  },
];

export const SOLUTION_PILLARS = [
  {
    title: "Upstream regulatory intelligence",
    body: "Unify NUPRC oil, gas, rig, and concession datasets into a governed intelligence fabric.",
  },
  {
    title: "Governance automation",
    body: "Metadata registry, lineage coverage, schema drift, and audit-ready exports by design.",
  },
  {
    title: "Operational oversight",
    body: "Pipeline orchestration, diagnostics, freshness monitoring, and executive dashboards.",
  },
  {
    title: "Data product strategy",
    body: "Medallion architecture from raw acquisition through warehouse data products.",
  },
  {
    title: "DAMA + IIBA-CPOA alignment",
    body: "Cataloging, quality, lineage, and business-outcome framing for upstream stakeholders.",
  },
  {
    title: "Business value",
    body: "Faster regulatory readiness, concession visibility, and production intelligence for operators and regulators.",
  },
];
