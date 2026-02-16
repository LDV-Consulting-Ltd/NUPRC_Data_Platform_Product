"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/control-panel");
  }, [router]);
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 flex items-center justify-center">
      <div className="text-slate-500">Redirecting to Control Panel…</div>
    </div>
  );
}
