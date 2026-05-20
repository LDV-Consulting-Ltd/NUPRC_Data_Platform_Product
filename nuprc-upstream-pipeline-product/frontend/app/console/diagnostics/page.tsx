"use client";

import Link from "next/link";
import { Stethoscope } from "lucide-react";
import SectionHeader from "@/components/enterprise/SectionHeader";

export default function DiagnosticsPage() {
  return (
    <div className="w-full">
      <SectionHeader
        icon={Stethoscope}
        title="Run Diagnostics"
        description="Deep-dive into pipeline failures, source reachability, and step-level logs."
      />
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm max-w-2xl">
        <p className="text-slate-600 mb-4">
          Select a run from Pipeline Control or Runs, then open diagnostics for user-friendly errors and technical
          details.
        </p>
        <Link
          href="/console/pipeline"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#0f2744] text-teal-300 font-semibold text-sm hover:bg-navy-800"
        >
          Go to Pipeline Control
        </Link>
        <span className="mx-3 text-slate-300">|</span>
        <Link href="/console/runs" className="text-[#0f2744] font-semibold text-sm hover:underline">
          View run history
        </Link>
      </div>
    </div>
  );
}
