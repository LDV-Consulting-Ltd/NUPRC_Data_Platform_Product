"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import V2Header from "../components/V2Header";
import { backendGet, backendDownload } from "@/lib/backend";

type RegulatoryExport = {
  export_id: string;
  name: string;
  category: "submission" | "bundle" | "snapshot";
  version?: string;
  tables: string[];
  row_count: number;
  size_label: string;
  download_url: string;
};

const FALLBACK_EXPORTS: RegulatoryExport[] = [
  {
    export_id: "submission_monthly_oil_gas",
    name: "Monthly Oil & Gas Report",
    category: "submission",
    version: "v2026.1",
    tables: ["fact_oil_production", "fact_gas_production"],
    row_count: 0,
    size_label: "—",
    download_url: "/regulatory/download/submission_monthly_oil_gas",
  },
  {
    export_id: "submission_quarterly_concession",
    name: "Quarterly Concession Snapshot",
    category: "submission",
    version: "v2026.Q1",
    tables: ["fact_concession_status"],
    row_count: 0,
    size_label: "—",
    download_url: "/regulatory/download/submission_quarterly_concession",
  },
  {
    export_id: "bundle_audit_dec_2025",
    name: "Audit export bundle — Dec 2025",
    category: "bundle",
    tables: ["fact_oil_production", "fact_gas_production", "fact_rig_disposition", "fact_concession_status"],
    row_count: 0,
    size_label: "—",
    download_url: "/regulatory/download/bundle_audit_dec_2025",
  },
  {
    export_id: "snapshot_v2026_1",
    name: "Regulatory snapshot v2026.1",
    category: "snapshot",
    version: "v2026.1",
    tables: ["fact_oil_production", "fact_gas_production", "fact_rig_disposition"],
    row_count: 0,
    size_label: "—",
    download_url: "/regulatory/download/snapshot_v2026_1",
  },
];

