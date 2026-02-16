import V2Header from "../components/V2Header";

export default function SLAPage() {
  const deadlines = [
    { label: "Daily pipeline delivery", date: "08 Feb 2026", time: "02:00", status: "Met" },
    { label: "Monthly submission", date: "15 Feb 2026", status: "On track" },
    { label: "Quarterly audit export", date: "31 Mar 2026", status: "Upcoming" },
  ];
  const breaches = [
    { run: "RUN-2026-02-06-0200", target: "02:00", actual: "—", impact: "Daily delivery missed" },
  ];

  return (
    <>
      <V2Header
        title="SLA & Compliance"
        subtitle="Calendar view: submission deadlines, SLA targets, breach alerts"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Calendar / deadlines */}
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="font-bold">Submission deadlines & SLA targets</div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            {deadlines.map((d) => (
              <div
                key={d.label}
                className="rounded-xl border border-slate-200 p-4"
              >
                <div className="font-semibold">{d.label}</div>
                <div className="text-sm text-slate-600 mt-1">{d.date}{d.time ? ` — ${d.time}` : ""}</div>
                <span
                  className={`inline-block mt-2 px-2 py-1 rounded-full text-xs font-semibold ${
                    d.status === "Met" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-700"
                  }`}
                >
                  {d.status}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Breach alerts */}
        <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between">
            <div className="font-bold">Breach alerts</div>
            <span className="px-2 py-1 rounded-full bg-red-100 text-ldv-red text-xs font-semibold">1 breach</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="text-left p-4 font-semibold">Run</th>
                  <th className="text-left p-4 font-semibold">Target</th>
                  <th className="text-left p-4 font-semibold">Actual</th>
                  <th className="text-left p-4 font-semibold">Impact</th>
                </tr>
              </thead>
              <tbody>
                {breaches.map((b) => (
                  <tr key={b.run} className="border-b border-slate-100">
                    <td className="p-4 font-mono text-xs">{b.run}</td>
                    <td className="p-4">{b.target}</td>
                    <td className="p-4">{b.actual}</td>
                    <td className="p-4 text-ldv-red font-medium">{b.impact}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Calendar placeholder */}
        <section className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="font-bold">Calendar view (V2)</div>
          <div className="mt-3 h-48 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500 text-sm">
            Calendar: submission deadlines and SLA windows
          </div>
        </section>
      </div>
    </>
  );
}
