import V2Header from "../components/V2Header";

export default function RegulatoryPage() {
  const submissions = [
    { name: "Monthly Oil & Gas Report", deadline: "15 Feb 2026", status: "On track", version: "v2026.1" },
    { name: "Quarterly Concession Snapshot", deadline: "31 Mar 2026", status: "On track", version: "v2026.Q1" },
  ];
  const bundles = [
    { name: "Audit export bundle — Dec 2025", created: "01 Jan 2026", size: "124 MB" },
    { name: "Regulatory snapshot — Jan 2026", created: "08 Feb 2026", size: "89 MB" },
  ];

  return (
    <>
      <V2Header
        title="Regulatory Views"
        subtitle="Pre-built submission datasets, audit export bundles, regulatory snapshot versioning"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Submission datasets */}
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="text-sm text-slate-500">Enterprise differentiator</div>
          <div className="text-xl font-bold mt-1">Submission datasets</div>
          <div className="mt-4 space-y-3">
            {submissions.map((s) => (
              <div
                key={s.name}
                className="rounded-xl border border-slate-200 p-4 flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold">{s.name}</div>
                  <div className="text-sm text-slate-500">Deadline: {s.deadline} · Version: {s.version}</div>
                </div>
                <span className="px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold">
                  {s.status}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Audit export bundles */}
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="font-bold">Audit export bundles</div>
          <div className="mt-4 space-y-3">
            {bundles.map((b) => (
              <div
                key={b.name}
                className="rounded-xl border border-slate-200 p-4 flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold">{b.name}</div>
                  <div className="text-sm text-slate-500">Created: {b.created} · {b.size}</div>
                </div>
                <button type="button" className="px-3 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold">
                  Download
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Regulatory snapshot versioning */}
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="font-bold">Regulatory snapshot versioning</div>
          <div className="text-sm text-slate-600 mt-1">Versioned snapshots for compliance and audit.</div>
          <div className="mt-4 flex gap-3 flex-wrap">
            <span className="px-3 py-1.5 rounded-full bg-slate-100 chip text-sm">v2026.1 (current)</span>
            <span className="px-3 py-1.5 rounded-full bg-slate-100 chip text-sm">v2025.12</span>
            <span className="px-3 py-1.5 rounded-full bg-slate-100 chip text-sm">v2025.Q4</span>
          </div>
        </section>
      </div>
    </>
  );
}
