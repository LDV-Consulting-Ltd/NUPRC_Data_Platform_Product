"use client";

import { Suspense } from "react";
import { usePathname } from "next/navigation";
import ConsoleShell from "./ConsoleShell";

export default function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "/";
  if (pathname === "/" || pathname.startsWith("/showcase")) {
    return <>{children}</>;
  }
  return (
    <ConsoleShell>
      <Suspense fallback={<p className="pc-lede">Loading the workspace…</p>}>{children}</Suspense>
    </ConsoleShell>
  );
}