export default function RegulatoryPage() {
  const [exports, setExports] = useState<RegulatoryExport[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const loadExports = useCallback(() => {
    setLoading(true);
    setErr(null);
    setOffline(false);
    backendGet<{ ok: boolean; exports: RegulatoryExport[] }>("/regulatory/exports")
      .then((data) => setExports(data.exports ?? []))
      .catch((e) => {
        setErr(String(e));
        setOffline(true);
        setExports(FALLBACK_EXPORTS);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadExports();
  }, [loadExports]);

  const submissions = exports.filter((e) => e.category === "submission");
  const bundles = exports.filter((e) => e.category === "bundle");
  const snapshots = exports.filter((e) => e.category === "snapshot");

  const handleDownload = async (item: RegulatoryExport) => {
    if (offline) return;
    setDownloadingId(item.export_id);
    setErr(null);
    try {
      const ext = item.tables.length > 1 ? "zip" : "csv";
      await backendDownload(item.download_url, `${item.export_id}.${ext}`);
    } catch (e) {
      setErr(String(e));
    } finally {
      setDownloadingId(null);
    }
  };

  const DownloadButton = ({ item }: { item: RegulatoryExport }) => (
    <button
      type="button"
      disabled={offline || downloadingId === item.export_id}
      onClick={() => handleDownload(item)}
      className="px-3 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold disabled:opacity-50"
    >
      {downloadingId === item.export_id ? "Downloading…" : "Download"}
    </button>
  );

  const Skeleton = () => (
    <motion.div className="space-y-3" aria-hidden>
      {[1, 2, 3].map((n) => (
        <div key={n} className="h-20 rounded-xl bg-slate-100 animate-pulse" />
      ))}
    </motion.div>
  );

  return (
    <>
      <V2Header
        title="Regulatory Views"
        subtitle="Pre-built submission datasets, audit export bundles, regulatory snapshot versioning"
      />
      <motion.div
        className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        {offline && (
          <motion.div className="p-4 rounded-xl border border-amber-200 bg-amber-50 text-sm text-amber-900">
            <p className="font-semibold">Backend unavailable — showing catalog preview only.</p>
            <p className="mt-1 text-amber-800/90">
              Start the API server and ensure PostgreSQL is connected, then{" "}
              <button type="button" onClick={loadExports} className="underline font-semibold">
                retry
              </button>
              . Downloads are disabled until the API responds.
            </p>
            <Link href="/console/pipeline" className="inline-block mt-2 text-teal-800 font-semibold hover:underline">
              Open Pipeline Control →
            </Link>
          </motion.div>
        )}

        {loading && <div className="text-sm text-slate-500">Loading export catalog…</div>}
        {err && !offline && (
          <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-sm text-red-700 flex flex-wrap items-center justify-between gap-3">
            <span>{err}</span>
            <button type="button" onClick={loadExports} className="px-3 py-1.5 rounded-lg bg-red-100 font-semibold">
              Retry
            </button>
          </div>
        )}

        <section className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <motion.div
            className="text-sm text-slate-500"
            animate={{ opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 2.8, repeat: Infinity }}
          >
            Live from silver layer
          </motion.div>
          <div className="text-xl font-bold mt-1 text-[#0f2744]">Submission datasets</div>
          <p className="text-xs text-slate-500 mt-1">Silver-layer tables exported as CSV or ZIP.</p>
          <div className="mt-4 space-y-3">
            {loading ? (
              <Skeleton />
            ) : (
              <>
                {submissions.length === 0 && (
                  <motion.div className="text-sm text-slate-500" animate={{ opacity: [0.6, 1, 0.6] }} transition={{ duration: 2.5, repeat: Infinity }}>
                    No submission exports configured.
                  </motion.div>
                )}
                {submissions.map((s) => (
                  <div
                    key={s.export_id}
                    className="rounded-xl border border-slate-200 p-4 flex items-center justify-between gap-4"
                  >
                    <div>
                      <div className="font-semibold">{s.name}</div>
                      <div className="text-sm text-slate-500">
                        Version: {s.version ?? "—"} · {s.row_count.toLocaleString()} rows · {s.size_label}
                      </div>
                      <motion.div
                        className="text-xs text-slate-400 mt-1"
                        animate={{ opacity: [0.65, 1, 0.65] }}
                        transition={{ duration: 2.4, repeat: Infinity }}
                      >
                        Tables: {s.tables.join(", ")}
                      </motion.div>
                    </div>
                    <motion.div className="flex items-center gap-3 shrink-0" whileHover={{ scale: 1.02 }}>
                      <span className="px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold">
                        {s.row_count > 0 ? "Ready" : "Empty"}
                      </span>
                      <DownloadButton item={s} />
                    </motion.div>
                  </div>
                ))}
              </>
            )}
          </div>
        </section>

        <section className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="font-bold text-[#0f2744]">Audit export bundles</div>
          <p className="text-xs text-slate-500 mt-1">Multi-table ZIP archives for audit and compliance.</p>
          <motion.div className="mt-4 space-y-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
            {loading ? (
              <Skeleton />
            ) : bundles.length === 0 ? (
              <div className="text-sm text-slate-500">No audit bundles available.</div>
            ) : (
              bundles.map((b) => (
                <motion.div
                  key={b.export_id}
                  className="rounded-xl border border-slate-200 p-4 flex items-center justify-between gap-4"
                  whileHover={{ borderColor: "rgba(20,184,166,0.35)" }}
                >
                  <motion.div animate={{ opacity: [0.88, 1, 0.88] }} transition={{ duration: 2.6, repeat: Infinity }}>
                    <motion.div className="font-semibold">{b.name}</motion.div>
                    <div className="text-sm text-slate-500">
                      {b.row_count.toLocaleString()} rows · {b.size_label} · {b.tables.length} tables
                    </div>
                  </motion.div>
                  <DownloadButton item={b} />
                </motion.div>
              ))
            )}
          </motion.div>
        </section>

        <section className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="font-bold text-[#0f2744]">Regulatory snapshot versioning</div>
          <div className="text-sm text-slate-600 mt-1">Versioned snapshots for compliance and audit.</div>
          <div className="mt-4 space-y-3">
            {loading ? (
              <Skeleton />
            ) : snapshots.length === 0 ? (
              <div className="text-sm text-slate-500">No regulatory snapshots available.</div>
            ) : (
              snapshots.map((snap, i) => (
                <div
                  key={snap.export_id}
                  className="rounded-xl border border-slate-200 p-4 flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span
                      className={`px-3 py-1.5 rounded-full text-sm shrink-0 ${
                        i === 0 ? "bg-teal-50 text-teal-800 font-semibold" : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {snap.version} {i === 0 ? "(current)" : ""}
                    </span>
                    <div className="text-sm text-slate-500 truncate">
                      {snap.row_count.toLocaleString()} rows · {snap.tables.join(", ")}
                    </div>
                  </div>
                  <DownloadButton item={snap} />
                </div>
              ))
            )}
          </div>
        </section>
      </motion.div>
    </>
  );
}
