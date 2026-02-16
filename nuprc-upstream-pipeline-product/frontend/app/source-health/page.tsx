import V2Header from "../components/V2Header";
import Link from "next/link";

export default function SourceHealthPage() {
  const sources = [
    { name: "Oil Production Status", latency: "1.2s", failureRate: "0%", schemaDrift: "None", status: "Healthy" },
    { name: "Gas Production Status", latency: "—", failureRate: "12%", schemaDrift: "None", status: "Degraded" },
    { name: "Rig Disposition", latency: "0.8s", failureRate: "0%", schemaDrift: "None", status: "Healthy" },
    { name: "Concession Situation", latency: "2.1s", failureRate: "0%", schemaDrift: "None", status: "Healthy" },
  ];

  return (
    <>
      <V2Header
        title="Source Health"
        subtitle="Source reliability: latency trends, failure frequency, schema drift events"
      />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Source Reliability Dashboard */}
        <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="p-4 sm:p-5 border-b border-slate-200">
            <div className="text-sm text-slate-500">Source Reliability Dashboard</div>
            <div className="text-xl font-bold mt-1">NUPRC source endpoints</div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="text-left p-4 font-semibold">Source</th>
                  <th className="text-left p-4 font-semibold">Avg Latency</th>
                  <th className="text-left p-4 font-semibold">Failure (7d)</th>
                  <th className="text-left p-4 font-semibold">Schema drift</th>
                  <th className="text-left p-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr key={s.name} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="p-4 font-semibold">{s.name}</td>
                    <td className="p-4">{s.latency}</td>
                    <td className="p-4">{s.failureRate}</td>
                    <td className="p-4">{s.schemaDrift}</td>
                    <td className="p-4">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          s.status === "Healthy" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Latency / failure trends placeholder */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <div className="font-bold">Latency trends (7d)</div>
            <div className="mt-3 h-32 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500 text-sm">
              Chart placeholder
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <div className="font-bold">Failure frequency</div>
            <div className="mt-3 h-32 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500 text-sm">
              Chart placeholder
            </div>
          </div>
        </section>

        <p className="text-sm text-slate-600">
          <Link href="/showcase/health" className="text-ldv-blue font-semibold hover:underline">Open legacy Source Health</Link>
        </p>
      </div>
    </>
  );
}
