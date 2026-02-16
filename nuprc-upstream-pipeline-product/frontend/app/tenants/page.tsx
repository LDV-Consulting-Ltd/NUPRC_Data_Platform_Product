import V2Header from "../components/V2Header";

export default function TenantsPage() {
  const tenants = [
    { name: "NUPRC Regulator", org: "Gov", activePipelines: 2, dataTrustAvg: 88, costUsage: "—", slaCompliance: "30/30" },
    { name: "LDV Internal", org: "LDV", activePipelines: 1, dataTrustAvg: 92, costUsage: "—", slaCompliance: "30/30" },
  ];

  return (
    <>
      <V2Header
        title="Tenants & Orgs"
        subtitle="Multi-tenant control center: active pipelines, data trust, cost, SLA compliance"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="text-sm text-slate-500">Admin (SaaS)</div>
          <div className="text-xl font-bold mt-1">Tenant cards</div>
          <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
            {tenants.map((t) => (
              <div
                key={t.name}
                className="rounded-2xl border border-slate-200 p-5 hover:border-ldv-green transition-colors"
              >
                <div className="font-bold text-lg">{t.name}</div>
                <div className="text-sm text-slate-500">{t.org}</div>
                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-xl bg-slate-50 p-3">
                    <div className="text-xs text-slate-500">Active pipelines</div>
                    <div className="font-semibold">{t.activePipelines}</div>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-3">
                    <div className="text-xs text-slate-500">Data trust avg</div>
                    <div className="font-semibold text-emerald-600">{t.dataTrustAvg}</div>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-3">
                    <div className="text-xs text-slate-500">Cost usage</div>
                    <div className="font-semibold">{t.costUsage}</div>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-3">
                    <div className="text-xs text-slate-500">SLA compliance</div>
                    <div className="font-semibold text-emerald-600">{t.slaCompliance}</div>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <button type="button" className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-sm font-semibold">
                    Settings
                  </button>
                  <button type="button" className="px-3 py-2 rounded-lg bg-ldv-green text-white text-sm font-semibold">
                    Open
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}
