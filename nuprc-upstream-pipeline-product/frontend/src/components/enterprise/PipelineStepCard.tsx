"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { CheckCircle2, XCircle, Clock, Loader2, ChevronDown, ChevronUp } from "lucide-react";

export type StepUiStatus = "waiting" | "running" | "done" | "failed";

export default function PipelineStepCard({
  index,
  title,
  description,
  icon: Icon,
  status,
  durationSeconds,
  rowsProcessed,
  filesProcessed,
  warnings,
  logMessage,
}: {
  index: number;
  title: string;
  description: string;
  icon: LucideIcon;
  status: StepUiStatus;
  durationSeconds?: number | null;
  rowsProcessed?: number;
  filesProcessed?: number;
  warnings?: number;
  logMessage?: string | null;
}) {
  const [open, setOpen] = useState(status === "running" || status === "failed");

  const border =
    status === "running"
      ? "border-teal-400 step-running"
      : status === "done"
        ? "border-emerald-300"
        : status === "failed"
          ? "border-red-300"
          : "border-slate-200";

  const StatusIcon =
    status === "done" ? CheckCircle2 : status === "failed" ? XCircle : status === "running" ? Loader2 : Clock;

  const statusColor =
    status === "done"
      ? "text-emerald-600 bg-emerald-50"
      : status === "failed"
        ? "text-red-600 bg-red-50"
        : status === "running"
          ? "text-teal-700 bg-teal-50"
          : "text-slate-500 bg-slate-100";

  return (
    <div className={`min-w-[240px] flex-1 rounded-2xl border-2 bg-white shadow-sm ${border}`}>
      <button type="button" onClick={() => setOpen(!open)} className="w-full text-left p-4 flex flex-col gap-3">
        <div className="flex items-center justify-between gap-2">
          <div className="h-11 w-11 rounded-xl bg-[#0f2744] text-teal-300 flex items-center justify-center">
            <Icon className="h-5 w-5" />
          </div>
          <span className={`text-xs font-bold uppercase px-2 py-1 rounded-full flex items-center gap-1 ${statusColor}`}>
            <StatusIcon className={`h-3.5 w-3.5 ${status === "running" ? "animate-spin" : ""}`} />
            {status}
          </span>
        </div>
        <div>
          <div className="text-xs text-slate-500 font-semibold">Step {index}</div>
          <div className="font-bold text-[#0f2744]">{title}</div>
          <p className="text-xs text-slate-500 mt-1 line-clamp-2">{description}</p>
        </div>
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>{durationSeconds != null ? `${durationSeconds}s` : "—"}</span>
          {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-slate-100 px-4 pb-4 text-sm text-slate-600 space-y-2 overflow-hidden"
          >
            <div className="grid grid-cols-2 gap-2 pt-3">
              <div className="rounded-lg bg-slate-50 p-2">
                <div className="text-xs text-slate-500">Files</div>
                <div className="font-semibold">{filesProcessed ?? "—"}</div>
              </div>
              <div className="rounded-lg bg-slate-50 p-2">
                <div className="text-xs text-slate-500">Rows</div>
                <div className="font-semibold">{rowsProcessed?.toLocaleString() ?? "—"}</div>
              </div>
            </div>
            {(warnings ?? 0) > 0 && (
              <p className="text-amber-700 text-xs font-medium">{warnings} drift warning(s)</p>
            )}
            {logMessage && <p className="text-xs font-mono bg-slate-50 p-2 rounded-lg">{logMessage}</p>}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
